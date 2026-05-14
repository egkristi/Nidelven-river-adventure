using UnityEngine;
using Nidelven.Environment;

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
        [Tooltip("Force per paddle stroke")]
        public float paddleForce = 150f;
        
        [Tooltip("Turning torque per stroke")]
        public float turnTorque = 50f;
        
        [Tooltip("Stamina for sprinting")]
        public float maxStamina = 100f;
        
        [Tooltip("Stamina drain rate")]
        public float staminaDrain = 20f;
        
        [Tooltip("Stamina recovery rate")]
        public float staminaRecover = 10f;
        
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
        
        // Water level at current position
        private float waterLevel = 0f;
        private float waterFlowSpeed = 0f;
        private Vector3 waterFlowDirection = Vector3.forward;
        
        // Buoyancy points (simplified as single center)
        private Vector3 buoyancyCenter = Vector3.zero;
        
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
            ApplyVesselStats();
        }
        
        void ApplyVesselStats()
        {
            switch (vesselType)
            {
                case VesselType.Kayak:
                    paddleForce = 200f;
                    turnTorque = 80f;
                    stabilityTorque = 3f;
                    waterDrag = 1.5f;
                    break;
                    
                case VesselType.Canoe:
                    paddleForce = 150f;
                    turnTorque = 50f;
                    stabilityTorque = 5f;
                    waterDrag = 2f;
                    break;
                    
                case VesselType.Raft:
                    paddleForce = 100f;
                    turnTorque = 30f;
                    stabilityTorque = 10f;
                    waterDrag = 3f;
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
            Vector3 force = transform.forward * paddleForce;
            rb.AddForce(force, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
            EmitPaddleSplash();
        }
        
        void PaddleBackward()
        {
            Vector3 force = -transform.forward * paddleForce * 0.5f;
            rb.AddForce(force, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
            EmitPaddleSplash();
        }
        
        void PaddleLeft()
        {
            // Paddle on right side = turn left
            Vector3 force = transform.forward * paddleForce * 0.3f;
            Vector3 torque = Vector3.up * -turnTorque;
            
            rb.AddForce(force, ForceMode.Impulse);
            rb.AddTorque(torque, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
        }
        
        void PaddleRight()
        {
            // Paddle on left side = turn right
            Vector3 force = transform.forward * paddleForce * 0.3f;
            Vector3 torque = Vector3.up * turnTorque;
            
            rb.AddForce(force, ForceMode.Impulse);
            rb.AddTorque(torque, ForceMode.Impulse);
            timeSinceLastStroke = 0f;
            PlayPaddleSound();
        }
        
        void Sprint()
        {
            if (currentStamina > 0)
            {
                Vector3 force = transform.forward * paddleForce * 0.5f;
                rb.AddForce(force * Time.deltaTime, ForceMode.Force);
                currentStamina -= staminaDrain * Time.deltaTime;
            }
        }
        
        void Brake()
        {
            rb.AddForce(-rb.linearVelocity * rb.mass * 2f * Time.deltaTime, ForceMode.Force);
        }
        
        void RecoverStamina()
        {
            if (!Input.GetKey(KeyCode.LeftShift) && timeSinceLastStroke > 1f)
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
            
            // Visual feedback
            // Could trigger animation, sound, etc.
        }
        
        void AttemptRecovery()
        {
            // Reset orientation
            transform.rotation = Quaternion.LookRotation(transform.forward, Vector3.up);
            isCapsized = false;
            
            // Add small penalty
            currentStamina *= 0.5f;
            
            Debug.Log("Boat recovered!");
        }
        
        void PlayPaddleSound()
        {
            // TODO: Trigger paddle sound
            // AudioManager.Instance?.PlayPaddleSound();
        }
        
        void EmitPaddleSplash()
        {
            if (riverParticles != null)
            {
                Vector3 splashPos = transform.position;
                splashPos.y = waterLevel;
                riverParticles.EmitSplash(splashPos, 1f);
            }
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
