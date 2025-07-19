#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from ackermann_msgs.msg import AckermannDriveStamped
from geometry_msgs.msg import Path
from std_msgs.msg import Header
import time
import math

class MockControlNode(Node):
    def __init__(self):
        super().__init__('mock_control_node')
        
        # Subscribe to path planning output
        self.path_subscription = self.create_subscription(
            Path,
            '/planned_path',
            self.path_callback,
            10
        )
        
        # Publish control commands
        self.cmd_publisher = self.create_publisher(
            AckermannDriveStamped,
            '/ackermann_cmd',
            10
        )
        
        # Timer for periodic control updates
        self.timer = self.create_timer(0.1, self.control_loop)  # 10 Hz
        
        self.current_path = None
        self.current_waypoint_index = 0
        self.get_logger().info('🎮 Mock Control Node initialized')
        
    def path_callback(self, msg):
        """Receive new path from path planner"""
        self.current_path = msg
        self.current_waypoint_index = 0
        self.get_logger().info(f'📍 Received new path with {len(msg.poses)} waypoints')
        
    def control_loop(self):
        """Main control loop - generates mock control commands"""
        if self.current_path is None or len(self.current_path.poses) == 0:
            # No path available, send stop command
            self.publish_control_command(0.0, 0.0)
            return
            
        # Simple path following logic
        if self.current_waypoint_index < len(self.current_path.poses):
            target_pose = self.current_path.poses[self.current_waypoint_index]
            
            # Extract target position
            target_x = target_pose.pose.position.x
            target_y = target_pose.pose.position.y
            
            # Simple control calculation
            # In a real system, this would use current vehicle state
            distance = math.sqrt(target_x**2 + target_y**2)
            
            # Calculate steering angle (simplified)
            steering_angle = math.atan2(target_y, target_x)
            steering_angle = max(-0.5, min(0.5, steering_angle))  # Limit steering
            
            # Calculate speed based on distance
            if distance > 2.0:
                speed = 2.0  # Max speed
            elif distance > 0.5:
                speed = distance * 0.8  # Proportional speed
            else:
                speed = 0.2  # Minimum speed
                self.current_waypoint_index += 1  # Move to next waypoint
                
            self.publish_control_command(speed, steering_angle)
            
            self.get_logger().info(
                f'🎯 Control: Speed={speed:.2f} m/s, Steering={steering_angle:.2f} rad, '
                f'Target=({target_x:.1f}, {target_y:.1f}), Waypoint {self.current_waypoint_index+1}/{len(self.current_path.poses)}'
            )
        else:
            # Reached end of path
            self.publish_control_command(0.0, 0.0)
            self.get_logger().info('🏁 Path completed - stopping vehicle')
            
    def publish_control_command(self, speed, steering_angle):
        """Publish Ackermann drive command"""
        msg = AckermannDriveStamped()
        msg.header = Header()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'base_link'
        
        # Ackermann drive parameters
        msg.drive.speed = speed
        msg.drive.steering_angle = steering_angle
        msg.drive.acceleration = 1.0
        msg.drive.jerk = 0.0
        msg.drive.steering_angle_velocity = 0.0
        
        self.cmd_publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    
    node = MockControlNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Mock Control Node shutting down')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
