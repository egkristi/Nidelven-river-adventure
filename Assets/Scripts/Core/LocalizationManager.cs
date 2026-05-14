using UnityEngine;
using System.Collections.Generic;
using System.IO;

namespace Nidelven.Core
{
    /// <summary>
    /// Simple localization system supporting Norwegian (nb) and English (en).
    /// Loads string tables from StreamingAssets/Localization/{lang}.json.
    /// Falls back to English if key is missing.
    /// </summary>
    public class LocalizationManager : MonoBehaviour
    {
        public static LocalizationManager Instance { get; private set; }

        public enum Language { English, Norwegian }

        [Header("Settings")]
        public Language currentLanguage = Language.English;

        private Dictionary<string, string> strings = new Dictionary<string, string>();
        private Dictionary<string, string> fallbackStrings = new Dictionary<string, string>();

        public static event System.Action OnLanguageChanged;

        void Awake()
        {
            if (Instance != null && Instance != this)
            {
                Destroy(gameObject);
                return;
            }
            Instance = this;
            DontDestroyOnLoad(gameObject);

            // Load saved language preference
            string savedLang = PlayerPrefs.GetString("Language", "en");
            currentLanguage = savedLang == "nb" ? Language.Norwegian : Language.English;

            LoadFallback();
            LoadLanguage(currentLanguage);
        }

        void LoadFallback()
        {
            // Built-in English strings as fallback (no file needed)
            fallbackStrings = GetBuiltinEnglish();
        }

        public void SetLanguage(Language lang)
        {
            currentLanguage = lang;
            PlayerPrefs.SetString("Language", lang == Language.Norwegian ? "nb" : "en");
            PlayerPrefs.Save();
            LoadLanguage(lang);
            OnLanguageChanged?.Invoke();
        }

        void LoadLanguage(Language lang)
        {
            string code = lang == Language.Norwegian ? "nb" : "en";
            string path = Path.Combine(Application.streamingAssetsPath, "Localization", $"{code}.json");

            if (File.Exists(path))
            {
                try
                {
                    string json = File.ReadAllText(path);
                    var data = JsonUtility.FromJson<LocalizationData>(json);
                    strings.Clear();
                    if (data?.entries != null)
                    {
                        foreach (var entry in data.entries)
                        {
                            strings[entry.key] = entry.value;
                        }
                    }
                    Debug.Log($"Localization loaded: {code} ({strings.Count} strings)");
                    return;
                }
                catch (System.Exception e)
                {
                    Debug.LogWarning($"Failed to load localization {code}: {e.Message}");
                }
            }

            // Use built-in strings
            strings = lang == Language.Norwegian ? GetBuiltinNorwegian() : GetBuiltinEnglish();
            Debug.Log($"Using built-in localization: {code} ({strings.Count} strings)");
        }

        /// <summary>
        /// Get a localized string by key. Returns key if not found.
        /// </summary>
        public string Get(string key)
        {
            if (strings.TryGetValue(key, out string value))
                return value;
            if (fallbackStrings.TryGetValue(key, out string fallback))
                return fallback;
            return key;
        }

        /// <summary>
        /// Shorthand static accessor.
        /// </summary>
        public static string L(string key)
        {
            return Instance != null ? Instance.Get(key) : key;
        }

        Dictionary<string, string> GetBuiltinEnglish()
        {
            return new Dictionary<string, string>
            {
                // UI
                { "ui.play", "Play" },
                { "ui.settings", "Settings" },
                { "ui.quit", "Quit" },
                { "ui.resume", "Resume" },
                { "ui.save", "Save" },
                { "ui.load", "Load" },
                { "ui.back", "Back" },
                { "ui.language", "Language" },
                { "ui.graphics", "Graphics" },
                { "ui.audio", "Audio" },
                { "ui.controls", "Controls" },
                // Settings
                { "settings.resolution", "Resolution" },
                { "settings.quality", "Quality" },
                { "settings.fullscreen", "Fullscreen" },
                { "settings.renderscale", "Render Scale" },
                { "settings.master_volume", "Master Volume" },
                { "settings.music_volume", "Music Volume" },
                { "settings.sfx_volume", "Effects Volume" },
                { "settings.reset", "Reset to Defaults" },
                // Tutorial
                { "tutorial.welcome", "Welcome to Nidelven" },
                { "tutorial.paddling", "Paddling" },
                { "tutorial.sprint", "Sprinting" },
                { "tutorial.current", "River Current" },
                { "tutorial.photo", "Photo Mode" },
                { "tutorial.ready", "Ready to Explore" },
                { "tutorial.skip", "Skip Tutorial" },
                { "tutorial.next", "Next" },
                // Gameplay
                { "game.capsized", "Capsized! Press SPACE to recover." },
                { "game.saved", "Game Saved" },
                { "game.photo_saved", "Photo Saved" },
                { "game.paused", "Paused" },
                // Photo Mode
                { "photo.title", "Photo Mode" },
                { "photo.capture", "Capture" },
                { "photo.exit", "Exit (F12)" },
                { "photo.brightness", "Brightness" },
                { "photo.contrast", "Contrast" },
                { "photo.saturation", "Saturation" },
            };
        }

        Dictionary<string, string> GetBuiltinNorwegian()
        {
            return new Dictionary<string, string>
            {
                // UI
                { "ui.play", "Spill" },
                { "ui.settings", "Innstillinger" },
                { "ui.quit", "Avslutt" },
                { "ui.resume", "Fortsett" },
                { "ui.save", "Lagre" },
                { "ui.load", "Last inn" },
                { "ui.back", "Tilbake" },
                { "ui.language", "Språk" },
                { "ui.graphics", "Grafikk" },
                { "ui.audio", "Lyd" },
                { "ui.controls", "Kontroller" },
                // Settings
                { "settings.resolution", "Oppløsning" },
                { "settings.quality", "Kvalitet" },
                { "settings.fullscreen", "Fullskjerm" },
                { "settings.renderscale", "Gjengivelsesskalering" },
                { "settings.master_volume", "Hovedvolum" },
                { "settings.music_volume", "Musikkvolum" },
                { "settings.sfx_volume", "Effektvolum" },
                { "settings.reset", "Tilbakestill" },
                // Tutorial
                { "tutorial.welcome", "Velkommen til Nidelven" },
                { "tutorial.paddling", "Padling" },
                { "tutorial.sprint", "Spurt" },
                { "tutorial.current", "Elvestrøm" },
                { "tutorial.photo", "Fotomodus" },
                { "tutorial.ready", "Klar til å utforske" },
                { "tutorial.skip", "Hopp over veiledning" },
                { "tutorial.next", "Neste" },
                // Gameplay
                { "game.capsized", "Veltet! Trykk MELLOMROM for å gjenopprette." },
                { "game.saved", "Spill lagret" },
                { "game.photo_saved", "Bilde lagret" },
                { "game.paused", "Pause" },
                // Photo Mode
                { "photo.title", "Fotomodus" },
                { "photo.capture", "Ta bilde" },
                { "photo.exit", "Avslutt (F12)" },
                { "photo.brightness", "Lysstyrke" },
                { "photo.contrast", "Kontrast" },
                { "photo.saturation", "Metning" },
            };
        }

        [System.Serializable]
        private class LocalizationData
        {
            public LocalizationEntry[] entries;
        }

        [System.Serializable]
        private class LocalizationEntry
        {
            public string key;
            public string value;
        }
    }
}
