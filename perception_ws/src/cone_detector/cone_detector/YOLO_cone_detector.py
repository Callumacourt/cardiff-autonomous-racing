"""
YOLOv8 cone detector with depth-based 3-D localisation.

Subscribes (synchronised):
    /zed/left/image_rect_color   sensor_msgs/Image   RGB camera
    /zed/depth/image_raw         sensor_msgs/Image   depth (32FC1, metres)
    /zed/left/camera_info        sensor_msgs/CameraInfo  intrinsics (once)

Publishes:
    /cone_cloud/local        sensor_msgs/PointCloud2 per cone:
                             (x, y, z, label, confidence),
                             CAMERA optical frame (X right, Y down, Z forward)
    /yolo_annotated_image    sensor_msgs/Image        debug view with boxes

Label field values (must match cone_mapper/constants.py ConeColor):
    0 = blue, 1 = yellow, 2 = orange, 3 = unknown
"""

import time

import cv2
import numpy as np
import torch
import message_filters
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import CameraInfo, Image, PointCloud2, PointField
from sensor_msgs_py import point_cloud2
from std_msgs.msg import Header
from ultralytics import YOLO

MODEL_PATH = '/workspace/perception_ws/models/best.pt'

# YOLO class id → (colour name, published label)
CLASS_TO_LABEL = {
    0: ('blue', 0),          # blue_cone
    1: ('orange', 2),        # large_orange_cone
    2: ('orange', 2),        # orange_cone
    3: ('unknown', 3),       # unknown_cone
    4: ('yellow', 1),        # yellow_cone
}

POINT_FIELDS = [
    PointField(name='x', offset=0, datatype=PointField.FLOAT32, count=1),
    PointField(name='y', offset=4, datatype=PointField.FLOAT32, count=1),
    PointField(name='z', offset=8, datatype=PointField.FLOAT32, count=1),
    PointField(name='label', offset=12, datatype=PointField.FLOAT32, count=1),
    PointField(name='confidence', offset=16, datatype=PointField.FLOAT32, count=1),
]


class YOLOConeDetector3D(Node):
    def __init__(self):
        super().__init__('yolo_cone_detector_3d_node')
        self.bridge = CvBridge()

        self.device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')
        self.get_logger().info(f'Using device: {self.device}')

        self.model = YOLO(MODEL_PATH)
        self.model.to(self.device)
        self.get_logger().info(
            f'YOLO model loaded ({MODEL_PATH}), classes: {self.model.model.names}')

        # Detection parameters
        self.conf_threshold = 0.5
        self.iou_threshold = 0.45
        self.max_detection_distance = 20.0  # metres
        self.mask_upper_fraction = 0.4      # black out sky/horizon (top 40 %)

        # Camera intrinsics — populated from /zed/left/camera_info once
        self.fx = self.fy = self.cx = self.cy = None
        self.create_subscription(
            CameraInfo, '/zed/left/camera_info', self._camera_info_cb, 1)

        # Synchronised RGB + depth
        self.rgb_sub = message_filters.Subscriber(
            self, Image, '/zed/left/image_rect_color')
        self.depth_sub = message_filters.Subscriber(
            self, Image, '/zed/depth/image_raw')
        self.ts = message_filters.ApproximateTimeSynchronizer(
            [self.rgb_sub, self.depth_sub], queue_size=10, slop=0.1)
        self.ts.registerCallback(self.image_callback)

        # Publishers
        self.image_pub = self.create_publisher(Image, 'yolo_annotated_image', 10)
        self.cone_pub = self.create_publisher(PointCloud2, 'cone_cloud/local', 10)

        # Performance tracking
        self.inference_times = []
        self.frame_count = 0

        self.get_logger().info('YOLO cone detector started.')

    def _camera_info_cb(self, msg: CameraInfo):
        if self.fx is not None:
            return
        self.fx, self.fy = msg.k[0], msg.k[4]
        self.cx, self.cy = msg.k[2], msg.k[5]
        self.get_logger().info(
            f'Camera intrinsics: fx={self.fx:.1f} fy={self.fy:.1f} '
            f'cx={self.cx:.1f} cy={self.cy:.1f}')

    @staticmethod
    def _depth_at(depth_image, px: int, py: int) -> float:
        """Median depth (m) of the valid pixels in a 5x5 patch around (px, py)."""
        h, w = depth_image.shape[:2]
        y0, y1 = max(0, py - 2), min(h, py + 3)
        x0, x1 = max(0, px - 2), min(w, px + 3)
        patch = depth_image[y0:y1, x0:x1]
        valid = patch[np.isfinite(patch) & (patch > 0.0)]
        return float(np.median(valid)) if valid.size else 0.0

    def _publish_cones(self, points, header_src) -> None:
        """Publish (x, y, z, label) tuples as PointCloud2 in the camera frame."""
        header = Header()
        header.stamp = header_src.stamp
        header.frame_id = header_src.frame_id
        self.cone_pub.publish(point_cloud2.create_cloud(header, POINT_FIELDS, points))

    def image_callback(self, rgb_msg, depth_msg):
        if self.fx is None:
            self.get_logger().warning(
                'Camera intrinsics not yet received, skipping frame',
                throttle_duration_sec=5.0)
            return

        start_time = time.time()
        rgb_image = self.bridge.imgmsg_to_cv2(rgb_msg, 'bgr8')
        depth_image = self.bridge.imgmsg_to_cv2(depth_msg, '32FC1')

        # Black out the sky/horizon so YOLO only sees the track
        masked_rgb = rgb_image.copy()
        mask_line_y = int(rgb_image.shape[0] * self.mask_upper_fraction)
        masked_rgb[:mask_line_y, :] = 0

        inference_start = time.time()
        try:
            results = self.model(
                masked_rgb, conf=self.conf_threshold, iou=self.iou_threshold,
                device=self.device, verbose=False)[0]
        except Exception as e:
            self.get_logger().error(f'YOLO inference failed: {e}')
            return
        inference_time = time.time() - inference_start

        points = []
        n_boxes = 0
        if results.boxes is not None:
            for box in results.boxes.cpu().numpy():
                n_boxes += 1
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = float(box.conf[0])
                class_id = int(box.cls[0])
                px, py = (x1 + x2) // 2, (y1 + y2) // 2

                colour, label = CLASS_TO_LABEL.get(class_id, ('unknown', -1))
                if label == -1:
                    continue

                depth = self._depth_at(depth_image, px, py)
                if depth <= 0.0 or depth > self.max_detection_distance:
                    continue

                # Pinhole back-projection, camera optical frame
                Z = depth
                X = (px - self.cx) * Z / self.fx
                Y = (py - self.cy) * Z / self.fy
                points.append((X, Y, Z, float(label), confidence))

                cv2.rectangle(rgb_image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(rgb_image, f'{colour} {confidence:.2f}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
                cv2.putText(rgb_image, f'[{X:.1f}, {Y:.1f}, {Z:.1f}]',
                            (x1, y2 + 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4,
                            (255, 255, 255), 1)

        if points:
            self._publish_cones(points, rgb_msg.header)

        # Annotated debug image (view in RViz: /yolo_annotated_image)
        cv2.line(rgb_image, (0, mask_line_y),
                 (rgb_image.shape[1], mask_line_y), (255, 0, 0), 2)
        try:
            annotated = self.bridge.cv2_to_imgmsg(rgb_image, encoding='bgr8')
            annotated.header = rgb_msg.header
            self.image_pub.publish(annotated)
        except Exception as e:
            self.get_logger().error(f'Failed to publish annotated image: {e}')

        # Periodic performance log
        self.inference_times.append(inference_time)
        self.frame_count += 1
        if self.frame_count % 100 == 0:
            avg_inf = np.mean(self.inference_times[-100:])
            total = time.time() - start_time
            fps = 1.0 / total if total > 0 else 0.0
            self.get_logger().info(
                f'Avg inference: {avg_inf:.3f}s, FPS: {fps:.1f}, '
                f'boxes: {n_boxes}, published cones: {len(points)}')


def main(args=None):
    rclpy.init(args=args)
    node = YOLOConeDetector3D()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
