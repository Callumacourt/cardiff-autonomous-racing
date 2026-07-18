#!/usr/bin/env python3
"""Standalone viewer for the webcam cone_detector test.

Does NOT touch cone_detector or cv_bridge's outbound conversion (broken on
this machine only, see conversation). Instead: subscribes to the raw RGB
frames (inbound cv_bridge works fine) and /cone_cloud/local (no cv_bridge
involved at all -- PointCloud2), back-projects each detected cone's camera
frame (X, Y, Z) to pixel space with the same intrinsics cone_detector used,
draws a marker + label, and writes a PNG snapshot to disk periodically.

Usage: python3 webcam_test_viewer.py [--out-dir DIR] [--period-sec N]
"""
import argparse
import pathlib
import time

import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, PointCloud2
from sensor_msgs_py import point_cloud2

LABEL_NAMES = {0: 'blue', 1: 'yellow', 2: 'orange', 3: 'unknown'}
LABEL_COLOURS = {0: (255, 128, 0), 1: (0, 220, 220), 2: (0, 140, 255), 3: (200, 200, 200)}

# Same placeholder intrinsics webcam_test_publisher.py sends as camera_info.
FX = FY = 640.0
CX, CY = 320.0, 240.0


class WebcamTestViewer(Node):
    def __init__(self, out_dir: pathlib.Path, period_sec: float):
        super().__init__('webcam_test_viewer')
        self.out_dir = out_dir
        self.out_dir.mkdir(parents=True, exist_ok=True)
        self.period_sec = period_sec
        self.bridge = CvBridge()
        self.latest_frame = None
        self.latest_cones = []
        self.last_save = 0.0
        self.n_saved = 0

        self.create_subscription(Image, '/webcam/rgb/image_raw', self._rgb_cb, 10)
        self.create_subscription(PointCloud2, '/cone_cloud/local', self._cones_cb, 10)
        self.create_timer(0.5, self._maybe_save)
        self.get_logger().info(f'Writing snapshots to {self.out_dir}')

    def _rgb_cb(self, msg: Image):
        self.latest_frame = self.bridge.imgmsg_to_cv2(msg, 'bgr8')

    def _cones_cb(self, msg: PointCloud2):
        self.latest_cones = list(point_cloud2.read_points(
            msg, field_names=('x', 'y', 'z', 'label', 'confidence'), skip_nans=True))

    def _maybe_save(self):
        if self.latest_frame is None:
            return
        now = time.time()
        if now - self.last_save < self.period_sec:
            return
        self.last_save = now

        frame = self.latest_frame.copy()
        for x, y, z, label, conf in self.latest_cones:
            if z <= 0:
                continue
            px = int(x * FX / z + CX)
            py = int(y * FY / z + CY)
            colour = LABEL_COLOURS.get(int(label), (255, 255, 255))
            name = LABEL_NAMES.get(int(label), 'unknown')
            cv2.drawMarker(frame, (px, py), colour, cv2.MARKER_TILTED_CROSS, 24, 3)
            cv2.putText(frame, f'{name} {conf:.2f}', (px + 12, py),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 2)

        cv2.putText(frame, f'cones: {len(self.latest_cones)}', (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        self.n_saved += 1
        out_path = self.out_dir / f'snapshot_{self.n_saved:04d}.png'
        cv2.imwrite(str(out_path), frame)
        latest_path = self.out_dir / 'latest.png'
        cv2.imwrite(str(latest_path), frame)
        self.get_logger().info(f'Saved {out_path.name} ({len(self.latest_cones)} cones)')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out-dir', default='/tmp/webcam_test_snapshots')
    parser.add_argument('--period-sec', type=float, default=2.0)
    args, ros_args = parser.parse_known_args()

    rclpy.init(args=ros_args)
    node = WebcamTestViewer(pathlib.Path(args.out_dir), args.period_sec)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
