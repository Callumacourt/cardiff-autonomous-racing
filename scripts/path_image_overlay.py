#!/usr/bin/env python3
"""
Project the planner's /planned_path back into the camera image.

Subscribes the YOLO annotated image (boxes already drawn), the camera
intrinsics, the SLAM pose and /planned_path (both map frame), and publishes
/path_overlay_image with the path drawn as a green polyline on the ground.

Transform chain is the exact inverse of cone_mapper's:
    world -> robot:  X_r = R^T (X_w - t)          (R, t from /odometry/slam)
    robot -> camera optical:  x_c = -y_r, y_c = -z_r, z_c = x_r
    camera -> pixel:  px = cx + fx*x_c/z_c,  py = cy + fy*y_c/z_c

Run:
    python3 scripts/path_image_overlay.py [--image /yolo_annotated_image]
"""
import argparse
import math

import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
import cv2

from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import CameraInfo, Image
from std_msgs.msg import String


def quat_to_R(x, y, z, w):
    return np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w),     2 * (x * z + y * w)],
        [2 * (x * y + z * w),     1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w),     2 * (y * z + x * w),     1 - 2 * (x * x + y * y)],
    ])


class PathOverlay(Node):
    def __init__(self, image_topic, info_topic):
        super().__init__('path_image_overlay')
        self.bridge = CvBridge()
        self.fx = self.fy = self.cx = self.cy = None
        self.pose_t = np.zeros(3)
        self.pose_R = np.eye(3)
        self.path = []            # [(x, y)] map frame

        # ground height in the map frame: z=0 is the CAMERA height (SLAM
        # origin), so draw the path at the median z of the mapped cones
        self.ground_z = 0.0
        self.create_subscription(CameraInfo, info_topic, self._info_cb, 10)
        self.create_subscription(Odometry, '/odometry/slam', self._odom_cb, 10)
        self.create_subscription(Path, '/planned_path', self._path_cb, 10)
        self.create_subscription(String, '/cone_map/local', self._cones_cb, 10)
        self.create_subscription(Image, image_topic, self._image_cb, 10)
        self.pub = self.create_publisher(Image, '/path_overlay_image', 10)
        self.get_logger().info(f'overlaying /planned_path onto {image_topic}')

    def _info_cb(self, msg):
        self.fx, self.fy = msg.k[0], msg.k[4]
        self.cx, self.cy = msg.k[2], msg.k[5]

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        q = msg.pose.pose.orientation
        self.pose_t = np.array([p.x, p.y, p.z])
        self.pose_R = quat_to_R(q.x, q.y, q.z, q.w)

    def _path_cb(self, msg):
        self.path = [(ps.pose.position.x, ps.pose.position.y) for ps in msg.poses]

    def _cones_cb(self, msg):
        zs = []
        for line in msg.data.strip().split('\n'):
            parts = line.strip().split(',')
            if len(parts) >= 3:
                try:
                    zs.append(float(parts[2]))
                except ValueError:
                    pass
        if zs:
            self.ground_z = float(np.median(zs))

    def _project(self, wx, wy, wz=0.0):
        """Map-frame point -> pixel, or None if behind the camera."""
        Xw = np.array([wx, wy, wz])
        xr, yr, zr = self.pose_R.T @ (Xw - self.pose_t)
        xc, yc, zc = -yr, -zr, xr
        if zc < 0.3:
            return None
        return (int(self.cx + self.fx * xc / zc),
                int(self.cy + self.fy * yc / zc))

    def _image_cb(self, msg):
        if self.fx is None:
            return
        img = self.bridge.imgmsg_to_cv2(msg, 'bgr8')
        pts = [self._project(x, y, self.ground_z) for x, y in self.path]
        pts = [p for p in pts if p is not None]
        for a, b in zip(pts, pts[1:]):
            cv2.line(img, a, b, (0, 255, 0), 3)
        for p in pts:
            cv2.circle(img, p, 6, (0, 200, 255), -1)
        if len(pts) < 2 and self.path:
            cv2.putText(img, 'path outside view', (10, 25),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        elif not self.path:
            cv2.putText(img, 'no /planned_path yet (need blue+yellow cones in view)',
                        (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)

        # manual construction: cv_bridge's cv2_to_imgmsg is broken on this stack
        out = Image()
        out.header = msg.header
        out.height, out.width = img.shape[:2]
        out.encoding = 'bgr8'
        out.step = out.width * 3
        out.data = np.ascontiguousarray(img).tobytes()
        self.pub.publish(out)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--image', default='/yolo_annotated_image')
    ap.add_argument('--camera-info', default='/zed/zed_node/left/camera_info')
    args = ap.parse_args()

    rclpy.init()
    node = PathOverlay(args.image, args.camera_info)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
