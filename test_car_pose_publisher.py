#!/usr/bin/env python3
"""
Test car pose publisher to verify path planner receives data
"""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped

class TestCarPosePublisher(Node):
    def __init__(self):
        super().__init__('test_car_pose_publisher')
        
        # Publisher
        self.pose_pub = self.create_publisher(PoseStamped, '/car_pose', 10)
        
        # Timer to publish test data
        self.timer = self.create_timer(0.1, self.publish_car_pose)
        
        self.get_logger().info('Test Car Pose Publisher started')
    
    def publish_car_pose(self):
        # Publish test car pose at origin
        pose_msg = PoseStamped()
        pose_msg.header.stamp = self.get_clock().now().to_msg()
        pose_msg.header.frame_id = 'map'
        pose_msg.pose.position.x = 0.0
        pose_msg.pose.position.y = 0.0
        pose_msg.pose.position.z = 0.0
        pose_msg.pose.orientation.w = 1.0
        self.pose_pub.publish(pose_msg)

def main(args=None):
    rclpy.init(args=args)
    node = TestCarPosePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
