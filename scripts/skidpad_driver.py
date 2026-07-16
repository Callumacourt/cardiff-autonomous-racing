#!/usr/bin/env python3
"""Skidpad mission driver for the real car (FS-AI ADS-DV).

Neither Path_Planning version handles a figure-8 and Control's cmd_node has
no AMI_SKIDPAD branch, so this node drives the whole skidpad mission itself:
it anchors the regulation figure-8 to the car's pose at the moment the car
enters AS_DRIVING, then tracks it with pure pursuit.

    perception (/odometry/slam)  ─┐
    ros_can    (/ros_can/state,   ├─>  skidpad_driver ──> /cmd
                /ros_can/twist)  ─┘                       /state_machine/driving_flag
                                                          /ros_can/mission_completed

Do NOT run Control's cmd_node at the same time — both publish /cmd and
cmd_node spams /ros_can/mission_completed False, which would mask our
mission-finished signal.

Only acts when ami_state == AMI_SKIDPAD and as_state == AS_DRIVING (see
require_mission param). Track geometry defaults follow the FS rules skidpad
(18.25 m centre-to-centre circles, 15.25/21.25 m inner/outer cone diameters):
the driven line is a circle of radius 9.125 m around each cone-circle centre.
CONFIRM entry_length and exit_length against the actual track layout on the
day — they are the two numbers most likely to differ.

Offline check (no ROS needed):  python3 skidpad_driver.py --selftest
"""
import argparse
import math
import sys

# ---------------------------------------------------------------------------
# Pure geometry/control — importable without ROS for offline testing
# ---------------------------------------------------------------------------

# Fixed protocol values from eufs_msgs/msg/CanState.msg
AS_DRIVING = 2
AMI_SKIDPAD = 12


def build_skidpad_path(entry_length=15.0, exit_length=25.0,
                       circle_radius=9.125, laps_per_circle=2,
                       step=0.25):
    """Waypoints (x, y) of the full skidpad run in the start frame.

    Start frame: origin at the car's anchor pose, +x along its heading.
    Sequence: entry straight -> right circle (clockwise, laps_per_circle
    laps) -> left circle (counter-clockwise, laps_per_circle laps) -> exit
    straight. The circle crossing point is at (entry_length, 0).
    """
    pts = []
    d, r = entry_length, circle_radius

    n = max(2, int(entry_length / step))
    for i in range(n):
        pts.append((d * i / n, 0.0))

    # Right circle: centre (d, -r); start at top (angle +pi/2), clockwise.
    dtheta = step / r
    n_arc = int(laps_per_circle * 2.0 * math.pi / dtheta)
    for i in range(n_arc):
        th = math.pi / 2.0 - i * dtheta
        pts.append((d + r * math.cos(th), -r + r * math.sin(th)))

    # Left circle: centre (d, +r); start at bottom (angle -pi/2), counter-clockwise.
    for i in range(n_arc):
        th = -math.pi / 2.0 + i * dtheta
        pts.append((d + r * math.cos(th), r + r * math.sin(th)))

    n = max(2, int(exit_length / step))
    for i in range(n + 1):
        pts.append((d + exit_length * i / n, 0.0))

    return pts


def transform_path(pts, x0, y0, yaw0):
    """Rotate/translate start-frame waypoints into the map frame."""
    c, s = math.cos(yaw0), math.sin(yaw0)
    return [(x0 + c * px - s * py, y0 + s * px + c * py) for px, py in pts]


class PurePursuitTracker:
    """Pure pursuit over an ordered waypoint list with monotonic progress.

    The skidpad path passes through the central crossing five times; a
    global nearest-point search would jump between visits. Progress is
    therefore only allowed to advance within a forward window, never to
    leap to a later (or earlier) crossing of the same spot.
    """

    def __init__(self, path, wheelbase=1.53, lookahead=2.5,
                 window_pts=60, max_steer=0.40):
        self.path = path
        self.wheelbase = wheelbase
        self.lookahead = lookahead
        self.window_pts = window_pts
        self.max_steer = max_steer   # rad; ros_can truncates at 24 deg = 0.419
        self.idx = 0

    def _advance(self, x, y):
        best_i, best_d = self.idx, float('inf')
        end = min(self.idx + self.window_pts, len(self.path))
        for i in range(self.idx, end):
            px, py = self.path[i]
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best_d:
                best_i, best_d = i, d
        self.idx = best_i
        return math.sqrt(best_d)

    def _target(self):
        acc = 0.0
        for i in range(self.idx, len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i + 1]
            acc += math.hypot(x2 - x1, y2 - y1)
            if acc >= self.lookahead:
                return self.path[i + 1]
        return self.path[-1]

    def remaining(self):
        acc = 0.0
        for i in range(self.idx, len(self.path) - 1):
            x1, y1 = self.path[i]
            x2, y2 = self.path[i + 1]
            acc += math.hypot(x2 - x1, y2 - y1)
        return acc

    def finished(self):
        return self.idx >= len(self.path) - 2

    def step(self, x, y, yaw):
        """Returns (steering_rad, cross_track_error_m)."""
        cte = self._advance(x, y)
        tx, ty = self._target()
        alpha = math.atan2(ty - y, tx - x) - yaw
        alpha = math.atan2(math.sin(alpha), math.cos(alpha))
        ld = max(math.hypot(tx - x, ty - y), 0.5)
        steer = math.atan2(2.0 * self.wheelbase * math.sin(alpha), ld)
        return max(-self.max_steer, min(self.max_steer, steer)), cte


def speed_target(base_speed, remaining, comfort_decel=1.5):
    """Taper the speed setpoint so the car arrives at the path end stopped."""
    return min(base_speed, math.sqrt(max(2.0 * comfort_decel * remaining, 0.0)))


# ---------------------------------------------------------------------------
# ROS node
# ---------------------------------------------------------------------------

def ros_main():
    import rclpy
    from rclpy.node import Node
    from ackermann_msgs.msg import AckermannDriveStamped
    from eufs_msgs.msg import CanState
    from geometry_msgs.msg import PoseStamped, TwistWithCovarianceStamped
    from nav_msgs.msg import Odometry, Path
    from std_msgs.msg import Bool

    class SkidpadDriver(Node):
        def __init__(self):
            super().__init__('skidpad_driver')
            p = self.declare_parameters('', [
                ('entry_length', 15.0), ('exit_length', 25.0),
                ('circle_radius', 9.125), ('laps_per_circle', 2),
                ('target_speed', 2.5), ('lookahead', 2.5),
                ('wheelbase', 1.53), ('max_accel', 1.0), ('max_decel', 6.0),
                ('speed_kp', 1.5),
                # False lets you bench-test without a mission selector.
                ('require_mission', True),
            ])
            g = lambda name: self.get_parameter(name).value
            self.cfg = {k: g(k) for k in (
                'entry_length', 'exit_length', 'circle_radius',
                'laps_per_circle', 'target_speed', 'lookahead', 'wheelbase',
                'max_accel', 'max_decel', 'speed_kp', 'require_mission')}

            self.as_state = 0
            self.ami_state = 0
            self.pose = None          # (x, y, yaw)
            self.pose_stamp = None
            self.speed = 0.0
            self.tracker = None       # set on arming
            self.mission_complete = False

            self.create_subscription(CanState, '/ros_can/state', self._on_state, 10)
            self.create_subscription(Odometry, '/odometry/slam', self._on_odom, 10)
            self.create_subscription(TwistWithCovarianceStamped, '/ros_can/twist',
                                     self._on_twist, 10)

            self.cmd_pub = self.create_publisher(AckermannDriveStamped, '/cmd', 1)
            self.flag_pub = self.create_publisher(Bool, '/state_machine/driving_flag', 1)
            self.done_pub = self.create_publisher(Bool, '/ros_can/mission_completed', 1)
            self.path_pub = self.create_publisher(Path, '/skidpad/path', 1)

            # 20 Hz: comfortably inside ros_can's 0.5 s cmd watchdog.
            self.create_timer(0.05, self._tick)
            self.get_logger().info('skidpad_driver ready — waiting for '
                                   'AMI_SKIDPAD + AS_DRIVING')

        def _on_state(self, msg):
            self.as_state = msg.as_state
            self.ami_state = msg.ami_state

        def _on_odom(self, msg):
            q = msg.pose.pose.orientation
            yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                             1.0 - 2.0 * (q.y * q.y + q.z * q.z))
            self.pose = (msg.pose.pose.position.x, msg.pose.pose.position.y, yaw)
            self.pose_stamp = self.get_clock().now()

        def _on_twist(self, msg):
            self.speed = msg.twist.twist.linear.x

        def _armed(self):
            if self.as_state != AS_DRIVING:
                return False
            if self.cfg['require_mission'] and self.ami_state != AMI_SKIDPAD:
                return False
            return True

        def _publish_cmd(self, accel, steer):
            msg = AckermannDriveStamped()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.drive.acceleration = float(accel)
            msg.drive.steering_angle = float(steer)
            self.cmd_pub.publish(msg)

        def _publish_flags(self):
            self.flag_pub.publish(Bool(data=self._armed()))
            self.done_pub.publish(Bool(data=self.mission_complete))

        def _tick(self):
            self._publish_flags()

            if not self._armed():
                self._publish_cmd(0.0, 0.0)
                return

            if self.pose is None:
                self.get_logger().warn('AS_DRIVING but no /odometry/slam yet — '
                                       'holding zero command', throttle_duration_sec=2.0)
                self._publish_cmd(0.0, 0.0)
                return

            # Odometry watchdog: SLAM died mid-run -> brake straight.
            age = (self.get_clock().now() - self.pose_stamp).nanoseconds / 1e9
            if age > 0.5:
                self.get_logger().error(f'/odometry/slam stale ({age:.2f}s) — braking')
                self._publish_cmd(-self.cfg['max_decel'], 0.0)
                return

            if self.tracker is None:
                x0, y0, yaw0 = self.pose
                pts = build_skidpad_path(
                    self.cfg['entry_length'], self.cfg['exit_length'],
                    self.cfg['circle_radius'], int(self.cfg['laps_per_circle']))
                self.tracker = PurePursuitTracker(
                    transform_path(pts, x0, y0, yaw0),
                    wheelbase=self.cfg['wheelbase'],
                    lookahead=self.cfg['lookahead'])
                self._publish_rviz_path()
                self.get_logger().info(
                    f'Anchored skidpad at ({x0:.2f}, {y0:.2f}, yaw {yaw0:.2f}) — '
                    f'{len(self.tracker.path)} waypoints')

            x, y, yaw = self.pose
            steer, cte = self.tracker.step(x, y, yaw)

            if self.tracker.finished():
                if abs(self.speed) < 0.05 and not self.mission_complete:
                    self.mission_complete = True
                    self.get_logger().info('Skidpad complete — mission_completed set')
                self._publish_cmd(0.0 if self.mission_complete else -self.cfg['max_decel'], 0.0)
                return

            v_ref = speed_target(self.cfg['target_speed'], self.tracker.remaining())
            accel = self.cfg['speed_kp'] * (v_ref - self.speed)
            accel = max(-self.cfg['max_decel'], min(self.cfg['max_accel'], accel))
            self._publish_cmd(accel, steer)

            if cte > 1.0:
                self.get_logger().warn(f'cross-track error {cte:.2f} m',
                                       throttle_duration_sec=1.0)

        def _publish_rviz_path(self):
            msg = Path()
            msg.header.frame_id = 'map'
            msg.header.stamp = self.get_clock().now().to_msg()
            for px, py in self.tracker.path:
                ps = PoseStamped()
                ps.header = msg.header
                ps.pose.position.x = px
                ps.pose.position.y = py
                ps.pose.orientation.w = 1.0
                msg.poses.append(ps)
            self.path_pub.publish(msg)

    rclpy.init()
    node = SkidpadDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


# ---------------------------------------------------------------------------
# Offline self-test: kinematic bicycle follows the path (no ROS required)
# ---------------------------------------------------------------------------

def selftest(plot=False):
    path = build_skidpad_path()
    tracker = PurePursuitTracker(path)
    x, y, yaw, v = 0.0, 0.0, 0.0, 0.0
    wheelbase, dt = 1.53, 0.02
    max_cte, trace = 0.0, []

    for step_i in range(60000):
        steer, cte = tracker.step(x, y, yaw)
        if tracker.finished():
            v_ref = 0.0
        else:
            v_ref = speed_target(2.5, tracker.remaining())
        accel = max(-6.0, min(1.0, 1.5 * (v_ref - v)))
        v = max(0.0, v + accel * dt)
        x += v * math.cos(yaw) * dt
        y += v * math.sin(yaw) * dt
        yaw += v / wheelbase * math.tan(steer) * dt
        # lane-keeping stat: exclude the terminal braking zone (last ~5 m),
        # where "cte" is really distance-to-endpoint, not lane deviation
        if not tracker.finished() and tracker.idx < len(path) - 20:
            max_cte = max(max_cte, cte)
        trace.append((x, y))
        if tracker.finished() and v < 0.01:
            break
    else:
        print('FAIL: did not finish within step budget')
        return 1

    total_len = sum(math.hypot(path[i + 1][0] - path[i][0],
                               path[i + 1][1] - path[i][1])
                    for i in range(len(path) - 1))
    overshoot = math.hypot(x - path[-1][0], y - path[-1][1])
    ok = max_cte < 0.5 and overshoot < 1.5 and tracker.finished()
    print(f'path length      : {total_len:.1f} m')
    print(f'finished at step : {step_i} ({step_i * dt:.1f} s simulated)')
    print(f'max cross-track  : {max_cte:.3f} m (limit 0.5)')
    print(f'stop overshoot   : {overshoot:.2f} m past path end (limit 1.5)')
    print(f'final position   : ({x:.2f}, {y:.2f}) — expect (~40+overshoot, ~0)')
    print('PASS' if ok else 'FAIL')

    if plot:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        plt.figure(figsize=(8, 8))
        plt.plot([p[0] for p in path], [p[1] for p in path], 'k--', lw=0.7,
                 label='reference')
        plt.plot([p[0] for p in trace], [p[1] for p in trace], 'r', lw=1.0,
                 label='driven')
        plt.axis('equal')
        plt.legend()
        plt.savefig('skidpad_selftest.png', dpi=120)
        print('wrote skidpad_selftest.png')
    return 0 if ok else 1


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--selftest', action='store_true',
                    help='run the offline kinematic check and exit')
    ap.add_argument('--plot', action='store_true',
                    help='with --selftest: save skidpad_selftest.png')
    args, _ = ap.parse_known_args()
    if args.selftest:
        sys.exit(selftest(plot=args.plot))
    ros_main()
