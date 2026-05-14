using UnityEngine;
using System.Collections.Generic;
using System.IO;

namespace Nidelven.Environment
{
    /// <summary>
    /// Manages the river - creates the river mesh, handles flow visualization,
    /// and provides trajectory data for camera following.
    /// </summary>
    public class RiverController : MonoBehaviour
    {
        [Header("River Path")]
        [Tooltip("Number of points along the river path")]
        public int pathResolution = 100;
        
        [Tooltip("River width in meters")]
        public float baseWidth = 20f;
        
        [Tooltip("River width variation")]
        public AnimationCurve widthCurve = AnimationCurve.Linear(0, 1, 1, 0.5f);
        
        [Header("Flow")]
        [Tooltip("Base flow speed")]
        public float baseFlowSpeed = 1f;
        
        [Tooltip("Flow speed variation along river")]
        public AnimationCurve flowSpeedCurve = AnimationCurve.EaseInOut(0, 0.5f, 1, 2f);
        
        [Header("Visual")]
        [Tooltip("Water material")]
        public Material waterMaterial;
        
        [Tooltip("River depth")]
        public float riverDepth = 2f;
        
        [Tooltip("Wave amplitude")]
        public float waveHeight = 0.3f;
        
        [Tooltip("Wave speed")]
        public float waveSpeed = 2f;
        
        [Header("Terrain Integration")]
        [Tooltip("Reference to terrain generator for height sampling")]
        public TerrainGenerator terrainGenerator;
        
        [Tooltip("Height offset from terrain")]
        public float waterLevelOffset = -1f;
        
        [Tooltip("Load river path from StreamingAssets/river_path.json if available")]
        public bool loadFromFile = true;
        
        // Generated river data
        [HideInInspector]
        public List<Vector3> riverPath = new List<Vector3>();
        
        [HideInInspector]
        public List<float> flowSpeeds = new List<float>();
        
        [HideInInspector]
        public List<float> riverWidths = new List<float>();
        
        private Mesh riverMesh;
        private MeshFilter meshFilter;
        private MeshRenderer meshRenderer;
        
        // For flow animation
        private Vector2 uvOffset = Vector2.zero;
        
        void Start()
        {
            GenerateRiver();
        }
        
        void Update()
        {
            // Animate water UVs for flow effect
            if (waterMaterial != null)
            {
                uvOffset.y += baseFlowSpeed * waveSpeed * Time.deltaTime * 0.1f;
                waterMaterial.SetVector("_FlowOffset", new Vector4(uvOffset.x, uvOffset.y, 0, 0));
                waterMaterial.SetFloat("_Time", Time.time);
            }
        }
        
        /// <summary>
        /// Generate the river path and mesh.
        /// </summary>
        public void GenerateRiver()
        {
            GenerateRiverPath();
            CreateRiverMesh();
            SetupComponents();
        }
        
        /// <summary>
        /// Generate the river trajectory following terrain elevation.
        /// Tries to load from StreamingAssets/river_path.json first.
        /// </summary>
        void GenerateRiverPath()
        {
            riverPath.Clear();
            flowSpeeds.Clear();
            riverWidths.Clear();
            
            if (loadFromFile && TryLoadRiverPathFromFile())
            {
                Debug.Log($"River path loaded from file: {riverPath.Count} points");
                return;
            }
            
            // Fallback: generate synthetic path
            
            // Start at one edge of terrain
            Vector3 startPos = new Vector3(0, 0, -500f);
            Vector3 endPos = new Vector3(0, 0, 500f);
            
            // Sample terrain height at start
            if (terrainGenerator != null)
            {
                startPos.y = terrainGenerator.GetHeightAt(startPos) + waterLevelOffset;
            }
            
            // Generate path using gradient following
            Vector3 currentPos = startPos;
            riverPath.Add(currentPos);
            flowSpeeds.Add(baseFlowSpeed);
            riverWidths.Add(baseWidth * widthCurve.Evaluate(0f));
            
            for (int i = 1; i < pathResolution; i++)
            {
                float t = i / (float)(pathResolution - 1);
                
                // Move towards end
                Vector3 targetPos = Vector3.Lerp(startPos, endPos, t);
                
                // Add meandering
                float meander = Mathf.Sin(t * Mathf.PI * 3f) * 100f;
                targetPos.x += meander;
                
                // Sample terrain height
                float terrainHeight = 0;
                if (terrainGenerator != null)
                {
                    terrainHeight = terrainGenerator.GetHeightAt(targetPos);
                }
                
                targetPos.y = terrainHeight + waterLevelOffset;
                
                // Calculate flow speed based on elevation drop
                float elevationDrop = riverPath[riverPath.Count - 1].y - targetPos.y;
                float flowSpeed = baseFlowSpeed + elevationDrop * 10f;
                flowSpeed = Mathf.Clamp(flowSpeed, baseFlowSpeed * 0.5f, baseFlowSpeed * 3f);
                
                // Calculate width
                float widthVariation = widthCurve.Evaluate(t);
                float width = baseWidth * widthVariation;
                
                riverPath.Add(targetPos);
                flowSpeeds.Add(flowSpeed);
                riverWidths.Add(width);
            }
            
            Debug.Log($"River path generated: {riverPath.Count} points");
        }
        
        /// <summary>
        /// Try to load river path from StreamingAssets/river_path.json.
        /// JSON format: { "points": [[x,y,z], ...], "widths": [...], "speeds": [...] }
        /// </summary>
        bool TryLoadRiverPathFromFile()
        {
            string path = Path.Combine(Application.streamingAssetsPath, "river_path.json");
            if (!File.Exists(path)) return false;
            
            try
            {
                string json = File.ReadAllText(path);
                RiverPathData data = JsonUtility.FromJson<RiverPathData>(json);
                
                if (data == null || data.points == null || data.points.Length < 2)
                    return false;
                
                for (int i = 0; i < data.points.Length; i++)
                {
                    Vector3 pos = new Vector3(data.points[i].x, data.points[i].y, data.points[i].z);
                    
                    // Optionally re-sample height from terrain
                    if (terrainGenerator != null)
                    {
                        float terrainHeight = terrainGenerator.GetHeightAt(pos);
                        pos.y = terrainHeight + waterLevelOffset;
                    }
                    
                    riverPath.Add(pos);
                    
                    float t = i / (float)(data.points.Length - 1);
                    float speed = (data.speeds != null && i < data.speeds.Length) 
                        ? data.speeds[i] 
                        : baseFlowSpeed * flowSpeedCurve.Evaluate(t);
                    float width = (data.widths != null && i < data.widths.Length) 
                        ? data.widths[i] 
                        : baseWidth * widthCurve.Evaluate(t);
                    
                    flowSpeeds.Add(speed);
                    riverWidths.Add(width);
                }
                
                return true;
            }
            catch (System.Exception e)
            {
                Debug.LogWarning($"Failed to load river_path.json: {e.Message}");
                return false;
            }
        }
        
        [System.Serializable]
        private class RiverPathData
        {
            public RiverPoint[] points;
            public float[] widths;
            public float[] speeds;
        }
        
        [System.Serializable]
        private class RiverPoint
        {
            public float x;
            public float y;
            public float z;
        }
        
        /// <summary>
        /// Create the river surface mesh.
        /// </summary>
        void CreateRiverMesh()
        {
            if (riverPath.Count < 2) return;
            
            riverMesh = new Mesh();
            riverMesh.name = "RiverMesh";
            
            List<Vector3> vertices = new List<Vector3>();
            List<Vector2> uvs = new List<Vector2>();
            List<Vector3> normals = new List<Vector3>();
            List<int> triangles = new List<int>();
            
            for (int i = 0; i < riverPath.Count; i++)
            {
                Vector3 point = riverPath[i];
                float width = riverWidths[i];
                
                // Calculate tangent direction
                Vector3 tangent;
                if (i == 0)
                {
                    tangent = riverPath[i + 1] - point;
                }
                else if (i == riverPath.Count - 1)
                {
                    tangent = point - riverPath[i - 1];
                }
                else
                {
                    tangent = riverPath[i + 1] - riverPath[i - 1];
                }
                tangent.Normalize();
                
                // Calculate perpendicular
                Vector3 perpendicular = Vector3.Cross(tangent, Vector3.up).normalized;
                
                // Left and right bank
                Vector3 leftBank = point - perpendicular * width * 0.5f;
                Vector3 rightBank = point + perpendicular * width * 0.5f;
                
                vertices.Add(leftBank);
                vertices.Add(rightBank);
                
                // UVs
                float v = i / (float)(riverPath.Count - 1);
                uvs.Add(new Vector2(0, v));
                uvs.Add(new Vector2(1, v));
                
                // Normals
                normals.Add(Vector3.up);
                normals.Add(Vector3.up);
            }
            
            // Generate triangles
            for (int i = 0; i < riverPath.Count - 1; i++)
            {
                int baseIdx = i * 2;
                
                // First triangle
                triangles.Add(baseIdx);
                triangles.Add(baseIdx + 1);
                triangles.Add(baseIdx + 2);
                
                // Second triangle
                triangles.Add(baseIdx + 1);
                triangles.Add(baseIdx + 3);
                triangles.Add(baseIdx + 2);
            }
            
            riverMesh.vertices = vertices.ToArray();
            riverMesh.uv = uvs.ToArray();
            riverMesh.normals = normals.ToArray();
            riverMesh.triangles = triangles.ToArray();
            
            riverMesh.RecalculateBounds();
            riverMesh.RecalculateNormals();
        }
        
        void SetupComponents()
        {
            meshFilter = GetComponent<MeshFilter>();
            if (meshFilter == null)
            {
                meshFilter = gameObject.AddComponent<MeshFilter>();
            }
            meshFilter.mesh = riverMesh;
            
            meshRenderer = GetComponent<MeshRenderer>();
            if (meshRenderer == null)
            {
                meshRenderer = gameObject.AddComponent<MeshRenderer>();
            }
            
            if (waterMaterial != null)
            {
                meshRenderer.material = waterMaterial;
            }
        }
        
        /// <summary>
        /// Get position along river at given progress (0-1).
        /// </summary>
        public Vector3 GetPositionOnRiver(float progress)
        {
            progress = Mathf.Clamp01(progress);
            
            if (riverPath.Count == 0) return Vector3.zero;
            if (riverPath.Count == 1) return riverPath[0];
            
            float indexF = progress * (riverPath.Count - 1);
            int index = Mathf.FloorToInt(indexF);
            float t = indexF - index;
            
            if (index >= riverPath.Count - 1)
            {
                return riverPath[riverPath.Count - 1];
            }
            
            return Vector3.Lerp(riverPath[index], riverPath[index + 1], t);
        }
        
        /// <summary>
        /// Get forward direction at given progress.
        /// </summary>
        public Vector3 GetForwardOnRiver(float progress)
        {
            progress = Mathf.Clamp01(progress);
            
            if (riverPath.Count < 2) return Vector3.forward;
            
            float indexF = progress * (riverPath.Count - 1);
            int index = Mathf.FloorToInt(indexF);
            
            if (index >= riverPath.Count - 1)
            {
                return (riverPath[riverPath.Count - 1] - riverPath[riverPath.Count - 2]).normalized;
            }
            
            return (riverPath[index + 1] - riverPath[index]).normalized;
        }
        
        /// <summary>
        /// Get flow speed at given progress.
        /// </summary>
        public float GetFlowSpeedAt(float progress)
        {
            progress = Mathf.Clamp01(progress);
            
            if (flowSpeeds.Count == 0) return baseFlowSpeed;
            
            float indexF = progress * (flowSpeeds.Count - 1);
            int index = Mathf.FloorToInt(indexF);
            float t = indexF - index;
            
            if (index >= flowSpeeds.Count - 1)
            {
                return flowSpeeds[flowSpeeds.Count - 1];
            }
            
            return Mathf.Lerp(flowSpeeds[index], flowSpeeds[index + 1], t);
        }
        
        // Cache last search index for O(1) amortized closest-point lookup
        private int lastClosestIndex = 0;
        
        /// <summary>
        /// Get closest point on river to world position.
        /// Uses local search around last known position for O(1) amortized performance.
        /// </summary>
        public float GetClosestProgress(Vector3 worldPos)
        {
            if (riverPath.Count <= 1) return 0f;
            
            float closestDistSqr = float.MaxValue;
            int closestIdx = lastClosestIndex;
            
            // Search locally first (±10 indices from last position)
            int searchRadius = 10;
            int start = Mathf.Max(0, lastClosestIndex - searchRadius);
            int end = Mathf.Min(riverPath.Count, lastClosestIndex + searchRadius);
            
            for (int i = start; i < end; i++)
            {
                float distSqr = (worldPos - riverPath[i]).sqrMagnitude;
                if (distSqr < closestDistSqr)
                {
                    closestDistSqr = distSqr;
                    closestIdx = i;
                }
            }
            
            // If best is at boundary of local search, do full search
            if (closestIdx == start || closestIdx == end - 1)
            {
                for (int i = 0; i < riverPath.Count; i++)
                {
                    float distSqr = (worldPos - riverPath[i]).sqrMagnitude;
                    if (distSqr < closestDistSqr)
                    {
                        closestDistSqr = distSqr;
                        closestIdx = i;
                    }
                }
            }
            
            lastClosestIndex = closestIdx;
            return closestIdx / (float)(riverPath.Count - 1);
        }
        
        void OnDrawGizmos()
        {
            // Draw river path in editor
            if (riverPath.Count > 0)
            {
                Gizmos.color = Color.cyan;
                
                for (int i = 0; i < riverPath.Count - 1; i++)
                {
                    Gizmos.DrawLine(riverPath[i], riverPath[i + 1]);
                }
                
                // Draw points
                Gizmos.color = Color.blue;
                foreach (var point in riverPath)
                {
                    Gizmos.DrawWireSphere(point, 2f);
                }
            }
        }
    }
}
