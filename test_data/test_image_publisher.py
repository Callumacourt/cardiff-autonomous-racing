"""
Test script to publish a static image for cone detection testing.
This publishes a test cone image to the camera topic for testing perception.
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from cv_bridge import CvBridge
import cv2
import numpy as np
import os


class TestImagePublisher(Node):
    """Publishes test images for cone detection testing."""

    def __init__(self):
        super().__init__('test_image_publisher')
        
        # Parameters
        self.declare_parameter('test_image_path', '/workspace/test_data/cone_images/test_cone.jpg')
        self.declare_parameter('image_topic', '/camera/image_raw')
        self.declare_parameter('camera_info_topic', '/camera/camera_info')
        self.declare_parameter('publish_rate', 10.0)  # Hz
        
        # Get parameters
        test_image_path = self.get_parameter('test_image_path').get_parameter_value().string_value
        image_topic = self.get_parameter('image_topic').get_parameter_value().string_value
        camera_info_topic = self.get_parameter('camera_info_topic').get_parameter_value().string_value
        publish_rate = self.get_parameter('publish_rate').get_parameter_value().double_value
        
        # Initialize CV bridge
        self.bridge = CvBridge()
        
        # Load test image
        try:
            if os.path.exists(test_image_path):
                self.test_image = cv2.imread(test_image_path)
                self.get_logger().info(f"Loaded test image: {test_image_path}")
            else:
                # Create a synthetic test image with colored rectangles (simulating cones)
                self.test_image = self.create_synthetic_cone_image()
                self.get_logger().info("Created synthetic cone test image")
        except Exception as e:
            self.get_logger().error(f"Error loading image: {e}")
            self.test_image = self.create_synthetic_cone_image()
        
        # Create publishers
        self.image_publisher = self.create_publisher(
            Image,
            image_topic,
            10
        )
        
        self.camera_info_publisher = self.create_publisher(
            CameraInfo,
            camera_info_topic,
            10
        )
        
        # Create timer for publishing
        self.timer = self.create_timer(
            1.0 / publish_rate,
            self.publish_test_data
        )
        
        self.get_logger().info(f"Publishing test images to {image_topic} at {publish_rate} Hz")

    def create_synthetic_cone_image(self):
        """Create a synthetic test image with cone-like objects."""
        # Create a 640x480 image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Add a green background (grass-like)
        img[:, :] = [34, 139, 34]  # Forest green
        
        # Add some "cones" as colored triangles/rectangles
        # Orange cone (left side)
        cv2.rectangle(img, (100, 300), (140, 400), (0, 165, 255), -1)  # Orange in BGR
        cv2.polygon(img, [np.array([[120, 280], [90, 340], [150, 340]])], (0, 165, 255))
        
        # Blue cone (center)
        cv2.rectangle(img, (300, 280), (340, 380), (255, 0, 0), -1)  # Blue in BGR
        cv2.polygon(img, [np.array([[320, 260], [290, 320], [350, 320]])], (255, 0, 0))
        
        # Yellow cone (right side)
        cv2.rectangle(img, (500, 320), (540, 420), (0, 255, 255), -1)  # Yellow in BGR
        cv2.polygon(img, [np.array([[520, 300], [490, 360], [550, 360]])], (0, 255, 255))
        
        # Add some noise and texture
        noise = np.random.randint(0, 30, img.shape, dtype=np.uint8)
        img = cv2.add(img, noise)
        
        return img

    def create_camera_info(self):
        """Create a basic camera info message."""
        camera_info = CameraInfo()
        
        # Set basic camera parameters (typical values for simulation)
        camera_info.header.frame_id = "camera_link"
        camera_info.width = 640
        camera_info.height = 480
        
        # Camera matrix (K)
        camera_info.k = [
            525.0, 0.0, 320.0,
            0.0, 525.0, 240.0,
            0.0, 0.0, 1.0
        ]
        
        # Distortion coefficients (assume no distortion for simplicity)
        camera_info.d = [0.0, 0.0, 0.0, 0.0, 0.0]
        camera_info.distortion_model = "plumb_bob"
        
        # Rectification matrix (R)
        camera_info.r = [
            1.0, 0.0, 0.0,
            0.0, 1.0, 0.0,
            0.0, 0.0, 1.0
        ]
        
        # Projection matrix (P)
        camera_info.p = [
            525.0, 0.0, 320.0, 0.0,
            0.0, 525.0, 240.0, 0.0,
            0.0, 0.0, 1.0, 0.0
        ]
        
        return camera_info

    def publish_test_data(self):
        """Publish test image and camera info."""
        try:
            # Create and publish image message
            img_msg = self.bridge.cv2_to_imgmsg(self.test_image, "bgr8")
            img_msg.header.stamp = self.get_clock().now().to_msg()
            img_msg.header.frame_id = "camera_link"
            
            self.image_publisher.publish(img_msg)
            
            # Create and publish camera info
            camera_info = self.create_camera_info()
            camera_info.header.stamp = img_msg.header.stamp
            
            self.camera_info_publisher.publish(camera_info)
            
        except Exception as e:
            self.get_logger().error(f"Error publishing test data: {e}")


def main(args=None):
    rclpy.init(args=args)
    
    test_publisher = TestImagePublisher()
    
    try:
        rclpy.spin(test_publisher)
    except KeyboardInterrupt:
        pass
    finally:
        test_publisher.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()