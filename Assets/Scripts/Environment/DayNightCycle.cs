using UnityEngine;

namespace Nidelven.Environment
{
    /// <summary>
    /// Manages day/night cycle with dynamic lighting, sky colors, and fog.
    /// Compresses 24 hours into configurable game time.
    /// </summary>
    public class DayNightCycle : MonoBehaviour
    {
        [Header("Time Settings")]
        [Tooltip("Current time of day (0-24 hours)")]
        [Range(0f, 24f)]
        public float timeOfDay = 6f; // Start at 6 AM
        
        [Tooltip("Speed multiplier (1 = real time)")]
        public float timeScale = 1f / 60f; // 1 hour = 1 minute real time
        
        [Tooltip("Pause time progression")]
        public bool pauseTime = false;
        
        [Header("Sun/Moon")]
        public Light sunLight;
        public Light moonLight;
        
        [Tooltip("Sunrise time (hours)")]
        public float sunriseTime = 6f;
        
        [Tooltip("Sunset time (hours)")]
        public float sunsetTime = 18f;
        
        [Header("Colors")]
        [GradientUsage(true)]
        public Gradient skyColorGradient;
        
        [GradientUsage(true)]
        public Gradient sunColorGradient;
        
        [GradientUsage(true)]
        public Gradient fogColorGradient;
        
        [Tooltip("Base ambient intensity")]
        public float baseAmbientIntensity = 0.5f;
        
        [Header("Fog")]
        public bool updateFog = true;
        
        [Tooltip("Day fog density")]
        public float dayFogDensity = 0.001f;
        
        [Tooltip("Night fog density")]
        public float nightFogDensity = 0.005f;
        
        // Internal state
        private float currentHour = 0f;
        private float normalizedTime = 0f; // 0-1 through the day
        
        void Start()
        {
            // Initialize gradients if not set
            if (skyColorGradient == null || skyColorGradient.colorKeys.Length == 0)
            {
                CreateDefaultGradients();
            }
            
            // Find lights if not assigned
            if (sunLight == null)
            {
                sunLight = RenderSettings.sun;
            }
            
            UpdateLighting();
        }
        
        void Update()
        {
            if (!pauseTime)
            {
                AdvanceTime();
            }
            
            UpdateLighting();
            UpdateSkybox();
            UpdateFog();
        }
        
        void AdvanceTime()
        {
            timeOfDay += Time.deltaTime * timeScale;
            
            // Wrap around 24 hours
            if (timeOfDay >= 24f)
            {
                timeOfDay = 0f;
            }
            
            currentHour = timeOfDay;
            normalizedTime = timeOfDay / 24f;
        }
        
        void UpdateLighting()
        {
            if (sunLight != null)
            {
                // Calculate sun position (rotate around X axis)
                // Noon (12) = 90 degrees overhead
                // Sunrise (6) = 0 degrees horizon
                // Sunset (18) = 180 degrees horizon
                float sunAngle = ((timeOfDay - 6f) / 12f) * 180f;
                sunLight.transform.rotation = Quaternion.Euler(sunAngle, 0f, 0f);
                
                // Sun intensity based on time
                float sunIntensity = CalculateSunIntensity();
                sunLight.intensity = sunIntensity;
                
                // Sun color
                sunLight.color = sunColorGradient.Evaluate(normalizedTime);
                
                // Enable/disable sun
                sunLight.enabled = sunIntensity > 0.01f;
            }
            
            if (moonLight != null)
            {
                // Moon is opposite to sun
                float moonAngle = sunLight != null ? sunLight.transform.rotation.eulerAngles.x + 180f : 0f;
                moonLight.transform.rotation = Quaternion.Euler(moonAngle, 0f, 0f);
                
                // Moon visible when sun is down
                float moonIntensity = 1f - CalculateSunIntensity();
                moonLight.intensity = moonIntensity * 0.3f;
                moonLight.enabled = moonIntensity > 0.1f;
            }
            
            // Update ambient light
            RenderSettings.ambientIntensity = baseAmbientIntensity * (0.2f + CalculateSunIntensity() * 0.8f);
            RenderSettings.ambientLight = skyColorGradient.Evaluate(normalizedTime) * 0.5f;
        }
        
        void UpdateSkybox()
        {
            // Update sky color (requires dynamic skybox material)
            Color skyColor = skyColorGradient.Evaluate(normalizedTime);
            RenderSettings.ambientSkyColor = skyColor;
            
            // If using a procedural skybox shader, update its properties
            // This would need shader-specific implementation
        }
        
        void UpdateFog()
        {
            if (!updateFog) return;
            
            // Fog color
            Color fogColor = fogColorGradient.Evaluate(normalizedTime);
            RenderSettings.fogColor = fogColor;
            
            // Fog density (thicker at night)
            float sunIntensity = CalculateSunIntensity();
            RenderSettings.fogDensity = Mathf.Lerp(nightFogDensity, dayFogDensity, sunIntensity);
        }
        
        float CalculateSunIntensity()
        {
            // Smooth transition around sunrise/sunset
            if (timeOfDay < sunriseTime - 1f || timeOfDay > sunsetTime + 1f)
            {
                return 0f; // Night
            }
            else if (timeOfDay >= sunriseTime + 1f && timeOfDay <= sunsetTime - 1f)
            {
                return 1f; // Full day
            }
            else if (timeOfDay >= sunriseTime - 1f && timeOfDay < sunriseTime + 1f)
            {
                // Sunrise transition
                return Mathf.InverseLerp(sunriseTime - 1f, sunriseTime + 1f, timeOfDay);
            }
            else
            {
                // Sunset transition
                return 1f - Mathf.InverseLerp(sunsetTime - 1f, sunsetTime + 1f, timeOfDay);
            }
        }
        
        void CreateDefaultGradients()
        {
            // Sky color gradient (midnight to midnight)
            Gradient skyGradient = new Gradient();
            GradientColorKey[] skyColors = new GradientColorKey[5];
            skyColors[0] = new GradientColorKey(new Color(0.05f, 0.05f, 0.15f), 0f);    // Midnight
            skyColors[1] = new GradientColorKey(new Color(0.3f, 0.2f, 0.4f), 0.2f);   // Dawn
            skyColors[2] = new GradientColorKey(new Color(0.5f, 0.7f, 0.9f), 0.5f);   // Noon
            skyColors[3] = new GradientColorKey(new Color(0.4f, 0.3f, 0.5f), 0.8f);   // Dusk
            skyColors[4] = new GradientColorKey(new Color(0.05f, 0.05f, 0.15f), 1f);   // Midnight
            skyGradient.colorKeys = skyColors;
            skyColorGradient = skyGradient;
            
            // Sun color gradient
            Gradient sunGradient = new Gradient();
            GradientColorKey[] sunColors = new GradientColorKey[5];
            sunColors[0] = new GradientColorKey(new Color(1f, 0.9f, 0.7f), 0f);      // Sunrise
            sunColors[1] = new GradientColorKey(new Color(1f, 1f, 0.9f), 0.25f);    // Morning
            sunColors[2] = new GradientColorKey(new Color(1f, 1f, 1f), 0.5f);       // Noon
            sunColors[3] = new GradientColorKey(new Color(1f, 0.9f, 0.7f), 0.75f);   // Afternoon
            sunColors[4] = new GradientColorKey(new Color(1f, 0.6f, 0.4f), 1f);       // Sunset
            sunGradient.colorKeys = sunColors;
            sunColorGradient = sunGradient;
            
            // Fog color gradient
            Gradient fogGradient = new Gradient();
            GradientColorKey[] fogColors = new GradientColorKey[5];
            fogColors[0] = new GradientColorKey(new Color(0.1f, 0.1f, 0.2f), 0f);    // Night
            fogColors[1] = new GradientColorKey(new Color(0.4f, 0.3f, 0.4f), 0.2f);   // Dawn
            fogColors[2] = new GradientColorKey(new Color(0.7f, 0.8f, 0.9f), 0.5f);   // Day
            fogColors[3] = new GradientColorKey(new Color(0.5f, 0.4f, 0.4f), 0.8f);   // Dusk
            fogColors[4] = new GradientColorKey(new Color(0.1f, 0.1f, 0.2f), 1f);    // Night
            fogGradient.colorKeys = fogColors;
            fogColorGradient = fogGradient;
        }
        
        /// <summary>
        /// Set time of day (0-24 hours).
        /// </summary>
        public void SetTime(float hour)
        {
            timeOfDay = Mathf.Clamp(hour, 0f, 24f);
        }
        
        /// <summary>
        /// Set time scale (1 = real time, 0.0167 = 1 hour per minute).
        /// </summary>
        public void SetTimeScale(float scale)
        {
            timeScale = Mathf.Max(0f, scale);
        }
        
        /// <summary>
        /// Toggle time progression.
        /// </summary>
        public void TogglePause()
        {
            pauseTime = !pauseTime;
        }
        
        /// <summary>
        /// Get current time as formatted string.
        /// </summary>
        public string GetFormattedTime()
        {
            int hours = Mathf.FloorToInt(timeOfDay);
            int minutes = Mathf.FloorToInt((timeOfDay - hours) * 60f);
            string ampm = hours < 12 ? "AM" : "PM";
            int displayHour = hours % 12;
            if (displayHour == 0) displayHour = 12;
            return $"{displayHour}:{minutes:00} {ampm}";
        }
        
#if UNITY_EDITOR
        void OnGUI()
        {
            // Debug display (editor only)
            if (GUILayout.Button("Toggle Time Pause"))
            {
                TogglePause();
            }
            
            GUILayout.Label($"Time: {GetFormattedTime()}");
            GUILayout.Label($"Scale: {timeScale:F4}x");
        }
#endif
    }
}
