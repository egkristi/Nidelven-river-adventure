using UnityEngine;
using UnityEngine.SceneManagement;
using Nidelven.Environment;
using Nidelven.Player;

namespace Nidelven.Core
{
    /// <summary>
    /// Central game manager - coordinates initialization and game state.
    /// </summary>
    public class GameManager : MonoBehaviour
    {
        public static GameManager Instance { get; private set; }
        
        [Header("Scene References")]
        public TerrainGenerator terrainGenerator;
        public RiverController riverController;
        public RiverCamera riverCamera;
        
        [Header("Game Settings")]
        public bool generateOnStart = true;
        public float gameTimeScale = 1f;
        
        [Header("UI")]
        public GameObject hudPanel;
        public GameObject pausePanel;
        
        // State
        public bool IsPaused { get; private set; }
        public bool IsGenerated { get; private set; }
        
        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
        }
        
        void Start()
        {
            if (generateOnStart)
            {
                GenerateWorld();
            }
            
            Time.timeScale = gameTimeScale;
        }
        
        void Update()
        {
            HandleInput();
            UpdateUI();
        }
        
        void HandleInput()
        {
            if (Input.GetKeyDown(KeyCode.Escape))
            {
                TogglePause();
            }
            
            if (Input.GetKeyDown(KeyCode.F1))
            {
                ShowControls();
            }
            
            if (Input.GetKeyDown(KeyCode.G))
            {
                RegenerateWorld();
            }
        }
        
        /// <summary>
        /// Generate the complete world - terrain and river.
        /// </summary>
        public void GenerateWorld()
        {
            Debug.Log("Generating world...");
            
            // Generate terrain first
            if (terrainGenerator != null)
            {
                terrainGenerator.GenerateTerrain();
            }
            
            // Then generate river (depends on terrain)
            if (riverController != null)
            {
                riverController.terrainGenerator = terrainGenerator;
                riverController.GenerateRiver();
            }
            
            // Setup camera
            if (riverCamera != null)
            {
                riverCamera.river = riverController;
                riverCamera.terrain = terrainGenerator;
            }
            
            IsGenerated = true;
            Debug.Log("World generation complete!");
        }
        
        /// <summary>
        /// Regenerate the world with new random parameters.
        /// </summary>
        public void RegenerateWorld()
        {
            IsGenerated = false;
            
            // Reseed random with better entropy
            Random.InitState(System.Environment.TickCount);
            
            GenerateWorld();
        }
        
        /// <summary>
        /// Toggle game pause state.
        /// </summary>
        public void TogglePause()
        {
            IsPaused = !IsPaused;
            Time.timeScale = IsPaused ? 0f : gameTimeScale;
            
            if (pausePanel != null)
            {
                pausePanel.SetActive(IsPaused);
            }
            
            Debug.Log($"Game {(IsPaused ? "paused" : "resumed")}");
        }
        
        /// <summary>
        /// Set the time scale for the game.
        /// </summary>
        public void SetTimeScale(float scale)
        {
            gameTimeScale = Mathf.Clamp(scale, 0.1f, 5f);
            if (!IsPaused)
            {
                Time.timeScale = gameTimeScale;
            }
        }
        
        void UpdateUI()
        {
            // Update HUD with current progress
            if (hudPanel != null && riverCamera != null)
            {
                // This would update UI elements - placeholder for now
            }
        }
        
        void ShowControls()
        {
            Debug.Log(@"
=== NIDELVEN RIVER ADVENTURE - CONTROLS ===

Camera:
  Space       - Pause/Resume auto-follow
  Left Click  - Orbit camera
  Scroll      - Zoom in/out
  Up/Down     - Speed up/slow down
  R           - Reset to start

Game:
  Escape      - Pause menu
  G           - Regenerate world
  F1          - Show controls

============================================");
        }
        
#if UNITY_EDITOR
        void OnGUI()
        {
            // Debug UI (editor only)
            if (IsGenerated && riverCamera != null)
            {
                float progress = riverCamera.GetProgress() * 100f;
                float speed = riverCamera.followSpeed * 100f;
                
                GUI.Label(new Rect(10, 10, 200, 20), $"Progress: {progress:F1}%");
                GUI.Label(new Rect(10, 30, 200, 20), $"Speed: {speed:F1}x");
                GUI.Label(new Rect(10, 50, 300, 20), $"Status: {(IsPaused ? "PAUSED" : "PLAYING")}");
                
                if (GUI.Button(new Rect(10, 80, 100, 30), IsPaused ? "Resume" : "Pause"))
                {
                    TogglePause();
                }
                
                if (GUI.Button(new Rect(120, 80, 100, 30), "Reset"))
                {
                    riverCamera.ResetCamera();
                }
            }
        }
#endif
        
        void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }
    }
}
