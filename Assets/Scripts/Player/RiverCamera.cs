using UnityEngine;
using Nidelven.Environment;

namespace Nidelven.Player
{
    /// <summary>
    /// Camera that smoothly follows the river trajectory.
    /// Provides automatic river following with optional manual orbit control.
    /// </summary>
    public class RiverCamera : MonoBehaviour
    {
        [Header("River Reference")]
        [Tooltip("River controller to follow")]
        public RiverController river;
        
        [Tooltip("Terrain generator for ground reference")]
        public TerrainGenerator terrain;
        
        [Header("Following")]
        [Tooltip("Auto-follow the river")]
        public bool autoFollow = true;
        
        [Tooltip("Speed of progression along river (0-1 per second)")]
        public float followSpeed = 0.05f;
        
        [Tooltip("Current progress along river (0-1)")]
        [Range(0f, 1f)]
        public float riverProgress = 0f;
        
        [Header("Camera Offsets")]
        [Tooltip("Height above water")]
        public float heightOffset = 15f;
        
        [Tooltip("Distance behind current position")]
        public float distanceOffset = 30f;
        
        [Tooltip("Look ahead distance")]
        public float lookAheadDistance = 50f;
        
        [Header("Smoothing")]
        [Tooltip("Position smoothing factor")]
        public float positionSmoothing = 0.1f;
        
        [Tooltip("Look direction smoothing factor")]
        public float lookSmoothing = 0.08f;
        
        [Header("Follow Target")]
        [Tooltip("If set, camera follows this transform along the river instead of auto-progressing")]
        public Transform followTarget;
        
        [Header("Orbit Control")]
        [Tooltip("Allow manual orbit with mouse")]
        public bool allowOrbit = true;
        
        [Tooltip("Orbit sensitivity")]
        public float orbitSensitivity = 0.5f;
        
        [Tooltip("Height adjustment sensitivity")]
        public float heightSensitivity = 0.1f;
        
        [Tooltip("Zoom sensitivity")]
        public float zoomSensitivity = 5f;
        
        [Tooltip("Minimum zoom distance")]
        public float minDistance = 10f;
        
        [Tooltip("Maximum zoom distance")]
        public float maxDistance = 100f;
        
        [Tooltip("Minimum height")]
        public float minHeight = 5f;
        
        [Tooltip("Maximum height")]
        public float maxHeight = 50f;
        
        // Internal state
        public float orbitAngle = 0f;
        private Vector3 currentPosition;
        private Vector3 currentLookTarget;
        private Vector3 targetPosition;
        private Vector3 targetLookTarget;
        private Vector3 positionVelocity;
        private Vector3 lookVelocity;
        private bool isPaused = false;
        
        void Start()
        {
            // Initialize position
            if (river != null)
            {
                currentPosition = river.GetPositionOnRiver(riverProgress);
                currentLookTarget = river.GetPositionOnRiver(Mathf.Min(riverProgress + 0.05f, 1f));
            }
            else
            {
                currentPosition = transform.position;
                currentLookTarget = currentPosition + Vector3.forward;
            }
        }
        
        void Update()
        {
            HandleInput();
            
            if (followTarget != null && river != null)
            {
                // Follow the target's position along the river
                riverProgress = river.GetClosestProgress(followTarget.position);
            }
            else if (autoFollow && !isPaused && river != null)
            {
                UpdateRiverProgress();
            }
            
            UpdateCameraPosition();
        }
        
        void HandleInput()
        {
            // Pause/unpause — only when no boat is being followed (avoids conflict with BoatController brake)
            if (followTarget == null && Input.GetKeyDown(KeyCode.Space))
            {
                TogglePause();
            }
            
            // Speed control
            if (Input.GetKey(KeyCode.UpArrow))
            {
                followSpeed = Mathf.Min(followSpeed + 0.01f, 0.5f);
            }
            if (Input.GetKey(KeyCode.DownArrow))
            {
                followSpeed = Mathf.Max(followSpeed - 0.01f, 0f);
            }
            
            // Zoom
            float scroll = Input.GetAxis("Mouse ScrollWheel");
            if (scroll != 0)
            {
                distanceOffset = Mathf.Clamp(distanceOffset - scroll * zoomSensitivity, 
                    minDistance, maxDistance);
            }
            
            // Orbit (mouse drag)
            if (allowOrbit && Input.GetMouseButton(0))
            {
                float mouseX = Input.GetAxis("Mouse X");
                float mouseY = Input.GetAxis("Mouse Y");
                
                orbitAngle += mouseX * orbitSensitivity;
                heightOffset = Mathf.Clamp(heightOffset + mouseY * heightSensitivity,
                    minHeight, maxHeight);
            }
            
            // Reset
            if (Input.GetKeyDown(KeyCode.R))
            {
                ResetCamera();
            }
        }
        
        void UpdateRiverProgress()
        {
            riverProgress += followSpeed * Time.deltaTime;
            
            if (riverProgress >= 1f)
            {
                riverProgress = 0f; // Loop back to start
            }
        }
        
        void UpdateCameraPosition()
        {
            if (river == null) return;
            
            // Get current river position
            Vector3 riverPos = river.GetPositionOnRiver(riverProgress);
            
            // Get forward direction
            Vector3 riverForward = river.GetForwardOnRiver(riverProgress);
            Vector3 riverRight = Vector3.Cross(riverForward, Vector3.up).normalized;
            
            // Calculate camera position with orbit
            float orbitRad = orbitAngle * Mathf.Deg2Rad;
            Vector3 offsetDirection = (riverForward * Mathf.Cos(orbitRad) + 
                                       riverRight * Mathf.Sin(orbitRad)).normalized;
            
            targetPosition = riverPos - offsetDirection * distanceOffset;
            targetPosition.y = riverPos.y + heightOffset;
            
            // Look ahead on river
            float lookAheadProgress = Mathf.Min(riverProgress + 0.05f, 1f);
            targetLookTarget = river.GetPositionOnRiver(lookAheadProgress);
            targetLookTarget.y += 5f; // Look slightly above water
            
            // Smooth movement (frame-rate independent)
            currentPosition = Vector3.SmoothDamp(currentPosition, targetPosition, ref positionVelocity, positionSmoothing);
            currentLookTarget = Vector3.SmoothDamp(currentLookTarget, targetLookTarget, ref lookVelocity, lookSmoothing);
            
            // Apply to transform
            transform.position = currentPosition;
            transform.LookAt(currentLookTarget);
        }
        
        /// <summary>
        /// Toggle pause state for auto-follow.
        /// </summary>
        public void TogglePause()
        {
            isPaused = !isPaused;
            Debug.Log($"Camera {(isPaused ? "paused" : "resumed")}");
        }
        
        /// <summary>
        /// Reset camera to start of river.
        /// </summary>
        public void ResetCamera()
        {
            riverProgress = 0f;
            orbitAngle = 0f;
            heightOffset = 15f;
            distanceOffset = 30f;
            
            if (river != null)
            {
                currentPosition = river.GetPositionOnRiver(0f);
                currentLookTarget = river.GetPositionOnRiver(0.05f);
            }
        }
        
        /// <summary>
        /// Set progress along river (0-1).
        /// </summary>
        public void SetProgress(float progress)
        {
            riverProgress = Mathf.Clamp01(progress);
        }
        
        /// <summary>
        /// Get current progress along river.
        /// </summary>
        public float GetProgress()
        {
            return riverProgress;
        }
        
        /// <summary>
        /// Enable/disable auto-follow.
        /// </summary>
        public void SetAutoFollow(bool enabled)
        {
            autoFollow = enabled;
        }
        
        void OnDrawGizmos()
        {
            // Draw camera trajectory
            Gizmos.color = Color.yellow;
            Gizmos.DrawLine(transform.position, transform.position + transform.forward * 10f);
            Gizmos.DrawWireSphere(transform.position, 1f);
        }
    }
}
