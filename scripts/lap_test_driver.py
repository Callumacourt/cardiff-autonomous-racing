#!/usr/bin/env python3
"""
Test-only lap driver: pure pursuit on the ground-truth track centerline.

Drives the EUFS sim car around the track WITHOUT path planning or control —
it cheats by using /ground_truth/odom and the track CSV, because its only job
is to exercise the perception stack for a full lap so SLAM and the cone map
can be validated against ground truth.

Run inside the SIM container (needs eufs_msgs + ackermann_msgs):
    python3 lap_test_driver.py [--laps 1] [--speed 2.5] \
        [--track /workspace/eufs_sim_humble/eufs_tracks/csv/small_track.csv]

Notes
-----
- /cmd must be published at >=20 Hz WALL clock: the race-car plugin barely
  applies commands streamed at sim-time rates when the RTF is low.
- Phase logic and speeds use SIM time throughout.
"""
import argparse
import csv
import math

import rclpy
from rclpy.clock import Clock
from rclpy.node import Node
from rclpy.parameter import Parameter
from ackermann_msgs.msg import AckermannDriveStamped
from eufs_msgs.srv import SetCanState
from nav_msgs.msg import Odometry
from std_msgs.msg import String

WHEELBASE = 1.53          # ADS-DV [m]
MAX_STEER = 0.4           # [rad]
LOOKAHEAD = 3.0           # pure pursuit lookahead [m]
CHAIN_BREAK_DIST = 8.0    # max gap when ordering centerline points [m]


def load_centerline(track_csv):
    """Ordered centerline in the ground-truth-odom frame (car spawn = origin).

    Midpoint of each blue cone and its nearest yellow cone, chained by
    nearest neighbour starting at the car spawn, oriented to match the
    car's starting heading.
    """
    blues, yellows, start = [], [], None
    with open(track_csv) as f:
        for row in csv.DictReader(f):
            x, y = float(row['x']), float(row['y'])
            if row['tag'] == 'blue':
                blues.append((x, y))
            elif row['tag'] == 'yellow':
                yellows.append((x, y))
            elif row['tag'] == 'car_start':
                start = (x, y, float(row['direction']))
    if not blues or not yellows or start is None:
        raise ValueError(f'{track_csv}: missing blue/yellow/car_start rows')

    mids = []
    for bx, by in blues:
        yx, yy = min(yellows, key=lambda c: (c[0] - bx) ** 2 + (c[1] - by) ** 2)
        mids.append(((bx + yx) / 2, (by + yy) / 2))

    sx, sy, syaw = start
    chain = []
    cur = min(mids, key=lambda m: (m[0] - sx) ** 2 + (m[1] - sy) ** 2)
    remaining = [m for m in mids if m is not cur]
    chain.append(cur)
    while remaining:
        nxt = min(remaining, key=lambda m: (m[0] - cur[0]) ** 2 + (m[1] - cur[1]) ** 2)
        if math.hypot(nxt[0] - cur[0], nxt[1] - cur[1]) > CHAIN_BREAK_DIST:
            break
        remaining.remove(nxt)
        chain.append(nxt)
        cur = nxt

    # Orient the loop to match the car's starting heading
    seg_yaw = math.atan2(chain[1][1] - chain[0][1], chain[1][0] - chain[0][0])
    if abs(math.atan2(math.sin(seg_yaw - syaw), math.cos(seg_yaw - syaw))) > math.pi / 2:
        chain = [chain[0]] + chain[1:][::-1]

    # Track frame -> ground-truth-odom frame (odom origin = car spawn pose)
    c, s = math.cos(-syaw), math.sin(-syaw)
    return [(c * (x - sx) - s * (y - sy), s * (x - sx) + c * (y - sy))
            for x, y in chain]


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class LapDriver(Node):
    def __init__(self, centerline, laps, target_speed):
        super().__init__('lap_test_driver')
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])

        self.centerline = centerline
        self.n = len(centerline)
        self.target_laps = laps
        self.target_speed = target_speed

        self.pose = None          # (x, y, yaw)
        self.speed = 0.0
        self.state = ''
        self.mission_sent = False
        self.driving = False
        self.done = False
        self.idx = None           # nearest centerline index (with hysteresis)
        self.laps_done = 0
        self.brake_until = None
        self.last_log = -1e9

        self.pub = self.create_publisher(AckermannDriveStamped, '/cmd', 10)
        self.create_subscription(Odometry, '/ground_truth/odom', self._odom_cb, 10)
        self.create_subscription(String, '/ros_can/state_str', self._state_cb, 10)
        self.cli = self.create_client(SetCanState, '/ros_can/set_mission')

        # WALL-clock timer — see module docstring
        self.create_timer(0.05, self._tick, clock=Clock())

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, yaw_from_quat(msg.pose.pose.orientation))
        t = msg.twist.twist.linear
        self.speed = math.hypot(t.x, t.y)

    def _state_cb(self, msg):
        self.state = msg.data

    def _now(self):
        return self.get_clock().now().nanoseconds * 1e-9

    def _nearest_idx(self):
        """Nearest centerline index; searches a window ahead of the last one."""
        x, y, _ = self.pose
        if self.idx is None:
            candidates = range(self.n)
        else:
            candidates = [(self.idx + k) % self.n for k in range(-2, 6)]
        return min(candidates,
                   key=lambda i: (self.centerline[i][0] - x) ** 2
                                 + (self.centerline[i][1] - y) ** 2)

    def _lookahead_point(self):
        x, y, _ = self.pose
        i = self.idx
        for _ in range(self.n):
            px, py = self.centerline[i]
            if math.hypot(px - x, py - y) >= LOOKAHEAD:
                return px, py
            i = (i + 1) % self.n
        return self.centerline[self.idx]

    def _tick(self):
        if not self.mission_sent:
            if self.cli.service_is_ready():
                req = SetCanState.Request()
                req.ami_state = 13  # AUTOCROSS
                self.cli.call_async(req)
                self.mission_sent = True
                self.get_logger().info('Mission AUTOCROSS requested')
            return

        if not self.driving:
            if 'AS:DRIVING' in self.state and self.pose is not None:
                self.driving = True
                self.get_logger().info(
                    f'AS_DRIVING — pure pursuit, {self.target_laps} lap(s) '
                    f'at {self.target_speed} m/s over {self.n} centerline points')
            return

        msg = AckermannDriveStamped()
        msg.header.stamp = self.get_clock().now().to_msg()

        # Braking phase after final lap
        if self.brake_until is not None:
            if self._now() >= self.brake_until and self.speed < 0.3:
                self.get_logger().info('LAP TEST COMPLETE')
                self.done = True
                return
            msg.drive.acceleration = -2.0
            self.pub.publish(msg)
            return

        prev_idx = self.idx
        self.idx = self._nearest_idx()

        # Lap counting: nearest index wrapped from end of loop to start
        if prev_idx is not None and prev_idx > self.n * 0.8 and self.idx < self.n * 0.2:
            self.laps_done += 1
            self.get_logger().info(f'Lap {self.laps_done} complete')
            if self.laps_done >= self.target_laps:
                self.brake_until = self._now() + 4.0
                return

        # Pure pursuit steering
        x, y, yaw = self.pose
        lx, ly = self._lookahead_point()
        alpha = math.atan2(ly - y, lx - x) - yaw
        delta = math.atan2(2.0 * WHEELBASE * math.sin(alpha), LOOKAHEAD)
        msg.drive.steering_angle = max(-MAX_STEER, min(MAX_STEER, delta))

        # Speed P-controller via acceleration command
        msg.drive.acceleration = max(-3.0, min(2.0, 1.5 * (self.target_speed - self.speed)))

        self.pub.publish(msg)

        now = self._now()
        if now - self.last_log >= 5.0:
            self.last_log = now
            self.get_logger().info(
                f'lap {self.laps_done + 1}: idx {self.idx}/{self.n}  '
                f'v={self.speed:.1f} m/s  pos=({x:.1f}, {y:.1f})')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', default='/workspace/eufs_sim_humble/eufs_tracks/csv/small_track.csv')
    ap.add_argument('--laps', type=int, default=1)
    ap.add_argument('--speed', type=float, default=2.5)
    args = ap.parse_args()

    centerline = load_centerline(args.track)

    rclpy.init()
    node = LapDriver(centerline, args.laps, args.speed)
    try:
        while rclpy.ok() and not node.done:
            rclpy.spin_once(node, timeout_sec=0.1)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
