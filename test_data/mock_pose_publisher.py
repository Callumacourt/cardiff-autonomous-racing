#!/usr/bin/env python3
# File: test_data/mock_pose_publisher.py
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import PoseStamped
import math

class MockPosePublisher(Node):
    def __init__(self):
        super().__init__('mock_pose_publisher')
        self.odom_pub = self.create_publisher(Odometry, '/odometry/slam', 10)
        self.pose_pub = self.create_publisher(PoseStamped, '/car_pose', 10)
        self.timer = self.create_timer(0.05, self.publish_pose)
        self.x = 0.0
        self.y = 0.0
        
    def publish_pose(self):
        self.x += 0.05
        
        odom_msg = Odometry()
        odom_msg.header.stamp = self.get_clock().now().to_msg()
        odom_msg.header.frame_id = 'map'
        odom_msg.pose.pose.position.x = self.x
        odom_msg.pose.pose.position.y = self.y
        odom_msg.pose.pose.position.z = 0.0
        odom_msg.pose.pose.orientation.w = 1.0
        
        self.odom_pub.publish(odom_msg)
        
        pose_msg = PoseStamped()
        pose_msg.header = odom_msg.header
        pose_msg.pose = odom_msg.pose.pose
        self.pose_pub.publish(pose_msg)

def main(args=None):
    rclpy.init(args=args)
    node = MockPosePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()