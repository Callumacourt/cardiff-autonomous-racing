"""RViz visualization utilities for cone mapper."""
from visualization_msgs.msg import Marker, MarkerArray
from geometry_msgs.msg import Point
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from typing import List, Dict, Tuple
import rclpy.time
import numpy as np

from .constants import ConeColor, CONE_COLORS_RGB


class ConeVisualizer:
    """Handles RViz marker generation for cone visualization."""
    
    def __init__(self, frame_id: str = 'map'):
        """
        Initialize visualizer.
        
        Args:
            frame_id: Reference frame for all markers (default: 'map')
        """
        self.frame_id = frame_id
    
    def create_cone_marker(
        self,
        cone: Dict,
        marker_id: int,
        namespace: str,
        timestamp: rclpy.time.Time,
        opacity: float = 1.0
    ) -> Marker:
        """
        Create a single cone marker.
        
        Args:
            cone: Dictionary with keys: x, y, z, color, confidence
            marker_id: Unique marker ID
            namespace: Marker namespace (e.g., 'local_cones', 'global_cones')
            timestamp: ROS timestamp for marker
            opacity: Base opacity (0.0-1.0), will be modulated by confidence
            
        Returns:
            Marker message for RViz
        """
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = timestamp.to_msg()
        marker.ns = namespace
        marker.id = marker_id
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD
        
        # Position
        marker.pose.position.x = cone['x']
        marker.pose.position.y = cone['y']
        marker.pose.position.z = cone['z']
        marker.pose.orientation.w = 1.0
        
        # Size based on confidence (higher confidence = larger)
        confidence = cone.get('confidence', 1.0)
        base_scale = 0.15
        scale = base_scale + confidence * 0.05
        marker.scale.x = scale
        marker.scale.y = scale
        marker.scale.z = 0.3  # Height of cylinder
        
        # Color based on cone type
        color_rgb = CONE_COLORS_RGB.get(cone['color'], (0.5, 0.5, 0.5))
        marker.color.r = float(color_rgb[0])
        marker.color.g = float(color_rgb[1])
        marker.color.b = float(color_rgb[2])
        marker.color.a = opacity * (0.3 + confidence * 0.7)  # Confidence affects transparency
        
        return marker
    
    def create_marker_array(
        self,
        local_cones: List[Dict],
        global_cones: List[Dict],
        timestamp: rclpy.time.Time
    ) -> MarkerArray:
        """
        Create complete marker array for all cones.
        
        Args:
            local_cones: List of cones in local buffer
            global_cones: List of cones in global map
            timestamp: Current ROS time
            
        Returns:
            MarkerArray with all cone markers
        """
        marker_array = MarkerArray()
        
        # Clear previous markers
        clear_marker = Marker()
        clear_marker.action = Marker.DELETEALL
        marker_array.markers.append(clear_marker)
        
        # Add local cones (semi-transparent)
        for i, cone in enumerate(local_cones):
            marker = self.create_cone_marker(
                cone, 
                i + 1, 
                'local_cones', 
                timestamp,
                opacity=0.6  # More transparent for local
            )
            marker_array.markers.append(marker)
        
        # Add global cones (fully opaque)
        for i, cone in enumerate(global_cones):
            marker = self.create_cone_marker(
                cone, 
                i + 1000,  # Offset IDs to avoid conflicts
                'global_cones', 
                timestamp,
                opacity=1.0  # Fully opaque for global
            )
            marker_array.markers.append(marker)
        
        return marker_array
    
    def create_centerline_marker(
        self,
        left_cones: List[Dict],
        right_cones: List[Dict],
        timestamp: rclpy.time.Time,
        color: Tuple[float, float, float] = (0.0, 1.0, 0.0)
    ) -> Marker:
        """
        Create centerline marker from left/right cone boundaries.
        
        Args:
            left_cones: List of left boundary cones (typically blue)
            right_cones: List of right boundary cones (typically yellow)
            timestamp: Current ROS time
            color: RGB color tuple for centerline (default: green)
            
        Returns:
            LINE_STRIP marker showing centerline
        """
        marker = Marker()
        marker.type = Marker.LINE_STRIP
        marker.header.frame_id = self.frame_id
        marker.header.stamp = timestamp.to_msg()
        marker.ns = 'centerline'
        marker.id = 999  # Fixed ID for centerline
        marker.action = Marker.ADD
        
        # Line appearance
        marker.color.r, marker.color.g, marker.color.b = color
        marker.color.a = 1.0
        marker.scale.x = 0.1  # Line width
        
        # Compute midpoints between left and right cones
        num_points = min(len(left_cones), len(right_cones))
        for i in range(num_points):
            p = Point()
            p.x = (left_cones[i]['x'] + right_cones[i]['x']) / 2.0
            p.y = (left_cones[i]['y'] + right_cones[i]['y']) / 2.0
            p.z = 0.0  # Keep centerline at ground level
            marker.points.append(p)
        
        return marker
    
    def create_boundary_markers(
        self,
        left_cones: List[Dict],
        right_cones: List[Dict],
        timestamp: rclpy.time.Time
    ) -> List[Marker]:
        """
        Create left and right boundary line markers.
        
        Args:
            left_cones: Left boundary cones
            right_cones: Right boundary cones  
            timestamp: Current ROS time
            
        Returns:
            List of two Marker objects (left boundary, right boundary)
        """
        markers = []
        
        # Left boundary (blue line)
        left_marker = Marker()
        left_marker.type = Marker.LINE_STRIP
        left_marker.header.frame_id = self.frame_id
        left_marker.header.stamp = timestamp.to_msg()
        left_marker.ns = 'left_boundary'
        left_marker.id = 997
        left_marker.action = Marker.ADD
        left_marker.scale.x = 0.08
        left_marker.color.r, left_marker.color.g, left_marker.color.b = 0.0, 0.0, 1.0
        left_marker.color.a = 0.7
        
        for cone in left_cones:
            p = Point()
            p.x, p.y, p.z = cone['x'], cone['y'], 0.0
            left_marker.points.append(p)
        
        markers.append(left_marker)
        
        # Right boundary (yellow line)
        right_marker = Marker()
        right_marker.type = Marker.LINE_STRIP
        right_marker.header.frame_id = self.frame_id
        right_marker.header.stamp = timestamp.to_msg()
        right_marker.ns = 'right_boundary'
        right_marker.id = 998
        right_marker.action = Marker.ADD
        right_marker.scale.x = 0.08
        right_marker.color.r, right_marker.color.g, right_marker.color.b = 1.0, 1.0, 0.0
        right_marker.color.a = 0.7
        
        for cone in right_cones:
            p = Point()
            p.x, p.y, p.z = cone['x'], cone['y'], 0.0
            right_marker.points.append(p)
        
        markers.append(right_marker)
        
        return markers
    
    def create_centerline_path(
        self,
        left_cones: List[Dict],
        right_cones: List[Dict],
        timestamp: rclpy.time.Time
    ) -> Path:
        """
        Create centerline as a Path message for path planning.
        
        Args:
            left_cones: Left boundary cones
            right_cones: Right boundary cones
            timestamp: Current ROS time
            
        Returns:
            Path message with centerline poses
        """
        path = Path()
        path.header.frame_id = self.frame_id
        path.header.stamp = timestamp.to_msg()
        
        # Sort cones by distance from origin (assuming track starts at origin)
        left_sorted = sorted(left_cones, key=lambda c: np.sqrt(c['x']**2 + c['y']**2))
        right_sorted = sorted(right_cones, key=lambda c: np.sqrt(c['x']**2 + c['y']**2))
        
        num_points = min(len(left_sorted), len(right_sorted))
        
        for i in range(num_points):
            left = left_sorted[i]
            right = right_sorted[i]
            
            # Midpoint
            cx = (left['x'] + right['x']) / 2.0
            cy = (left['y'] + right['y']) / 2.0
            cz = (left['z'] + right['z']) / 2.0
            
            pose = PoseStamped()
            pose.header.frame_id = self.frame_id
            pose.header.stamp = timestamp.to_msg()
            pose.pose.position.x = cx
            pose.pose.position.y = cy
            pose.pose.position.z = cz
            
            # Calculate orientation (tangent to path)
            if i < num_points - 1:
                next_left = left_sorted[i + 1]
                next_right = right_sorted[i + 1]
                next_cx = (next_left['x'] + next_right['x']) / 2.0
                next_cy = (next_left['y'] + next_right['y']) / 2.0
                
                # Calculate yaw angle
                dx = next_cx - cx
                dy = next_cy - cy
                yaw = np.arctan2(dy, dx)
                
                # Convert to quaternion
                pose.pose.orientation.w = np.cos(yaw / 2.0)
                pose.pose.orientation.z = np.sin(yaw / 2.0)
            else:
                pose.pose.orientation.w = 1.0
            
            path.poses.append(pose)
        
        return path
    
    def create_text_marker(
        self,
        text: str,
        position: Tuple[float, float, float],
        marker_id: int,
        timestamp: rclpy.time.Time,
        scale: float = 0.5,
        color: Tuple[float, float, float] = (1.0, 1.0, 1.0)
    ) -> Marker:
        """
        Create a text marker for annotations.
        
        Args:
            text: Text to display
            position: (x, y, z) position
            marker_id: Unique marker ID
            timestamp: ROS timestamp
            scale: Text height in meters
            color: RGB color tuple
            
        Returns:
            TEXT_VIEW_FACING marker
        """
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = timestamp.to_msg()
        marker.ns = 'text_labels'
        marker.id = marker_id
        marker.type = Marker.TEXT_VIEW_FACING
        marker.action = Marker.ADD
        
        marker.pose.position.x = position[0]
        marker.pose.position.y = position[1]
        marker.pose.position.z = position[2]
        marker.pose.orientation.w = 1.0
        
        marker.scale.z = scale
        marker.color.r, marker.color.g, marker.color.b = color
        marker.color.a = 1.0
        marker.text = text
        
        return marker