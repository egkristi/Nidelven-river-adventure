"""
Camera controller for following the river trajectory.
Provides smooth camera movement along the river path with orbit capabilities.
"""

import numpy as np
from typing import Optional, List, Tuple
import glm


class RiverCamera:
    """
    Camera that follows a river trajectory with smooth interpolation.
    """
    
    def __init__(self):
        # Position
        self.position = np.array([0.0, 10.0, 50.0], dtype=np.float32)
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        self.up = np.array([0.0, 1.0, 0.0], dtype=np.float32)
        
        # River following
        self.river_path: Optional[np.ndarray] = None
        self.progress = 0.0  # 0.0 to 1.0 along the path
        self.speed = 0.05    # Progress per second
        
        # Camera offsets
        self.height_offset = 15.0
        self.distance = 30.0
        self.look_ahead_distance = 50.0
        
        # Orbit
        self.orbit_angle = 0.0
        self.orbit_height = 0.3  # Vertical angle (radians)
        
        # Smoothing
        self.position_smooth = 0.1
        self.target_smooth = 0.08
        
        # Internal smoothed values
        self._smooth_position = self.position.copy()
        self._smooth_target = self.target.copy()
        
        # State
        self.auto_follow = True
        self.paused = False
    
    def set_river_path(self, path: np.ndarray, elevations: Optional[np.ndarray] = None):
        """
        Set the river path to follow.
        
        Args:
            path: Nx3 array of world positions or Nx2 array of grid coordinates
            elevations: Optional elevation for each point
        """
        self.river_path = path
        self.progress = 0.0
        
        # Convert 2D to 3D if needed
        if path.shape[1] == 2 and elevations is not None:
            self.river_path = np.column_stack([path, elevations])
        elif path.shape[1] == 2:
            # Assume flat terrain
            self.river_path = np.column_stack([
                path[:, 0],
                np.zeros(len(path)),
                path[:, 1]
            ])
    
    def update(self, dt: float):
        """Update camera position for this frame."""
        if self.river_path is None or len(self.river_path) == 0:
            return
        
        # Update progress
        if self.auto_follow and not self.paused:
            self.progress += self.speed * dt
            if self.progress >= 1.0:
                self.progress = 0.0  # Loop
        
        # Get position on path
        idx = int(self.progress * (len(self.river_path) - 1))
        idx = min(idx, len(self.river_path) - 1)
        
        # Interpolate for smoother movement
        t = self.progress * (len(self.river_path) - 1) - idx
        t = np.clip(t, 0.0, 1.0)
        
        if idx + 1 < len(self.river_path):
            current_pos = self._lerp(self.river_path[idx], self.river_path[idx + 1], t)
        else:
            current_pos = self.river_path[idx]
        
        # Look ahead
        look_idx = min(idx + int(self.look_ahead_distance), len(self.river_path) - 1)
        if look_idx + 1 < len(self.river_path):
            look_t = t
            look_pos = self._lerp(self.river_path[look_idx], self.river_path[look_idx + 1], look_t)
        else:
            look_pos = self.river_path[look_idx]
        
        # Calculate camera position with orbit
        direction = look_pos - current_pos
        direction[1] = 0  # Ignore height for orbit
        direction_len = np.linalg.norm(direction)
        
        if direction_len > 0.001:
            direction = direction / direction_len
            
            # Perpendicular vector
            perp = np.array([-direction[2], 0.0, direction[0]])
            perp_len = np.linalg.norm(perp)
            if perp_len > 0.001:
                perp = perp / perp_len
            
            # Calculate camera offset
            cos_orbit = np.cos(self.orbit_angle)
            sin_orbit = np.sin(self.orbit_angle)
            
            offset = (direction * cos_orbit + perp * sin_orbit) * self.distance
            offset[1] = self.height_offset
            
            target = current_pos.copy()
            target[1] += 2.0  # Look slightly above the water
            
            self.position = current_pos + offset
            self.target = target
        else:
            # Fallback if direction is too small
            self.position = current_pos + np.array([0.0, self.height_offset, -self.distance])
            self.target = current_pos
        
        # Smooth
        self._smooth_position = self._lerp(
            self._smooth_position, self.position, self.position_smooth
        )
        self._smooth_target = self._lerp(
            self._smooth_target, self.target, self.target_smooth
        )
    
    def _lerp(self, a: np.ndarray, b: np.ndarray, t: float) -> np.ndarray:
        """Linear interpolation between two vectors."""
        return a + (b - a) * t
    
    def get_view_matrix(self) -> np.ndarray:
        """Get the view matrix."""
        pos = self._smooth_position
        target = self._smooth_target
        up = self.up
        
        # Using glm for matrix math
        eye = glm.vec3(pos[0], pos[1], pos[2])
        center = glm.vec3(target[0], target[1], target[2])
        up_vec = glm.vec3(up[0], up[1], up[2])
        
        view = glm.lookAt(eye, center, up_vec)
        return np.array(view, dtype=np.float32)
    
    def get_projection_matrix(self, aspect_ratio: float, fov: float = 60.0, 
                               near: float = 0.1, far: float = 10000.0) -> np.ndarray:
        """Get the projection matrix."""
        proj = glm.perspective(glm.radians(fov), aspect_ratio, near, far)
        return np.array(proj, dtype=np.float32)
    
    def set_orbit(self, angle: float, height: float):
        """Set camera orbit angle and height."""
        self.orbit_angle = angle
        self.orbit_height = np.clip(height, -0.5, 0.8)
    
    def set_speed(self, speed: float):
        """Set auto-follow speed."""
        self.speed = np.clip(speed, 0.0, 1.0)
    
    def toggle_pause(self):
        """Toggle pause state."""
        self.paused = not self.paused
    
    def reset(self):
        """Reset to start of river."""
        self.progress = 0.0
        self._smooth_position = self.position.copy()
        self._smooth_target = self.target.copy()


class OrbitCamera:
    """
    Manual orbit camera for free exploration.
    """
    
    def __init__(self, aspect_ratio: float = 16.0/9.0):
        self.aspect_ratio = aspect_ratio
        
        # Spherical coordinates
        self.distance = 50.0
        self.azimuth = 0.0  # Horizontal angle
        self.elevation = 0.3  # Vertical angle
        
        # Target
        self.target = np.array([0.0, 0.0, 0.0], dtype=np.float32)
        
        # Movement
        self.move_speed = 10.0
        self.rotate_speed = 1.0
        self.zoom_speed = 5.0
        
        # Limits
        self.min_distance = 5.0
        self.max_distance = 500.0
        self.min_elevation = -0.4
        self.max_elevation = 0.8
    
    def update(self, dt: float):
        """Update camera (no-op for orbit camera)."""
        pass
    
    def get_position(self) -> np.ndarray:
        """Calculate position from spherical coordinates."""
        x = self.target[0] + self.distance * np.cos(self.elevation) * np.sin(self.azimuth)
        y = self.target[1] + self.distance * np.sin(self.elevation)
        z = self.target[2] + self.distance * np.cos(self.elevation) * np.cos(self.azimuth)
        return np.array([x, y, z], dtype=np.float32)
    
    def get_view_matrix(self) -> np.ndarray:
        """Get view matrix."""
        pos = self.get_position()
        eye = glm.vec3(pos[0], pos[1], pos[2])
        center = glm.vec3(self.target[0], self.target[1], self.target[2])
        up = glm.vec3(0.0, 1.0, 0.0)
        
        view = glm.lookAt(eye, center, up)
        return np.array(view, dtype=np.float32)
    
    def get_projection_matrix(self, fov: float = 60.0, 
                               near: float = 0.1, far: float = 10000.0) -> np.ndarray:
        """Get projection matrix."""
        proj = glm.perspective(glm.radians(fov), self.aspect_ratio, near, far)
        return np.array(proj, dtype=np.float32)
    
    def orbit(self, delta_azimuth: float, delta_elevation: float):
        """Orbit around target."""
        self.azimuth += delta_azimuth * self.rotate_speed
        self.elevation = np.clip(
            self.elevation + delta_elevation * self.rotate_speed,
            self.min_elevation, self.max_elevation
        )
    
    def zoom(self, delta: float):
        """Zoom in/out."""
        self.distance = np.clip(
            self.distance + delta * self.zoom_speed,
            self.min_distance, self.max_distance
        )
    
    def pan(self, delta_x: float, delta_y: float):
        """Pan target position."""
        right = np.array([
            np.cos(self.azimuth),
            0.0,
            -np.sin(self.azimuth)
        ], dtype=np.float32)
        
        forward = np.array([
            np.sin(self.azimuth) * np.cos(self.elevation),
            np.sin(self.elevation),
            np.cos(self.azimuth) * np.cos(self.elevation)
        ], dtype=np.float32)
        
        up = np.cross(right, forward)
        up = up / np.linalg.norm(up)
        
        self.target += right * delta_x * self.move_speed
        self.target += up * delta_y * self.move_speed
