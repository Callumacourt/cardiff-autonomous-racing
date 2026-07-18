#!/usr/bin/env python3
"""
Interim path follower: pure pursuit on the planner's /planned_path.

Closes the control end of the full autonomy loop WITHOUT touching the Control
module: perception (/odometry/slam, /cone_map/local) -> path_planning
(/planned_path) -> this node (/cmd). The same pure-pursuit logic belongs in
Control/ros_control mission_control's autocross/trackdrive branches once the
Control team picks it up.

Unlike scripts/lap_test_driver.py this node uses NO ground truth: pose comes
from SLAM and the path from the planner, so it exercises the real stack.

Run inside the SIM container (needs eufs_msgs + ackermann_msgs):
    python3 path_follower.py [--speed 2.0] [--laps 1] [--mission 13]

Notes
-----
- /cmd must be published at >=20 Hz WALL clock: the race-car plugin barely
  applies commands streamed at sim-time rates when the RTF is low.
- Lap detection: SLAM pose leaves the start disc (>15 m), then returns
  (<4 m). After the final lap the car brakes to a stop and the mission is
  flagged complete.
"""
import argparse
import math

import rclpy
from rclpy.clock import Clock
from rclpy.node import Node
from rclpy.parameter import Parameter
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.srv import SetCanState
from geometry_msgs.msg import TwistWithCovarianceStamped, Vector3Stamped
from nav_msgs.msg import Odometry, Path
from std_msgs.msg import Bool, String

WHEELBASE = 1.53          # ADS-DV [m]
MAX_STEER = 0.4           # [rad]
LOOKAHEAD = 3.0           # pure pursuit lookahead [m]
PATH_STALE_S = 8.0        # brake if the planner goes quiet this long [s, wall]
ODOM_STALE_S = 4.0        # brake if SLAM goes quiet this long [s, wall]
# NOTE: thresholds are wall-clock and sized for low sim RTF; on the real car
# tighten these (SLAM at 50+ Hz makes 0.5-1 s appropriate).
LAP_LEAVE_DIST = 15.0     # start-disc radii for lap detection [m]
LAP_RETURN_DIST = 4.0


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class PathFollower(Node):
    def __init__(self, target_speed, laps, mission, real_car=False):
        super().__init__('path_follower')
        # sim time only in the simulator; the car runs on wall clock
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, not real_car)])

        self.target_speed = target_speed
        self.target_laps = laps
        self.mission = mission
        self.real_car = real_car
        # staleness gates are wall-clock; sim values absorb low RTF, the car
        # publishes SLAM at 50+ Hz so it gets much tighter ones
        self.path_stale_s = 2.0 if real_car else PATH_STALE_S
        self.odom_stale_s = 0.5 if real_car else ODOM_STALE_S

        self.pose = None            # (x, y, yaw) map frame, from SLAM
        self.speed = 0.0
        self.path = []              # [(x, y)] map frame, car-forward order
        self.last_path_wall = None
        self.last_odom_wall = None
        self.state = ''
        self.mission_sent = False
        self.mission_sent_wall = -1e9
        self.driving = False
        self.done = False

        self.start_xy = None
        self.armed = False          # left the start disc
        self.laps_done = 0
        self.braking = False
        self.last_log = -1e9

        self.wall = Clock()

        self.cmd_pub = self.create_publisher(AckermannDriveStamped, '/cmd', 10)
        self.flag_pub = self.create_publisher(Bool, '/state_machine/driving_flag', 10)
        self.done_pub = self.create_publisher(Bool, '/ros_can/mission_completed', 10)
        self.create_subscription(Odometry, '/odometry/slam', self._odom_cb, 10)
        self.create_subscription(Path, '/planned_path', self._path_cb, 10)
        self.create_subscription(String, '/ros_can/state_str', self._state_cb, 10)
        # speed fallbacks: some landmark_slam builds publish a zero twist.
        # Sim: /gps_controller/vel (GPS plugin). Real car: /ros_can/twist
        # (wheel odometry). Both are sensors SLAM itself fuses, NOT ground truth.
        self.gps_speed = 0.0
        self.gps_speed_wall = -1e9
        self.can_speed = 0.0
        self.can_speed_wall = -1e9
        self.create_subscription(Vector3Stamped, '/gps_controller/vel', self._gps_vel_cb, 10)
        self.create_subscription(TwistWithCovarianceStamped, '/ros_can/twist', self._can_twist_cb, 10)
        self.cli = self.create_client(SetCanState, '/ros_can/set_mission')

        # WALL-clock timer — see module docstring
        self.create_timer(0.05, self._tick, clock=self.wall)

    # ------------------------------------------------------------------

    def _wall_now(self):
        return self.wall.now().nanoseconds * 1e-9

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, yaw_from_quat(msg.pose.pose.orientation))
        t = msg.twist.twist.linear
        slam_speed = math.hypot(t.x, t.y)
        if slam_speed > 0.01:
            self.speed = slam_speed
        elif self.gps_speed_wall >= self.can_speed_wall:
            self.speed = self.gps_speed
        else:
            self.speed = self.can_speed
        self.last_odom_wall = self._wall_now()

    def _gps_vel_cb(self, msg):
        self.gps_speed = math.hypot(msg.vector.x, msg.vector.y)
        self.gps_speed_wall = self._wall_now()

    def _can_twist_cb(self, msg):
        t = msg.twist.twist.linear
        self.can_speed = math.hypot(t.x, t.y)
        self.can_speed_wall = self._wall_now()

    def _path_cb(self, msg):
        self.path = [(ps.pose.position.x, ps.pose.position.y) for ps in msg.poses]
        self.last_path_wall = self._wall_now()

    def _state_cb(self, msg):
        self.state = msg.data

    def _lookahead_point(self):
        """First path point at least LOOKAHEAD away, walking car-forward order."""
        x, y, _ = self.pose
        for px, py in self.path:
            if math.hypot(px - x, py - y) >= LOOKAHEAD:
                return px, py
        return self.path[-1] if self.path else None

    def _publish_cmd(self, accel, steer):
        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.drive.acceleration = float(accel)
        msg.drive.steering_angle = float(max(-MAX_STEER, min(MAX_STEER, steer)))
        self.cmd_pub.publish(msg)

    # ------------------------------------------------------------------

    def _tick(self):
        now = self._wall_now()
        # "ready to drive" = SLAM pose and a fresh planner path are in hand.
        # ros_can only reports MISSION_RUNNING to the VCU (the AS_READY ->
        # AS_DRIVING transition) and only forwards /cmd while the driving
        # flag is true, so it must be asserted BEFORE AS_DRIVING exists —
        # waiting for AS:DRIVING to raise it deadlocks the real car.
        ready = (self.pose is not None
                 and self.last_odom_wall is not None
                 and now - self.last_odom_wall <= self.odom_stale_s
                 and self.last_path_wall is not None
                 and now - self.last_path_wall <= self.path_stale_s)
        self.flag_pub.publish(Bool(data=(ready or self.driving) and not self.done))
        self.done_pub.publish(Bool(data=self.done))

        # Mission handshake, only until driving is latched: multiple sim nodes
        # can publish conflicting /ros_can/state_str, so once we have seen
        # AS:DRIVING we stop reacting to the state churn entirely.
        # On the real car the mission comes from the AMI selector switch, so
        # we never call set_mission — we only wait for AS:DRIVING.
        if not self.driving:
            if 'AS:DRIVING' in self.state and self.pose is not None:
                self.driving = True
                self.start_xy = (self.pose[0], self.pose[1])
                self.get_logger().info(
                    f'AS_DRIVING — following /planned_path, {self.target_laps} '
                    f'lap(s) at {self.target_speed} m/s')
            elif not self.real_car and ('AMI:NOT_SELECTED' in self.state or not self.state):
                # request the mission until a state machine reflects it — a
                # single call can be lost when it races the sim reset
                now = self._wall_now()
                if self.cli.service_is_ready() and (
                        not self.mission_sent or now - self.mission_sent_wall > 10.0):
                    req = SetCanState.Request()
                    req.ami_state = self.mission
                    self.cli.call_async(req)
                    self.mission_sent = True
                    self.mission_sent_wall = now
                    self.get_logger().info(f'Mission {self.mission} requested')
            return

        if self.done:
            self._publish_cmd(0.0, 0.0)
            return

        now = self._wall_now()

        # Safety: stale SLAM or planner -> brake straight
        if (self.last_odom_wall is None or now - self.last_odom_wall > self.odom_stale_s
                or self.last_path_wall is None or now - self.last_path_wall > self.path_stale_s):
            self._publish_cmd(-2.0, 0.0)
            if now - self.last_log >= 5.0:
                self.last_log = now
                self.get_logger().warning('stale SLAM/path — braking')
            return

        x, y, yaw = self.pose

        # Lap detection on the SLAM start disc
        d_start = math.hypot(x - self.start_xy[0], y - self.start_xy[1])
        if not self.armed and d_start > LAP_LEAVE_DIST:
            self.armed = True
        if self.armed and d_start < LAP_RETURN_DIST:
            self.armed = False
            self.laps_done += 1
            self.get_logger().info(f'Lap {self.laps_done} complete')
            if self.laps_done >= self.target_laps:
                self.braking = True

        if self.braking:
            self._publish_cmd(-2.0, 0.0)
            if self.speed < 0.3:
                self.done = True
                self.get_logger().info('FULL AUTONOMOUS LAP COMPLETE — stopped')
            return

        target = self._lookahead_point()
        if target is None:
            self._publish_cmd(-1.0, 0.0)
            return

        # Pure pursuit steering
        alpha = math.atan2(target[1] - y, target[0] - x) - yaw
        alpha = math.atan2(math.sin(alpha), math.cos(alpha))
        if abs(alpha) > 2.0:
            # target is essentially behind us — a mispaired midpoint, not a
            # waypoint; slow down and wait for a sane path instead of chasing it
            self._publish_cmd(-1.0, 0.0)
            return
        steer = math.atan2(2.0 * WHEELBASE * math.sin(alpha), LOOKAHEAD)

        # Speed P-controller via acceleration command
        accel = max(-3.0, min(2.0, 1.5 * (self.target_speed - self.speed)))
        self._publish_cmd(accel, steer)

        if now - self.last_log >= 5.0:
            self.last_log = now
            self.get_logger().info(
                f'lap {self.laps_done + 1}: v={self.speed:.1f} m/s '
                f'pos=({x:.1f}, {y:.1f}) d_start={d_start:.1f} m '
                f'path={len(self.path)} pts')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--speed', type=float, default=2.0)
    ap.add_argument('--laps', type=int, default=1)
    ap.add_argument('--mission', type=int, default=13,
                    help='AMI state to request (13 = AUTOCROSS); ignored with --real-car')
    ap.add_argument('--real-car', action='store_true',
                    help='real car: no set_mission (AMI selector decides), '
                         'wall clock, speed fallback from /ros_can/twist')
    args = ap.parse_args()

    rclpy.init()
    node = PathFollower(args.speed, args.laps, args.mission, real_car=args.real_car)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
        # linger briefly so the final mission_completed flags go out
        for _ in range(20):
            rclpy.spin_once(node, timeout_sec=0.05)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
