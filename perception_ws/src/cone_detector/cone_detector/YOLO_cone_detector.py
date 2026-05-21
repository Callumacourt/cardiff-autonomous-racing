import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, PointCloud2, PointField, CameraInfo
from sensor_msgs_py import point_cloud2
from cv_bridge import CvBridge
import cv2
import numpy as np
import message_filters
from std_msgs.msg import Header
import torch
from ultralytics import YOLO


class YOLOConeDetector3D(Node):
    def __init__(self):
        super().__init__('yolo_cone_detector_3d_node')
        self.bridge = CvBridge()

        # --- Parameters ---
        self.show_display = self.declare_parameter('show_display', False).get_parameter_value().bool_value
        model_path = self.declare_parameter(
            'model_path', '/workspace/perception_ws/models/best.pt'
        ).get_parameter_value().string_value
        self.conf_threshold = self.declare_parameter('conf_threshold', 0.5).get_parameter_value().double_value
        self.iou_threshold = self.declare_parameter('iou_threshold', 0.45).get_parameter_value().double_value
        self.max_detection_distance = self.declare_parameter('max_distance', 20.0).get_parameter_value().double_value
        self.mask_upper_fraction = self.declare_parameter('mask_upper_fraction', 0.4).get_parameter_value().double_value
        rgb_topic = self.declare_parameter('rgb_topic', '/zed/left/image_rect_color').get_parameter_value().string_value
        depth_topic = self.declare_parameter('depth_topic', '/zed/depth/image_raw').get_parameter_value().string_value
        camera_info_topic = self.declare_parameter(
            'camera_info_topic', '/zed/left/camera_info'
        ).get_parameter_value().string_value

        # --- Camera intrinsics — defaults used until CameraInfo arrives ---
        # Fallback values match the EUFS sim ZED at 640×480.
        # Overwritten by /zed/left/camera_info when that topic exists.
        self.fx: float = self.declare_parameter('fx', 525.0).get_parameter_value().double_value
        self.fy: float = self.declare_parameter('fy', 525.0).get_parameter_value().double_value
        self.cx: float = self.declare_parameter('cx', 320.0).get_parameter_value().double_value
        self.cy: float = self.declare_parameter('cy', 240.0).get_parameter_value().double_value
        self._camera_info_received = False

        # --- Device ---
        self.device = self._setup_device()

        # --- Model ---
        self.model = self._load_model(model_path)

        # --- Subscribers ---
        self.camera_info_sub = self.create_subscription(
            CameraInfo, camera_info_topic, self._camera_info_callback, 1)
        self.rgb_sub = message_filters.Subscriber(self, Image, rgb_topic)
        self.depth_sub = message_filters.Subscriber(self, Image, depth_topic)
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.rgb_sub, self.depth_sub], queue_size=10, slop=0.1)
        self.ts.registerCallback(self._image_callback)

        # --- Publishers ---
        self.image_pub = self.create_publisher(Image, '/yolo_annotated_image', 10)
        self.cone_pc_pub = self.create_publisher(PointCloud2, '/cone_cloud/local', 10)

        # --- Performance tracking ---
        self.inference_times = []
        self.frame_count = 0

        self.get_logger().info(
            f'YOLO ConeDetector3D started | device={self.device} | show_display={self.show_display}'
        )

    # ------------------------------------------------------------------ #
    #  Initialisation helpers                                              #
    # ------------------------------------------------------------------ #

    def _camera_info_callback(self, msg: CameraInfo):
        """Override intrinsics with calibrated values when CameraInfo arrives."""
        if self._camera_info_received:
            return
        K = msg.k
        self.fx, self.fy = K[0], K[4]
        self.cx, self.cy = K[2], K[5]
        self._camera_info_received = True
        self.get_logger().info(
            f'Camera intrinsics from CameraInfo: fx={self.fx:.1f} fy={self.fy:.1f} '
            f'cx={self.cx:.1f} cy={self.cy:.1f}'
        )

    def _setup_device(self):
        try:
            if torch.cuda.is_available():
                name = torch.cuda.get_device_name(0)
                mem = torch.cuda.get_device_properties(0).total_memory / 1e9
                self.get_logger().info(f'GPU: {name} ({mem:.1f} GB)')
                device = torch.device('cuda:0')
                t = torch.randn(10, 10).to(device)
                _ = t @ t.T
                self.get_logger().info('GPU test passed')
                return device
        except Exception as e:
            self.get_logger().error(f'GPU setup failed: {e}')
        self.get_logger().info('Using CPU')
        return torch.device('cpu')

    def _load_model(self, model_path):
        self.get_logger().info(f'Loading YOLO model from: {model_path}')
        try:
            model = YOLO(model_path)
            model.to(self.device)
            if hasattr(model.model, 'names'):
                self.get_logger().info(f'Model classes: {model.model.names}')
            model(np.zeros((640, 640, 3), dtype=np.uint8), verbose=False)
            self.get_logger().info('Model loaded and warm-up pass complete')
            return model
        except FileNotFoundError:
            self.get_logger().fatal(f'Model not found: {model_path}')
            raise
        except Exception as e:
            self.get_logger().fatal(f'Failed to load model: {e}')
            raise

    # ------------------------------------------------------------------ #
    #  Inference helpers                                                   #
    # ------------------------------------------------------------------ #

    def _run_yolo(self, image):
        try:
            results = self.model(
                image,
                conf=self.conf_threshold,
                iou=self.iou_threshold,
                device=self.device,
                verbose=False,
            )
            return results[0]
        except RuntimeError as e:
            if 'out of memory' in str(e).lower() and torch.cuda.is_available():
                torch.cuda.empty_cache()
            self.get_logger().error(f'YOLO inference failed: {e}')
            return None

    def _sample_depth(self, depth_image: np.ndarray, cx_pixel: int, cy_pixel: int, radius: int = 3):
        """
        Return median depth of a small window centred on the detection.
        Handles NaN/zero values from stereo disparity holes.
        Returns None if fewer than 3 valid pixels found.
        """
        h, w = depth_image.shape
        y1 = max(0, cy_pixel - radius)
        y2 = min(h, cy_pixel + radius + 1)
        x1 = max(0, cx_pixel - radius)
        x2 = min(w, cx_pixel + radius + 1)
        patch = depth_image[y1:y2, x1:x2]
        valid = patch[np.isfinite(patch) & (patch > 0.1)]
        if len(valid) < 3:
            return None
        return float(np.median(valid))

    def _get_cone_color(self, class_id: int):
        """Map YOLO class ID to (color_name, label_int). label -1 = skip."""
        mapping = {
            0: ('blue', 0),
            1: ('large_orange', 2),
            2: ('orange', 2),
            3: ('unknown', 3),
            4: ('yellow', 1),
        }
        return mapping.get(class_id, ('unknown', -1))

    def _mask_roi(self, image: np.ndarray) -> np.ndarray:
        masked = image.copy()
        masked[:int(image.shape[0] * self.mask_upper_fraction), :] = 0
        return masked

    # ------------------------------------------------------------------ #
    #  Main callback                                                       #
    # ------------------------------------------------------------------ #

    def _image_callback(self, rgb_msg: Image, depth_msg: Image):
        import time
        t0 = time.time()

        rgb_image = self.bridge.imgmsg_to_cv2(rgb_msg, 'bgr8')
        depth_image = self.bridge.imgmsg_to_cv2(depth_msg, '32FC1')

        results = self._run_yolo(self._mask_roi(rgb_image))
        inference_time = time.time() - t0

        if results is None or results.boxes is None:
            self._publish_annotated(rgb_image, rgb_msg)
            return

        # Accumulate detections as (x_cam, y_cam, z_cam, label_float)
        points = []

        for box in results.boxes.cpu().numpy():
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            confidence = float(box.conf[0])
            class_id = int(box.cls[0])

            cx_px = (x1 + x2) // 2
            cy_px = (y1 + y2) // 2

            depth = self._sample_depth(depth_image, cx_px, cy_px)
            if depth is None or depth > self.max_detection_distance:
                continue

            Z = depth
            X = (cx_px - self.cx) * Z / self.fx
            Y = (cy_px - self.cy) * Z / self.fy

            colour, label = self._get_cone_color(class_id)
            if label == -1:
                continue

            points.append((X, Y, Z, float(label)))

            # Annotate image
            class_name = (self.model.model.names.get(class_id, str(class_id))
                          if hasattr(self.model.model, 'names') else str(class_id))
            cv2.rectangle(rgb_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(rgb_image, f'{colour} {confidence:.2f}',
                        (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            cv2.putText(rgb_image, f'[{X:.1f},{Y:.1f},{Z:.1f}]m',
                        (x1, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (200, 200, 200), 1)

        # Publish PointCloud2 in camera frame
        if points:
            header = Header()
            header.stamp = rgb_msg.header.stamp
            header.frame_id = rgb_msg.header.frame_id
            fields = [
                PointField(name='x', offset=0,  datatype=PointField.FLOAT32, count=1),
                PointField(name='y', offset=4,  datatype=PointField.FLOAT32, count=1),
                PointField(name='z', offset=8,  datatype=PointField.FLOAT32, count=1),
                PointField(name='label', offset=12, datatype=PointField.FLOAT32, count=1),
            ]
            self.cone_pc_pub.publish(point_cloud2.create_cloud(header, fields, points))

        # ROI line + publish annotated image
        mask_y = int(rgb_image.shape[0] * self.mask_upper_fraction)
        cv2.line(rgb_image, (0, mask_y), (rgb_image.shape[1], mask_y), (255, 0, 0), 2)
        self._publish_annotated(rgb_image, rgb_msg)

        # Optional live display (requires DISPLAY; off by default in competition)
        if self.show_display:
            cv2.imshow('YOLO Cone Detection 3D', rgb_image)
            cv2.waitKey(1)

        # Performance logging (every 100 frames)
        self.inference_times.append(inference_time)
        self.frame_count += 1
        if self.frame_count % 100 == 0:
            avg = np.mean(self.inference_times[-100:])
            self.get_logger().info(
                f'Inference avg={avg*1000:.1f}ms  FPS={1.0/avg:.1f}  '
                f'detections={len(points)}'
            )

    def _publish_annotated(self, rgb_image: np.ndarray, rgb_msg: Image):
        try:
            ann_msg = self.bridge.cv2_to_imgmsg(rgb_image, encoding='bgr8')
            ann_msg.header = rgb_msg.header
            self.image_pub.publish(ann_msg)
        except Exception as e:
            self.get_logger().error(f'Failed to publish annotated image: {e}')


def main(args=None):
    rclpy.init(args=args)
    node = YOLOConeDetector3D()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
