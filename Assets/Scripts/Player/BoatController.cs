using UnityEngine;
using Nidelven.Environment;
using Nidelven.Core;

namespace Nidelven.Player
{
    /// <summary>
    /// Physics-based boat controller with buoyancy and paddle mechanics.
    /// Boat responds to river current and player input.
    /// </summary>
    [RequireComponent(typeof(Rigidbody))]
    public class BoatController : MonoBehaviour
    {
        [Header("River Reference")]
        public RiverController river;
        public TerrainGenerator terrain;
        public RiverParticles riverParticles;
        
        [Header("Physics")]
        [Tooltip("Boat mass in kg")]
        public float boatMass = 80f;
        
        [Tooltip("Buoyancy force multiplier")]
        public float buoyancyForce = 10f;
        
        [Tooltip("Water drag coefficient")]
        public float waterDrag = 2f;
        
        [Tooltip("Angular drag in water")]
        public float waterAngularDrag = 1f;
        
        [Header("Paddle Mechanics")]
        [Tooltip("Force per paddle stroke (Newtons)")]
        public float paddleForce = 40f;
        
        [Tooltip("Turning torque per stroke")]
        public float turnTorque = 15f;
        
        [Tooltip("Minimum seconds between paddle strokes")]
        public float strokeCooldown = 0.4f;
        
        [Tooltip("Maximum boat speed (m/s) from paddling alone")]
        public float maxPaddleSpeed = 5f;
        
        [Tooltip("Sprint speed multiplier")]
        public float sprintMultiplier = 1.6f;
        
        [Tooltip("Stamina for sprinting")]
        public float maxStamina = 100f;
        
        [Tooltip("Stamina drain rate while sprinting")]
        public float staminaDrain = 25f;
        
        [Tooltip("Stamina recovery rate when resting")]
        public float staminaRecover = 15f;
        
        [Tooltip("Recovery delay after stamina depletion (seconds)")]
        public float staminaRecoveryDelay = 2f;
        
        [Header("Vessel Types")]
        public VesselType vesselType = VesselType.Kayak;
        
        [Header("Stability")]
        [Tooltip("Righting torque when tilted")]
        public float stabilityTorque = 5f;
        
        [Tooltip("Max tilt angle before capsizing")]
        public float maxTiltAngle = 60f;
        
        // Internal state
        private Rigidbody rb;
        private float currentStamina;
        private bool isCapsized = false;
        private float timeSinceLastStroke = 0f;
        private float staminaDepletedTimer = 0f;
        private bool staminaDepleted = false;
        
        // Water level at current position
        private float waterLevel = 0f;
        private float waterFlowSpeed = 0f;
        private Vector3 waterFlowDirection = Vector3.forward;
        
        // Buoyancy points (simplified as single center)
        private Vector3 buoyancyCenter = Vector3.zero;
        
        // Achievement tracking
        private float totalDistance = 0f;
        private Vector3 lastAchievementPos;
        private bool firstJourneyUnlocked = false;
        
        public enum VesselType
        {
            Kayak,    // Fast, less stable
            Canoe,    // Balanced
            Raft      // Slow, very stable
        }
        
        void Awake()
        {
            rb = GetComponent<Rigidbody>();
            rb.mass = boatMass;
            rb.useGravity = true;
            rb.interpolation = RigidbodyInterpolation.Interpolate;
            
            currentStamina = maxStamina;
            lastAchievementPos = transform.position;
            ApplyVesselStats();
        }
        
        void ApplyVesselStats()
        {
            switch (vesselType)
            {
                case VesselType.Kayak:
                    paddleForce = 50f;
                    turnTorque = 20f;
                    stabilityTorque = 3f;
                    waterDrag = 1.5f;
                    maxPaddleSpeed = 6f;
                    strokeCooldown = 0.35f;
                    break;
                    
                case VesselType.Canoe:
                    paddleForce = 40f;
                    turnTorque = 15f;
                    stabilityTorque = 5f;
                    waterDrag = 2f;
                    maxPaddleSpeed = 5f;
                    strokeCooldown = 0.45f;
                    break;
                    
                case VesselType.Raft:
                    paddleForce = 25f;
                    turnTorque = 8f;
                    stabilityTorque = 10f;
                    waterDrag = 3f;
                    maxPaddleSpeed = 3f;
                    strokeCooldown = 0.6f;
                    break;
            }
        }
        
        void FixedUpdate()
        {
            UpdateWaterData();
            ApplyBuoyancy();
            ApplyWaterDrag();
            ApplyRiverCurrent();
            ApplyStability();
            CheckCapsize();
        }
        
        void Update()
        {
            HandleInput();
            RecoverStamina();
            timeSinceLastStroke += Time.deltaTime;
            TrackAchievements();
        }
        
        void TrackAchievements()
        {
            float frameDist = Vector3.Distance(transform.position, lastAchievementPos);
            totalDistance += frameDist;
            lastAchievementPos = transform.position;
            
            // First Journey: travel 100m
            if (!firstJourneyUnlocked && totalDistance > 100f)
            {
                firstJourneyUnlocked = true;
                if (SteamManager.Instance != null)
                    SteamManager.Instance.UnlockAchievement(SteamManager.Achievements.FIRST_JOURNEY);
            }
            
            // 10km achievement
            if (totalDistance > 10000f)
            {
                if (SteamManager.Instance != null)
                    SteamManager.Instance.UnlockAchievement(SteamManager.Achievements.COMPLETE_10KM);
            }
            
            // Speed demon: > 8 m/s
            if (rb.linearVelocity.magnitude > 8f)
            {
                if (SteamManager.Instance != null)
                    SteamManager.Instance.UnlockAchievement(SteamManager.Achievements.SPEED_DEMON);
            }
        }
        
        void UpdateWaterData()
        {
            if (river != null)
            {
                // Get closest point on river
                float progress = river.GetClosestProgress(transform.position);
                
                // Get water level at position
                waterLevel = river.GetPositionOnRiver(progress).y;
                waterFlowSpeed = river.GetFlowSpeedAt(progress);
                waterFlowDirection = river.GetForwardOnRiver(progress);
            }
            else if (terrain != null)
            {
                // Fallback: water level is terrain height minus offset
                waterLevel = terrain.GetHeightAt(transform.position) - 1f;
            }
        }
        
        void ApplyBuoyancy()
        {
            float submersion = waterLevel - (transform.position.y + buoyancyCenter.y);
            
            if (submersion > 0)
            {
                // Apply upward buoyancy force
                float force = submersion * buoyancyForce * Physics.gravity.magnitude;
                Vector3 buoyancyForceVector = Vector3.up * force;
                rb.AddForceAtPosition(buoyancyForceVector, transform.TransformPoint(buoyancyCenter));
            }
        }
        
        void ApplyWaterDrag()
        {
            if (transform.position.y < waterLevel + 0.5f)
            {
                // Linear drag
                rb.AddForce(-rb.linearVelocity * waterDrag * rb.mass);
                
                // Angular drag
                rb.angularDamping = waterAngularDrag;
            }
            else
            {
                rb.angularDamping = 0.05f;
            }
        }
        
        void ApplyRiverCurrent()
        {
            if (river == null || isCapsized) return;
            
            // Only apply current if in water
            if (transform.position.y < waterLevel + 0.5f)
            {
                // Apply force in flow direction
                Vector3 currentForce = waterFlowDirection * waterFlowSpeed * rb.mass * 0.5f;
                rb.AddForce(currentForce);
            }
        }
        
        void ApplyStability()
        {
            if (isCapsized) return;
            
            // Calculate tilt
            float tiltAngle = Vector3.Angle(transform.up, Vector3.up);
            
            if (tiltAngle > 5f)
            {
                // Apply righting torque
                Vector3 rightingAxis = Vector3.Cross(transform.up, Vector3.up);
                float rightingForce = tiltAngle / maxTiltAngle * stabilityTorque * rb.mass;
                rb.AddTorque(rightingAxis * rightingForce);
            }
        }
        
        void HandleInput()
        {
            if (isCapsized)
            {
                // Recovery input
                if (Input.GetKeyDown(KeyCode.Space))
                {
                    AttemptRecovery();
                }
                return;
            }
            
            // Paddle forward
            if (Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow))
            {
                PaddleForward();
            }
            
            // Paddle backward
            if (Input.GetKeyDown(KeyCode.S) || Input.GetKeyDown(KeyCode.DownArrow))
            {
                PaddleBackward();
            }
            
            // Turn left (paddle right side)
            if (Input.GetKeyDown(KeyCode.A) || Input.GetKeyDown(KeyCode.LeftArrow))
            {
                PaddleLeft();
            }
            
            // Turn right (paddle left side)
            if (Input.GetKeyDown(KeyCode.D) || Input.GetKeyDown(KeyCode.RightArrow))
            {
                PaddleRight();
            }
            
            // Sprint (hold Shift)
            if (Input.GetKey(KeyCode.LeftShift) && currentStamina > 0)
            {
                Sprint();
            }
            
            // Brake (Space)
            if (Input.GetKey(KeyCode.Space))
            {
                Brake();
            }
        }
        
        void PaddleForward()
        {
            if (timeSinceLastStroke < strokeCooldown) return;
            
            // Scale force down if already near max speed
            float speedFactor = 1f - Mathf.Clamp01(rb.linearVelocity.magnitude / maxPaddleSpeed);
            Vector3 force = transform.forward * paddleForce * (0.3f + 0.7f * speedFactor);
            rb.AddForce(force, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
            EmitPaddleSplash();
        }
        
        void PaddleBackward()
        {
            if (timeSinceLastStroke < strokeCooldown) return;
            
            Vector3 force = -transform.forward * paddleForce * 0.4f;
            rb.AddForce(force, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
            EmitPaddleSplash();
        }
        
        void PaddleLeft()
        {
            if (timeSinceLastStroke < strokeCooldown) return;
            
            // Paddle on right side = turn left + slight forward
            Vector3 force = transform.forward * paddleForce * 0.2f;
            Vector3 torque = Vector3.up * -turnTorque;
            
            rb.AddForce(force, ForceMode.Impulse);
            rb.AddTorque(torque, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
        }
        
        void PaddleRight()
        {
            if (timeSinceLastStroke < strokeCooldown) return;
            
            // Paddle on left side = turn right + slight forward
            Vector3 force = transform.forward * paddleForce * 0.2f;
            Vector3 torque = Vector3.up * turnTorque;
            
            rb.AddForce(force, ForceMode.Impulse);
            rb.AddTorque(torque, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
        }
        
        void Sprint()
        {
            if (currentStamina > 0 && !staminaDepleted)
            {
                float speedFactor = 1f - Mathf.Clamp01(rb.linearVelocity.magnitude / (maxPaddleSpeed * sprintMultiplier));
                Vector3 force = transform.forward * paddleForce * sprintMultiplier * speedFactor;
                rb.AddForce(force * Time.deltaTime, ForceMode.Force);
                currentStamina -= staminaDrain * Time.deltaTime;
                
                if (currentStamina <= 0)
                {
                    currentStamina = 0;
                    staminaDepleted = true;
                    staminaDepletedTimer = staminaRecoveryDelay;
                }
            }
        }
        
        void Brake()
        {
            rb.AddForce(-rb.linearVelocity * rb.mass * 2f * Time.deltaTime, ForceMode.Force);
        }
        
        void RecoverStamina()
        {
            if (staminaDepleted)
            {
                staminaDepletedTimer -= Time.deltaTime;
                if (staminaDepletedTimer <= 0f)
                    staminaDepleted = false;
                return;
            }
            
            if (!Input.GetKey(KeyCode.LeftShift) && timeSinceLastStroke > 0.8f)
            {
                currentStamina = Mathf.Min(currentStamina + staminaRecover * Time.deltaTime, maxStamina);
            }
        }
        
        void CheckCapsize()
        {
            float tiltAngle = Vector3.Angle(transform.up, Vector3.up);
            
            if (tiltAngle > maxTiltAngle && !isCapsized)
            {
                Capsize();
            }
        }
        
        void Capsize()
        {
            isCapsized = true;
            Debug.Log("Boat capsized! Press SPACE to recover.");
            AudioManager.Instance?.PlayCapsizeSound();
        }
        
        void AttemptRecovery()
        {
            // Reset orientation
            transform.rotation = Quaternion.LookRotation(transform.forward, Vector3.up);
            isCapsized = false;
            
            // Add small penalty
            currentStamina *= 0.5f;
            
            AudioManager.Instance?.PlayRecoverySound();
            
            // Achievement: recover from capsize
            if (SteamManager.Instance != null)
                SteamManager.Instance.UnlockAchievement(SteamManager.Achievements.CAPSIZE_RECOVERY);
            
            Debug.Log("Boat recovered!");
        }
        
        void PlayPaddleSound()
        {
            AudioManager.Instance?.PlayPaddleSound();
        }
        
        void EmitPaddleSplash()
        {
            Vector3 splashPos = transform.position;
            splashPos.y = waterLevel;
            
            if (riverParticles != null)
            {
                riverParticles.EmitSplash(splashPos, 1f);
            }
            
            AudioManager.Instance?.PlaySplashSound(splashPos, 0.5f);
        }
        
        void OnDrawGizmos()
        {
            // Draw water level
            if (Application.isPlaying)
            {
                Gizmos.color = Color.cyan;
                Vector3 center = transform.position;
                center.y = waterLevel;
                Gizmos.DrawWireCube(center, Vector3.one * 5f);
                
                // Draw flow direction
                Gizmos.color = Color.blue;
                Gizmos.DrawRay(center, waterFlowDirection * waterFlowSpeed * 5f);
            }
            
            // Draw boat orientation
            Gizmos.color = Color.green;
            Gizmos.DrawRay(transform.position, transform.forward * 3f);
            
            Gizmos.color = Color.red;
            Gizmos.DrawRay(transform.position, transform.right * 2f);
        }
        
        public float GetSpeed()
        {
            return rb.linearVelocity.magnitude;
        }
        
        public float GetStamina()
        {
            return currentStamina / maxStamina;
        }
        
        public bool IsCapsized()
        {
            return isCapsized;
        }
    }
}
