import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from cv_bridge import CvBridge
import cv2
import numpy as np
import message_filters  
from std_msgs.msg import String, Header
import torch
from ultralytics import YOLO  


class YOLOConeDetector3D(Node):
    def __init__(self):
        super().__init__('yolo_cone_detector_3d_node')
        self.bridge = CvBridge()
        
        # Device detection and setup
        self.device = self.setup_device()
        
        # Load YOLO model
        model_path = '/workspace/perception_ws/models/best.pt'  # Model copied by Dockerfile
        self.model = self.load_model(model_path)
        
        # Model parameters
        self.conf_threshold = 0.5  # Confidence threshold
        self.iou_threshold = 0.45  # IoU threshold for NMS
        self.max_detection_distance = 20.0  # Maximum detection distance in meters
        
        # Image masking parameters (remove upper third of image)
        self.mask_upper_fraction = 0.4  # Mask upper 33% of image
        
        # Subscribe to RGB + depth images
        self.rgb_sub = message_filters.Subscriber(self, Image, '/zed/left/image_rect_color')
        self.depth_sub = message_filters.Subscriber(self, Image, '/zed/depth/image_raw')
        
        # Sync both image streams
        self.ts = message_filters.ApproximateTimeSynchronizer([self.rgb_sub, self.depth_sub], queue_size=10, slop=0.1)
        self.ts.registerCallback(self.image_callback)
        
        self.get_logger().info("YOLO ConeDetector 3D node started.")
        # Publisher for annotated image with bounding boxes
        self.image_publisher_ = self.create_publisher(Image, 'yolo_annotated_image', 10)
        # Cone detection publication (subscribe here!!)
        self.cone_pc = self.create_publisher(PointCloud2, 'cone_cloud/local', 10)
        
        # Performance tracking
        self.inference_times = []
        self.frame_count = 0
        
        self.depth_saved = False  
    
    def setup_device(self):
        """Setup computing device with comprehensive GPU detection"""
        try:
            # Check if CUDA is available
            if torch.cuda.is_available():
                device_count = torch.cuda.device_count()
                device_name = torch.cuda.get_device_name(0)
                memory_gb = torch.cuda.get_device_properties(0).total_memory / 1e9
                
                self.get_logger().info(f"GPU detected: {device_name}")
                self.get_logger().info(f"GPU memory: {memory_gb:.1f} GB")
                self.get_logger().info(f"Number of GPUs: {device_count}")
                
                device = torch.device('cuda:0')
                
                # Test GPU functionality
                test_tensor = torch.randn(10, 10).to(device)
                _ = test_tensor @ test_tensor.T  # Simple matrix multiplication test
                
                self.get_logger().info("GPU functionality test passed - using GPU")
                return device
                
            else:
                self.get_logger().warning("CUDA not available")
                
        except Exception as e:
            self.get_logger().error(f"GPU setup failed: {e}")
        
        # Fallback to CPU
        self.get_logger().info("Falling back to CPU")
        return torch.device('cpu')
    
    def load_model(self, model_path):
        """Load YOLO model with error handling"""
        try:
            self.get_logger().info(f"Loading model from: {model_path}")
            
            # Load model
            model = YOLO(model_path)
            
            # Move model to device
            model.to(self.device)
            
            # Get model info
            model_info = model.info()
            self.get_logger().info(f"Model loaded successfully")
            self.get_logger().info(f"Model device: {next(model.model.parameters()).device}")
            
            # Print class names for debugging
            if hasattr(model.model, 'names'):
                class_names = model.model.names
                self.get_logger().info(f"Model classes: {class_names}")
                
                # Print the corrected mapping
                self.get_logger().info("Class mapping being used:")
                for class_id, name in class_names.items():
                    color, label = self.get_cone_color_from_class(class_id, model)
                    self.get_logger().info(f"  {class_id}: {name} -> {color} (label: {label})")
            
            # Test inference with dummy image
            dummy_image = np.zeros((640, 640, 3), dtype=np.uint8)
            test_results = model(dummy_image, verbose=False)
            self.get_logger().info("Model inference test passed")
            
            return model
            
        except FileNotFoundError:
            self.get_logger().error(f"Model file not found: {model_path}")
            self.get_logger().info("Available files in weights folder:")
            import os
            if os.path.exists('weights'):
                for file in os.listdir('weights'):
                    self.get_logger().info(f"  - {file}")
            raise
            
        except Exception as e:
            self.get_logger().error(f"Failed to load model: {e}")
            raise
    
    def run_yolo_inference(self, image):
        """Run YOLO inference on the input image"""
        try:
            # YOLOv8 inference with device specification
            results = self.model(image, conf=self.conf_threshold, iou=self.iou_threshold, device=self.device)
            return results[0]  # First (and only) result
            
        except RuntimeError as e:
            if "out of memory" in str(e).lower():
                self.get_logger().error("GPU out of memory! Consider:")
                self.get_logger().error("1. Reducing image size")
                self.get_logger().error("2. Using a smaller model")
                self.get_logger().error("3. Reducing batch size")
                
                # Try to clear GPU cache
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()
                    
            self.get_logger().error(f"YOLO inference failed: {e}")
            return None
            
        except Exception as e:
            self.get_logger().error(f"YOLO inference failed: {e}")
            return None
    
    def parse_yolo_results(self, results):
        """Parse YOLO results into bounding boxes and classes"""
        detections = []
        
        if results is None or results.boxes is None:
            return detections
            
        boxes = results.boxes.cpu().numpy()
        
        for box in boxes:
            # Extract bounding box coordinates
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])
            
            # Convert to x, y, w, h format
            x, y, w, h = x1, y1, x2 - x1, y2 - y1
            
            detections.append({
                'bbox': (x, y, w, h),
                'confidence': confidence,
                'class_id': class_id,
                'center': (x + w // 2, y + h // 2)
            })
        
        return detections
    
    def get_cone_color_from_class(self, class_id, model=None):
        """Map YOLO class ID to cone color and label"""
        class_mapping = {
            0: ("blue", 0),              # blue_cone
            1: ("large_orange", 2),      # large_orange_cone -> treat as orange
            2: ("orange", 2),            # orange_cone
            3: ("unknown", 3),           # unknown_cone
            4: ("yellow", 1),            # yellow_cone
        }
        
        result = class_mapping.get(class_id, ("unknown", -1))
        
        # Debug logging (only if model is available)
        if model and hasattr(model.model, 'names'):
            model_class_name = model.model.names.get(class_id, 'unknown')
            if hasattr(self, 'frame_count') and self.frame_count % 100 == 0:  # Log less frequently
                self.get_logger().debug(f"Class {class_id} ({model_class_name}) -> {result}")
        
        return result
    
    def mask_image_roi(self, image):
        """Mask the upper portion of the image to focus on relevant area"""
        height, width = image.shape[:2]
        mask_height = int(height * self.mask_upper_fraction)
        
        # Create masked image (set upper portion to black)
        masked_image = image.copy()
        masked_image[:mask_height, :] = 0
        
        return masked_image
    

    def get_cones(self, message_lines, frame_id='map', stamp=None):
        """Convert message lines (X,Y,Z,label) into a PointCloud2 and publish to cone_pc topic
        Args:
            message_lines: iterable of strings like 'X,Y,Z,label'
            frame_id: frame to set on the header (default 'map')
            stamp: optional builtin Time to use for header.stamp
        """
        if not message_lines:
            return

        points = []
        for line in message_lines:
            try:
                x, y, z, lab = line.split(',')
                points.append((float(x), float(y), float(z), float(lab)))
            except Exception:
                # Skip malformed lines
                continue

        if not points:
            return

        header = Header()
        header.stamp = stamp if stamp is not None else self.get_clock().now().to_msg()
        header.frame_id = frame_id

        fields = [
            PointField(name = 'x', offset =  0, datatype = PointField.FLOAT32, count = 1),
            PointField(name = 'y', offset = 4, datatype = PointField.FLOAT32, count = 1),
            PointField(name = 'z', offset = 8, datatype = PointField.FLOAT32, count = 1),
            # 0: blue_cone, 1: large_orange_cone, 2: orange_cone, 3: unknown_cone, 4: yellow_cone
            PointField(name ='label', offset = 12, datatype = PointField.FLOAT32, count = 1),
        ]

        pc_msg = point_cloud2.create_cloud(header, fields, points)
        self.cone_pc.publish(pc_msg)


    
    def image_callback(self, rgb_msg, depth_msg):
        import time
        start_time = time.time()
        
        rgb_image = self.bridge.imgmsg_to_cv2(rgb_msg, 'bgr8')
        depth_image = self.bridge.imgmsg_to_cv2(depth_msg, '32FC1')
        
        # Save depth image only once for debugging
        if not self.depth_saved:
            depth_vis = np.clip(depth_image, 0, 20)  # Clip to 0-20 meters
            depth_vis = (depth_vis / 20.0 * 255).astype(np.uint8)
            cv2.imwrite('/tmp/depth_debug.png', depth_vis)
            self.depth_saved = True

        # Apply ROI masking to focus on relevant area
        masked_rgb = self.mask_image_roi(rgb_image)
        
        # Run YOLO inference on masked image
        inference_start = time.time()
        results = self.run_yolo_inference(masked_rgb)
        inference_time = time.time() - inference_start
        
        # Parse results
        detections = self.parse_yolo_results(results)
        
        # Camera intrinsics
        fx, fy = 525.0, 525.0
        cx, cy = rgb_image.shape[1] // 2, rgb_image.shape[0] // 2
        
        message_lines = []  # All cone lines to be published
        
        # Debug: Count detections by class
        class_counts = {}
        
        for detection in detections:
            x, y, w, h = detection['bbox']
            cx_pixel, cy_pixel = detection['center']
            confidence = detection['confidence']
            class_id = detection['class_id']
            
            # Count detections by class for debugging
            class_counts[class_id] = class_counts.get(class_id, 0) + 1
            
            # Get depth at cone center
            depth = float(depth_image[cy_pixel, cx_pixel])
            if np.isnan(depth) or depth == 0.0:
                self.get_logger().debug(f"Skipping detection due to invalid depth: {depth}")
                continue
            
            # Calculate 3D position
            Z = depth
            X = (cx_pixel - cx) * Z / fx
            Y = (cy_pixel - cy) * Z / fy
            
            # Apply distance filter
            if Z > self.max_detection_distance:
                self.get_logger().debug(f"Skipping detection beyond {self.max_detection_distance}m: {Z:.1f}m")
                continue
            
            # Get cone color from class
            colour, label = self.get_cone_color_from_class(class_id, self.model)
            if label == -1:
                self.get_logger().debug(f"Skipping unknown class: {class_id}")
                continue  # Skip unknown classes
            
            message_lines.append(f"{X:.2f},{Y:.2f},{Z:.2f},{label}")
            
            # Get original class name for debugging
            model_class_name = "unknown"
            if hasattr(self.model.model, 'names'):
                model_class_name = self.model.model.names.get(class_id, "unknown")
        
            
            # Draw bounding box and label
            cv2.rectangle(rgb_image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(rgb_image, f"{model_class_name}", 
                       (x, y - 25), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 0), 1)
            cv2.putText(rgb_image, f"{colour} {confidence:.2f}", 
                       (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(rgb_image, f"[{X:.1f}, {Y:.1f}, {Z:.1f}]", 
                       (x, y + h + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        
        # Debug: Print class distribution every 50 frames
        if self.frame_count % 50 == 0 and class_counts:
            self.get_logger().info(f"Detection class distribution: {class_counts}")

        # Publish point cloud of cones (camera frame by default)
        try:
            self.get_cones(message_lines,
                           frame_id=rgb_msg.header.frame_id,
                           stamp=rgb_msg.header.stamp)
        except Exception as e:
            self.get_logger().error(f"Failed to publish cone pointcloud: {e}")

        
        # Performance tracking
        total_time = time.time() - start_time
        self.inference_times.append(inference_time)
        self.frame_count += 1
        
        # Log performance every 100 frames
        if self.frame_count % 100 == 0:
            avg_inference_time = np.mean(self.inference_times[-100:])
            fps = 1.0 / total_time if total_time > 0 else 0
            self.get_logger().info(f"Avg inference time: {avg_inference_time:.3f}s, FPS: {fps:.1f}, Detections: {len(detections)}")
        
        # Draw ROI mask boundary for visualisation
        height = rgb_image.shape[0]
        mask_line_y = int(height * self.mask_upper_fraction)
        cv2.line(rgb_image, (0, mask_line_y), (rgb_image.shape[1], mask_line_y), (255, 0, 0), 2)
        cv2.putText(rgb_image, "ROI Mask", (10, mask_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
        
        # Publish annotated image for RVIZ visualization
        try:
            annotated_msg = self.bridge.cv2_to_imgmsg(rgb_image, encoding='bgr8')
            annotated_msg.header = rgb_msg.header  # Preserve timestamp and frame_id
            self.image_publisher_.publish(annotated_msg)
        except Exception as e:
            self.get_logger().error(f"Failed to publish annotated image: {e}")
        
        # Display image
        cv2.imshow("YOLO Cone Detection 3D", rgb_image)
        cv2.waitKey(1)

# --- Entry Point ---
def main(args=None):
    rclpy.init(args=args)
    node = YOLOConeDetector3D()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()
    cv2.destroy_all_windows()

if __name__ == '__main__':
    main()