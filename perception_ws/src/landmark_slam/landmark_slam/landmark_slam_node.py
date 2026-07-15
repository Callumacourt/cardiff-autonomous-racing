"""
Landmark SLAM ROS2 node — drop-in replacement for ORB-SLAM3.

Publishes  /odometry/slam  (nav_msgs/Odometry) by fusing:
  • imu_topic (param)      IMU yaw rate → prediction step (required)
                           default /imu/data (sim); real car is /ros_can/imu
                           (published by the ros_can node, ADS-DV onboard IMU)
  • /cone_cloud/local      YOLO cone detections in camera frame → EKF update
  • /ros_can/twist         forward velocity from race-car CAN (real car;
                           published by the ros_can node, NOT present in sim)
  • /gps_controller/vel    GPS velocity vector (EUFS sim; used whenever
                           /ros_can/twist is not being received)

A forward-velocity source is REQUIRED for usable output: without one the
EKF prediction step cannot translate the pose and position error grows
with every metre driven.  The node warns if neither source is alive.

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
max_obs_age         float  0.4   Discard cone clouds older than this vs IMU (s).
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
from geometry_msgs.msg import TwistWithCovarianceStamped, Vector3Stamped
from nav_msgs.msg import Odometry
from sensor_msgs.msg import Imu, PointCloud2
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
        self.declare_parameter('max_obs_age',       0.4)
        self.declare_parameter('frame_id',          'map')
        self.declare_parameter('child_frame_id',    'base_link')

        obs_noise  = self._p_float('obs_noise_xy')
        proc_xy    = self._p_float('process_noise_xy')
        proc_yaw   = self._p_float('process_noise_yaw')
        self._max_range    = self._p_float('max_cone_range')
        self._min_range    = self._p_float('min_cone_range')
        self._max_obs_age  = self._p_float('max_obs_age')
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
        self._last_imu_stamp: Optional[float] = None    # seconds (msg stamp)
        self._last_stamp_msg = None                     # builtin Time of same
        self._last_imu_yaw: Optional[float] = None      # rad, from orientation
        self._forward_velocity: float = 0.0             # m/s, best source below
        self._last_can_stamp: Optional[float] = None    # /ros_can/twist msg stamp
        self._velocity_received: bool = False

        # ── Publisher ─────────────────────────────────────────────────────
        self._odom_pub = self.create_publisher(Odometry, '/odometry/slam', 10)

        # ── Subscribers ───────────────────────────────────────────────────
        # IMU — runs the prediction step at full IMU rate.  Topic is a ROS
        # param: sim's IMU plugin publishes /imu/data, the real car's IMU
        # (onboard the ADS-DV, via ros_can) publishes /ros_can/imu instead —
        # override at launch with -p imu_topic:=/ros_can/imu on the real car.
        self.declare_parameter('imu_topic', '/imu/data')
        imu_topic = self.get_parameter('imu_topic').value
        self.create_subscription(Imu, imu_topic, self._imu_cb, 200)

        # Cone detections — runs the EKF update step.  Depth 1: only the
        # newest cloud matters; a backlog of stale clouds would drag the
        # pose towards where the car used to be.
        self.create_subscription(
            PointCloud2, '/cone_cloud/local', self._cone_cb, 1)

        # Forward velocity, real car: published by ros_can from the VCU
        self.create_subscription(
            TwistWithCovarianceStamped, '/ros_can/twist', self._twist_cb, 50)

        # Forward velocity, EUFS sim: GPS velocity vector (world frame).
        # Only used while /ros_can/twist is silent.
        self.create_subscription(
            Vector3Stamped, '/gps_controller/vel', self._gps_vel_cb, 50)

        # Warn once if no velocity source comes up
        self._vel_check_timer = self.create_timer(5.0, self._velocity_check)

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

    @staticmethod
    def _yaw_from_imu(msg: Imu) -> Optional[float]:
        """Yaw from the IMU orientation quaternion, or None if unfilled."""
        q = msg.orientation
        if (q.x * q.x + q.y * q.y + q.z * q.z + q.w * q.w) < 1e-6:
            return None   # orientation not provided (all-zero quaternion)
        siny = 2.0 * (q.w * q.z + q.x * q.y)
        cosy = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        return math.atan2(siny, cosy)

    def _imu_cb(self, msg: Imu) -> None:
        now = self._stamp_to_sec(msg.header.stamp)
        yaw = self._yaw_from_imu(msg)

        if self._last_imu_stamp is None:
            self._last_imu_stamp = now
            self._last_stamp_msg = msg.header.stamp
            self._last_imu_yaw = yaw
            return

        dt = now - self._last_imu_stamp
        self._last_imu_stamp = now

        if dt <= 0.0 or dt > 0.5:
            # Bad dt: skip but keep last stamp to resync
            self._last_imu_yaw = yaw
            return

        # Heading rate: prefer the delta of the IMU's own orientation
        # estimate — unlike ω·dt it stays correct even when samples are
        # dropped or processed late.  Fall back to the raw yaw rate.
        if yaw is not None and self._last_imu_yaw is not None:
            omega = wrap_angle(yaw - self._last_imu_yaw) / dt
        else:
            omega = float(msg.angular_velocity.z)
        self._last_imu_yaw = yaw

        self._ekf.predict(self._forward_velocity, omega, dt)
        self._last_stamp_msg = msg.header.stamp
        self._publish_odom(msg.header.stamp)

    # ── Velocity callbacks ────────────────────────────────────────────────

    def _twist_cb(self, msg: TwistWithCovarianceStamped) -> None:
        # linear.x is forward velocity in body frame (m/s) from the VCU
        self._forward_velocity = float(msg.twist.twist.linear.x)
        self._last_can_stamp = self._stamp_to_sec(msg.header.stamp)
        self._velocity_received = True

    def _gps_vel_cb(self, msg: Vector3Stamped) -> None:
        # CAN twist has priority: ignore GPS if CAN arrived within the last 1 s
        if (self._last_can_stamp is not None and self._last_imu_stamp is not None
                and self._last_imu_stamp - self._last_can_stamp < 1.0):
            return
        # World-frame velocity vector → speed over ground.  The car only
        # drives forward, so the unsigned magnitude is the forward velocity.
        # Deadband: the magnitude of GPS noise never averages to zero, so
        # without it the pose creeps forward ~0.05 m/s while parked.
        speed = math.hypot(float(msg.vector.x), float(msg.vector.y))
        self._forward_velocity = speed if speed > 0.15 else 0.0
        self._velocity_received = True

    def _velocity_check(self) -> None:
        if self._velocity_received:
            self._vel_check_timer.cancel()
            return
        self.get_logger().warning(
            'No velocity source yet (/ros_can/twist or /gps_controller/vel) — '
            'position will NOT track until one is publishing')

    # ── Cone callback — EKF update ────────────────────────────────────────

    def _cone_cb(self, msg) -> None:
        """Process a PointCloud2 cone detection message."""
        if self._last_imu_stamp is None:
            # No IMU data yet — cannot meaningfully update
            return

        # Drop stale detections: the EKF pose is at IMU time, so applying
        # an observation taken much earlier corrupts the estimate.
        obs_age = self._last_imu_stamp - self._stamp_to_sec(msg.header.stamp)
        if obs_age > self._max_obs_age:
            self.get_logger().warning(
                f'Dropping cone cloud {obs_age:.2f}s older than latest IMU '
                f'(max_obs_age={self._max_obs_age:.2f}s)',
                throttle_duration_sec=5.0)
            return

        if 'label' not in {f.name for f in msg.fields}:
            self.get_logger().warning(
                "Cone cloud has no 'label' field — dropping message",
                throttle_duration_sec=5.0)
            return

        points = list(point_cloud2.read_points(
            msg,
            field_names=('x', 'y', 'z', 'label'),
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
            # Publish with the newest IMU stamp — the corrected pose is an
            # estimate at IMU time; using the older image stamp would make
            # /odometry/slam stamps jump backwards.
            self._publish_odom(self._last_stamp_msg)

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
