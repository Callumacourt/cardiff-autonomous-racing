#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
import json
import time
from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.msg import CanState, WheelSpeedsStamped, VehicleCommandsStamped
from std_msgs.msg import Bool, String

class MockControlNode(Node):
    """
    Mock Control Node for Autonomous Racing
    Simulates vehicle control system with CAN interface
    """
    
    def __init__(self):
        super().__init__('mock_control_node')
        
        # Publishers for simulated control outputs
        self.can_state_pub = self.create_publisher(CanState, '/ros_can/state', 10)
        self.wheel_speeds_pub = self.create_publisher(WheelSpeedsStamped, '/ros_can/wheel_speeds', 10)
        self.vehicle_commands_pub = self.create_publisher(VehicleCommandsStamped, '/ros_can/vehicle_commands', 10)
        self.state_string_pub = self.create_publisher(String, '/ros_can/state_str', 10)
        
        # Subscriber for path commands from path planning
        self.path_sub = self.create_subscription(
            Path, '/path', self.path_callback, 10)
        
        # Internal state
        self.current_speed = 0.0
        self.current_steering = 0.0
        self.as_state = 1  # AS_READY
        self.mission_status = 2  # MISSION_RUNNING
        
        # Timer for publishing control data
        self.timer = self.create_timer(0.1, self.publish_control_data)  # 10Hz
        
        self.get_logger().info('🎮 Mock Control Node initialized - simulating vehicle control')
        
    def path_callback(self, msg):
        """Process path from path planning and generate control commands"""
        if len(msg.poses) >= 2:
            # Simple control logic: follow the path
            target_pose = msg.poses[1].pose  # Take second point as target
            
            # Calculate steering angle (simplified)
            target_x = target_pose.position.x
            target_y = target_pose.position.y
            
            if target_x > 0:
                steering_angle = target_y / target_x * 20.0  # Simple proportional control
                steering_angle = max(-24.0, min(24.0, steering_angle))  # Limit to ±24 degrees
            else:
                steering_angle = 0.0
            
            # Calculate target speed
            target_speed = min(5.0, target_x * 0.5)  # Speed based on distance
            target_speed = max(0.0, target_speed)
            
            self.current_steering = steering_angle
            self.current_speed = target_speed
            
            self.get_logger().info(f'📍 Path received - Target: ({target_x:.2f}, {target_y:.2f}), '
                                 f'Speed: {target_speed:.2f} m/s, Steering: {steering_angle:.2f}°')
    
    def publish_control_data(self):
        """Publish simulated control data"""
        current_time = self.get_clock().now()
        
        # Publish CAN State
        can_state = CanState()
        can_state.header.stamp = current_time.to_msg()
        can_state.header.frame_id = 'base_link'
        can_state.as_state = self.as_state
        can_state.mission_status = self.mission_status
        can_state.ebs_state = False
        can_state.can_active = True
        can_state.error_count = 0
        can_state.status = 'RUNNING'
        self.can_state_pub.publish(can_state)
        
        # Publish Wheel Speeds (simulate from current speed)
        wheel_speeds = WheelSpeedsStamped()
        wheel_speeds.header.stamp = current_time.to_msg()
        wheel_speeds.header.frame_id = 'base_link'
        wheel_speeds.front_left_speed = self.current_speed
        wheel_speeds.front_right_speed = self.current_speed
        wheel_speeds.rear_left_speed = self.current_speed
        wheel_speeds.rear_right_speed = self.current_speed
        wheel_speeds.steering_angle = self.current_steering
        self.wheel_speeds_pub.publish(wheel_speeds)
        
        # Publish Vehicle Commands
        vehicle_cmd = VehicleCommandsStamped()
        vehicle_cmd.header.stamp = current_time.to_msg()
        vehicle_cmd.header.frame_id = 'base_link'
        vehicle_cmd.steering_angle_deg = self.current_steering
        vehicle_cmd.torque_request = self.current_speed * 50.0  # Convert speed to torque
        vehicle_cmd.brake_request = 0.0
        vehicle_cmd.rpm_request = self.current_speed * 100.0  # Convert speed to RPM
        vehicle_cmd.mission_finished = False
        vehicle_cmd.driving_flag = True
        vehicle_cmd.emergency_stop = False
        vehicle_cmd.ebs_request = False
        self.vehicle_commands_pub.publish(vehicle_cmd)
        
        # Publish state string for debugging
        state_str = String()
        state_dict = {
            'as_state': 'AS_READY' if self.as_state == 1 else 'AS_DRIVING',
            'mission_status': 'MISSION_RUNNING',
            'speed': f'{self.current_speed:.2f} m/s',
            'steering': f'{self.current_steering:.2f}°',
            'torque': f'{self.current_speed * 50.0:.1f} Nm',
            'timestamp': str(current_time.nanoseconds)
        }
        state_str.data = json.dumps(state_dict, indent=2)
        self.state_string_pub.publish(state_str)

def main(args=None):
    rclpy.init(args=args)
    
    node = MockControlNode()
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('🛑 Mock Control Node shutting down...')
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
