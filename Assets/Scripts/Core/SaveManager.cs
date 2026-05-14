using UnityEngine;
using System.IO;
using System;
using System.Collections;
using Nidelven.Environment;
using Nidelven.Player;

namespace Nidelven.Core
{
    /// <summary>
    /// Handles saving and loading game progress.
    /// Uses JSON for serialization.
    /// </summary>
    public class SaveManager : MonoBehaviour
    {
        public static SaveManager Instance { get; private set; }
        
        [Header("Save Settings")]
        [Tooltip("Auto-save interval in seconds")]
        public float autoSaveInterval = 60f;
        
        [Tooltip("Number of save slots")]
        public int saveSlotCount = 3;
        
        [Tooltip("Maximum number of auto-saves per slot")]
        public int maxAutoSaves = 5;
        
        [Header("References")]
        public RiverCamera riverCamera;
        public BoatController boatController;
        
        // Save data structure
        [Serializable]
        public class SaveData
        {
            public string version = "0.1.0";
            public string saveDate;
            public string screenshotPath;
            
            // Progress
            public float riverProgress;
            public Vector3 boatPosition;
            public Quaternion boatRotation;
            
            // Camera settings
            public float cameraHeight;
            public float cameraDistance;
            public float cameraOrbitAngle;
            
            // Boat state
            public string vesselType;
            public float stamina;
            
            // Game settings
            public float masterVolume;
            public float musicVolume;
            public bool autoFollow;
            public float followSpeed;
            
            // Stats
            public float totalDistanceTraveled;
            public float totalTimePlayed;
            public int paddleStrokeCount;
        }
        
        // Internal state
        private float lastAutoSaveTime = 0f;
        private float sessionStartTime = 0f;
        private float totalDistanceTraveled = 0f;
        private Vector3 lastPosition;
        private Texture2D[] screenshotCache;
        
        // Save path
        private string SaveDirectory => Path.Combine(Application.persistentDataPath, "Saves");
        
        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            
            // Ensure save directory exists
            Directory.CreateDirectory(SaveDirectory);
            
            sessionStartTime = Time.time;
            screenshotCache = new Texture2D[saveSlotCount];
            
            // Initialize lastPosition to boat position to avoid bogus distance on first frame
            if (boatController != null)
                lastPosition = boatController.transform.position;
        }
        
        void Update()
        {
            // Track distance traveled
            if (boatController != null)
            {
                float distance = Vector3.Distance(boatController.transform.position, lastPosition);
                totalDistanceTraveled += distance;
                lastPosition = boatController.transform.position;
            }
            
            // Auto-save
            if (Time.time - lastAutoSaveTime > autoSaveInterval)
            {
                AutoSave();
                lastAutoSaveTime = Time.time;
            }
        }
        
        /// <summary>
        /// Save game to specified slot.
        /// </summary>
        public void SaveGame(int slot)
        {
            if (slot < 0 || slot >= saveSlotCount)
            {
                Debug.LogError($"Invalid save slot: {slot}");
                return;
            }
            
            SaveData data = CreateSaveData();
            string json = JsonUtility.ToJson(data, true);
            string filePath = GetSavePath(slot);
            
            try
            {
                File.WriteAllText(filePath, json);
                Debug.Log($"Game saved to slot {slot}: {filePath}");
                
                // Capture screenshot preview for save slot
                StartCoroutine(CaptureSlotScreenshot(slot));
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to save game: {e.Message}");
            }
        }
        
        IEnumerator CaptureSlotScreenshot(int slot)
        {
            yield return new WaitForEndOfFrame();
            
            int width = Screen.width / 4;
            int height = Screen.height / 4;
            Texture2D screenshot = new Texture2D(width, height, TextureFormat.RGB24, false);
            
            RenderTexture rt = new RenderTexture(width, height, 24);
            Camera cam = Camera.main;
            if (cam != null)
            {
                cam.targetTexture = rt;
                cam.Render();
                RenderTexture.active = rt;
                screenshot.ReadPixels(new Rect(0, 0, width, height), 0, 0);
                screenshot.Apply();
                cam.targetTexture = null;
                RenderTexture.active = null;
            }
            
            byte[] bytes = screenshot.EncodeToPNG();
            string screenshotPath = GetScreenshotPath(slot);
            File.WriteAllBytes(screenshotPath, bytes);
            
            UnityEngine.Object.Destroy(rt);
            UnityEngine.Object.Destroy(screenshot);
        }
        
        /// <summary>
        /// Get the screenshot texture for a save slot (for UI display).
        /// </summary>
        public Texture2D GetSlotScreenshot(int slot)
        {
            if (slot < 0 || slot >= saveSlotCount) return null;
            
            // Return cached texture if available
            if (screenshotCache[slot] != null) return screenshotCache[slot];
            
            string path = GetScreenshotPath(slot);
            if (!File.Exists(path)) return null;
            
            byte[] bytes = File.ReadAllBytes(path);
            Texture2D tex = new Texture2D(2, 2);
            tex.LoadImage(bytes);
            screenshotCache[slot] = tex;
            return tex;
        }
        
        string GetScreenshotPath(int slot)
        {
            return Path.Combine(SaveDirectory, $"save_{slot}_preview.png");
        }
        
        /// <summary>
        /// Load game from specified slot.
        /// </summary>
        public bool LoadGame(int slot)
        {
            if (slot < 0 || slot >= saveSlotCount)
            {
                Debug.LogError($"Invalid save slot: {slot}");
                return false;
            }
            
            string filePath = GetSavePath(slot);
            
            if (!File.Exists(filePath))
            {
                Debug.LogWarning($"No save file found in slot {slot}");
                return false;
            }
            
            try
            {
                string json = File.ReadAllText(filePath);
                SaveData data = JsonUtility.FromJson<SaveData>(json);
                
                // Validate version
                if (data.version != "0.1.0")
                {
                    Debug.LogWarning($"Save file version mismatch: {data.version}");
                }
                
                ApplySaveData(data);
                Debug.Log($"Game loaded from slot {slot}");
                return true;
            }
            catch (Exception e)
            {
                Debug.LogError($"Failed to load game: {e.Message}");
                return false;
            }
        }
        
        /// <summary>
        /// Check if a save exists in the specified slot.
        /// </summary>
        public bool HasSave(int slot)
        {
            return File.Exists(GetSavePath(slot));
        }
        
        /// <summary>
        /// Delete save from specified slot.
        /// </summary>
        public void DeleteSave(int slot)
        {
            string filePath = GetSavePath(slot);
            if (File.Exists(filePath))
            {
                File.Delete(filePath);
                Debug.Log($"Save deleted from slot {slot}");
            }
        }
        
        /// <summary>
        /// Get save data for UI display.
        /// </summary>
        public SaveData GetSaveInfo(int slot)
        {
            string filePath = GetSavePath(slot);
            
            if (!File.Exists(filePath))
            {
                return null;
            }
            
            try
            {
                string json = File.ReadAllText(filePath);
                return JsonUtility.FromJson<SaveData>(json);
            }
            catch
            {
                return null;
            }
        }
        
        void AutoSave()
        {
            // Save to auto-save slot (last slot)
            int autoSaveSlot = saveSlotCount - 1;
            SaveGame(autoSaveSlot);
            Debug.Log("Auto-saved game");
        }
        
        SaveData CreateSaveData()
        {
            SaveData data = new SaveData();
            
            data.saveDate = DateTime.Now.ToString("yyyy-MM-dd HH:mm:ss");
            
            // Save progress
            if (riverCamera != null)
            {
                data.riverProgress = riverCamera.GetProgress();
                data.cameraHeight = riverCamera.heightOffset;
                data.cameraDistance = riverCamera.distanceOffset;
                data.cameraOrbitAngle = riverCamera.orbitAngle;
                data.autoFollow = riverCamera.autoFollow;
                data.followSpeed = riverCamera.followSpeed;
            }
            
            // Save boat state
            if (boatController != null)
            {
                data.boatPosition = boatController.transform.position;
                data.boatRotation = boatController.transform.rotation;
                data.vesselType = boatController.vesselType.ToString();
                data.stamina = boatController.GetStamina();
            }
            
            // Save audio settings
            if (AudioManager.Instance != null)
            {
                data.masterVolume = 1f; // TODO: Get from AudioManager
                data.musicVolume = AudioManager.Instance.musicVolume;
            }
            
            // Save stats
            data.totalDistanceTraveled = totalDistanceTraveled;
            data.totalTimePlayed = Time.time - sessionStartTime;
            
            return data;
        }
        
        void ApplySaveData(SaveData data)
        {
            // Restore camera state
            if (riverCamera != null)
            {
                riverCamera.SetProgress(data.riverProgress);
                riverCamera.heightOffset = data.cameraHeight;
                riverCamera.distanceOffset = data.cameraDistance;
                riverCamera.orbitAngle = data.cameraOrbitAngle;
                riverCamera.autoFollow = data.autoFollow;
                riverCamera.followSpeed = data.followSpeed;
            }
            
            // Restore boat state
            if (boatController != null)
            {
                boatController.transform.position = data.boatPosition;
                boatController.transform.rotation = data.boatRotation;
                
                // Parse vessel type
                if (Enum.TryParse(data.vesselType, out BoatController.VesselType vessel))
                {
                    boatController.vesselType = vessel;
                }
            }
            
            // Restore audio settings
            if (AudioManager.Instance != null)
            {
                AudioManager.Instance.SetMusicVolume(data.musicVolume);
            }
            
            // Restore stats
            totalDistanceTraveled = data.totalDistanceTraveled;
            sessionStartTime = Time.time - data.totalTimePlayed;
        }
        
        string GetSavePath(int slot)
        {
            return Path.Combine(SaveDirectory, $"save_{slot}.json");
        }
        
        void OnDestroy()
        {
            if (Instance == this)
            {
                Instance = null;
            }
        }
    }
}
