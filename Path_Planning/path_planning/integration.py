#!/usr/bin/env python3
"""
Path Planning Integration Node

Consumes perception's outputs (see PERCEPTION_FORMAT.md):
    /odometry/slam   nav_msgs/Odometry   car pose in the map frame
    /cone_map/local  std_msgs/String     CSV "x,y,z,color,confidence" per line,
                                         positions in the map frame
Publishes:
    /planned_path    nav_msgs/Path       ordered centerline in the map frame,
                                         starting at the car and running forward

Color IDs: 0 = blue (left boundary), 1 = yellow (right boundary),
           2 = orange (ignored for boundaries), 3 = unknown (ignored).

The TUM optimizer is optional (needs trajectory_planning_helpers); when it is
not installed the node publishes the paired-midpoint centerline, which is
enough for pure-pursuit control to lap the track.
"""

import math

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from nav_msgs.msg import Odometry, Path

try:
    from path_planning.tum_wrapper import TUMTrajectoryOptimizer, TUM_AVAILABLE
except ImportError:
    try:
        from tum_wrapper import TUMTrajectoryOptimizer, TUM_AVAILABLE
    except ImportError:
        TUMTrajectoryOptimizer, TUM_AVAILABLE = None, False

# Max distance between consecutive same-colour cones when chaining a boundary.
# EUFS/FS cones on one side are ~5 m apart; anything further is another part
# of the track (e.g. the opposite side of a hairpin).
CHAIN_BREAK_DIST = 7.0
# Max blue-to-yellow distance for a valid midpoint pair (track width ~3-5 m).
MAX_PAIR_DIST = 7.0
# Half of assumed track width, used when only one boundary is visible.
HALF_TRACK_WIDTH = 1.75
# Ignore cones further than this from the car: the local buffer can retain
# stale far-away cones and distant clusters confuse the chaining.
MAX_CONE_RANGE = 25.0
# Cones slightly behind the car still matter for the first midpoint.
BEHIND_TOLERANCE = 3.0


def yaw_from_quaternion(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


def chain_from(points, start, heading=None, break_dist=CHAIN_BREAK_DIST):
    """Order points by nearest-neighbour walking, starting near `start`.

    If `heading` is given the first step is constrained to the forward
    half-plane so the chain runs the same way the car is pointing.
    """
    if not points:
        return []
    remaining = list(points)
    first = min(remaining, key=lambda p: (p[0] - start[0]) ** 2 + (p[1] - start[1]) ** 2)
    remaining.remove(first)
    chain = [first]
    while remaining:
        cx, cy = chain[-1]
        if heading is not None and len(chain) == 1:
            hx, hy = math.cos(heading), math.sin(heading)
            forward = [p for p in remaining if (p[0] - cx) * hx + (p[1] - cy) * hy > 0.0]
            candidates = forward if forward else remaining
        else:
            candidates = remaining
        nxt = min(candidates, key=lambda p: (p[0] - cx) ** 2 + (p[1] - cy) ** 2)
        if math.hypot(nxt[0] - cx, nxt[1] - cy) > break_dist:
            break
        remaining.remove(nxt)
        chain.append(nxt)
    return chain


class PathPlannerNode(Node):
    def __init__(self):
        super().__init__('path_planner')

        self.declare_parameter('use_tum', False)
        self.use_tum = self.get_parameter('use_tum').get_parameter_value().bool_value

        self.pose = None          # (x, y, yaw) in map frame
        self.left_cones = []      # blue
        self.right_cones = []     # yellow
        self.centerline = []
        self.optimized_trajectory = None

        self.tum_optimizer = None
        if self.use_tum and TUM_AVAILABLE:
            self.tum_optimizer = TUMTrajectoryOptimizer(vehicle_width=1.5,
                                                        vehicle_length=2.5)
        elif self.use_tum:
            self.get_logger().warning(
                'use_tum requested but trajectory_planning_helpers is not '
                'installed — publishing plain centerline')

        self.create_subscription(Odometry, '/odometry/slam', self.odom_callback, 10)
        self.create_subscription(String, '/cone_map/local', self.cones_callback, 10)
        self.path_pub = self.create_publisher(Path, '/planned_path', 10)

        self.timer = self.create_timer(0.2, self.main_loop)  # 5 Hz
        self.plan_count = 0
        self.get_logger().info('Path Planner Node initialized '
                               f'(TUM optimizer: {self.tum_optimizer is not None})')

    # ------------------------------------------------------------------
    # Inputs
    # ------------------------------------------------------------------

    def odom_callback(self, msg: Odometry):
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, yaw_from_quaternion(msg.pose.pose.orientation))

    def cones_callback(self, msg: String):
        """Parse /cone_map/local CSV: x,y,z,color,confidence per line."""
        left, right = [], []
        for line in msg.data.strip().split('\n'):
            parts = line.strip().split(',')
            if len(parts) < 4:
                continue
            try:
                x, y = float(parts[0]), float(parts[1])
                color = int(float(parts[3]))
            except ValueError:
                continue
            if color == 0:
                left.append((x, y))
            elif color == 1:
                right.append((x, y))
            # orange (2) / unknown (3): not track boundaries
        self.left_cones = left
        self.right_cones = right

    # ------------------------------------------------------------------
    # Planning
    # ------------------------------------------------------------------

    def generate_centerline(self):
        """Ordered centerline from the car forward, in the map frame."""
        if self.pose is None:
            return []
        x, y, yaw = self.pose
        hx, hy = math.cos(yaw), math.sin(yaw)

        def usable(cones):
            out = []
            for cx, cy in cones:
                dx, dy = cx - x, cy - y
                if math.hypot(dx, dy) > MAX_CONE_RANGE:
                    continue
                if dx * hx + dy * hy < -BEHIND_TOLERANCE:
                    continue
                out.append((cx, cy))
            return out

        left = usable(self.left_cones)
        right = usable(self.right_cones)

        if left and right:
            # Chain the better-populated side, pair each cone with the
            # nearest opposite cone: chain order => centerline order.
            primary, secondary = (left, right) if len(left) >= len(right) else (right, left)
            chain = chain_from(primary, (x, y), yaw)
            mids = []
            for px, py in chain:
                qx, qy = min(secondary,
                             key=lambda c: (c[0] - px) ** 2 + (c[1] - py) ** 2)
                if math.hypot(qx - px, qy - py) <= MAX_PAIR_DIST:
                    mids.append(((px + qx) / 2.0, (py + qy) / 2.0))
            if mids:
                return mids
            # fall through to single-side handling if pairing failed
        side = left or right
        if not side:
            return []
        # One boundary only: offset perpendicular to the chain, towards the
        # track centre (right of blue/left boundary, left of yellow).
        sign = -1.0 if side is left else 1.0
        chain = chain_from(side, (x, y), yaw)
        if len(chain) < 2:
            return []
        mids = []
        for i, (px, py) in enumerate(chain):
            j = min(i + 1, len(chain) - 1)
            k = max(i - 1, 0)
            tx, ty = chain[j][0] - chain[k][0], chain[j][1] - chain[k][1]
            norm = math.hypot(tx, ty)
            if norm < 1e-6:
                continue
            # left normal is (-ty, tx); sign flips it to the right for blue
            mids.append((px + sign * (-ty / norm) * HALF_TRACK_WIDTH,
                         py + sign * (tx / norm) * HALF_TRACK_WIDTH))
        return mids

    def optimize_trajectory_tum(self):
        """Optional racing-line refinement of the current centerline."""
        try:
            reftrack = self.tum_optimizer.cones_to_reftrack(
                self.left_cones, self.right_cones, min_points=5)
            if reftrack is None:
                return None
            return self.tum_optimizer.optimize_trajectory(reftrack, opt_type='mincurv')
        except Exception as e:  # noqa: BLE001 - optimizer failures must not kill planning
            self.get_logger().warning(f'TUM optimization failed: {e}')
            return None

    def main_loop(self):
        if self.pose is None:
            return
        self.centerline = self.generate_centerline()
        # a single midpoint is as likely to be a cross-track mispair as a real
        # target — never publish it, the follower treats a quiet planner safely
        if len(self.centerline) < 2:
            return

        path_points = self.centerline
        if (self.tum_optimizer is not None
                and len(self.left_cones) >= 5 and len(self.right_cones) >= 5):
            trajectory = self.optimize_trajectory_tum()
            if trajectory is not None and len(trajectory) > 1:
                path_points = [(float(p[0]), float(p[1])) for p in trajectory]

        msg = Path()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        for px, py in path_points:
            pose = PoseStamped()
            pose.header = msg.header
            pose.pose.position.x = float(px)
            pose.pose.position.y = float(py)
            pose.pose.orientation.w = 1.0
            msg.poses.append(pose)
        self.path_pub.publish(msg)

        self.plan_count += 1
        if self.plan_count % 25 == 1:  # every ~5 s
            self.get_logger().info(
                f'plan #{self.plan_count}: {len(self.left_cones)} blue / '
                f'{len(self.right_cones)} yellow cones -> '
                f'{len(path_points)} path points')


def main(args=None):
    rclpy.init(args=args)
    node = PathPlannerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
