using UnityEngine;
using System.IO;

namespace Nidelven.Environment
{
    /// <summary>
    /// Loads weather data from StreamingAssets/weather_data.json and applies
    /// atmospheric conditions: fog, rain particles, wind, cloud cover,
    /// river mist, and lighting adjustments.
    ///
    /// Data sources (via Python pipeline):
    /// - MET Norway Locationforecast 2.0 (current weather)
    /// - MET Norway Frost API (historical observations)
    /// - Climate normals 1991-2020 (seasonal fallback)
    /// </summary>
    public class WeatherSystem : MonoBehaviour
    {
        [Header("References")]
        public DayNightCycle dayNightCycle;
        public RiverController river;
        public RiverParticles riverParticles;
        public Light sunLight;

        [Header("Weather Data")]
        [Tooltip("Load weather from StreamingAssets/weather_data.json")]
        public bool loadFromFile = true;

        [Tooltip("Fallback month if no data file (1-12, 0=current)")]
        [Range(0, 12)]
        public int fallbackMonth = 0;

        [Header("Rain")]
        public ParticleSystem rainParticleSystem;
        [Tooltip("Auto-create rain particles if none assigned")]
        public bool autoCreateRain = true;

        [Header("Wind")]
        [Tooltip("Wind affects vegetation sway (apply to shader)")]
        public float windMultiplier = 1f;

        [Header("Atmosphere")]
        [Tooltip("Transition speed for weather changes")]
        public float transitionSpeed = 0.5f;

        // Current weather state
        private WeatherState currentState;
        private WeatherState targetState;
        private WeatherData loadedData;

        // Rain system
        private ParticleSystem rainSystem;

        [System.Serializable]
        public class WeatherState
        {
            public float temperature;
            public float windSpeed;
            public float windDirectionX;
            public float windDirectionZ;
            public float cloudCover;
            public float fogDensity;
            public Color fogColor = new Color(0.7f, 0.75f, 0.8f);
            public float rainIntensity;
            public float sunIntensityMultiplier = 1f;
            public float ambientIntensityMultiplier = 1f;
            public float waterWaveHeight = 0.3f;
            public float waterWaveSpeed = 2f;
            public bool riverMistEnabled;
            public float riverMistDensity;
            public float sunriseHour = 6f;
            public float sunsetHour = 18f;
        }

        // JSON deserialization classes
        [System.Serializable]
        private class WeatherData
        {
            public string generated_at;
            public WeatherLocation location;
            public WeatherEntry seasonal;
            public WeatherEntry current;
            public WeatherEntry historical;
            public WeatherEntry active;
            public UnityParams unity_params;
        }

        [System.Serializable]
        private class WeatherLocation
        {
            public float lat;
            public float lon;
            public string name;
        }

        [System.Serializable]
        private class WeatherEntry
        {
            public string source;
            public float temperature_celsius;
            public float wind_speed_ms;
            public float wind_direction_deg;
            public float cloud_cover_fraction;
            public float rain_probability;
            public float fog_probability;
            public float river_mist_probability;
            public float sunrise_hour;
            public float sunset_hour;
            public string description;
        }

        [System.Serializable]
        private class UnityParams
        {
            public float sunrise_hour;
            public float sunset_hour;
            public float fog_density;
            public float fog_color_r;
            public float fog_color_g;
            public float fog_color_b;
            public float rain_intensity;
            public int rain_particle_rate;
            public float wind_speed;
            public float wind_direction_x;
            public float wind_direction_z;
            public float water_wave_height;
            public float water_wave_speed;
            public bool river_mist_enabled;
            public float river_mist_density;
            public float cloud_cover;
            public float sun_intensity_multiplier;
            public float ambient_intensity_multiplier;
            public float temperature_celsius;
            public bool snow_on_ground;
            public bool breath_visible;
        }

        void Start()
        {
            currentState = new WeatherState();
            targetState = new WeatherState();

            if (loadFromFile)
            {
                LoadWeatherData();
            }
            else
            {
                ApplySeasonalDefaults();
            }

            SetupRainSystem();
            ApplyWeatherImmediate();
        }

        void Update()
        {
            LerpWeatherState();
            ApplyWeatherEffects();
        }

        void LoadWeatherData()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "weather_data.json");

            if (!File.Exists(path))
            {
                Debug.Log("weather_data.json not found, using seasonal defaults");
                ApplySeasonalDefaults();
                return;
            }

            try
            {
                string json = File.ReadAllText(path);
                loadedData = JsonUtility.FromJson<WeatherData>(json);

                if (loadedData?.unity_params != null)
                {
                    ApplyUnityParams(loadedData.unity_params);
                    string source = loadedData.active?.source ?? "unknown";
                    float temp = loadedData.active?.temperature_celsius ?? 0;
                    Debug.Log($"Weather loaded: {source}, {temp}°C");
                }
                else
                {
                    ApplySeasonalDefaults();
                }
            }
            catch (System.Exception e)
            {
                Debug.LogWarning($"Failed to parse weather_data.json: {e.Message}");
                ApplySeasonalDefaults();
            }
        }

        void ApplyUnityParams(UnityParams p)
        {
            targetState.sunriseHour = p.sunrise_hour;
            targetState.sunsetHour = p.sunset_hour;
            targetState.fogDensity = p.fog_density;
            targetState.fogColor = new Color(p.fog_color_r, p.fog_color_g, p.fog_color_b);
            targetState.rainIntensity = p.rain_intensity;
            targetState.windSpeed = p.wind_speed;
            targetState.windDirectionX = p.wind_direction_x;
            targetState.windDirectionZ = p.wind_direction_z;
            targetState.waterWaveHeight = p.water_wave_height;
            targetState.waterWaveSpeed = p.water_wave_speed;
            targetState.riverMistEnabled = p.river_mist_enabled;
            targetState.riverMistDensity = p.river_mist_density;
            targetState.cloudCover = p.cloud_cover;
            targetState.sunIntensityMultiplier = p.sun_intensity_multiplier;
            targetState.ambientIntensityMultiplier = p.ambient_intensity_multiplier;
            targetState.temperature = p.temperature_celsius;
        }

        void ApplySeasonalDefaults()
        {
            // May defaults (southern Norway late spring)
            int month = fallbackMonth > 0 ? fallbackMonth : System.DateTime.Now.Month;

            // Approximate seasonal values
            float[] temps = { -2, -1.5f, 1.5f, 6, 11, 15, 17, 16, 12, 7, 3, -0.5f };
            float[] winds = { 2.5f, 2.5f, 2.8f, 2.5f, 2.2f, 2.0f, 1.8f, 1.9f, 2.3f, 2.8f, 3.0f, 2.8f };
            float[] clouds = { 0.75f, 0.63f, 0.63f, 0.63f, 0.63f, 0.63f, 0.63f, 0.63f, 0.63f, 0.75f, 0.75f, 0.75f };

            int idx = Mathf.Clamp(month - 1, 0, 11);

            targetState.temperature = temps[idx];
            targetState.windSpeed = winds[idx];
            targetState.cloudCover = clouds[idx];
            targetState.fogDensity = 0.005f + clouds[idx] * 0.01f;
            targetState.fogColor = new Color(0.7f, 0.75f, 0.8f);
            targetState.rainIntensity = 0f;
            targetState.sunIntensityMultiplier = 1f - clouds[idx] * 0.5f;
            targetState.ambientIntensityMultiplier = 0.6f + clouds[idx] * 0.4f;
            targetState.waterWaveHeight = 0.1f + winds[idx] * 0.05f;
            targetState.waterWaveSpeed = 1f + winds[idx] * 0.3f;
            targetState.riverMistEnabled = month >= 4 && month <= 5 || month >= 9 && month <= 10;
            targetState.riverMistDensity = targetState.riverMistEnabled ? 0.3f : 0f;

            // Daylight hours for 58.5°N
            float[] daylight = { 6.5f, 8.5f, 11f, 14f, 16.5f, 18.5f, 18f, 15.5f, 12.5f, 10f, 7.5f, 6f };
            targetState.sunriseHour = 12f - daylight[idx] / 2f;
            targetState.sunsetHour = 12f + daylight[idx] / 2f;
        }

        void SetupRainSystem()
        {
            if (rainParticleSystem != null)
            {
                rainSystem = rainParticleSystem;
            }
            else if (autoCreateRain)
            {
                GameObject go = new GameObject("RainSystem");
                go.transform.SetParent(transform);
                go.transform.localPosition = Vector3.up * 50f;
                rainSystem = go.AddComponent<ParticleSystem>();
                ConfigureRain(rainSystem);
            }
        }

        void ConfigureRain(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = 2f;
            main.startSpeed = new ParticleSystem.MinMaxCurve(8f, 12f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.02f, 0.05f);
            main.startColor = new Color(0.7f, 0.75f, 0.85f, 0.4f);
            main.gravityModifier = 1.5f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 5000;

            var emission = ps.emission;
            emission.rateOverTime = 0; // Controlled dynamically

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(60f, 1f, 60f);

            var renderer = ps.GetComponent<ParticleSystemRenderer>();
            renderer.renderMode = ParticleSystemRenderMode.Stretch;
            renderer.lengthScale = 3f;
        }

        void LerpWeatherState()
        {
            float t = transitionSpeed * Time.deltaTime;

            currentState.temperature = Mathf.Lerp(currentState.temperature, targetState.temperature, t);
            currentState.windSpeed = Mathf.Lerp(currentState.windSpeed, targetState.windSpeed, t);
            currentState.windDirectionX = Mathf.Lerp(currentState.windDirectionX, targetState.windDirectionX, t);
            currentState.windDirectionZ = Mathf.Lerp(currentState.windDirectionZ, targetState.windDirectionZ, t);
            currentState.cloudCover = Mathf.Lerp(currentState.cloudCover, targetState.cloudCover, t);
            currentState.fogDensity = Mathf.Lerp(currentState.fogDensity, targetState.fogDensity, t);
            currentState.fogColor = Color.Lerp(currentState.fogColor, targetState.fogColor, t);
            currentState.rainIntensity = Mathf.Lerp(currentState.rainIntensity, targetState.rainIntensity, t);
            currentState.sunIntensityMultiplier = Mathf.Lerp(currentState.sunIntensityMultiplier, targetState.sunIntensityMultiplier, t);
            currentState.ambientIntensityMultiplier = Mathf.Lerp(currentState.ambientIntensityMultiplier, targetState.ambientIntensityMultiplier, t);
            currentState.waterWaveHeight = Mathf.Lerp(currentState.waterWaveHeight, targetState.waterWaveHeight, t);
            currentState.waterWaveSpeed = Mathf.Lerp(currentState.waterWaveSpeed, targetState.waterWaveSpeed, t);
            currentState.riverMistDensity = Mathf.Lerp(currentState.riverMistDensity, targetState.riverMistDensity, t);
            currentState.sunriseHour = targetState.sunriseHour;
            currentState.sunsetHour = targetState.sunsetHour;
            currentState.riverMistEnabled = targetState.riverMistEnabled;
        }

        void ApplyWeatherImmediate()
        {
            currentState.temperature = targetState.temperature;
            currentState.windSpeed = targetState.windSpeed;
            currentState.windDirectionX = targetState.windDirectionX;
            currentState.windDirectionZ = targetState.windDirectionZ;
            currentState.cloudCover = targetState.cloudCover;
            currentState.fogDensity = targetState.fogDensity;
            currentState.fogColor = targetState.fogColor;
            currentState.rainIntensity = targetState.rainIntensity;
            currentState.sunIntensityMultiplier = targetState.sunIntensityMultiplier;
            currentState.ambientIntensityMultiplier = targetState.ambientIntensityMultiplier;
            currentState.waterWaveHeight = targetState.waterWaveHeight;
            currentState.waterWaveSpeed = targetState.waterWaveSpeed;
            currentState.riverMistDensity = targetState.riverMistDensity;
            currentState.sunriseHour = targetState.sunriseHour;
            currentState.sunsetHour = targetState.sunsetHour;
            currentState.riverMistEnabled = targetState.riverMistEnabled;

            ApplyWeatherEffects();
        }

        void ApplyWeatherEffects()
        {
            // Fog
            RenderSettings.fog = currentState.fogDensity > 0.001f;
            RenderSettings.fogDensity = currentState.fogDensity;
            RenderSettings.fogColor = currentState.fogColor;

            // Sun intensity
            if (sunLight != null)
            {
                sunLight.intensity = Mathf.Clamp(sunLight.intensity * currentState.sunIntensityMultiplier, 0f, 2f);
            }

            // Day/Night cycle sync
            if (dayNightCycle != null)
            {
                dayNightCycle.sunriseTime = currentState.sunriseHour;
                dayNightCycle.sunsetTime = currentState.sunsetHour;
            }

            // Rain particles
            if (rainSystem != null)
            {
                var emission = rainSystem.emission;
                emission.rateOverTime = currentState.rainIntensity * 500f;

                // Wind affects rain direction
                var velocityOverLifetime = rainSystem.velocityOverLifetime;
                velocityOverLifetime.enabled = currentState.windSpeed > 1f;
                if (currentState.windSpeed > 1f)
                {
                    velocityOverLifetime.x = currentState.windDirectionX * currentState.windSpeed * windMultiplier;
                    velocityOverLifetime.z = currentState.windDirectionZ * currentState.windSpeed * windMultiplier;
                }
            }

            // Water shader — wind affects waves
            if (river != null && river.GetComponent<MeshRenderer>() != null)
            {
                var mat = river.GetComponent<MeshRenderer>().sharedMaterial;
                if (mat != null)
                {
                    mat.SetFloat("_WaveHeight", currentState.waterWaveHeight);
                    mat.SetFloat("_WaveSpeed", currentState.waterWaveSpeed);
                }
            }

            // Wind vector for vegetation shader (global)
            Shader.SetGlobalVector("_WindDirection",
                new Vector4(currentState.windDirectionX, 0, currentState.windDirectionZ, currentState.windSpeed));
        }

        /// <summary>
        /// Get current weather state for other systems to query.
        /// </summary>
        public WeatherState GetCurrentWeather() => currentState;

        /// <summary>
        /// Get the loaded seasonal data description.
        /// </summary>
        public string GetWeatherDescription()
        {
            if (loadedData?.active != null)
                return loadedData.active.description ?? $"{currentState.temperature:F0}°C";
            return $"{currentState.temperature:F0}°C";
        }

        /// <summary>
        /// Force reload weather data from file.
        /// </summary>
        public void ReloadWeather()
        {
            LoadWeatherData();
        }

        /// <summary>
        /// Set weather for a specific month (useful for time-of-year selector).
        /// </summary>
        public void SetMonth(int month)
        {
            fallbackMonth = Mathf.Clamp(month, 1, 12);
            ApplySeasonalDefaults();
        }
    }
}
