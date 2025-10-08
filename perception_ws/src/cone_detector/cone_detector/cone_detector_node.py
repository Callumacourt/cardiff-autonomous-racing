"""
Racing Cone Detection Node

A ROS2 node that detects racing cones in camera images using computer vision.
Uses YOLOv8 object detection model to find cones and publishes their positions.

Author: Cardiff Autonomous Racing Team
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from geometry_msgs.msg import PointStamped
from cv_bridge import CvBridge
import cv2
import numpy as np

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False


class ConeDetectorNode(Node):
    """
    Detects racing cones in camera images and publishes their positions.
    
    This node subscribes to camera images, processes them with YOLO object detection,
    and publishes detected cone positions for use by other racing systems.
    """

    def __init__(self):
        super().__init__('cone_detector')
        
        # Declare parameters
        self.declare_parameter('model_path', 'yolov8n.pt')
        self.declare_parameter('confidence_threshold', 0.5)
        self.declare_parameter('camera_topic', '/camera/image_raw')
        self.declare_parameter('output_topic', '/cone_detections')
        self.declare_parameter('debug_image_topic', '/cone_detector/debug_image')
        self.declare_parameter('publish_debug_image', True)
        
        # Get parameters
        model_path = self.get_parameter('model_path').get_parameter_value().string_value
        self.confidence_threshold = self.get_parameter('confidence_threshold').get_parameter_value().double_value
        camera_topic = self.get_parameter('camera_topic').get_parameter_value().string_value
        output_topic = self.get_parameter('output_topic').get_parameter_value().string_value
        debug_image_topic = self.get_parameter('debug_image_topic').get_parameter_value().string_value
        self.publish_debug_image = self.get_parameter('publish_debug_image').get_parameter_value().bool_value
        
        # Initialize OpenCV bridge for ROS<->OpenCV image conversion
        self.bridge = CvBridge()
        
        # Load object detection model
        if not YOLO_AVAILABLE:
            self.get_logger().error("YOLOv8 not available. Install with: pip install ultralytics")
            return
            
        try:
            self.model = YOLO(model_path)
            self.get_logger().info(f"Loaded object detection model: {model_path}")
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            return
        
        # Create ROS subscribers and publishers
        self.image_subscription = self.create_subscription(
            Image,
            camera_topic,
            self.image_callback,
            10
        )
        
        self.cone_publisher = self.create_publisher(
            PointStamped,
            output_topic,
            10
        )
        
        if self.publish_debug_image:
            self.debug_image_publisher = self.create_publisher(
                Image,
                debug_image_topic,
                10
            )
        
        self.get_logger().info("Cone detector node initialized")
        self.get_logger().info(f"Subscribing to: {camera_topic}")
        self.get_logger().info(f"Publishing cone detections to: {output_topic}")
        if self.publish_debug_image:
            self.get_logger().info(f"Publishing debug images to: {debug_image_topic}")

    def image_callback(self, msg):
        """
        Process incoming camera images to detect cones.
        
        Args:
            msg: sensor_msgs/Image message from camera
        """
        try:
            # Convert ROS image to OpenCV format
            cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
            
            # Run object detection on the image
            results = self.model(cv_image, conf=self.confidence_threshold)
            
            # Process each detection result
            for result in results:
                if result.boxes is not None:
                    boxes = result.boxes.xyxy.cpu().numpy()      # Bounding box coordinates
                    confidences = result.boxes.conf.cpu().numpy()  # Detection confidence
                    classes = result.boxes.cls.cpu().numpy()       # Object class IDs
                    
                    # Look for cone-like objects in the detections
                    for box, conf, cls in zip(boxes, confidences, classes):
                        class_id = int(cls)
                        class_name = self.model.names[class_id] if hasattr(self.model, 'names') else f"object_{class_id}"
                        
                        # Check if this detection could be a cone
                        if self.is_cone_like_object(class_id, class_name):
                            self.publish_cone_detection(box, conf, msg.header)
                            
                            # Draw bounding box for visualization
                            if self.publish_debug_image:
                                self.draw_detection_box(cv_image, box, class_name, conf)
            
            # Publish debug image with detection boxes
            if self.publish_debug_image:
                debug_msg = self.bridge.cv2_to_imgmsg(cv_image, "bgr8")
                debug_msg.header = msg.header
                self.debug_image_publisher.publish(debug_msg)
                
        except Exception as e:
            self.get_logger().error(f"Error processing image: {e}")

    def is_cone_like_object(self, class_id, class_name):
        """
        Determine if a detected object could be a racing cone.
        
        Args:
            class_id: YOLO class ID number
            class_name: Human-readable class name
            
        Returns:
            bool: True if object could be a cone
        """
        # YOLO COCO dataset doesn't have racing cones, so we look for similar objects
        # Common cone-like objects in COCO dataset:
        cone_like_classes = [
            39,  # bottle (cylindrical shape)
            41,  # cup (cone-like shape)
            46,  # banana (curved cone shape)
            67   # cell phone (rectangular but often cone-sized)
        ]
        
        # For now, accept all detections to see what's being found
        # Later, train a custom model specifically for racing cones
        return True  # TODO: Replace with trained cone detection model

    def draw_detection_box(self, image, box, class_name, confidence):
        """
        Draw a bounding box around a detected object.
        
        Args:
            image: OpenCV image to draw on
            box: Bounding box coordinates [x1, y1, x2, y2]
            class_name: Name of detected object class
            confidence: Detection confidence score
        """
        x1, y1, x2, y2 = map(int, box)
        
        # Draw rectangle around detection
        cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Add text label with class and confidence
        label = f'{class_name}: {confidence:.2f}'
        cv2.putText(image, label, (x1, y1 - 10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    def publish_cone_detection(self, box, confidence, header):
        """
        Publish a detected cone as a ROS message.
        
        Args:
            box: Bounding box coordinates [x1, y1, x2, y2]
            confidence: Detection confidence score
            header: Original image header for timestamp and frame
        """
        # Calculate center point of detection box
        x1, y1, x2, y2 = box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2
        
        # Create ROS message for cone position
        cone_msg = PointStamped()
        cone_msg.header = header
        cone_msg.point.x = center_x  # Pixel coordinates for now
        cone_msg.point.y = center_y  # TODO: Convert to real-world coordinates
        cone_msg.point.z = confidence  # Store confidence in z field temporarily
        
        # Publish the detection
        self.cone_publisher.publish(cone_msg)


def main(args=None):
    """Main function to start the cone detector node."""
    rclpy.init(args=args)
    
    cone_detector = ConeDetectorNode()
    
    try:
        rclpy.spin(cone_detector)
    except KeyboardInterrupt:
        pass
    finally:
        cone_detector.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()