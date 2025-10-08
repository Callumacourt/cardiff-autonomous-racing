"""
Test Image Publisher

Publishes test images with cone-like objects for testing the cone detection system.
Creates synthetic racing cones on a track background for development and testing.

Author: Cardiff Autonomous Racing Team
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import os


class TestImagePublisher(Node):
    """
    Publishes test images for cone detection development.
    
    Creates synthetic images with racing cones for testing the perception system
    when real camera data is not available.
    """

    def __init__(self):
        super().__init__('test_image_publisher')
        
        # Configuration parameters
        self.declare_parameter('test_image_path', '/workspace/test_data/cone_images/test_cone.jpg')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('publish_rate', 10.0)  # Hz
        
        # Get configuration
        test_image_path = self.get_parameter('test_image_path').get_parameter_value().string_value
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        
        # Initialize image converter
        self.bridge = CvBridge()
        
        # Load or create test image
        self.test_image = self.load_test_image(test_image_path)
        
        # Set up publishers
        self.image_publisher = self.create_publisher(Image, image_topic, 10)
        self.camera_info_publisher = self.create_publisher(CameraInfo, camera_info_topic, 10)
        
        # Start publishing timer
        self.timer = self.create_timer(1.0 / publish_rate, self.publish_test_data)
        
        self.get_logger().info(f"Publishing test images to {image_topic} at {publish_rate} Hz")
        self.get_logger().info("Use this for testing cone detection without real camera")

    def load_test_image(self, image_path):
        """
        Load test image or create synthetic one if file doesn't exist.
        
        Args:
            image_path: Path to test image file
            
        Returns:
            numpy.ndarray: Test image in BGR format
        """
        try:
            if os.path.exists(image_path):
                image = cv2.imread(image_path)
                self.get_logger().info(f"Loaded test image: {image_path}")
                return image
        except Exception as e:
            self.get_logger().warning(f"Could not load image from {image_path}: {e}")
        
        # Create synthetic test image
        self.get_logger().info("Creating synthetic cone test image")
        return self.create_racing_scene()

    def create_racing_scene(self):
        """
        Create synthetic racing scene with cones.
        
        Returns:
            numpy.ndarray: Synthetic racing image with colored cones
        """
        # Create track background (640x480 standard resolution)
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Track surface (dark gray asphalt)
        img[:, :] = [50, 50, 50]
        
        # Add track markings (white lines)
        cv2.line(img, (0, 400), (640, 400), (255, 255, 255), 2)  # Lane marking
        cv2.line(img, (320, 300), (320, 480), (255, 255, 255), 1)  # Center line
        
        # Add racing cones
        # Orange cone (left side of track)
        self.draw_cone(img, (150, 350), (0, 165, 255))  # Orange in BGR
        
        # Blue cone (center-left)
        self.draw_cone(img, (280, 320), (255, 0, 0))  # Blue in BGR
        
        # Yellow cone (center-right)
        self.draw_cone(img, (360, 320), (0, 255, 255))  # Yellow in BGR
        
        # Orange cone (right side)
        self.draw_cone(img, (490, 350), (0, 165, 255))  # Orange in BGR
        
        # Add some realistic noise and lighting variation
        noise = np.random.randint(-10, 10, img.shape, dtype=np.int16)
        img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
        
        return img

    def draw_cone(self, img, position, color):
        """
        Draw a racing cone at the specified position.
        
        Args:
            img: Image to draw on
            position: (x, y) position of cone base
            color: BGR color tuple
        """
        x, y = position
        
        # Cone dimensions
        cone_width = 30
        cone_height = 40
        
        # Draw cone body (trapezoid shape)
        cone_points = np.array([
            [x, y],  # Bottom center
            [x - cone_width//2, y],  # Bottom left
            [x - cone_width//4, y - cone_height],  # Top left
            [x + cone_width//4, y - cone_height],  # Top right
            [x + cone_width//2, y]  # Bottom right
        ])
        
        cv2.fillPoly(img, [cone_points], color)
        
        # Add cone highlights for realism
        highlight_color = tuple(min(255, c + 50) for c in color)
        cv2.line(img, (x - cone_width//4, y - cone_height), 
                (x - cone_width//8, y - cone_height//2), highlight_color, 2)

    def create_camera_info(self):
        """
        Create camera calibration information for the test images.
        
        Returns:
            sensor_msgs/CameraInfo: Camera calibration data
        """
        camera_info = CameraInfo()
        camera_info.header.frame_id = "camera_link"
        
        # Standard camera resolution
        camera_info.width = 640
        camera_info.height = 480
        
        # Camera intrinsic matrix (typical values for simulation)
        focal_length = 525.0
        center_x = 320.0
        center_y = 240.0
        
        camera_info.k = [
            focal_length, 0.0, center_x,
            0.0, focal_length, center_y,
            0.0, 0.0, 1.0
        ]
        
        # No lens distortion for synthetic images
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        camera_info.distortion_model = "plumb_bob"
        
        # Identity rectification matrix
        camera_info.r = [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        ]
        
        # Projection matrix
        camera_info.p = [
            focal_length, 0.0, center_x, 0.0,
            0.0, focal_length, center_y, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        
        return camera_info

    def publish_test_data(self):
        """Publish test image and camera calibration data."""
        try:
            # Get current timestamp
            timestamp = self.get_clock().now().to_msg()
            
            # Publish test image
            img_msg = self.bridge.cv2_to_imgmsg(self.test_image, "bgr8")
            img_msg.header.stamp = timestamp
            img_msg.header.frame_id = "camera_link"
            self.image_publisher.publish(img_msg)
            
            # Publish camera calibration
            camera_info = self.create_camera_info()
            camera_info.header.stamp = timestamp
            self.camera_info_publisher.publish(camera_info)
            
        except Exception as e:
            self.get_logger().error(f"Error publishing test data: {e}")


def main(args=None):
    """Main function to run the test image publisher."""
    rclpy.init(args=args)
    
    test_publisher = TestImagePublisher()
    
    try:
        rclpy.spin(test_publisher)
    except KeyboardInterrupt:
        test_publisher.get_logger().info("Test image publisher stopped")
    finally:
        test_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()