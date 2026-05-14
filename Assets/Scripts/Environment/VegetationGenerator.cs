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
        
        private List<Matrix4x4> treeMatrices = new List<Matrix4x4>();
        private List<Matrix4x4> rockMatrices = new List<Matrix4x4>();
        private MaterialPropertyBlock propertyBlock;
        
        // Pre-allocated batch arrays to avoid GC pressure (PF2 fix)
        private Matrix4x4[][] treeBatches;
        private int[] treeBatchCounts;
        private Matrix4x4[][] rockBatches;
        private int[] rockBatchCounts;
        
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
            
            PreAllocateBatches();
            
            Debug.Log($"Generated {treeMatrices.Count} trees and {rockMatrices.Count} rocks");
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
            
            // Render trees
            if (treeBatches != null)
            {
                for (int meshIdx = 0; meshIdx < treeMeshes.Length; meshIdx++)
                {
                    Mesh mesh = treeMeshes[meshIdx];
                    Material mat = treeMaterials[meshIdx % treeMaterials.Length];
                    
                    if (mesh != null && mat != null)
                    {
                        for (int b = 0; b < treeBatches.Length; b++)
                        {
                            Graphics.DrawMeshInstanced(mesh, 0, mat, treeBatches[b], treeBatchCounts[b], propertyBlock);
                        }
                    }
                }
            }
            
            // Render rocks
            if (rockBatches != null)
            {
                for (int meshIdx = 0; meshIdx < rockMeshes.Length; meshIdx++)
                {
                    Mesh mesh = rockMeshes[meshIdx];
                    Material mat = rockMaterials[meshIdx % rockMaterials.Length];
                    
                    if (mesh != null && mat != null)
                    {
                        for (int b = 0; b < rockBatches.Length; b++)
                        {
                            Graphics.DrawMeshInstanced(mesh, 0, mat, rockBatches[b], rockBatchCounts[b], propertyBlock);
                        }
                    }
                }
            }
        }
        
        void PreAllocateBatches()
        {
            treeBatches = BuildBatches(treeMatrices, out treeBatchCounts);
            rockBatches = BuildBatches(rockMatrices, out rockBatchCounts);
        }
        
        static Matrix4x4[][] BuildBatches(List<Matrix4x4> matrices, out int[] batchCounts)
        {
            int totalBatches = (matrices.Count + 1022) / 1023;
            var batches = new Matrix4x4[totalBatches][];
            batchCounts = new int[totalBatches];
            
            for (int b = 0; b < totalBatches; b++)
            {
                int start = b * 1023;
                int count = Mathf.Min(1023, matrices.Count - start);
                batches[b] = new Matrix4x4[1023];
                batchCounts[b] = count;
                for (int i = 0; i < count; i++)
                {
                    batches[b][i] = matrices[start + i];
                }
            }
            
            return batches;
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
