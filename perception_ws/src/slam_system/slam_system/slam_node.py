#!/usr/bin/env python3

"""
Visual SLAM System Node

A ROS2 node that tracks the racing car's position and builds maps using camera images.
This is a template for integrating ORB-SLAM3 or other visual SLAM algorithms.

Currently publishes demo trajectory data. Replace with actual ORB-SLAM3 integration.

Author: Cardiff Autonomous Racing Team
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from geometry_msgs.msg import PoseStamped, TransformStamped
from nav_msgs.msg import Path
from tf2_ros import TransformBroadcaster
from cv_bridge import CvBridge
import cv2
import numpy as np
import math


class SlamSystemNode(Node):
    """
    Visual SLAM system for tracking car position and building maps.
    
    This node processes camera images to determine where the car is located
    and builds a map of the racing environment. Currently shows demo data.
    
    TODO: Integrate with ORB-SLAM3 C++ library for real SLAM functionality.
    """

    def __init__(self):
        super().__init__('slam_system')
        
        # Declare parameters
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('pose_topic', '/slam/pose')
        self.declare_parameter('path_topic', '/slam/path')
        
        # Get parameters
        camera_topic = self.get_parameter('camera_topic').get_parameter_value().string_value
        camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        pose_topic = self.get_parameter('pose_topic').get_parameter_value().string_value
        path_topic = self.get_parameter('path_topic').get_parameter_value().string_value
        
        # Initialize tools
        self.bridge = CvBridge()  # Convert between ROS and OpenCV images
        self.tf_broadcaster = TransformBroadcaster(self)  # Publish car position
        
        # Initialize trajectory storage
        self.path = Path()
        self.path.header.frame_id = "map"
        
        # Camera calibration data (filled by camera_info messages)
        self.camera_matrix = None
        self.distortion_coeffs = None
        
        # SLAM system placeholder - replace with ORB-SLAM3
        self.slam_initialized = False
        
        # Create ROS subscribers
        self.image_subscription = self.create_subscription(
            Image,
            camera_topic,
            self.image_callback,
            10
        )
        
        self.camera_info_subscription = self.create_subscription(
            CameraInfo,
            camera_info_topic,
            self.camera_info_callback,
            10
        )
        
        # Create ROS publishers
        self.pose_publisher = self.create_publisher(PoseStamped, pose_topic, 10)
        self.path_publisher = self.create_publisher(Path, path_topic, 10)
        
        self.get_logger().info("SLAM system node initialized")
        self.get_logger().info(f"Subscribing to camera: {camera_topic}")
        self.get_logger().info(f"Publishing pose to: {pose_topic}")
        self.get_logger().info(f"Publishing trajectory to: {path_topic}")
        self.get_logger().warn("Currently publishing demo data - ORB-SLAM3 integration needed")

    def camera_info_callback(self, msg):
        """
        Store camera calibration information.
        
        Camera calibration tells us the camera's intrinsic properties like
        focal length and distortion, which are needed for accurate SLAM.
        
        Args:
            msg: sensor_msgs/CameraInfo with calibration data
        """
        self.camera_matrix = np.array(msg.k).reshape(3, 3)
        self.distortion_coeffs = np.array(msg.d)
        
        self.get_logger().info("Received camera calibration data", once=True)

    def image_callback(self, msg):
        """
        Process camera images for SLAM.
        
        This is where the main SLAM processing happens. Currently generates
        demo trajectory data. Replace with ORB-SLAM3 processing.
        
        Args:
            msg: sensor_msgs/Image from camera
        """
        try:
            # Convert ROS image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # TODO: Replace this demo code with actual ORB-SLAM3 processing
            # Current demo: Generate circular trajectory for visualization
            current_pose = self.generate_demo_pose(msg.header.stamp)
            
            # Publish the current pose estimate
            self.publish_pose(current_pose, msg.header)
            
            # Add to trajectory and publish
            self.update_trajectory(current_pose, msg.header)
            
            # Publish transform for visualization in RViz
            self.publish_transform(current_pose, msg.header)
            
        except Exception as e:
            self.get_logger().error(f"Error processing image for SLAM: {e}")

    def generate_demo_pose(self, timestamp):
        """
        Generate demo trajectory data for testing visualization.
        
        TODO: Replace this with actual ORB-SLAM3 pose estimation.
        
        Args:
            timestamp: ROS timestamp
            
        Returns:
            dict: Pose data with x, y, z position and orientation
        """
        # Create circular trajectory for demo
        time_sec = timestamp.sec + timestamp.nanosec * 1e-9
        
        # Circular motion parameters
        radius = 3.0
        speed = 0.1  # radians per second
        
        angle = time_sec * speed
        x = radius * math.cos(angle)
        y = radius * math.sin(angle)
        z = 0.0
        
        return {
            'x': x,
            'y': y, 
            'z': z,
            'orientation': {'x': 0.0, 'y': 0.0, 'z': 0.0, 'w': 1.0}
        }

    def publish_pose(self, pose_data, header):
        """
        Publish the car's current pose estimate.
        
        Args:
            pose_data: Dictionary with position and orientation
            header: Original message header for timestamp
        """
        pose_msg = PoseStamped()
        pose_msg.header = header
        pose_msg.header.frame_id = "map"
        
        # Position
        pose_msg.pose.position.x = pose_data['x']
        pose_msg.pose.position.y = pose_data['y']
        pose_msg.pose.position.z = pose_data['z']
        
        # Orientation (quaternion)
        pose_msg.pose.orientation.x = pose_data['orientation']['x']
        pose_msg.pose.orientation.y = pose_data['orientation']['y']
        pose_msg.pose.orientation.z = pose_data['orientation']['z']
        pose_msg.pose.orientation.w = pose_data['orientation']['w']
        
        self.pose_publisher.publish(pose_msg)

    def update_trajectory(self, pose_data, header):
        """
        Add current pose to trajectory and publish the path.
        
        Args:
            pose_data: Current pose information
            header: Message header
        """
        # Create pose for trajectory
        pose_stamped = PoseStamped()
        pose_stamped.header = header
        pose_stamped.header.frame_id = "map"
        pose_stamped.pose.position.x = pose_data['x']
        pose_stamped.pose.position.y = pose_data['y']
        pose_stamped.pose.position.z = pose_data['z']
        pose_stamped.pose.orientation.w = 1.0
        
        # Add to trajectory
        self.path.header.stamp = header.stamp
        self.path.poses.append(pose_stamped)
        
        # Keep trajectory length reasonable for performance
        max_trajectory_length = 1000
        if len(self.path.poses) > max_trajectory_length:
            self.path.poses.pop(0)
        
        # Publish updated trajectory
        self.path_publisher.publish(self.path)

    def publish_transform(self, pose_data, header):
        """
        Publish transform for RViz visualization.
        
        Args:
            pose_data: Current pose
            header: Message header
        """
        transform = TransformStamped()
        transform.header = header
        transform.header.frame_id = "map"
        transform.child_frame_id = "camera_link"
        
        # Position
        transform.transform.translation.x = pose_data['x']
        transform.transform.translation.y = pose_data['y']
        transform.transform.translation.z = pose_data['z']
        
        # Orientation
        transform.transform.rotation.x = pose_data['orientation']['x']
        transform.transform.rotation.y = pose_data['orientation']['y']
        transform.transform.rotation.z = pose_data['orientation']['z']
        transform.transform.rotation.w = pose_data['orientation']['w']
        
        self.tf_broadcaster.sendTransform(transform)

    def integrate_orb_slam3(self):
        """
        Placeholder for ORB-SLAM3 integration.
        
        TODO: Implement this function to:
        1. Initialize ORB-SLAM3 system
        2. Load vocabulary and camera settings
        3. Process images through ORB-SLAM3
        4. Extract pose and map data
        5. Handle tracking loss/recovery
        """
        # This is where you'll integrate the ORB-SLAM3 C++ library
        # You'll need to create Python bindings or use existing ones
        pass

    def shutdown_slam(self):
        """Clean shutdown of SLAM system."""
        if hasattr(self, 'slam_system') and self.slam_system is not None:
            # TODO: Properly shutdown ORB-SLAM3 system
            pass
        self.get_logger().info("SLAM system shutdown")


def main(args=None):
    """Main function to start the SLAM system node."""
    rclpy.init(args=args)
    
    slam_system = SlamSystemNode()
    
    try:
        rclpy.spin(slam_system)
    except KeyboardInterrupt:
        pass
    finally:
        slam_system.shutdown_slam()
        slam_system.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()