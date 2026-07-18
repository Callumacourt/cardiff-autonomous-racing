#!/usr/bin/env python3
"""Publishes a USB webcam as RGB + a constant placeholder depth image, so
cone_detector's synchronised rgb/depth/camera_info inputs can be exercised
without a real depth sensor. Distances from the placeholder depth are NOT
real 3D positions -- this is for validating the 2D detector only.

Usage: ros2 run --prefix 'python3' ... or just: python3 webcam_test_publisher.py
"""
import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo

PLACEHOLDER_DEPTH_M = 5.0


def to_image_msg(array: np.ndarray, encoding: str) -> Image:
    """Build a sensor_msgs/Image directly from a numpy array.

    Bypasses cv_bridge.cv2_to_imgmsg, which raises KeyError on this machine
    -- the installed opencv-python (5.x) doesn't match the type table baked
    into ros-humble-cv-bridge (3.2.1, built against OpenCV 4.x).
    """
    msg = Image()
    msg.height, msg.width = array.shape[:2]
    msg.encoding = encoding
    msg.is_bigendian = 0
    msg.step = array.strides[0]
    msg.data = np.ascontiguousarray(array).tobytes()
    return msg


class WebcamTestPublisher(Node):
    def __init__(self):
        super().__init__('webcam_test_publisher')
        self.declare_parameter('device', '/dev/video0')
        self.declare_parameter('rate_hz', 10.0)
        device = self.get_parameter('device').value
        rate_hz = self.get_parameter('rate_hz').value

        self.cap = cv2.VideoCapture(device, cv2.CAP_V4L2)
        self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*'MJPG'))
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        if not self.cap.isOpened():
            raise RuntimeError(f'Could not open {device}')
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.get_logger().info(f'Opened {device} at {self.width}x{self.height}')

        self.rgb_pub = self.create_publisher(Image, '/webcam/rgb/image_raw', 10)
        self.depth_pub = self.create_publisher(Image, '/webcam/depth/image_raw', 10)
        self.info_pub = self.create_publisher(CameraInfo, '/webcam/camera_info', 10)

        # Rough placeholder intrinsics (not calibrated) -- fine for exercising
        # the 2D detector; only affects the (meaningless, since depth is
        # fake) X/Y back-projection, not the YOLO boxes themselves.
        fx = fy = float(self.width)
        cx, cy = self.width / 2.0, self.height / 2.0
        self.camera_info = CameraInfo()
        self.camera_info.width = self.width
        self.camera_info.height = self.height
        self.camera_info.k = [fx, 0.0, cx, 0.0, fy, cy, 0.0, 0.0, 1.0]

        self.depth_image = np.full((self.height, self.width), PLACEHOLDER_DEPTH_M, dtype=np.float32)

        self.create_timer(1.0 / rate_hz, self._tick)

    def _tick(self):
        ok, frame = self.cap.read()
        if not ok:
            self.get_logger().warning('Frame grab failed', throttle_duration_sec=5.0)
            return
        now = self.get_clock().now().to_msg()

        rgb_msg = to_image_msg(frame, 'bgr8')
        rgb_msg.header.stamp = now
        rgb_msg.header.frame_id = 'webcam'
        self.rgb_pub.publish(rgb_msg)

        depth_msg = to_image_msg(self.depth_image, '32FC1')
        depth_msg.header.stamp = now
        depth_msg.header.frame_id = 'webcam'
        self.depth_pub.publish(depth_msg)

        self.camera_info.header.stamp = now
        self.camera_info.header.frame_id = 'webcam'
        self.info_pub.publish(self.camera_info)

    def destroy_node(self):
        self.cap.release()
        super().destroy_node()


def main():
    rclpy.init()
    node = WebcamTestPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
