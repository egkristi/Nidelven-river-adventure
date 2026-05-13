using UnityEngine;
using UnityEngine.UI;
using System.Collections;

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
