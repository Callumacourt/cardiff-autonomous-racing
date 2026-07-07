"""
Landmark SLAM ROS2 node — drop-in replacement for ORB-SLAM3.

Publishes  /odometry/slam  (nav_msgs/Odometry) by fusing:
  • /imu/data              IMU yaw rate → prediction step (required)
  • /cone_cloud/local      YOLO cone detections in camera frame → EKF update
  • /ros_can/twist         forward velocity from race-car CAN (optional;
                           if absent the node falls back to IMU-only dead-
                           reckoning which will drift in position but remain
                           corrected by landmark observations)

Topic /odometry/slam is published:
  • at every IMU sample   (high-rate dead-reckoning pose)
  • additionally at every cone-cloud callback  (after EKF update)

The interface is identical to the old ORB-SLAM3 stereo-inertial node so
cone_mapper, path_planner, and cmd_node require no changes.

ROS Parameters
--------------
obs_noise_xy        float  0.5   Std-dev (m) of cone observation noise.
process_noise_xy    float  0.1   Std-dev (m/√s) of position prediction noise.
process_noise_yaw   float  0.05  Std-dev (rad/√s) of heading prediction noise.
camera_x_offset     float  0.0   Camera forward offset from car ref (m).
camera_y_offset     float  0.0   Camera lateral offset from car ref (m).
max_cone_range      float  15.0  Discard detections beyond this depth (m).
min_cone_range      float  0.5   Discard detections closer than this (m).
frame_id            str   "map"  Frame of the published odometry.
child_frame_id      str   "base_link"

EUFS Sim Usage
--------------
    ros2 run landmark_slam landmark_slam

Real-car Usage (after measuring camera offset)
----------------------------------------------
    ros2 run landmark_slam landmark_slam \\
        --ros-args -p camera_x_offset:=0.35 -p obs_noise_xy:=0.4
"""

import math
from typing import Optional

import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistWithCovarianceStamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu
from sensor_msgs_py import point_cloud2

from .ekf import EKFSlam, wrap_angle, yaw_to_quaternion
from .camera_transform import CameraMount, camera_to_robot_2d

# Cone colour labels (match cone_mapper/constants.py ConeColor enum)
_BLUE = 0
_YELLOW = 1
_ORANGE = 2   # start/finish line markers — skip for localisation


class LandmarkSLAMNode(Node):
    """EKF-SLAM node: /imu/data + /cone_cloud/local → /odometry/slam."""

    def __init__(self) -> None:
        super().__init__('landmark_slam')

        # ── ROS Parameters ────────────────────────────────────────────────
        self.declare_parameter('obs_noise_xy',      0.5)
        self.declare_parameter('process_noise_xy',  0.1)
        self.declare_parameter('process_noise_yaw', 0.05)
        self.declare_parameter('camera_x_offset',   0.0)
        self.declare_parameter('camera_y_offset',   0.0)
        self.declare_parameter('max_cone_range',    15.0)
        self.declare_parameter('min_cone_range',    0.5)
        self.declare_parameter('frame_id',          'map')
        self.declare_parameter('child_frame_id',    'base_link')

        obs_noise  = self._p_float('obs_noise_xy')
        proc_xy    = self._p_float('process_noise_xy')
        proc_yaw   = self._p_float('process_noise_yaw')
        self._max_range    = self._p_float('max_cone_range')
        self._min_range    = self._p_float('min_cone_range')
        self._frame_id     = self._p_str('frame_id')
        self._child_frame  = self._p_str('child_frame_id')

        self._mount = CameraMount(
            x_offset=self._p_float('camera_x_offset'),
            y_offset=self._p_float('camera_y_offset'),
        )

        # ── EKF ───────────────────────────────────────────────────────────
        self._ekf = EKFSlam(
            initial_pose=np.zeros(3),
            process_noise_xy=proc_xy,
            process_noise_yaw=proc_yaw,
            obs_noise_xy=obs_noise,
        )

        # ── Node state ────────────────────────────────────────────────────
        self._last_imu_stamp: Optional[float] = None   # seconds
        self._forward_velocity: float = 0.0            # m/s from /ros_can/twist

        # ── Publisher ─────────────────────────────────────────────────────
        self._odom_pub = self.create_publisher(Odometry, '/odometry/slam', 10)

        # ── Subscribers ───────────────────────────────────────────────────
        # IMU — runs the prediction step at full IMU rate
        self.create_subscription(Imu, '/imu/data', self._imu_cb, 200)

        # Cone detections — runs the EKF update step
        self.create_subscription(
            __import__('sensor_msgs').msg.PointCloud2,
            '/cone_cloud/local',
            self._cone_cb,
            10,
        )

        # Forward velocity from CAN bus (available in sim from race_car node)
        self.create_subscription(
            TwistWithCovarianceStamped,
            '/ros_can/twist',
            self._twist_cb,
            50,
        )

        self.get_logger().info('landmark_slam node started')
        self.get_logger().info(
            f'  params: obs_noise={obs_noise:.2f}m  proc_xy={proc_xy:.3f}  '
            f'proc_yaw={proc_yaw:.4f}  range=[{self._min_range:.1f}, {self._max_range:.1f}]m'
        )
        self.get_logger().info(
            f'  camera mount offset: fwd={self._mount.x_offset:.3f}m  '
            f'lat={self._mount.y_offset:.3f}m'
        )

        # Publish an initial zero-pose so downstream nodes see the topic immediately
        self._publish_odom_now()

    # ── Private helpers ───────────────────────────────────────────────────

    def _p_float(self, name: str) -> float:
        return self.get_parameter(name).get_parameter_value().double_value

    def _p_str(self, name: str) -> str:
        return self.get_parameter(name).get_parameter_value().string_value

    @staticmethod
    def _stamp_to_sec(stamp) -> float:
        return float(stamp.sec) + float(stamp.nanosec) * 1e-9

    # ── IMU callback — prediction ─────────────────────────────────────────

    def _imu_cb(self, msg: Imu) -> None:
        now = self._stamp_to_sec(msg.header.stamp)

        if self._last_imu_stamp is None:
            self._last_imu_stamp = now
            return

        dt = now - self._last_imu_stamp
        self._last_imu_stamp = now

        if dt <= 0.0 or dt > 0.5:
            # Bad dt: skip but keep last stamp to resync
            return

        omega = float(msg.angular_velocity.z)   # yaw rate (rad/s)
        self._ekf.predict(self._forward_velocity, omega, dt)
        self._publish_odom(msg.header.stamp)

    # ── /ros_can/twist callback — forward velocity ────────────────────────

    def _twist_cb(self, msg: TwistWithCovarianceStamped) -> None:
        # linear.x is forward velocity in body frame (m/s) from EUFS race_car
        self._forward_velocity = float(msg.twist.twist.linear.x)

    # ── Cone callback — EKF update ────────────────────────────────────────

    def _cone_cb(self, msg) -> None:
        """Process a PointCloud2 cone detection message."""
        if self._last_imu_stamp is None:
            # No IMU data yet — cannot meaningfully update
            return

        available_fields = {f.name for f in msg.fields}
        label_field = 'label' if 'label' in available_fields else 'confidence'

        points = list(point_cloud2.read_points(
            msg,
            field_names=('x', 'y', 'z', label_field),
            skip_nans=True,
        ))

        n_update = 0
        n_new = 0

        for pt in points:
            try:
                x_cam, y_cam, z_cam, label_f = float(pt[0]), float(pt[1]), float(pt[2]), float(pt[3])
            except (ValueError, TypeError, IndexError):
                continue

            color = int(round(label_f))

            # Only use blue and yellow cones for localisation
            if color not in (_BLUE, _YELLOW):
                continue

            # Depth range filter (z_cam = forward depth)
            if not (self._min_range <= z_cam <= self._max_range):
                continue

            # Camera frame → robot body frame (2-D)
            obs_x, obs_y = camera_to_robot_2d(x_cam, y_cam, z_cam, self._mount)

            if not (math.isfinite(obs_x) and math.isfinite(obs_y)):
                continue

            obs = np.array([obs_x, obs_y])

            # Data association + update / add landmark
            idx, _ = self._ekf.associate(obs, color=color)
            if idx is not None:
                self._ekf.update(obs, idx)
                n_update += 1
            else:
                self._ekf.add_landmark(obs, color=color)
                n_new += 1

        if points:
            self._publish_odom(msg.header.stamp)

        if n_new > 0:
            self.get_logger().debug(
                f'EKF update: {n_update} associated, {n_new} new  '
                f'(total landmarks={self._ekf.n_landmarks})  '
                f'pose=({self._ekf.x:.2f}, {self._ekf.y:.2f}, '
                f'{math.degrees(self._ekf.theta):.1f}°)'
            )

    # ── Odometry publisher ────────────────────────────────────────────────

    def _publish_odom(self, stamp) -> None:
        msg = self._build_odom_msg(stamp)
        self._odom_pub.publish(msg)

    def _publish_odom_now(self) -> None:
        """Publish with current node clock time (used for initial pose)."""
        stamp = self.get_clock().now().to_msg()
        self._odom_pub.publish(self._build_odom_msg(stamp))

    def _build_odom_msg(self, stamp) -> Odometry:
        pose = self._ekf.pose
        P3 = self._ekf.pose_covariance_3x3()

        msg = Odometry()
        msg.header.stamp = stamp
        msg.header.frame_id = self._frame_id
        msg.child_frame_id = self._child_frame

        msg.pose.pose.position.x = pose[0]
        msg.pose.pose.position.y = pose[1]
        msg.pose.pose.position.z = 0.0

        qx, qy, qz, qw = yaw_to_quaternion(pose[2])
        msg.pose.pose.orientation.x = qx
        msg.pose.pose.orientation.y = qy
        msg.pose.pose.orientation.z = qz
        msg.pose.pose.orientation.w = qw

        # 6×6 pose covariance (x, y, z, rx, ry, rz) — row-major
        cov = [0.0] * 36
        cov[0]  = P3[0, 0]   # var(x)
        cov[1]  = P3[0, 1]   # cov(x,y)
        cov[5]  = P3[0, 2]   # cov(x,yaw)
        cov[6]  = P3[1, 0]
        cov[7]  = P3[1, 1]   # var(y)
        cov[11] = P3[1, 2]   # cov(y,yaw)
        cov[30] = P3[2, 0]
        cov[31] = P3[2, 1]
        cov[35] = P3[2, 2]   # var(yaw)
        msg.pose.covariance = cov

        msg.twist.twist.linear.x  = self._forward_velocity
        msg.twist.twist.angular.z = 0.0

        return msg


# ── Entry point ───────────────────────────────────────────────────────────

def main(args=None) -> None:
    rclpy.init(args=args)
    node = LandmarkSLAMNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
