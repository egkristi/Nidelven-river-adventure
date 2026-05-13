using UnityEngine;
using System.Collections.Generic;

namespace Nidelven.Environment
{
    /// <summary>
    /// Spawns and manages wildlife (birds, fish, deer) for environmental immersion.
    /// Issue #9: Wildlife System
    /// </summary>
    public class WildlifeSpawner : MonoBehaviour
    {
        [Header("References")]
        public RiverController river;
        public TerrainGenerator terrain;
        public Transform player;
        
        [Header("Birds")]
        public GameObject[] birdPrefabs;
        public int maxBirds = 20;
        public float birdSpawnRadius = 100f;
        public float birdSpawnInterval = 5f;
        
        [Header("Fish")]
        public GameObject[] fishPrefabs;
        public int maxFish = 10;
        public float fishSpawnDepth = -2f;
        
        [Header("Deer")]
        public GameObject[] deerPrefabs;
        public int maxDeer = 5;
        public float deerSpawnRadius = 80f;
        
        [Header("Spawn Settings")]
        public float despawnDistance = 150f;
        public LayerMask spawnLayers;
        
        private List<GameObject> activeWildlife = new List<GameObject>();
        private float birdTimer = 0f;
        private float deerTimer = 0f;
        
        void Update()
        {
            // Spawn birds
            birdTimer += Time.deltaTime;
            if (birdTimer >= birdSpawnInterval)
            {
                SpawnBirds();
                birdTimer = 0f;
            }
            
            // Spawn deer
            deerTimer += Time.deltaTime;
            if (deerTimer >= birdSpawnInterval * 3f)
            {
                SpawnDeer();
                deerTimer = 0f;
            }
            
            // Cleanup distant wildlife
            CleanupWildlife();
        }
        
        void SpawnBirds()
        {
            if (birdPrefabs.Length == 0) return;
            if (CountWildlifeOfType("Bird") >= maxBirds) return;
            
            if (player == null) return;
            
            // Spawn around player
            Vector3 spawnPos = player.position + Random.insideUnitSphere * birdSpawnRadius;
            spawnPos.y = Random.Range(20f, 50f); // Height in sky
            
            GameObject bird = Instantiate(
                birdPrefabs[Random.Range(0, birdPrefabs.Length)],
                spawnPos,
                Quaternion.identity
            );
            
            bird.tag = "Bird";
            activeWildlife.Add(bird);
            
            // Setup bird behavior
            BirdBehavior behavior = bird.GetComponent<BirdBehavior>();
            if (behavior == null) behavior = bird.AddComponent<BirdBehavior>();
            behavior.Initialize(player);
        }
        
        void SpawnDeer()
        {
            if (deerPrefabs.Length == 0) return;
            if (CountWildlifeOfType("Deer") >= maxDeer) return;
            if (player == null) return;
            
            // Spawn on terrain near river
            Vector3 spawnPos = player.position + Random.insideUnitSphere * deerSpawnRadius;
            
            if (terrain != null)
            {
                spawnPos.y = terrain.GetHeightAt(spawnPos);
            }
            
            // Check distance from river
            if (river != null)
            {
                float riverDist = river.GetClosestProgress(spawnPos);
                if (riverDist < 20f) return; // Too close to river
            }
            
            GameObject deer = Instantiate(
                deerPrefabs[Random.Range(0, deerPrefabs.Length)],
                spawnPos,
                Quaternion.Euler(0, Random.Range(0f, 360f), 0)
            );
            
            deer.tag = "Deer";
            activeWildlife.Add(deer);
            
            // Setup deer behavior
            DeerBehavior behavior = deer.GetComponent<DeerBehavior>();
            if (behavior == null) behavior = deer.AddComponent<DeerBehavior>();
            behavior.Initialize(player, river);
        }
        
        void CleanupWildlife()
        {
            if (player == null) return;
            
            for (int i = activeWildlife.Count - 1; i >= 0; i--)
            {
                if (activeWildlife[i] == null)
                {
                    activeWildlife.RemoveAt(i);
                    continue;
                }
                
                float distance = Vector3.Distance(player.position, activeWildlife[i].transform.position);
                if (distance > despawnDistance)
                {
                    Destroy(activeWildlife[i]);
                    activeWildlife.RemoveAt(i);
                }
            }
        }
        
        int CountWildlifeOfType(string tag)
        {
            int count = 0;
            foreach (var wildlife in activeWildlife)
            {
                if (wildlife != null && wildlife.CompareTag(tag))
                    count++;
            }
            return count;
        }
        
        void OnDrawGizmosSelected()
        {
            if (player == null) return;
            
            Gizmos.color = Color.yellow;
            Gizmos.DrawWireSphere(player.position, birdSpawnRadius);
            
            Gizmos.color = Color.green;
            Gizmos.DrawWireSphere(player.position, deerSpawnRadius);
        }
    }
    
    // Bird behavior component
    public class BirdBehavior : MonoBehaviour
    {
        private Transform player;
        private Vector3 flyDirection;
        private float speed;
        
        public void Initialize(Transform target)
        {
            player = target;
            flyDirection = Random.insideUnitSphere;
            flyDirection.y = 0;
            speed = Random.Range(5f, 10f);
        }
        
        void Update()
        {
            if (player == null) return;
            
            // Fly in direction
            transform.position += flyDirection * speed * Time.deltaTime;
            
            // Circle around area
            transform.Rotate(Vector3.up, Random.Range(-1f, 1f));
            
            // Face direction
            transform.rotation = Quaternion.LookRotation(flyDirection);
        }
    }
    
    // Deer behavior component
    public class DeerBehavior : MonoBehaviour
    {
        private Transform player;
        private RiverController river;
        private Vector3 targetPos;
        private float idleTimer;
        private bool isGrazing = true;
        
        public void Initialize(Transform playerRef, RiverController riverRef)
        {
            player = playerRef;
            river = riverRef;
            idleTimer = Random.Range(2f, 5f);
        }
        
        void Update()
        {
            if (player == null) return;
            
            float distanceToPlayer = Vector3.Distance(transform.position, player.position);
            
            // Flee if player too close
            if (distanceToPlayer < 30f)
            {
                Vector3 fleeDir = (transform.position - player.position).normalized;
                transform.position += fleeDir * 5f * Time.deltaTime;
                transform.rotation = Quaternion.LookRotation(fleeDir);
                isGrazing = false;
            }
            else
            {
                IdleBehavior();
            }
        }
        
        void IdleBehavior()
        {
            idleTimer -= Time.deltaTime;
            
            if (idleTimer <= 0)
            {
                // Pick new random target
                targetPos = transform.position + Random.insideUnitSphere * 20f;
                targetPos.y = transform.position.y;
                isGrazing = !isGrazing;
                idleTimer = Random.Range(3f, 8f);
            }
            
            if (!isGrazing)
            {
                // Move to target
                Vector3 dir = (targetPos - transform.position).normalized;
                transform.position += dir * 2f * Time.deltaTime;
                transform.rotation = Quaternion.LookRotation(dir);
            }
        }
    }
}
