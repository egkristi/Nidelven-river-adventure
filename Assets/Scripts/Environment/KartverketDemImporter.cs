using UnityEngine;
using System.IO;

namespace Nidelven.Environment
{
    /// <summary>
    /// Imports DEM data from Kartverket (Norwegian Mapping Authority).
    /// Loads 16-bit RAW files and metadata JSON.
    /// </summary>
    public class KartverketDemImporter : MonoBehaviour
    {
        [Header("Data Source")]
        [Tooltip("Path to .raw file (in StreamingAssets or absolute)")]
        public string rawFilePath = "DEM/nidelven_amli_10m.raw";
        
        [Tooltip("Path to metadata JSON (optional)")]
        public string metadataPath = "DEM/nidelven_amli_10m.json";
        
        [Header("Import Settings")]
        [Tooltip("Flip Y coordinate (Unity vs GIS convention)")]
        public bool flipY = true;
        
        [Tooltip("Height scale multiplier")]
        public float heightScale = 1f;
        
        [Tooltip("Override terrain size (0 = use metadata)")]
        public Vector3 terrainSizeOverride = Vector3.zero;
        
        // Loaded data
        private float[,] heightData;
        private DemMetadata metadata;
        
        [System.Serializable]
        public class DemMetadata
        {
            public int width;
            public int height;
            public float elevation_min;
            public float elevation_max;
            public float height_scale;
            public int depth;
            public string byte_order;
        }
        
        void Start()
        {
            ImportDem();
        }
        
        /// <summary>
        /// Import DEM and apply to attached Terrain.
        /// </summary>
        public void ImportDem()
        {
            string fullRawPath = GetFullPath(rawFilePath);
            string fullMetaPath = GetFullPath(metadataPath);
            
            if (!File.Exists(fullRawPath))
            {
                Debug.LogError($"DEM file not found: {fullRawPath}");
                return;
            }
            
            // Load metadata
            if (File.Exists(fullMetaPath))
            {
                LoadMetadata(fullMetaPath);
            }
            else
            {
                Debug.LogWarning($"Metadata not found: {fullMetaPath}. Using defaults.");
                metadata = new DemMetadata { width = 512, height = 512 };
            }
            
            // Load height data
            if (LoadRawFile(fullRawPath))
            {
                ApplyToTerrain();
            }
        }
        
        void LoadMetadata(string path)
        {
            string json = File.ReadAllText(path);
            metadata = JsonUtility.FromJson<DemMetadata>(json);
            
            Debug.Log($"Loaded metadata: {metadata.width}x{metadata.height}, " +
                     $"elevation {metadata.elevation_min:F1}m - {metadata.elevation_max:F1}m");
        }
        
        bool LoadRawFile(string path)
        {
            try
            {
                byte[] bytes = File.ReadAllBytes(path);
                
                int width = metadata.width;
                int height = metadata.height;
                
                heightData = new float[height, width];
                
                // Read 16-bit values (big-endian)
                for (int y = 0; y < height; y++)
                {
                    for (int x = 0; x < width; x++)
                    {
                        int idx = (y * width + x) * 2;
                        
                        if (idx + 1 < bytes.Length)
                        {
                            // Big-endian
                            ushort value = (ushort)((bytes[idx] << 8) | bytes[idx + 1]);
                            
                            // Normalize to 0-1
                            float normalized = value / 65535f;
                            
                            // Apply height scale from metadata
                            if (metadata.height_scale > 0)
                            {
                                // Convert to meters then normalize for Unity
                                float meters = metadata.elevation_min + normalized * 
                                              (metadata.elevation_max - metadata.elevation_min);
                                normalized = meters / metadata.height_scale;
                            }
                            
                            // Flip Y for Unity
                            int targetY = flipY ? (height - 1 - y) : y;
                            heightData[targetY, x] = normalized;
                        }
                    }
                }
                
                Debug.Log($"Loaded DEM: {width}x{height}");
                return true;
            }
            catch (System.Exception e)
            {
                Debug.LogError($"Failed to load RAW file: {e.Message}");
                return false;
            }
        }
        
        void ApplyToTerrain()
        {
            Terrain terrain = GetComponent<Terrain>();
            if (terrain == null)
            {
                Debug.LogError("No Terrain component found.");
                return;
            }
            
            TerrainData terrainData = terrain.terrainData;
            
            // Set terrain size
            Vector3 size = terrainSizeOverride != Vector3.zero ? 
                          terrainSizeOverride : terrainData.size;
            
            if (metadata != null && terrainSizeOverride == Vector3.zero)
            {
                // Calculate size from bbox (would need actual coordinates)
                // For now, use reasonable defaults
                size = new Vector3(2000f, 500f, 2000f);
            }
            
            terrainData.size = size;
            terrainData.heightmapResolution = heightData.GetLength(1);
            
            // Apply heights
            terrainData.SetHeights(0, 0, heightData);
            
            Debug.Log($"Applied DEM to terrain: {size}");
        }
        
        string GetFullPath(string relativePath)
        {
            if (Path.IsPathRooted(relativePath))
            {
                return relativePath;
            }
            
            return Path.Combine(Application.streamingAssetsPath, relativePath);
        }
        
        /// <summary>
        /// Get height at world position (for river alignment).
        /// </summary>
        public float GetHeightAt(float x, float z)
        {
            if (heightData == null) return 0f;
            
            // Convert world to heightmap coordinates
            Terrain terrain = GetComponent<Terrain>();
            if (terrain == null) return 0f;
            
            TerrainData td = terrain.terrainData;
            float normX = (x / td.size.x) + 0.5f;
            float normZ = (z / td.size.z) + 0.5f;
            
            return td.GetInterpolatedHeight(normX, normZ);
        }
    }
}
