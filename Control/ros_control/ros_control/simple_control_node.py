import rclpy
from rclpy.node import Node
import math
import time

from nav_msgs.msg import Path
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Float32, String

# Import EUFS messages
try:
    from eufs_msgs.msg import CanState, CarState, VehicleCommandsStamped, WheelSpeeds
    EUFS_MSGS_AVAILABLE = True
    print("✅ EUFS messages imported successfully")
except ImportError as e:
    print(f"⚠️ EUFS messages not available: {e}")
    EUFS_MSGS_AVAILABLE = False

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
        
        # Publisher for vehicle position feedback
        self.pose_pub = self.create_publisher(PoseStamped, '/car_pose', 10)
        
        # EUFS message publishers (if available)
        if EUFS_MSGS_AVAILABLE:
            self.can_state_pub = self.create_publisher(CanState, '/can_state', 10)
            self.car_state_pub = self.create_publisher(CarState, '/car_state', 10)
            self.vehicle_commands_pub = self.create_publisher(VehicleCommandsStamped, '/vehicle_commands', 10)
            self.get_logger().info('🚗 EUFS message publishers initialized')
        else:
            self.get_logger().warn('⚠️ EUFS messages not available, using fallback publishers')
        
        # Vehicle state for position integration
        self.current_pos_x = 0.0
        self.current_pos_y = 0.0
        self.current_heading = 0.0  # radians
        self.current_speed = 0.0
        
        # Vehicle state
        self.current_path = None
        self.target_speed = 5.0  # m/s
        
        # Control loop timer
        self.control_timer = self.create_timer(0.1, self.control_loop)
        
        self.get_logger().info('🎮 Simple Mock Control Node initialized')
        self.get_logger().info('📡 Subscribed to: /planned_path')
        self.get_logger().info('📤 Publishing: /racing/control/steering, /racing/control/throttle, /racing/control/status, /car_pose')
        
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
        """Publish control commands and update vehicle position"""
        dt = 0.1  # Control loop time step (10 Hz)
        
        # Simple vehicle dynamics integration
        # Update speed based on throttle
        self.current_speed = throttle * self.target_speed  # Simple throttle to speed mapping
        
        # Update heading based on steering (simple bicycle model)
        wheelbase = 2.5  # meters - typical race car wheelbase
        if abs(self.current_speed) > 0.01:  # Only turn if moving
            self.current_heading += (self.current_speed / wheelbase) * math.tan(steering * 0.5) * dt
        
        # Update position based on current speed and heading
        self.current_pos_x += self.current_speed * math.cos(self.current_heading) * dt
        self.current_pos_y += self.current_speed * math.sin(self.current_heading) * dt
        
        # Publish updated position
        self.publish_vehicle_pose()
        
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
        
        # Publish EUFS messages if available
        self.publish_eufs_messages(steering, throttle, status)
        
        # Log every 5 seconds with position info
        if int(time.time()) % 5 == 0:
            eufs_status = "with EUFS msgs" if EUFS_MSGS_AVAILABLE else "fallback mode"
            self.get_logger().info(f'🚗 Control: pos=({self.current_pos_x:.1f},{self.current_pos_y:.1f}) steering={steering:.2f}, throttle={throttle:.2f}, status={status} ({eufs_status})')
    
    def publish_vehicle_pose(self):
        """Publish current vehicle position for path planning feedback"""
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = "map"
        pose_msg.pose.position.x = self.current_pos_x
        pose_msg.pose.position.y = self.current_pos_y
        pose_msg.pose.position.z = 0.0
        
        # Convert heading to quaternion (simplified - only yaw rotation)
        pose_msg.pose.orientation.x = 0.0
        pose_msg.pose.orientation.y = 0.0
        pose_msg.pose.orientation.z = math.sin(self.current_heading / 2.0)
        pose_msg.pose.orientation.w = math.cos(self.current_heading / 2.0)
        
        self.pose_pub.publish(pose_msg)
    
    def publish_eufs_messages(self, steering, throttle, status):
        """Publish EUFS-specific messages if available"""
        if not EUFS_MSGS_AVAILABLE:
            return
            
        current_time = self.get_clock().now().to_msg()
        
        # Publish CAN State (real EUFS structure)
        can_state_msg = CanState()
        can_state_msg.as_state = CanState.AS_DRIVING if status == "FOLLOWING_PATH" else CanState.AS_READY
        can_state_msg.ami_state = CanState.AMI_AUTOCROSS  # Autocross mission
        self.can_state_pub.publish(can_state_msg)
        
        # Publish Vehicle Commands
        vehicle_cmd_msg = VehicleCommandsStamped()
        vehicle_cmd_msg.header.stamp = current_time
        vehicle_cmd_msg.header.frame_id = "base_link"
        # Note: VehicleCommandsStamped structure may vary, adjust as needed
        self.vehicle_commands_pub.publish(vehicle_cmd_msg)
    
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
