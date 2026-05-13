using UnityEngine;

namespace Nidelven.Core
{
    /// <summary>
    /// Handles graceful game exit for PC builds.
    /// Required for PC release.
    /// </summary>
    public class GameQuitter : MonoBehaviour
    {
        [Header("Exit Settings")]
        [Tooltip("Key to exit game")]
        public KeyCode exitKey = KeyCode.F10;
        
        [Tooltip("Show confirmation dialog")]
        public bool showConfirmation = true;
        
        [Tooltip("Auto-save on exit")]
        public bool autoSaveOnExit = true;
        
        private bool isQuitting = false;
        
        void Update()
        {
            // Exit on key press
            if (Input.GetKeyDown(exitKey))
            {
                RequestExit();
            }
            
            // Exit on Alt+F4 (Windows) or Cmd+Q (Mac)
            if (Input.GetKey(KeyCode.LeftAlt) && Input.GetKeyDown(KeyCode.F4))
            {
                RequestExit();
            }
        }
        
        /// <summary>
        /// Request game exit with optional confirmation and auto-save.
        /// </summary>
        public void RequestExit()
        {
            if (isQuitting) return;
            
            if (showConfirmation)
            {
                // In a real build, show UI confirmation
                // For now, just log
                Debug.Log("Exit requested - showing confirmation...");
            }
            
            // Auto-save if enabled
            if (autoSaveOnExit && SaveManager.Instance != null)
            {
                Debug.Log("Auto-saving before exit...");
                SaveManager.Instance.SaveGame(0); // Save to slot 0
            }
            
            // Quit
            QuitGame();
        }
        
        /// <summary>
        /// Immediate quit without confirmation.
        /// </summary>
        public void QuitGame()
        {
            isQuitting = true;
            
            Debug.Log("Exiting game...");
            
            #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
            #else
            Application.Quit();
            #endif
        }
        
        void OnApplicationQuit()
        {
            // Cleanup if needed
            Debug.Log("Application quitting");
        }
    }
}
