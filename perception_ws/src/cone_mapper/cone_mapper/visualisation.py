"""RViz visualization utilities for cone mapper."""
from typing import Dict, List

import rclpy.time
from visualization_msgs.msg import Marker, MarkerArray

from .constants import CONE_COLORS_RGB


class ConeVisualizer:
    """Publishes cone cylinders for RViz (/cone_map/markers)."""

    def __init__(self, frame_id: str = 'map'):
        self.frame_id = frame_id

    def create_cone_marker(
        self,
        cone: Dict,
        marker_id: int,
        namespace: str,
        timestamp: rclpy.time.Time,
        opacity: float = 1.0,
    ) -> Marker:
        """One cylinder per cone; size and opacity scale with confidence."""
        marker = Marker()
        marker.header.frame_id = self.frame_id
        marker.header.stamp = timestamp.to_msg()
        marker.ns = namespace
        marker.id = marker_id
        marker.type = Marker.CYLINDER
        marker.action = Marker.ADD

        marker.pose.position.x = cone['x']
        marker.pose.position.y = cone['y']
        marker.pose.position.z = cone['z']
        marker.pose.orientation.w = 1.0

        confidence = cone.get('confidence', 1.0)
        scale = 0.15 + confidence * 0.05
        marker.scale.x = scale
        marker.scale.y = scale
        marker.scale.z = 0.3

        color_rgb = CONE_COLORS_RGB.get(cone['color'], (0.5, 0.5, 0.5))
        marker.color.r = float(color_rgb[0])
        marker.color.g = float(color_rgb[1])
        marker.color.b = float(color_rgb[2])
        marker.color.a = opacity * (0.3 + confidence * 0.7)

        return marker

    def create_marker_array(
        self,
        local_cones: List[Dict],
        global_cones: List[Dict],
        timestamp: rclpy.time.Time,
    ) -> MarkerArray:
        """All cones as one MarkerArray: local semi-transparent, global opaque."""
        marker_array = MarkerArray()

        clear_marker = Marker()
        clear_marker.action = Marker.DELETEALL
        marker_array.markers.append(clear_marker)

        for i, cone in enumerate(local_cones):
            marker_array.markers.append(self.create_cone_marker(
                cone, i + 1, 'local_cones', timestamp, opacity=0.6))

        # Offset global IDs so they never collide with local ones
        for i, cone in enumerate(global_cones):
            marker_array.markers.append(self.create_cone_marker(
                cone, i + 1000, 'global_cones', timestamp, opacity=1.0))

        return marker_array
