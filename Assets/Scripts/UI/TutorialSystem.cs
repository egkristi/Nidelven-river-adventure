using UnityEngine;
using UnityEngine.UI;
using System.Collections;
using Nidelven.Core;

namespace Nidelven.UI
{
    /// <summary>
    /// Tutorial system for first-time players.
    /// Guides through basic controls and mechanics.
    /// </summary>
    public class TutorialSystem : MonoBehaviour
    {
        [System.Serializable]
        public class TutorialStep
        {
            public string title;
            [TextArea(3, 10)]
            public string description;
            public KeyCode waitForKey;
            public bool waitForTime;
            public float waitDuration;
            public bool requiresPlayerInput;
        }
        
        [Header("UI")]
        public GameObject tutorialPanel;
        public Text titleText;
        public Text descriptionText;
        public Button continueButton;
        public Button skipButton;
        
        [Header("Steps")]
        public TutorialStep[] tutorialSteps;
        
        [Header("Settings")]
        public bool showOnFirstLaunch = true;
        public string playerPrefKey = "TutorialCompleted";
        
        private int currentStep = 0;
        private bool isShowing = false;
        
        void Awake()
        {
            // If no steps assigned in Inspector, use built-in defaults
            if (tutorialSteps == null || tutorialSteps.Length == 0)
            {
                tutorialSteps = CreateDefaultSteps();
            }
        }
        
        TutorialStep[] CreateDefaultSteps()
        {
            return new TutorialStep[]
            {
                new TutorialStep
                {
                    title = "Welcome to Nidelven",
                    description = "You are kayaking on the Nidelven river in Agder, Norway.\nReal terrain data from Copernicus satellite elevation maps shapes the valley around you.\n\nPress any key to continue.",
                    waitForKey = KeyCode.None,
                    waitForTime = false,
                    requiresPlayerInput = false
                },
                new TutorialStep
                {
                    title = "Paddling",
                    description = "Use W to paddle forward.\nA and D steer left and right.\nS brakes against the current.\n\nPress W to continue.",
                    waitForKey = KeyCode.W,
                    waitForTime = false,
                    requiresPlayerInput = true
                },
                new TutorialStep
                {
                    title = "Sprinting",
                    description = "Hold SHIFT to sprint — this uses stamina.\nStamina recovers when you rest.\n\nPress SHIFT to continue.",
                    waitForKey = KeyCode.LeftShift,
                    waitForTime = false,
                    requiresPlayerInput = true
                },
                new TutorialStep
                {
                    title = "River Current",
                    description = "The river has a natural current that carries you downstream.\nSteer to avoid obstacles and enjoy the scenery.\n\nPress any key to continue.",
                    waitForKey = KeyCode.None,
                    waitForTime = false,
                    requiresPlayerInput = false
                },
                new TutorialStep
                {
                    title = "Photo Mode",
                    description = "Press F12 to enter Photo Mode.\nFreeze time, move the camera freely, and capture screenshots.\nAdjust brightness, contrast, and saturation with sliders.\n\nPress F12 to try it.",
                    waitForKey = KeyCode.F12,
                    waitForTime = false,
                    requiresPlayerInput = true
                },
                new TutorialStep
                {
                    title = "Ready to Explore",
                    description = "That's everything you need to know.\nEnjoy paddling through the Nidelven valley.\n\nPress ESC at any time for settings.\n\nPress any key to begin your journey.",
                    waitForKey = KeyCode.None,
                    waitForTime = false,
                    requiresPlayerInput = false
                }
            };
        }
        
        void Start()
        {
            // Check if tutorial already completed
            if (PlayerPrefs.GetInt(playerPrefKey, 0) == 1 && showOnFirstLaunch)
            {
                Debug.Log("Tutorial already completed");
                return;
            }
            
            // Setup buttons
            if (continueButton != null)
            {
                continueButton.onClick.AddListener(NextStep);
            }
            if (skipButton != null)
            {
                skipButton.onClick.AddListener(SkipTutorial);
            }
            
            // Start tutorial
            StartTutorial();
        }
        
        public void StartTutorial()
        {
            if (tutorialSteps.Length == 0) return;
            
            currentStep = 0;
            isShowing = true;
            ShowStep(currentStep);
            
            // Pause game
            if (GameManager.Instance != null)
                GameManager.Instance.RequestPause();
            else
                Time.timeScale = 0f;
        }
        
        void ShowStep(int index)
        {
            if (index >= tutorialSteps.Length)
            {
                CompleteTutorial();
                return;
            }
            
            TutorialStep step = tutorialSteps[index];
            
            if (tutorialPanel != null)
            {
                tutorialPanel.SetActive(true);
            }
            
            if (titleText != null)
            {
                titleText.text = $"{step.title} ({index + 1}/{tutorialSteps.Length})";
            }
            
            if (descriptionText != null)
            {
                descriptionText.text = step.description;
            }
            
            // Handle input waiting
            if (step.waitForTime)
            {
                StartCoroutine(WaitForTime(step.waitDuration));
            }
        }
        
        IEnumerator WaitForTime(float duration)
        {
            yield return new WaitForSecondsRealtime(duration);
            NextStep();
        }
        
        void Update()
        {
            if (!isShowing) return;
            
            TutorialStep step = tutorialSteps[currentStep];
            
            // Check for key press
            if (step.waitForKey != KeyCode.None)
            {
                if (Input.GetKeyDown(step.waitForKey))
                {
                    NextStep();
                }
            }
            
            // Alternative: any key to continue
            if (!step.requiresPlayerInput && Input.anyKeyDown)
            {
                if (Input.GetKeyDown(KeyCode.Escape))
                {
                    SkipTutorial();
                }
                else
                {
                    NextStep();
                }
            }
        }
        
        public void NextStep()
        {
            currentStep++;
            
            if (currentStep >= tutorialSteps.Length)
            {
                CompleteTutorial();
            }
            else
            {
                ShowStep(currentStep);
            }
        }
        
        public void SkipTutorial()
        {
            Debug.Log("Tutorial skipped");
            CompleteTutorial();
        }
        
        void CompleteTutorial()
        {
            isShowing = false;
            
            if (tutorialPanel != null)
            {
                tutorialPanel.SetActive(false);
            }
            
            // Mark as completed
            PlayerPrefs.SetInt(playerPrefKey, 1);
            PlayerPrefs.Save();
            
            // Resume game
            if (GameManager.Instance != null)
                GameManager.Instance.ReleasePause();
            else
                Time.timeScale = 1f;
            
            Debug.Log("Tutorial completed");
        }
        
        void OnDestroy()
        {
            if (continueButton != null)
            {
                continueButton.onClick.RemoveListener(NextStep);
            }
            if (skipButton != null)
            {
                skipButton.onClick.RemoveListener(SkipTutorial);
            }
        }
    }
}
