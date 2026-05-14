using UnityEngine;

namespace Nidelven.Environment
{
    /// <summary>
    /// Spawns and manages particle effects along the river:
    /// splash (paddle/rapids), foam (fast flow areas), and mist (waterfalls/morning).
    /// Attaches to the RiverController GameObject or a child.
    /// </summary>
    public class RiverParticles : MonoBehaviour
    {
        [Header("References")]
        public RiverController river;
        public Transform playerTransform;

        [Header("Splash")]
        [Tooltip("Splash particle prefab (or auto-created if null)")]
        public ParticleSystem splashPrefab;
        [Tooltip("Splash intensity multiplier")]
        public float splashIntensity = 1f;

        [Header("Foam")]
        [Tooltip("Foam particle prefab (or auto-created if null)")]
        public ParticleSystem foamPrefab;
        [Tooltip("Flow speed threshold to emit foam")]
        public float foamSpeedThreshold = 2f;
        [Tooltip("Max foam emitters along the river")]
        public int maxFoamEmitters = 5;

        [Header("Mist")]
        [Tooltip("Mist particle prefab (or auto-created if null)")]
        public ParticleSystem mistPrefab;
        [Tooltip("Height drop threshold to spawn mist (waterfall detection)")]
        public float mistHeightDropThreshold = 3f;
        [Tooltip("Max mist emitters")]
        public int maxMistEmitters = 3;

        [Header("Performance")]
        [Tooltip("Max distance from player to emit particles")]
        public float activationDistance = 100f;

        // Runtime systems
        private ParticleSystem splashSystem;
        private ParticleSystem[] foamSystems;
        private ParticleSystem[] mistSystems;
        private Vector3[] foamPositions;
        private Vector3[] mistPositions;
        private float activationDistSqr;

        void Start()
        {
            activationDistSqr = activationDistance * activationDistance;

            if (river == null)
                river = GetComponentInParent<RiverController>();

            CreateSplashSystem();
            FindFoamLocations();
            FindMistLocations();
            CreateFoamSystems();
            CreateMistSystems();
        }

        void Update()
        {
            if (playerTransform == null) return;

            UpdateSplash();
            UpdateDistanceCulling();
        }

        /// <summary>
        /// Trigger a splash burst at a world position (e.g., paddle stroke).
        /// </summary>
        public void EmitSplash(Vector3 position, float intensity = 1f)
        {
            if (splashSystem == null) return;

            splashSystem.transform.position = position;
            var emission = splashSystem.emission;
            int count = Mathf.RoundToInt(10 * intensity * splashIntensity);
            splashSystem.Emit(count);
        }

        void CreateSplashSystem()
        {
            if (splashPrefab != null)
            {
                splashSystem = Instantiate(splashPrefab, transform);
            }
            else
            {
                GameObject go = new GameObject("SplashParticles");
                go.transform.SetParent(transform);
                splashSystem = go.AddComponent<ParticleSystem>();
                ConfigureSplash(splashSystem);
            }

            // Splash is burst-only, no continuous emission
            var emission = splashSystem.emission;
            emission.enabled = false;
        }

        void ConfigureSplash(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = 0.8f;
            main.startSpeed = new ParticleSystem.MinMaxCurve(2f, 5f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.05f, 0.15f);
            main.startColor = new Color(0.8f, 0.9f, 1f, 0.7f);
            main.gravityModifier = 1f;
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 200;

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Hemisphere;
            shape.radius = 0.5f;

            var colorOverLifetime = ps.colorOverLifetime;
            colorOverLifetime.enabled = true;
            Gradient grad = new Gradient();
            grad.SetKeys(
                new GradientColorKey[] {
                    new GradientColorKey(Color.white, 0f),
                    new GradientColorKey(Color.white, 1f)
                },
                new GradientAlphaKey[] {
                    new GradientAlphaKey(0.7f, 0f),
                    new GradientAlphaKey(0f, 1f)
                }
            );
            colorOverLifetime.color = grad;

            var sizeOverLifetime = ps.sizeOverLifetime;
            sizeOverLifetime.enabled = true;
            sizeOverLifetime.size = new ParticleSystem.MinMaxCurve(1f,
                AnimationCurve.Linear(0, 1, 1, 0.2f));
        }

        void FindFoamLocations()
        {
            if (river == null || river.riverPath.Count < 2 || river.flowSpeeds.Count < 2)
            {
                foamPositions = new Vector3[0];
                return;
            }

            // Find points where flow speed exceeds threshold (rapids)
            var candidates = new System.Collections.Generic.List<Vector3>();
            for (int i = 0; i < river.flowSpeeds.Count; i++)
            {
                if (river.flowSpeeds[i] >= foamSpeedThreshold)
                {
                    candidates.Add(river.riverPath[i]);
                }
            }

            // Limit to maxFoamEmitters, evenly spaced among candidates
            int count = Mathf.Min(candidates.Count, maxFoamEmitters);
            foamPositions = new Vector3[count];
            if (count == 0) return;

            float step = candidates.Count / (float)count;
            for (int i = 0; i < count; i++)
            {
                int idx = Mathf.Min(Mathf.FloorToInt(i * step), candidates.Count - 1);
                foamPositions[i] = candidates[idx];
            }
        }

        void FindMistLocations()
        {
            if (river == null || river.riverPath.Count < 3)
            {
                mistPositions = new Vector3[0];
                return;
            }

            // Find points with large height drops (waterfalls/rapids)
            var candidates = new System.Collections.Generic.List<Vector3>();
            for (int i = 1; i < river.riverPath.Count; i++)
            {
                float drop = river.riverPath[i - 1].y - river.riverPath[i].y;
                if (drop >= mistHeightDropThreshold)
                {
                    candidates.Add(river.riverPath[i]);
                }
            }

            int count = Mathf.Min(candidates.Count, maxMistEmitters);
            mistPositions = new Vector3[count];
            if (count == 0) return;

            float step = candidates.Count / (float)count;
            for (int i = 0; i < count; i++)
            {
                int idx = Mathf.Min(Mathf.FloorToInt(i * step), candidates.Count - 1);
                mistPositions[i] = candidates[idx];
            }
        }

        void CreateFoamSystems()
        {
            foamSystems = new ParticleSystem[foamPositions.Length];
            for (int i = 0; i < foamPositions.Length; i++)
            {
                ParticleSystem ps;
                if (foamPrefab != null)
                {
                    ps = Instantiate(foamPrefab, foamPositions[i], Quaternion.identity, transform);
                }
                else
                {
                    GameObject go = new GameObject($"FoamEmitter_{i}");
                    go.transform.SetParent(transform);
                    go.transform.position = foamPositions[i];
                    ps = go.AddComponent<ParticleSystem>();
                    ConfigureFoam(ps);
                }
                foamSystems[i] = ps;
            }
        }

        void ConfigureFoam(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = new ParticleSystem.MinMaxCurve(1f, 3f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.1f, 0.5f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.3f, 0.8f);
            main.startColor = new Color(1f, 1f, 1f, 0.4f);
            main.gravityModifier = -0.02f; // Slight upward drift
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 50;

            var emission = ps.emission;
            emission.rateOverTime = 8f;

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Circle;
            shape.radius = 3f;

            var colorOverLifetime = ps.colorOverLifetime;
            colorOverLifetime.enabled = true;
            Gradient grad = new Gradient();
            grad.SetKeys(
                new GradientColorKey[] {
                    new GradientColorKey(Color.white, 0f),
                    new GradientColorKey(Color.white, 1f)
                },
                new GradientAlphaKey[] {
                    new GradientAlphaKey(0f, 0f),
                    new GradientAlphaKey(0.4f, 0.3f),
                    new GradientAlphaKey(0f, 1f)
                }
            );
            colorOverLifetime.color = grad;
        }

        void CreateMistSystems()
        {
            mistSystems = new ParticleSystem[mistPositions.Length];
            for (int i = 0; i < mistPositions.Length; i++)
            {
                ParticleSystem ps;
                if (mistPrefab != null)
                {
                    ps = Instantiate(mistPrefab, mistPositions[i], Quaternion.identity, transform);
                }
                else
                {
                    GameObject go = new GameObject($"MistEmitter_{i}");
                    go.transform.SetParent(transform);
                    go.transform.position = mistPositions[i];
                    ps = go.AddComponent<ParticleSystem>();
                    ConfigureMist(ps);
                }
                mistSystems[i] = ps;
            }
        }

        void ConfigureMist(ParticleSystem ps)
        {
            var main = ps.main;
            main.startLifetime = new ParticleSystem.MinMaxCurve(3f, 6f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(0.2f, 0.8f);
            main.startSize = new ParticleSystem.MinMaxCurve(2f, 5f);
            main.startColor = new Color(0.9f, 0.95f, 1f, 0.2f);
            main.gravityModifier = -0.05f; // Rises slowly
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 30;

            var emission = ps.emission;
            emission.rateOverTime = 3f;

            var shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(8f, 1f, 4f);

            var colorOverLifetime = ps.colorOverLifetime;
            colorOverLifetime.enabled = true;
            Gradient grad = new Gradient();
            grad.SetKeys(
                new GradientColorKey[] {
                    new GradientColorKey(new Color(0.9f, 0.95f, 1f), 0f),
                    new GradientColorKey(new Color(0.9f, 0.95f, 1f), 1f)
                },
                new GradientAlphaKey[] {
                    new GradientAlphaKey(0f, 0f),
                    new GradientAlphaKey(0.2f, 0.2f),
                    new GradientAlphaKey(0.2f, 0.7f),
                    new GradientAlphaKey(0f, 1f)
                }
            );
            colorOverLifetime.color = grad;

            var sizeOverLifetime = ps.sizeOverLifetime;
            sizeOverLifetime.enabled = true;
            sizeOverLifetime.size = new ParticleSystem.MinMaxCurve(1f,
                AnimationCurve.Linear(0, 0.5f, 1, 1.5f));
        }

        void UpdateSplash()
        {
            // Splash is triggered externally via EmitSplash() — nothing continuous here
        }

        void UpdateDistanceCulling()
        {
            Vector3 playerPos = playerTransform.position;

            // Enable/disable foam systems based on distance
            for (int i = 0; i < foamSystems.Length; i++)
            {
                if (foamSystems[i] == null) continue;
                float distSqr = (foamPositions[i] - playerPos).sqrMagnitude;
                var emission = foamSystems[i].emission;
                emission.enabled = distSqr <= activationDistSqr;
            }

            // Enable/disable mist systems based on distance
            for (int i = 0; i < mistSystems.Length; i++)
            {
                if (mistSystems[i] == null) continue;
                float distSqr = (mistPositions[i] - playerPos).sqrMagnitude;
                var emission = mistSystems[i].emission;
                emission.enabled = distSqr <= activationDistSqr;
            }
        }
    }
}
