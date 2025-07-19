#!/usr/bin/env python3
"""
Simple cone mapper without SciPy dependencies for testing
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
import numpy as np
import time
import math
from typing import List, Tuple, Dict, Optional

# Color constants
BLUE_CONE = 0
YELLOW_CONE = 1
ORANGE_CONE = 2

class SimpleConeMapper(Node):
    """Simple cone mapper without SciPy dependencies"""
    
    def __init__(self):
        super().__init__('simple_cone_mapper')
        
        # Vehicle state
        self.vehicle_position = (0.0, 0.0)
        self.local_cones = []
        
        # Subscriptions
        self.cone_sub = self.create_subscription(
            String, '/detected_cones', self.cone_callback, 10)
        self.pose_sub = self.create_subscription(
            Odometry, '/odometry/slam', self.pose_callback, 10)
        
        # Publishers
        self.local_map_pub = self.create_publisher(String, '/cone_map/local', 10)
        
        # Timer to publish local map
        self.local_timer = self.create_timer(0.1, self.publish_local_map)
        
        self.get_logger().info('Simple Cone Mapper initialized')
    
    def pose_callback(self, msg):
        """Handle pose updates"""
        pos = msg.pose.pose.position
        self.vehicle_position = (pos.x, pos.y)
    
    def cone_callback(self, msg):
        """Process cone detections"""
        if not msg.data.strip():
            return
        
        try:
            lines = msg.data.strip().split('\n')
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 4:
                    x, y, z, color = map(float, parts[:4])
                    
                    # Add cone with default confidence
                    cone = {
                        'x': x, 'y': y, 'z': z, 
                        'color': int(color),
                        'confidence': 0.8,
                        'timestamp': time.time()
                    }
                    
                    # Simple duplicate removal - check if cone already exists nearby
                    existing = False
                    for existing_cone in self.local_cones:
                        dist = math.sqrt((cone['x'] - existing_cone['x'])**2 + 
                                       (cone['y'] - existing_cone['y'])**2)
                        if dist < 1.0 and cone['color'] == existing_cone['color']:
                            # Update existing cone position (simple averaging)
                            existing_cone['x'] = (existing_cone['x'] + cone['x']) / 2
                            existing_cone['y'] = (existing_cone['y'] + cone['y']) / 2
                            existing_cone['timestamp'] = cone['timestamp']
                            existing = True
                            break
                    
                    if not existing:
                        self.local_cones.append(cone)
                        self.get_logger().info(f"Added cone: color={int(color)}, pos=({x:.1f}, {y:.1f})")
            
            # Remove old cones (older than 5 seconds)
            current_time = time.time()
            self.local_cones = [cone for cone in self.local_cones 
                              if current_time - cone['timestamp'] < 5.0]
            
        except Exception as e:
            self.get_logger().error(f'Error processing cone detections: {e}')
    
    def publish_local_map(self):
        """Publish local cone map"""
        if not self.local_cones:
            return
        
        # Create message in the format expected by path planner
        output_lines = []
        for cone in self.local_cones:
            output_lines.append(
                f"{cone['x']:.2f},{cone['y']:.2f},{cone['z']:.2f},"
                f"{cone['color']},{cone['confidence']:.2f}")
        
        msg = String()
        msg.data = '\n'.join(output_lines)
        self.local_map_pub.publish(msg)
        
        # Log periodically
        if len(self.local_cones) > 0:
            blue_count = sum(1 for c in self.local_cones if c['color'] == BLUE_CONE)
            yellow_count = sum(1 for c in self.local_cones if c['color'] == YELLOW_CONE)
            self.get_logger().info(f"Publishing {len(self.local_cones)} cones: {blue_count} blue, {yellow_count} yellow")

def main(args=None):
    rclpy.init(args=args)
    node = SimpleConeMapper()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
