#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import math
import time

from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, String

class SimpleMockControlNode(Node):
    """
    Simple Mock Control Node for Autonomous Racing
    Demonstrates complete pipeline without complex message dependencies
    """
    
    def __init__(self):
        super().__init__('simple_mock_control')
        
        # Subscribe to path planning
        self.path_subscription = self.create_subscription(
            Path,
            '/planned_path',
            self.path_callback,
            10
        )
        
        # Publishers for control outputs (using simple message types)
        self.steering_pub = self.create_publisher(Float32, '/racing/control/steering', 10)
        self.throttle_pub = self.create_publisher(Float32, '/racing/control/throttle', 10)
        self.status_pub = self.create_publisher(String, '/racing/control/status', 10)
        
        # Vehicle state
        self.current_path = None
        self.target_speed = 5.0  # m/s
        
        # Control loop timer
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('🎮 Simple Mock Control Node initialized')
        self.get_logger().info('📡 Subscribed to: /planned_path')
        self.get_logger().info('📤 Publishing: /racing/control/steering, /racing/control/throttle, /racing/control/status')
        
    def path_callback(self, msg):
        """Process incoming path from planning"""
        self.current_path = msg
        if len(msg.poses) > 0:
            self.get_logger().info(f'🛣️ Received path with {len(msg.poses)} waypoints')
        
    def control_loop(self):
        """Main control loop"""
        if self.current_path is None or len(self.current_path.poses) == 0:
            # No path available, stay stationary
            self.publish_control_commands(0.0, 0.0, "WAITING_FOR_PATH")
            return
        
        # Simple proportional steering control
        # Get first waypoint as target
        target_pose = self.current_path.poses[0]
        target_x = target_pose.pose.position.x
        target_y = target_pose.pose.position.y
        
        # Simple lateral control (assuming current position is origin)
        lateral_error = target_y
        steering_command = self.clamp(lateral_error * 2.0, -1.0, 1.0)  # Proportional control
        
        # Throttle control based on path length
        if len(self.current_path.poses) > 1:
            throttle_command = 0.5  # Forward throttle
        else:
            throttle_command = 0.1  # Slow down near goal
            
        self.publish_control_commands(steering_command, throttle_command, "FOLLOWING_PATH")
        
    def publish_control_commands(self, steering, throttle, status):
        """Publish control commands"""
        # Publish steering
        steering_msg = Float32()
        steering_msg.data = steering
        self.steering_pub.publish(steering_msg)
        
        # Publish throttle
        throttle_msg = Float32()
        throttle_msg.data = throttle
        self.throttle_pub.publish(throttle_msg)
        
        # Publish status
        status_msg = String()
        status_msg.data = status
        self.status_pub.publish(status_msg)
        
        # Log every 5 seconds
        if int(time.time()) % 5 == 0:
            self.get_logger().info(f'🚗 Control: steering={steering:.2f}, throttle={throttle:.2f}, status={status}')
    
    def clamp(self, value, min_val, max_val):
        """Clamp value between min and max"""
        return max(min_val, min(value, max_val))

def main(args=None):
    rclpy.init(args=args)
    
    try:
        control_node = SimpleMockControlNode()
        rclpy.spin(control_node)
    except KeyboardInterrupt:
        pass
    finally:
        if 'control_node' in locals():
            control_node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
