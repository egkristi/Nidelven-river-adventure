using UnityEngine;
using System.IO;
using System.Collections;

namespace Nidelven.Core
{
    /// <summary>
    /// Photo mode for capturing and sharing scenic moments.
    /// Freezes time, hides UI, and allows camera control.
    /// </summary>
    public class PhotoMode : MonoBehaviour
    {
        [Header("References")]
        public Camera mainCamera;
        public GameObject hudPanel;
        public GameObject photoModeUI;
        
        [Header("Photo Settings")]
        [Tooltip("Screenshot resolution multiplier")]
        public int resolutionMultiplier = 2;
        
        [Tooltip("Save folder name")]
        public string saveFolder = "Screenshots";
        
        [Tooltip("Photo filters")]
        public bool enableFilters = true;
        
        [Header("Camera Controls")]
        [Tooltip("Photo mode move speed")]
        public float moveSpeed = 10f;
        
        [Tooltip("Photo mode look speed")]
        public float lookSpeed = 2f;
        
        [Tooltip("Photo mode zoom speed")]
        public float zoomSpeed = 5f;
        
        // State
        private bool isPhotoMode = false;
        private Vector3 originalPosition;
        private Quaternion originalRotation;
        private float originalFOV;
        private float timeScaleBefore;
        
        // Filters
        [Range(0f, 2f)]
        public float contrast = 1f;
        [Range(0f, 2f)]
        public float saturation = 1f;
        [Range(0f, 2f)]
        public float brightness = 1f;
        
        void Start()
        {
            if (mainCamera == null)
            {
                mainCamera = Camera.main;
            }
            
            // Ensure save directory exists
            string savePath = Path.Combine(Application.persistentDataPath, saveFolder);
            Directory.CreateDirectory(savePath);
        }
        
        void Update()
        {
            // Toggle photo mode
            if (Input.GetKeyDown(KeyCode.F12))
            {
                TogglePhotoMode();
            }
            
            if (isPhotoMode)
            {
                HandlePhotoModeInput();
            }
        }
        
        void TogglePhotoMode()
        {
            if (isPhotoMode)
            {
                ExitPhotoMode();
            }
            else
            {
                EnterPhotoMode();
            }
        }
        
        void EnterPhotoMode()
        {
            isPhotoMode = true;
            
            // Freeze time
            timeScaleBefore = Time.timeScale;
            Time.timeScale = 0f;
            
            // Save camera state
            originalPosition = mainCamera.transform.position;
            originalRotation = mainCamera.transform.rotation;
            originalFOV = mainCamera.fieldOfView;
            
            // Hide HUD
            if (hudPanel != null)
            {
                hudPanel.SetActive(false);
            }
            
            // Show photo mode UI
            if (photoModeUI != null)
            {
                photoModeUI.SetActive(true);
            }
            
            // Unlock cursor
            Cursor.lockState = CursorLockMode.None;
            Cursor.visible = true;
            
            Debug.Log("Photo Mode: Press F12 to exit, SPACE to capture");
        }
        
        void ExitPhotoMode()
        {
            isPhotoMode = false;
            
            // Restore time
            Time.timeScale = timeScaleBefore;
            
            // Restore camera
            mainCamera.transform.position = originalPosition;
            mainCamera.transform.rotation = originalRotation;
            mainCamera.fieldOfView = originalFOV;
            
            // Show HUD
            if (hudPanel != null)
            {
                hudPanel.SetActive(true);
            }
            
            // Hide photo mode UI
            if (photoModeUI != null)
            {
                photoModeUI.SetActive(false);
            }
            
            Debug.Log("Photo Mode: Exited");
        }
        
        void HandlePhotoModeInput()
        {
            // Movement (WASD)
            Vector3 move = Vector3.zero;
            if (Input.GetKey(KeyCode.W)) move += mainCamera.transform.forward;
            if (Input.GetKey(KeyCode.S)) move -= mainCamera.transform.forward;
            if (Input.GetKey(KeyCode.A)) move -= mainCamera.transform.right;
            if (Input.GetKey(KeyCode.D)) move += mainCamera.transform.right;
            if (Input.GetKey(KeyCode.Q)) move -= Vector3.up;
            if (Input.GetKey(KeyCode.E)) move += Vector3.up;
            
            mainCamera.transform.position += move * moveSpeed * Time.unscaledDeltaTime;
            
            // Look (hold right click)
            if (Input.GetMouseButton(1))
            {
                float mouseX = Input.GetAxis("Mouse X") * lookSpeed;
                float mouseY = Input.GetAxis("Mouse Y") * lookSpeed;
                
                mainCamera.transform.Rotate(Vector3.up * mouseX, Space.World);
                mainCamera.transform.Rotate(Vector3.left * mouseY, Space.Self);
            }
            
            // Zoom (scroll)
            float scroll = Input.GetAxis("Mouse ScrollWheel");
            mainCamera.fieldOfView = Mathf.Clamp(mainCamera.fieldOfView - scroll * zoomSpeed, 10f, 120f);
            
            // Capture
            if (Input.GetKeyDown(KeyCode.Space))
            {
                CaptureScreenshot();
            }
            
            // Reset filters
            if (Input.GetKeyDown(KeyCode.R))
            {
                contrast = 1f;
                saturation = 1f;
                brightness = 1f;
            }
        }
        
        void CaptureScreenshot()
        {
            StartCoroutine(CaptureScreenshotCoroutine());
        }
        
        IEnumerator CaptureScreenshotCoroutine()
        {
            // Wait for end of frame to capture rendered image
            yield return new WaitForEndOfFrame();
            
            // Generate filename with timestamp
            string timestamp = System.DateTime.Now.ToString("yyyy-MM-dd_HH-mm-ss");
            string filename = $"Nidelven_{timestamp}.png";
            string filepath = Path.Combine(Application.persistentDataPath, saveFolder, filename);
            
            // Capture at higher resolution
            int width = Screen.width * resolutionMultiplier;
            int height = Screen.height * resolutionMultiplier;
            
            // Create render texture
            RenderTexture rt = new RenderTexture(width, height, 24);
            mainCamera.targetTexture = rt;
            
            // Render
            Texture2D screenshot = new Texture2D(width, height, TextureFormat.RGB24, false);
            mainCamera.Render();
            
            // Read pixels
            RenderTexture.active = rt;
            screenshot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
            
            // Apply filters if enabled
            if (enableFilters)
            {
                ApplyFilters(screenshot);
            }
            
            // Encode and save
            byte[] bytes = screenshot.EncodeToPNG();
            File.WriteAllBytes(filepath, bytes);
            
            // Cleanup
            mainCamera.targetTexture = null;
            RenderTexture.active = null;
            Destroy(rt);
            Destroy(screenshot);
            
            Debug.Log($"Photo saved: {filepath}");
            
            // Show notification (if UI available)
            // Could trigger a UI animation here
        }
        
        void ApplyFilters(Texture2D image)
        {
            // GPU-based filter using a temporary material + Graphics.Blit
            // This replaces the previous per-pixel CPU loop (PF3 fix)
            Shader filterShader = Shader.Find("Hidden/PhotoFilter");
            if (filterShader != null)
            {
                Material filterMat = new Material(filterShader);
                filterMat.SetFloat("_Brightness", brightness);
                filterMat.SetFloat("_Contrast", contrast);
                filterMat.SetFloat("_Saturation", saturation);

                RenderTexture src = RenderTexture.GetTemporary(image.width, image.height, 0);
                RenderTexture dst = RenderTexture.GetTemporary(image.width, image.height, 0);

                Graphics.Blit(image, src);
                Graphics.Blit(src, dst, filterMat);

                RenderTexture.active = dst;
                image.ReadPixels(new Rect(0, 0, image.width, image.height), 0, 0);
                image.Apply();
                RenderTexture.active = null;

                RenderTexture.ReleaseTemporary(src);
                RenderTexture.ReleaseTemporary(dst);
                Destroy(filterMat);
            }
            else
            {
                // Fallback: batch pixel processing (still faster than individual pixel ops)
                Color[] pixels = image.GetPixels();
                for (int i = 0; i < pixels.Length; i++)
                {
                    Color c = pixels[i];
                    c.r = Mathf.Clamp01(((c.r * brightness) - 0.5f) * contrast + 0.5f);
                    c.g = Mathf.Clamp01(((c.g * brightness) - 0.5f) * contrast + 0.5f);
                    c.b = Mathf.Clamp01(((c.b * brightness) - 0.5f) * contrast + 0.5f);
                    float lum = c.r * 0.2126f + c.g * 0.7152f + c.b * 0.0722f;
                    c.r = Mathf.Lerp(lum, c.r, saturation);
                    c.g = Mathf.Lerp(lum, c.g, saturation);
                    c.b = Mathf.Lerp(lum, c.b, saturation);
                    pixels[i] = c;
                }
                image.SetPixels(pixels);
                image.Apply();
            }
        }
        
        void OnGUI()
        {
            if (!isPhotoMode) return;
            
            // Photo mode overlay
            GUI.Label(new Rect(10, 10, 300, 20), "PHOTO MODE - F12: Exit | SPACE: Capture | R: Reset Filters");
            GUI.Label(new Rect(10, 30, 300, 20), $"Contrast: {contrast:F2} | Saturation: {saturation:F2} | Brightness: {brightness:F2}");
            GUI.Label(new Rect(10, 50, 300, 20), "WASD: Move | QE: Up/Down | Right Click: Look | Scroll: Zoom");
            
            // Filter sliders
            GUILayout.BeginArea(new Rect(10, 80, 200, 150));
            GUILayout.Label("Filters:");
            contrast = GUILayout.HorizontalSlider(contrast, 0f, 2f);
            saturation = GUILayout.HorizontalSlider(saturation, 0f, 2f);
            brightness = GUILayout.HorizontalSlider(brightness, 0f, 2f);
            GUILayout.EndArea();
        }
        
        public bool IsInPhotoMode()
        {
            return isPhotoMode;
        }
    }
}
