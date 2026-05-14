using UnityEngine;
using System.Collections.Generic;

namespace Nidelven.Environment
{
    /// <summary>
    /// Generates vegetation (trees, rocks) on terrain based on elevation and slope.
    /// Uses GPU instancing for performance.
    /// </summary>
    public class VegetationGenerator : MonoBehaviour
    {
        [Header("Terrain")]
        public TerrainGenerator terrain;
        public RiverController river;
        
        [Header("Trees")]
        public Mesh[] treeMeshes;
        public Material[] treeMaterials;
        public int treeCount = 500;
        
        [Header("Placement Rules")]
        [Tooltip("Minimum elevation for trees")]
        public float minElevation = 5f;
        
        [Tooltip("Maximum slope angle for trees")]
        public float maxSlopeAngle = 30f;
        
        [Tooltip("Minimum distance from river")]
        public float riverBuffer = 15f;
        
        [Header("Rocks")]
        public Mesh[] rockMeshes;
        public Material[] rockMaterials;
        public int rockCount = 100;
        
        [Header("Performance")]
        public bool useGPUInstancing = true;
        public bool generateOnStart = true;
        
        [Header("LOD")]
        [Tooltip("Maximum render distance for trees")]
        public float treeLODDistance = 200f;
        [Tooltip("Maximum render distance for rocks")]
        public float rockLODDistance = 100f;
        [Tooltip("Distance at which trees/rocks start fading (fraction of max)")]
        [Range(0.5f, 1f)]
        public float lodFadeStart = 0.7f;
        
        private List<Matrix4x4> treeMatrices = new List<Matrix4x4>();
        private List<Matrix4x4> rockMatrices = new List<Matrix4x4>();
        private Vector3[] treePositions;
        private Vector3[] rockPositions;
        private MaterialPropertyBlock propertyBlock;
        
        // LOD working buffers (pre-allocated)
        private Matrix4x4[] lodBuffer;
        private Camera mainCamera;
        
        void Start()
        {
            if (generateOnStart)
            {
                GenerateVegetation();
            }
        }
        
        void Update()
        {
            if (useGPUInstancing)
            {
                RenderInstanced();
            }
        }
        
        public void GenerateVegetation()
        {
            if (terrain == null)
            {
                Debug.LogError("VegetationGenerator: Terrain reference required");
                return;
            }
            
            treeMatrices.Clear();
            rockMatrices.Clear();
            
            GenerateTrees();
            GenerateRocks();
            
            // Cache positions for LOD distance checks
            treePositions = new Vector3[treeMatrices.Count];
            for (int i = 0; i < treeMatrices.Count; i++)
                treePositions[i] = treeMatrices[i].GetColumn(3);
            
            rockPositions = new Vector3[rockMatrices.Count];
            for (int i = 0; i < rockMatrices.Count; i++)
                rockPositions[i] = rockMatrices[i].GetColumn(3);
            
            // Pre-allocate LOD working buffer (max possible batch)
            int maxCount = Mathf.Max(treeMatrices.Count, rockMatrices.Count);
            lodBuffer = new Matrix4x4[Mathf.Min(maxCount, 1023)];
            
            Debug.Log($"Generated {treeMatrices.Count} trees and {rockMatrices.Count} rocks (LOD: trees {treeLODDistance}m, rocks {rockLODDistance}m)");
        }
        
        void GenerateTrees()
        {
            if (treeMeshes.Length == 0 || treeMaterials.Length == 0) return;
            
            Vector3 terrainSize = terrain.terrainSize;
            int attempts = 0;
            int placed = 0;
            
            while (placed < treeCount && attempts < treeCount * 10)
            {
                attempts++;
                
                // Random position on terrain
                Vector3 pos = new Vector3(
                    Random.Range(-terrainSize.x * 0.5f, terrainSize.x * 0.5f),
                    0,
                    Random.Range(-terrainSize.z * 0.5f, terrainSize.z * 0.5f)
                );
                
                // Check if position is valid
                if (IsValidPosition(pos))
                {
                    // Sample terrain height
                    pos.y = terrain.GetHeightAt(pos);
                    
                    // Random rotation
                    Quaternion rot = Quaternion.Euler(0, Random.Range(0f, 360f), 0);
                    
                    // Random scale variation
                    float scale = Random.Range(0.8f, 1.2f);
                    Vector3 scl = Vector3.one * scale;
                    
                    treeMatrices.Add(Matrix4x4.TRS(pos, rot, scl));
                    placed++;
                }
            }
        }
        
        void GenerateRocks()
        {
            if (rockMeshes.Length == 0 || rockMaterials.Length == 0) return;
            
            Vector3 terrainSize = terrain.terrainSize;
            int attempts = 0;
            int placed = 0;
            
            while (placed < rockCount && attempts < rockCount * 10)
            {
                attempts++;
                
                // Prefer higher elevations and steeper slopes
                Vector3 pos = new Vector3(
                    Random.Range(-terrainSize.x * 0.5f, terrainSize.x * 0.5f),
                    0,
                    Random.Range(-terrainSize.z * 0.5f, terrainSize.z * 0.5f)
                );
                
                if (IsValidPosition(pos, true))
                {
                    pos.y = terrain.GetHeightAt(pos);
                    
                    Quaternion rot = Random.rotation;
                    float scale = Random.Range(0.5f, 2f);
                    
                    rockMatrices.Add(Matrix4x4.TRS(pos, rot, Vector3.one * scale));
                    placed++;
                }
            }
        }
        
        bool IsValidPosition(Vector3 pos, bool isRock = false)
        {
            // Check elevation
            float height = terrain.GetHeightAt(pos);
            if (height < minElevation && !isRock) return false;
            
            // Check slope
            Vector3 normal = terrain.GetNormalAt(pos);
            float slope = Vector3.Angle(normal, Vector3.up);
            if (slope > maxSlopeAngle && !isRock) return false;
            if (slope < 10f && isRock) return false; // Rocks need some slope
            
            // Check distance from river
            if (river != null)
            {
                float riverDist = DistanceToRiver(pos);
                if (riverDist < riverBuffer) return false;
            }
            
            return true;
        }
        
        float DistanceToRiver(Vector3 pos)
        {
            if (river == null || river.riverPath.Count == 0) return float.MaxValue;
            
            float minDist = float.MaxValue;
            
            // Sample some points along river
            int step = Mathf.Max(1, river.riverPath.Count / 50);
            for (int i = 0; i < river.riverPath.Count; i += step)
            {
                float dist = Vector3.Distance(pos, river.riverPath[i]);
                minDist = Mathf.Min(minDist, dist);
            }
            
            return minDist;
        }
        
        void RenderInstanced()
        {
            if (propertyBlock == null)
            {
                propertyBlock = new MaterialPropertyBlock();
            }
            
            if (mainCamera == null)
                mainCamera = Camera.main;
            
            if (mainCamera == null) return;
            
            Vector3 camPos = mainCamera.transform.position;
            float treeLODSqr = treeLODDistance * treeLODDistance;
            float rockLODSqr = rockLODDistance * rockLODDistance;
            
            // Render trees with LOD culling
            if (treeMeshes.Length > 0 && treeMatrices.Count > 0)
            {
                RenderWithLOD(treeMeshes, treeMaterials, treeMatrices, treePositions, camPos, treeLODSqr);
            }
            
            // Render rocks with LOD culling
            if (rockMeshes.Length > 0 && rockMatrices.Count > 0)
            {
                RenderWithLOD(rockMeshes, rockMaterials, rockMatrices, rockPositions, camPos, rockLODSqr);
            }
        }
        
        void RenderWithLOD(Mesh[] meshes, Material[] materials, List<Matrix4x4> matrices, Vector3[] positions, Vector3 camPos, float maxDistSqr)
        {
            int count = 0;
            
            for (int i = 0; i < matrices.Count; i++)
            {
                float distSqr = (positions[i] - camPos).sqrMagnitude;
                if (distSqr > maxDistSqr) continue;
                
                lodBuffer[count] = matrices[i];
                count++;
                
                if (count >= 1023)
                {
                    FlushBatch(meshes, materials, lodBuffer, count);
                    count = 0;
                }
            }
            
            if (count > 0)
            {
                FlushBatch(meshes, materials, lodBuffer, count);
            }
        }
        
        void FlushBatch(Mesh[] meshes, Material[] materials, Matrix4x4[] batch, int count)
        {
            for (int meshIdx = 0; meshIdx < meshes.Length; meshIdx++)
            {
                Mesh mesh = meshes[meshIdx];
                Material mat = materials[meshIdx % materials.Length];
                if (mesh != null && mat != null)
                {
                    Graphics.DrawMeshInstanced(mesh, 0, mat, batch, count, propertyBlock);
                }
            }
        }
        
        void OnDrawGizmosSelected()
        {
            // Draw vegetation bounds
            if (terrain != null)
            {
                Gizmos.color = Color.green;
                Vector3 size = terrain.terrainSize;
                Gizmos.DrawWireCube(Vector3.zero, size);
            }
        }
    }
}
