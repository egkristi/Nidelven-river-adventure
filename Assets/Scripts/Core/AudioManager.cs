using UnityEngine;
using UnityEngine.Audio;
using System.Collections;
using Nidelven.Environment;

namespace Nidelven.Core
{
    /// <summary>
    /// Manages all game audio - river ambience, environment, and UI sounds.
    /// Uses layered soundscape approach with spatial audio.
    /// </summary>
    public class AudioManager : MonoBehaviour
    {
        public static AudioManager Instance { get; private set; }
        
        [Header("Audio Mixers")]
        public AudioMixer masterMixer;
        public AudioMixerGroup ambienceGroup;
        public AudioMixerGroup sfxGroup;
        public AudioMixerGroup uiGroup;
        
        [Header("River Sounds")]
        [Tooltip("Base river ambience (calm water)")]
        public AudioClip riverCalm;
        
        [Tooltip("River rapids ambience")]
        public AudioClip riverRapids;
        
        [Tooltip("Paddle stroke sounds")]
        public AudioClip[] paddleSounds;
        
        [Header("Environment")]
        [Tooltip("Forest ambience (wind, leaves)")]
        public AudioClip forestAmbience;
        
        [Tooltip("Bird sounds (various birds)")]
        public AudioClip[] birdSounds;
        
        [Tooltip("Bird call interval min/max")]
        public Vector2 birdInterval = new Vector2(5f, 15f);
        
        [Header("Music")]
        [Tooltip("Ambient background music")]
        public AudioClip ambientMusic;
        
        [Tooltip("Music volume (0-1)")]
        [Range(0f, 1f)]
        public float musicVolume = 0.3f;
        
        [Header("References")]
        public RiverController river;
        public Transform playerTransform;
        
        // Audio sources
        private AudioSource riverSource;
        private AudioSource rapidsSource;
        private AudioSource forestSource;
        private AudioSource musicSource;
        
        // Child objects for spatial audio (PF4 fix)
        private Transform riverAudioTransform;
        private Transform forestAudioTransform;
        
        // State
        private float nextBirdTime = 0f;
        private float currentRiverSpeed = 0f;
        
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
            SetupAudioSources();
            StartAmbience();
            nextBirdTime = Time.time + Random.Range(birdInterval.x, birdInterval.y);
        }
        
        void Update()
        {
            UpdateRiverSound();
            UpdateBirdSounds();
        }
        
        void SetupAudioSources()
        {
            // Create child object for river sounds (follows player)
            var riverObj = new GameObject("RiverAudio");
            riverObj.transform.SetParent(transform);
            riverAudioTransform = riverObj.transform;
            
            // River ambience (calm)
            riverSource = riverObj.AddComponent<AudioSource>();
            riverSource.outputAudioMixerGroup = ambienceGroup;
            riverSource.spatialBlend = 1f; // 3D audio
            riverSource.loop = true;
            riverSource.playOnAwake = false;
            
            // River rapids
            rapidsSource = riverObj.AddComponent<AudioSource>();
            rapidsSource.outputAudioMixerGroup = ambienceGroup;
            rapidsSource.spatialBlend = 1f;
            rapidsSource.loop = true;
            rapidsSource.playOnAwake = false;
            
            // Create child object for forest sounds (follows player at offset)
            var forestObj = new GameObject("ForestAudio");
            forestObj.transform.SetParent(transform);
            forestAudioTransform = forestObj.transform;
            
            // Forest ambience
            forestSource = forestObj.AddComponent<AudioSource>();
            forestSource.outputAudioMixerGroup = ambienceGroup;
            forestSource.spatialBlend = 0.5f; // Semi-spatial (surrounds player)
            forestSource.loop = true;
            forestSource.playOnAwake = false;
            
            // Music (on manager itself — 2D, no spatial)
            if (ambientMusic != null)
            {
                musicSource = gameObject.AddComponent<AudioSource>();
                musicSource.outputAudioMixerGroup = ambienceGroup;
                musicSource.spatialBlend = 0f; // 2D music
                musicSource.loop = true;
                musicSource.volume = musicVolume;
                musicSource.playOnAwake = false;
            }
        }
        
        void StartAmbience()
        {
            // Start river ambience
            if (riverCalm != null && riverSource != null)
            {
                riverSource.clip = riverCalm;
                riverSource.Play();
            }
            
            // Start rapids layer
            if (riverRapids != null && rapidsSource != null)
            {
                rapidsSource.clip = riverRapids;
                rapidsSource.volume = 0f; // Start silent, blend in
                rapidsSource.Play();
            }
            
            // Start forest ambience
            if (forestAmbience != null && forestSource != null)
            {
                forestSource.clip = forestAmbience;
                forestSource.Play();
            }
            
            // Start music
            if (ambientMusic != null && musicSource != null)
            {
                musicSource.clip = ambientMusic;
                musicSource.Play();
            }
        }
        
        void UpdateRiverSound()
        {
            if (river == null || playerTransform == null) return;
            
            // Get river speed at player position
            float progress = river.GetClosestProgress(playerTransform.position);
            currentRiverSpeed = river.GetFlowSpeedAt(progress);
            
            // Move river audio child to player (not the manager itself)
            riverAudioTransform.position = playerTransform.position;
            forestAudioTransform.position = playerTransform.position;
            
            // Blend between calm and rapids based on speed
            float normalizedSpeed = Mathf.InverseLerp(0.5f, 3f, currentRiverSpeed);
            
            riverSource.volume = Mathf.Lerp(1f, 0.3f, normalizedSpeed);
            rapidsSource.volume = Mathf.Lerp(0f, 1f, normalizedSpeed);
            
            // Pitch modulation for variety
            riverSource.pitch = 0.95f + Mathf.PerlinNoise(Time.time * 0.5f, 0f) * 0.1f;
        }
        
        void UpdateBirdSounds()
        {
            if (Time.time >= nextBirdTime && birdSounds.Length > 0)
            {
                PlayRandomBirdSound();
                nextBirdTime = Time.time + Random.Range(birdInterval.x, birdInterval.y);
            }
        }
        
        void PlayRandomBirdSound()
        {
            if (birdSounds.Length == 0) return;
            
            AudioClip clip = birdSounds[Random.Range(0, birdSounds.Length)];
            
            // Random position around player (but above)
            Vector3 randomPos = playerTransform.position + new Vector3(
                Random.Range(-20f, 20f),
                Random.Range(5f, 15f),
                Random.Range(-20f, 20f)
            );
            
            AudioSource.PlayClipAtPoint(clip, randomPos, 0.5f);
        }
        
        /// <summary>
        /// Play a paddle stroke sound.
        /// </summary>
        public void PlayPaddleSound()
        {
            if (paddleSounds.Length == 0) return;
            
            AudioClip clip = paddleSounds[Random.Range(0, paddleSounds.Length)];
            
            // Play at player position
            if (playerTransform != null)
            {
                AudioSource.PlayClipAtPoint(clip, playerTransform.position, 0.7f);
            }
        }
        
        /// <summary>
        /// Play a one-shot sound effect.
        /// </summary>
        public void PlaySFX(AudioClip clip, Vector3 position, float volume = 1f)
        {
            if (clip == null) return;
            AudioSource.PlayClipAtPoint(clip, position, volume);
        }
        
        /// <summary>
        /// Set master volume (0-1).
        /// </summary>
        public void SetMasterVolume(float volume)
        {
            volume = Mathf.Clamp01(volume);
            float db = volume > 0.0001f ? 20f * Mathf.Log10(volume) : -80f;
            masterMixer?.SetFloat("MasterVolume", db);
        }
        
        /// <summary>
        /// Set music volume (0-1).
        /// </summary>
        public void SetMusicVolume(float volume)
        {
            musicVolume = Mathf.Clamp01(volume);
            if (musicSource != null)
            {
                musicSource.volume = musicVolume;
            }
        }
        
        /// <summary>
        /// Toggle music on/off.
        /// </summary>
        public void ToggleMusic()
        {
            if (musicSource != null)
            {
                musicSource.mute = !musicSource.mute;
            }
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
