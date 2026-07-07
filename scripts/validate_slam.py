#!/usr/bin/env python3
"""
Landmark SLAM validation script.

Subscribes to /odometry/slam and /ground_truth/odom inside EUFS sim and
prints live position error + heading error statistics.

Usage (inside the perception container or any container on racing_network):
    source /opt/ros/humble/setup.bash
    source /workspace/perception_ws/install/setup.bash
    python3 /workspace/scripts/validate_slam.py

Output columns:
    t(s)  x_est  y_est  th_est(deg)  x_gt  y_gt  th_gt(deg)
    err_pos(m)  err_heading(deg)  n_samples  rmse_pos(m)

Press Ctrl-C to stop and see final statistics.
"""

import math
import sys
import time
from typing import List, Optional, Tuple

import rclpy
from rclpy.node import Node
from rclpy.executors import ExternalShutdownException
from nav_msgs.msg import Odometry


def _yaw_from_quat(quat) -> float:
    """Extract yaw from geometry_msgs.Quaternion."""
    x, y, z, w = quat.x, quat.y, quat.z, quat.w
    siny = 2.0 * (w * z + x * y)
    cosy = 1.0 - 2.0 * (y * y + z * z)
    return math.atan2(siny, cosy)


def _wrap_angle(a: float) -> float:
    return (a + math.pi) % (2.0 * math.pi) - math.pi


class SLAMValidator(Node):
    def __init__(self):
        super().__init__('slam_validator')

        self._slam_pose: Optional[Tuple[float, float, float]] = None
        self._gt_pose:   Optional[Tuple[float, float, float]] = None
        self._slam_stamp: Optional[float] = None
        self._gt_stamp:   Optional[float] = None

        self._errors_pos: List[float] = []
        self._errors_hdg: List[float] = []
        self._t0: Optional[float] = None

        self.create_subscription(Odometry, '/odometry/slam',
                                 self._slam_cb, 50)
        self.create_subscription(Odometry, '/ground_truth/odom',
                                 self._gt_cb, 50)

        self.create_timer(0.5, self._report)

        self.get_logger().info('SLAM validator started.')
        self.get_logger().info('Waiting for /odometry/slam and /ground_truth/odom ...')
        print('\n{:>8}  {:>7} {:>7} {:>8}  {:>7} {:>7} {:>8}  {:>8} {:>12}  {:>8}'.format(
            't(s)', 'x_est', 'y_est', 'th_est°', 'x_gt', 'y_gt', 'th_gt°',
            'err_pos(m)', 'err_hdg(°)', 'rmse(m)',
        ))
        print('-' * 100)

    def _slam_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        self._slam_pose = (p.x, p.y, _yaw_from_quat(msg.pose.pose.orientation))
        self._slam_stamp = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec) * 1e-9

    def _gt_cb(self, msg: Odometry) -> None:
        p = msg.pose.pose.position
        self._gt_pose = (p.x, p.y, _yaw_from_quat(msg.pose.pose.orientation))
        self._gt_stamp = float(msg.header.stamp.sec) + float(msg.header.stamp.nanosec) * 1e-9

    def _report(self) -> None:
        if self._slam_pose is None or self._gt_pose is None:
            return

        # Only report if stamps are close (within 1 s)
        if (self._slam_stamp is not None and self._gt_stamp is not None and
                abs(self._slam_stamp - self._gt_stamp) > 1.0):
            return

        if self._t0 is None:
            self._t0 = self._slam_stamp or 0.0

        t = (self._slam_stamp or 0.0) - self._t0

        sx, sy, sth = self._slam_pose
        gx, gy, gth = self._gt_pose

        err_pos = math.sqrt((sx - gx) ** 2 + (sy - gy) ** 2)
        err_hdg = abs(_wrap_angle(sth - gth))

        self._errors_pos.append(err_pos)
        self._errors_hdg.append(err_hdg)

        n = len(self._errors_pos)
        rmse = math.sqrt(sum(e ** 2 for e in self._errors_pos) / n)

        print(
            f'{t:8.1f}  '
            f'{sx:7.3f} {sy:7.3f} {math.degrees(sth):8.2f}  '
            f'{gx:7.3f} {gy:7.3f} {math.degrees(gth):8.2f}  '
            f'{err_pos:8.3f} {math.degrees(err_hdg):12.2f}  '
            f'{rmse:8.3f}'
        )

    def print_summary(self) -> None:
        if not self._errors_pos:
            print('\nNo data collected.')
            return

        n = len(self._errors_pos)
        rmse = math.sqrt(sum(e ** 2 for e in self._errors_pos) / n)
        mean_err = sum(self._errors_pos) / n
        max_err  = max(self._errors_pos)
        mean_hdg = math.degrees(sum(self._errors_hdg) / n)
        max_hdg  = math.degrees(max(self._errors_hdg))

        print('\n' + '=' * 60)
        print('SLAM VALIDATION SUMMARY')
        print('=' * 60)
        print(f'  Samples:              {n}')
        print(f'  Position RMSE:        {rmse:.4f} m')
        print(f'  Position mean error:  {mean_err:.4f} m')
        print(f'  Position max error:   {max_err:.4f} m')
        print(f'  Heading mean error:   {mean_hdg:.2f}°')
        print(f'  Heading max error:    {max_hdg:.2f}°')
        print('=' * 60)


def main():
    rclpy.init()
    node = SLAMValidator()
    try:
        rclpy.spin(node)
    except (KeyboardInterrupt, ExternalShutdownException):
        pass
    finally:
        node.print_summary()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
