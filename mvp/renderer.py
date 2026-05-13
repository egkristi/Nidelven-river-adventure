"""
3D Renderer for Nidelven River Adventure MVP.
Uses ModernGL for OpenGL rendering with:
- Terrain mesh rendering
- River surface rendering
- Camera following river trajectory
- Basic lighting and sky
"""

import numpy as np
import moderngl
import moderngl_window as mglw
from moderngl_window import geometry
from moderngl_window.scene import Camera
from pathlib import Path
from typing import Optional, Dict, List
import glm

# Vertex shader for terrain
TERRAIN_VERTEX_SHADER = """
#version 330

uniform mat4 mvp;
uniform mat4 model;
uniform vec3 light_dir;

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

out vec3 v_normal;
out vec2 v_uv;
out float v_height;
out vec3 v_world_pos;

void main() {
    v_world_pos = (model * vec4(in_position, 1.0)).xyz;
    v_normal = mat3(transpose(inverse(model))) * in_normal;
    v_uv = in_uv;
    v_height = in_position.y;
    
    gl_Position = mvp * vec4(in_position, 1.0);
}
"""

# Fragment shader for terrain
TERRAIN_FRAGMENT_SHADER = """
#version 330

uniform vec3 light_dir;
uniform vec3 camera_pos;
uniform float time;

in vec3 v_normal;
in vec2 v_uv;
in float v_height;
in vec3 v_world_pos;

out vec4 fragColor;

// Simple noise function
float hash(vec2 p) {
    return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453);
}

float noise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    f = f * f * (3.0 - 2.0 * f);
    
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    
    return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

void main() {
    // Normalize normal
    vec3 normal = normalize(v_normal);
    
    // Lighting
    float diff = max(dot(normal, -light_dir), 0.0);
    float ambient = 0.3;
    
    // Terrain coloring based on height
    vec3 low_color = vec3(0.2, 0.4, 0.1);    // Dark green (low)
    vec3 mid_color = vec3(0.4, 0.6, 0.2);    // Light green (mid)
    vec3 high_color = vec3(0.6, 0.5, 0.3);   // Brown (high)
    vec3 rock_color = vec3(0.5, 0.5, 0.5);   // Gray (peaks)
    
    // Normalize height to 0-1 range (approximate)
    float h = clamp(v_height / 20.0, 0.0, 1.0);
    
    vec3 color;
    if (h < 0.3) {
        color = mix(low_color, mid_color, h / 0.3);
    } else if (h < 0.7) {
        color = mix(mid_color, high_color, (h - 0.3) / 0.4);
    } else {
        color = mix(high_color, rock_color, (h - 0.7) / 0.3);
    }
    
    // Add noise for texture
    float n = noise(v_world_pos.xz * 0.5);
    color = mix(color, color * (0.8 + 0.4 * n), 0.3);
    
    // Apply lighting
    color *= (ambient + diff * 0.7);
    
    // Fog
    float fog_dist = length(v_world_pos - camera_pos);
    float fog_amount = 1.0 - exp(-fog_dist * 0.001);
    vec3 fog_color = vec3(0.6, 0.7, 0.8);
    color = mix(color, fog_color, clamp(fog_amount, 0.0, 0.7));
    
    fragColor = vec4(color, 1.0);
}
"""

# Vertex shader for water
WATER_VERTEX_SHADER = """
#version 330

uniform mat4 mvp;
uniform mat4 model;
uniform float time;

in vec3 in_position;
in vec3 in_normal;
in vec2 in_uv;

out vec3 v_normal;
out vec2 v_uv;
out vec3 v_world_pos;
out float v_flow_speed;

void main() {
    // Add wave displacement
    float wave1 = sin(in_position.x * 0.5 + time * 2.0) * 0.1;
    float wave2 = cos(in_position.z * 0.3 + time * 1.5) * 0.1;
    float wave3 = sin(in_position.x * 0.2 + in_position.z * 0.4 + time) * 0.05;
    
    vec3 displaced = in_position + vec3(0.0, wave1 + wave2 + wave3, 0.0);
    
    v_world_pos = (model * vec4(displaced, 1.0)).xyz;
    v_normal = mat3(transpose(inverse(model))) * in_normal;
    v_uv = in_uv;
    v_flow_speed = in_uv.x;  // Use U coordinate as flow speed indicator
    
    gl_Position = mvp * vec4(displaced, 1.0);
}
"""

# Fragment shader for water
WATER_FRAGMENT_SHADER = """
#version 330

uniform vec3 light_dir;
uniform vec3 camera_pos;
uniform float time;

in vec3 v_normal;
in vec2 v_uv;
in vec3 v_world_pos;
in float v_flow_speed;

out vec4 fragColor;

void main() {
    vec3 normal = normalize(v_normal);
    
    // Water colors
    vec3 deep_color = vec3(0.0, 0.1, 0.3);
    vec3 shallow_color = vec3(0.0, 0.3, 0.5);
    vec3 foam_color = vec3(0.9, 0.95, 1.0);
    
    // Mix based on flow speed
    vec3 color = mix(deep_color, shallow_color, v_flow_speed);
    
    // Add foam in rapids (high flow speed)
    float foam = smoothstep(0.6, 1.0, v_flow_speed);
    color = mix(color, foam_color, foam * 0.5);
    
    // Specular highlight
    vec3 view_dir = normalize(camera_pos - v_world_pos);
    vec3 half_dir = normalize(-light_dir + view_dir);
    float spec = pow(max(dot(normal, half_dir), 0.0), 64.0);
    color += vec3(0.3, 0.3, 0.3) * spec;
    
    // Fresnel
    float fresnel = pow(1.0 - max(dot(view_dir, normal), 0.0), 3.0);
    color = mix(color, vec3(0.6, 0.7, 0.8), fresnel * 0.3);
    
    // Lighting
    float diff = max(dot(normal, -light_dir), 0.0);
    color *= (0.4 + diff * 0.6);
    
    // Fog
    float fog_dist = length(v_world_pos - camera_pos);
    float fog_amount = 1.0 - exp(-fog_dist * 0.001);
    vec3 fog_color = vec3(0.6, 0.7, 0.8);
    color = mix(color, fog_color, clamp(fog_amount, 0.0, 0.6));
    
    // Alpha based on depth (simple)
    float alpha = 0.85 + fresnel * 0.15;
    
    fragColor = vec4(color, alpha);
}
"""


class NidelvenRenderer(mglw.WindowConfig):
    """
    Main renderer window for Nidelven River Adventure MVP.
    """
    title = "Nidelven River Adventure - MVP"
    width = 1280
    height = 720
    resource_dir = (Path(__file__).parent / 'output').resolve()
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.ctx.enable(moderngl.DEPTH_TEST)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # Camera setup
        self.camera = Camera(aspect_ratio=self.wnd.aspect_ratio)
        self.camera.velocity = 5.0
        
        # Time
        self.time = 0.0
        
        # River trajectory data
        self.river_path = None
        self.river_progress = 0.0
        self.river_speed = 0.05  # Progress per second
        
        # Mouse state for camera control
        self.mouse_pressed = False
        self.last_mouse_pos = (0, 0)
        self.camera_angle = 0.0
        self.camera_height = 10.0
        self.camera_distance = 20.0
        
        # Meshes
        self.terrain_vao = None
        self.water_vao = None
        
        # Shaders
        self.terrain_program = None
        self.water_program = None
        
        # Light direction
        self.light_dir = np.array([0.3, -0.8, 0.2], dtype=np.float32)
        self.light_dir /= np.linalg.norm(self.light_dir)
    
    def load_mesh(self, mesh_data: Dict, shader_type: str = "terrain"):
        """
        Load a mesh from generated data.
        
        Args:
            mesh_data: Dict with 'vertices', 'indices', 'normals', 'uvs'
            shader_type: "terrain" or "water"
        """
        vertices = mesh_data['vertices'].astype(np.float32)
        indices = mesh_data['indices'].astype(np.uint32)
        normals = mesh_data['normals'].astype(np.float32)
        uvs = mesh_data['uvs'].astype(np.float32)
        
        # Interleave vertex data
        vertex_data = np.zeros(len(vertices), dtype=[
            ('in_position', np.float32, 3),
            ('in_normal', np.float32, 3),
            ('in_uv', np.float32, 2)
        ])
        vertex_data['in_position'] = vertices
        vertex_data['in_normal'] = normals
        vertex_data['in_uv'] = uvs
        
        vbo = self.ctx.buffer(vertex_data.tobytes())
        ibo = self.ctx.buffer(indices.tobytes())
        
        # Create shader program
        if shader_type == "terrain":
            program = self.ctx.program(
                vertex_shader=TERRAIN_VERTEX_SHADER,
                fragment_shader=TERRAIN_FRAGMENT_SHADER
            )
        else:
            program = self.ctx.program(
                vertex_shader=WATER_VERTEX_SHADER,
                fragment_shader=WATER_FRAGMENT_SHADER
            )
        
        vao = self.ctx.vertex_array(
            program,
            [(vbo, '3f 3f 2f', 'in_position', 'in_normal', 'in_uv')],
            ibo
        )
        
        return vao, program
    
    def set_terrain_mesh(self, mesh_data: Dict):
        """Set the terrain mesh."""
        self.terrain_vao, self.terrain_program = self.load_mesh(mesh_data, "terrain")
    
    def set_water_mesh(self, mesh_data: Dict):
        """Set the water/river mesh."""
        self.water_vao, self.water_program = self.load_mesh(mesh_data, "water")
    
    def set_river_path(self, path: np.ndarray, elevations: np.ndarray = None):
        """
        Set the river trajectory for camera following.
        
        Args:
            path: Nx2 array of (row, col) or Nx3 array of world positions
            elevations: Optional elevation data for each point
        """
        if path.shape[1] == 2:
            # Convert from grid coordinates to world positions
            # This is a simplified conversion - adjust based on your terrain scale
            self.river_path = path
        else:
            self.river_path = path
        
        self.river_progress = 0.0
    
    def get_camera_position(self) -> np.ndarray:
        """Calculate camera position following the river."""
        if self.river_path is None or len(self.river_path) == 0:
            return np.array([0.0, 20.0, 50.0])
        
        # Get current position on river path
        idx = int(self.river_progress * (len(self.river_path) - 1))
        idx = min(idx, len(self.river_path) - 1)
        
        if self.river_path.shape[1] == 2:
            # Grid coordinates - need conversion
            # For now, use simple scaling
            pos = np.array([
                self.river_path[idx, 1] * 10.0,  # x
                self.camera_height,                # y
                self.river_path[idx, 0] * 10.0   # z
            ])
        else:
            # World coordinates
            pos = self.river_path[idx].copy()
            pos[1] = self.camera_height  # Override height
        
        # Offset camera based on angle
        pos[0] += np.cos(self.camera_angle) * self.camera_distance
        pos[2] += np.sin(self.camera_angle) * self.camera_distance
        
        return pos
    
    def get_look_at(self) -> np.ndarray:
        """Calculate look-at point (ahead on river)."""
        if self.river_path is None or len(self.river_path) == 0:
            return np.array([0.0, 0.0, 0.0])
        
        # Look ahead on the path
        look_ahead_idx = min(
            int(self.river_progress * (len(self.river_path) - 1)) + 10,
            len(self.river_path) - 1
        )
        
        if self.river_path.shape[1] == 2:
            return np.array([
                self.river_path[look_ahead_idx, 1] * 10.0,
                0.0,
                self.river_path[look_ahead_idx, 0] * 10.0
            ])
        else:
            return self.river_path[look_ahead_idx]
    
    def render(self, time: float, frametime: float):
        """Main render loop."""
        self.time = time
        
        # Update river progress (auto-follow)
        self.river_progress += self.river_speed * frametime
        if self.river_progress >= 1.0:
            self.river_progress = 0.0  # Loop
        
        # Update camera
        camera_pos = self.get_camera_position()
        look_at = self.get_look_at()
        
        self.camera.position = camera_pos
        self.camera.look_at = look_at
        self.camera.update()
        
        # Clear
        self.ctx.clear(0.6, 0.7, 0.8, 1.0)
        
        # Model matrix (identity for now)
        model = np.eye(4, dtype=np.float32)
        
        # Render terrain
        if self.terrain_vao:
            mvp = self.camera.projection.matrix * self.camera.matrix
            
            self.terrain_program['mvp'].write(mvp.astype('f4').tobytes())
            self.terrain_program['model'].write(model.astype('f4').tobytes())
            self.terrain_program['light_dir'].write(self.light_dir.tobytes())
            self.terrain_program['camera_pos'].write(camera_pos.astype('f4').tobytes())
            self.terrain_program['time'].value = time
            
            self.terrain_vao.render()
        
        # Render water
        if self.water_vao:
            # Water is slightly offset up to avoid z-fighting
            water_model = model.copy()
            water_model[1, 3] = 0.5  # Slight offset
            
            mvp = self.camera.projection.matrix * self.camera.matrix
            
            self.water_program['mvp'].write(mvp.astype('f4').tobytes())
            self.water_program['model'].write(water_model.astype('f4').tobytes())
            self.water_program['light_dir'].write(self.light_dir.tobytes())
            self.water_program['camera_pos'].write(camera_pos.astype('f4').tobytes())
            self.water_program['time'].value = time
            
            self.water_vao.render()
    
    def mouse_drag_event(self, x: int, y: int, dx: int, dy: int):
        """Handle mouse drag for camera control."""
        if self.mouse_pressed:
            self.camera_angle += dx * 0.01
            self.camera_height = max(2.0, min(50.0, self.camera_height - dy * 0.1))
    
    def mouse_press_event(self, x: int, y: int, button: int):
        """Handle mouse press."""
        if button == 1:  # Left click
            self.mouse_pressed = True
            self.last_mouse_pos = (x, y)
    
    def mouse_release_event(self, x: int, y: int, button: int):
        """Handle mouse release."""
        if button == 1:
            self.mouse_pressed = False
    
    def key_event(self, key: int, action: int, modifiers: int):
        """Handle keyboard input."""
        if action == self.wnd.keys.ACTION_PRESS:
            if key == self.wnd.keys.SPACE:
                # Pause/unpause auto-follow
                self.river_speed = 0.0 if self.river_speed > 0 else 0.05
            elif key == self.wnd.keys.UP:
                self.river_speed = min(0.5, self.river_speed + 0.01)
            elif key == self.wnd.keys.DOWN:
                self.river_speed = max(0.0, self.river_speed - 0.01)
            elif key == self.wnd.keys.LEFT:
                self.camera_distance = max(5.0, self.camera_distance - 2.0)
            elif key == self.wnd.keys.RIGHT:
                self.camera_distance = min(100.0, self.camera_distance + 2.0)
            elif key == self.wnd.keys.R:
                self.river_progress = 0.0


def run_renderer(terrain_mesh: Optional[Dict] = None,
                 water_mesh: Optional[Dict] = None,
                 river_path: Optional[np.ndarray] = None):
    """
    Run the renderer with loaded data.
    
    Args:
        terrain_mesh: Terrain mesh data dict
        water_mesh: Water mesh data dict
        river_path: River trajectory for camera following
    """
    # Store data for the renderer to access
    NidelvenRenderer._terrain_mesh = terrain_mesh
    NidelvenRenderer._water_mesh = water_mesh
    NidelvenRenderer._river_path = river_path
    
    # Run
    mglw.run_window_config(NidelvenRenderer)


if __name__ == "__main__":
    print("Nidelven River Adventure - MVP Renderer")
    print("=" * 50)
    print("Controls:")
    print("  Mouse drag: Orbit camera")
    print("  Space: Pause/unpause auto-follow")
    print("  Up/Down: Speed up/slow down")
    print("  Left/Right: Zoom in/out")
    print("  R: Reset to start")
    print("=" * 50)
    
    # Run with no data (will show empty scene)
    run_renderer()
