#!/usr/bin/env python3
"""
Test cone detection publisher to verify data flow
"""

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Point, Pose, Quaternion
import time

class TestConePublisher(Node):
    def __init__(self):
        super().__init__('test_cone_publisher')
        
        # Publishers
        self.cone_pub = self.create_publisher(String, '/detected_cones', 10)
        self.odom_pub = self.create_publisher(Odometry, '/odometry/slam', 10)
        
        # Timer to publish test data
        self.timer = self.create_timer(1.0, self.publish_test_data)
        
        self.get_logger().info('Test Cone Publisher started')
    
    def publish_test_data(self):
        # Publish test cone data - Create a proper racing corridor
        # Right cones (orange, color=0) on the right side (positive Y)
        # Left cones (blue, color=1) on the left side (negative Y)
        # Format: x,y,z,color (0=orange/right, 1=blue/left)
        cone_msg = String()
        cone_msg.data = "5.0,2.0,0.0,0\n10.0,2.5,0.0,0\n5.0,-2.0,0.0,1\n10.0,-2.5,0.0,1"
        self.cone_pub.publish(cone_msg)
        
        # Publish test odometry
        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = 'map'
        odom_msg.pose.pose.position.x = 0.0
        odom_msg.pose.pose.position.y = 0.0
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation.w = 1.0
        self.odom_pub.publish(odom_msg)
        
        self.get_logger().info('Published test cone and odometry data')

def main(args=None):
    rclpy.init(args=args)
    node = TestConePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
