using UnityEngine;
using System.Collections;

namespace Nidelven.Core
{
    /// <summary>
    /// Steam integration manager - handles initialization, achievements, and cloud saves.
    /// Requires Steamworks.NET package.
    /// </summary>
    public class SteamManager : MonoBehaviour
    {
        public static SteamManager Instance { get; private set; }
        
        [Header("Steam App ID")]
        public uint steamAppId = 0; // Replace with your actual App ID
        
        [Header("Debug")]
        public bool debugMode = true;
        
        private bool isSteamInitialized = false;
        
        // Achievement IDs (must match Steam partner backend)
        public static class Achievements
        {
            public const string FIRST_JOURNEY = "ACH_FIRST_JOURNEY";
            public const string REACH_ARENDAL = "ACH_REACH_ARENDAL";
            public const string PHOTOGRAPHER = "ACH_PHOTOGRAPHER";
            public const string SPEED_DEMON = "ACH_SPEED_DEMON";
            public const string CAPSIZE_RECOVERY = "ACH_CAPSIZE_RECOVERY";
            public const string COMPLETE_10KM = "ACH_COMPLETE_10KM";
            public const string NIGHT_PADDLE = "ACH_NIGHT_PADDLE";
            public const string WILDLIFE_SPOTTER = "ACH_WILDLIFE_SPOTTER";
        }
        
        void Awake()
        {
            if (Instance != null)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);
            
            InitializeSteam();
        }
        
        void InitializeSteam()
        {
            #if !DISABLESTEAMWORKS
            try
            {
                if (Steamworks.SteamAPI.Init())
                {
                    isSteamInitialized = true;
                    Debug.Log($"Steam initialized. User: {Steamworks.SteamUser.GetSteamID()}");
                    
                    // Request stats on init
                    Steamworks.SteamUserStats.RequestCurrentStats();
                }
                else
                {
                    Debug.LogWarning("Steam failed to initialize. Running without Steam.");
                }
            }
            catch (System.DllNotFoundException)
            {
                Debug.LogWarning("Steamworks.NET not found. Running without Steam.");
            }
            #else
            Debug.Log("Steamworks disabled in build.");
            #endif
        }
        
        /// <summary>
        /// Unlock an achievement.
        /// </summary>
        public void UnlockAchievement(string achievementId)
        {
            if (!isSteamInitialized) return;
            
            #if !DISABLESTEAMWORKS
            Steamworks.SteamUserStats.SetAchievement(achievementId);
            Steamworks.SteamUserStats.StoreStats();
            Debug.Log($"Achievement unlocked: {achievementId}");
            #endif
        }
        
        /// <summary>
        /// Check if achievement is unlocked.
        /// </summary>
        public bool IsAchievementUnlocked(string achievementId)
        {
            if (!isSteamInitialized) return false;
            
            #if !DISABLESTEAMWORKS
            bool achieved = false;
            Steamworks.SteamUserStats.GetAchievement(achievementId, out achieved);
            return achieved;
            #else
            return false;
            #endif
        }
        
        /// <summary>
        /// Set a stat value.
        /// </summary>
        public void SetStat(string statName, int value)
        {
            if (!isSteamInitialized) return;
            
            #if !DISABLESTEAMWORKS
            Steamworks.SteamUserStats.SetStat(statName, value);
            Steamworks.SteamUserStats.StoreStats();
            #endif
        }
        
        /// <summary>
        /// Set a float stat value.
        /// </summary>
        public void SetStat(string statName, float value)
        {
            if (!isSteamInitialized) return;
            
            #if !DISABLESTEAMWORKS
            Steamworks.SteamUserStats.SetStat(statName, value);
            Steamworks.SteamUserStats.StoreStats();
            #endif
        }
        
        /// <summary>
        /// Get a stat value.
        /// </summary>
        public int GetStatInt(string statName)
        {
            if (!isSteamInitialized) return 0;
            
            #if !DISABLESTEAMWORKS
            int value = 0;
            Steamworks.SteamUserStats.GetStat(statName, out value);
            return value;
            #else
            return 0;
            #endif
        }
        
        /// <summary>
        /// Upload save to Steam Cloud.
        /// </summary>
        public void UploadSaveToCloud(string saveName, byte[] data)
        {
            if (!isSteamInitialized) return;
            
            #if !DISABLESTEAMWORKS
            var result = Steamworks.SteamRemoteStorage.FileWrite(saveName, data, data.Length);
            Debug.Log($"Cloud save uploaded: {saveName} ({result})");
            #endif
        }
        
        /// <summary>
        /// Download save from Steam Cloud.
        /// </summary>
        public byte[] DownloadSaveFromCloud(string saveName)
        {
            if (!isSteamInitialized) return null;
            
            #if !DISABLESTEAMWORKS
            if (Steamworks.SteamRemoteStorage.FileExists(saveName))
            {
                int fileSize = Steamworks.SteamRemoteStorage.GetFileSize(saveName);
                byte[] data = new byte[fileSize];
                Steamworks.SteamRemoteStorage.FileRead(saveName, data, fileSize);
                return data;
            }
            #endif
            return null;
        }
        
        /// <summary>
        /// Get list of cloud save files.
        /// </summary>
        public string[] GetCloudSaveFiles()
        {
            if (!isSteamInitialized) return new string[0];
            
            #if !DISABLESTEAMWORKS
            int fileCount = Steamworks.SteamRemoteStorage.GetFileCount();
            string[] files = new string[fileCount];
            for (int i = 0; i < fileCount; i++)
            {
                files[i] = Steamworks.SteamRemoteStorage.GetFileNameAndSize(i, out int _);
            }
            return files;
            #else
            return new string[0];
            #endif
        }
        
        void OnEnable()
        {
            #if !DISABLESTEAMWORKS
            // Callbacks would be set up here for achievement notifications, etc.
            #endif
        }
        
        void OnDisable()
        {
            #if !DISABLESTEAMWORKS
            // Cleanup callbacks
            #endif
        }
        
        void Update()
        {
            #if !DISABLESTEAMWORKS
            // Run Steam callbacks
            if (isSteamInitialized)
            {
                Steamworks.SteamAPI.RunCallbacks();
            }
            #endif
        }
        
        void OnDestroy()
        {
            #if !DISABLESTEAMWORKS
            if (isSteamInitialized)
            {
                Steamworks.SteamAPI.Shutdown();
            }
            #endif
            
            if (Instance == this)
            {
                Instance = null;
            }
        }
        
        void OnGUI()
        {
            if (!debugMode) return;
            
            GUILayout.BeginArea(new Rect(10, Screen.height - 100, 200, 90));
            GUILayout.Label($"Steam: {(isSteamInitialized ? "Connected" : "Disconnected")}");
            
            if (GUILayout.Button("Test Achievement"))
            {
                UnlockAchievement(Achievements.FIRST_JOURNEY);
            }
            GUILayout.EndArea();
        }
    }
}
