using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Audio;
using System.Collections.Generic;
using Nidelven.Core;

namespace Nidelven.UI
{
    /// <summary>
    /// Settings menu for graphics, audio, and controls.
    /// Required for PC release.
    /// </summary>
    public class SettingsMenu : MonoBehaviour
    {
        [Header("Panels")]
        public GameObject settingsPanel;
        public GameObject graphicsPanel;
        public GameObject audioPanel;
        public GameObject controlsPanel;
        
        [Header("Graphics Settings")]
        public Dropdown resolutionDropdown;
        public Dropdown qualityDropdown;
        public Toggle fullscreenToggle;
        public Slider renderScaleSlider;
        public Text renderScaleText;
        
        [Header("Audio Settings")]
        public Slider masterVolumeSlider;
        public Slider musicVolumeSlider;
        public Slider sfxVolumeSlider;
        public Text masterVolumeText;
        public Text musicVolumeText;
        public Text sfxVolumeText;
        
        [Header("Audio Mixer")]
        public AudioMixer audioMixer;
        
        [Header("Language")]
        public Dropdown languageDropdown;
        
        [Header("Key Bindings")]
        public Transform keyBindContainer;
        public GameObject keyBindPrefab;
        
        // Resolution list
        private Resolution[] resolutions;
        private List<string> resolutionOptions = new List<string>();
        
        void Start()
        {
            InitializeGraphicsSettings();
            InitializeAudioSettings();
            InitializeKeyBindings();
            InitializeLanguage();
            
            // Hide on start
            settingsPanel.SetActive(false);
        }
        
        void Update()
        {
            // Only handle Escape in SettingsMenu when settings panel is already open
            // GameManager handles the initial Escape press to pause
            if (Input.GetKeyDown(KeyCode.Escape) && settingsPanel.activeSelf)
            {
                ToggleSettings();
            }
        }
        
        void InitializeGraphicsSettings()
        {
            // Get available resolutions
            resolutions = Screen.resolutions;
            resolutionOptions.Clear();
            
            int currentResolutionIndex = 0;
            for (int i = 0; i < resolutions.Length; i++)
            {
                string option = $"{resolutions[i].width} x {resolutions[i].height}";
                resolutionOptions.Add(option);
                
                if (resolutions[i].width == Screen.currentResolution.width &&
                    resolutions[i].height == Screen.currentResolution.height)
                {
                    currentResolutionIndex = i;
                }
            }
            
            resolutionDropdown.ClearOptions();
            resolutionDropdown.AddOptions(resolutionOptions);
            resolutionDropdown.value = currentResolutionIndex;
            resolutionDropdown.RefreshShownValue();
            
            // Quality settings (URP presets)
            qualityDropdown.ClearOptions();
            qualityDropdown.AddOptions(new List<string>(QualitySettings.names));
            qualityDropdown.value = QualitySettings.GetQualityLevel();
            
            // Fullscreen
            fullscreenToggle.isOn = Screen.fullScreen;
            
            // Render scale (URP)
            renderScaleSlider.value = 1f;
            renderScaleText.text = "100%";
        }
        
        void InitializeAudioSettings()
        {
            // Load saved volumes or defaults
            float masterVol = PlayerPrefs.GetFloat("MasterVolume", 0.8f);
            float musicVol = PlayerPrefs.GetFloat("MusicVolume", 0.6f);
            float sfxVol = PlayerPrefs.GetFloat("SFXVolume", 0.8f);
            
            masterVolumeSlider.value = masterVol;
            musicVolumeSlider.value = musicVol;
            sfxVolumeSlider.value = sfxVol;
            
            UpdateVolumeText();
        }
        
        void InitializeKeyBindings()
        {
            // Key binding setup would go here
            // For now, use default Unity Input Manager
        }
        
        void InitializeLanguage()
        {
            if (languageDropdown == null) return;
            
            languageDropdown.ClearOptions();
            languageDropdown.AddOptions(new List<string> { "English", "Norsk" });
            
            if (LocalizationManager.Instance != null)
            {
                languageDropdown.value = LocalizationManager.Instance.currentLanguage == LocalizationManager.Language.Norwegian ? 1 : 0;
            }
        }
        
        public void OnLanguageChanged(int index)
        {
            if (LocalizationManager.Instance != null)
            {
                var lang = index == 1 ? LocalizationManager.Language.Norwegian : LocalizationManager.Language.English;
                LocalizationManager.Instance.SetLanguage(lang);
            }
        }
        
        public void ToggleSettings()
        {
            settingsPanel.SetActive(!settingsPanel.activeSelf);
            
            if (settingsPanel.activeSelf)
            {
                Time.timeScale = 0f; // Pause game
                Cursor.lockState = CursorLockMode.None;
                Cursor.visible = true;
                ShowPanel("graphics");
            }
            else
            {
                Time.timeScale = 1f; // Resume game
                Cursor.lockState = CursorLockMode.Locked;
                Cursor.visible = false;
            }
        }
        
        public void ShowPanel(string panelName)
        {
            graphicsPanel.SetActive(panelName == "graphics");
            audioPanel.SetActive(panelName == "audio");
            controlsPanel.SetActive(panelName == "controls");
        }
        
        // Graphics callbacks
        public void OnResolutionChanged(int index)
        {
            Resolution resolution = resolutions[index];
            Screen.SetResolution(resolution.width, resolution.height, Screen.fullScreen);
            PlayerPrefs.SetInt("ResolutionIndex", index);
        }
        
        public void OnQualityChanged(int index)
        {
            QualitySettings.SetQualityLevel(index);
            PlayerPrefs.SetInt("QualityLevel", index);
        }
        
        public void OnFullscreenChanged(bool isFullscreen)
        {
            Screen.fullScreen = isFullscreen;
            PlayerPrefs.SetInt("Fullscreen", isFullscreen ? 1 : 0);
        }
        
        public void OnRenderScaleChanged(float value)
        {
            int percentage = Mathf.RoundToInt(value * 100);
            renderScaleText.text = $"{percentage}%";
            
            // Update URP render scale
            #if UNITY_6000_0_OR_NEWER && !DISABLE_URP
            UnityEngine.Rendering.Universal.UniversalRenderPipeline.asset.renderScale = value;
            #endif
            
            PlayerPrefs.SetFloat("RenderScale", value);
        }
        
        // Audio callbacks
        public void OnMasterVolumeChanged(float value)
        {
            float db = value > 0.0001f ? Mathf.Log10(value) * 20f : -80f;
            audioMixer.SetFloat("MasterVolume", db);
            PlayerPrefs.SetFloat("MasterVolume", value);
            UpdateVolumeText();
        }
        
        public void OnMusicVolumeChanged(float value)
        {
            float db = value > 0.0001f ? Mathf.Log10(value) * 20f : -80f;
            audioMixer.SetFloat("MusicVolume", db);
            PlayerPrefs.SetFloat("MusicVolume", value);
            UpdateVolumeText();
        }
        
        public void OnSFXVolumeChanged(float value)
        {
            float db = value > 0.0001f ? Mathf.Log10(value) * 20f : -80f;
            audioMixer.SetFloat("SFXVolume", db);
            PlayerPrefs.SetFloat("SFXVolume", value);
            UpdateVolumeText();
        }
        
        void UpdateVolumeText()
        {
            masterVolumeText.text = $"{Mathf.RoundToInt(masterVolumeSlider.value * 100)}%";
            musicVolumeText.text = $"{Mathf.RoundToInt(musicVolumeSlider.value * 100)}%";
            sfxVolumeText.text = $"{Mathf.RoundToInt(sfxVolumeSlider.value * 100)}%";
        }
        
        public void SaveSettings()
        {
            PlayerPrefs.Save();
            Debug.Log("Settings saved");
        }
        
        public void ResetToDefaults()
        {
            // Graphics
            resolutionDropdown.value = resolutions.Length - 1;
            qualityDropdown.value = 2; // High
            fullscreenToggle.isOn = true;
            renderScaleSlider.value = 1f;
            
            // Audio
            masterVolumeSlider.value = 0.8f;
            musicVolumeSlider.value = 0.6f;
            sfxVolumeSlider.value = 0.8f;
            
            // Apply
            OnResolutionChanged(resolutionDropdown.value);
            OnQualityChanged(qualityDropdown.value);
            OnFullscreenChanged(true);
            OnRenderScaleChanged(1f);
            OnMasterVolumeChanged(0.8f);
            OnMusicVolumeChanged(0.6f);
            OnSFXVolumeChanged(0.8f);
            
            SaveSettings();
        }
        
        public void ExitToDesktop()
        {
            #if UNITY_EDITOR
            UnityEditor.EditorApplication.isPlaying = false;
            #else
            Application.Quit();
            #endif
        }
    }
}
