#!/usr/bin/env python3
"""
Record exactly what a path-planning node subscribed to /odometry/slam and
/cone_map/local would see over time — for demonstrating / debugging the
perception -> planning interface without running the planner itself.

Every --period seconds (sim time) it logs:
  - car pose (x, y, yaw) from /odometry/slam
  - the full /cone_map/local CSV payload, plus a left/right count parsed
    exactly as Path_Planning/integration.py parses it

Run inside the perception container:
    python3 record_planner_view.py --period 5 --out /workspace/logs/planner_view.jsonl
"""
import argparse
import json
import math
import time

import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from nav_msgs.msg import Odometry
from std_msgs.msg import String


def yaw_from_quat(q):
    return math.atan2(2.0 * (q.w * q.z + q.x * q.y),
                      1.0 - 2.0 * (q.y * q.y + q.z * q.z))


class PlannerViewRecorder(Node):
    def __init__(self, period, out_path):
        super().__init__('planner_view_recorder')
        self.set_parameters([Parameter('use_sim_time', Parameter.Type.BOOL, True)])
        self.pose = None
        self.local_map = ''
        self.out_path = out_path
        self.create_subscription(Odometry, '/odometry/slam', self._odom_cb, 10)
        self.create_subscription(String, '/cone_map/local', self._map_cb, 10)
        self.create_timer(period, self._snapshot)
        self._f = open(out_path, 'w')

    def _odom_cb(self, msg):
        p = msg.pose.pose.position
        self.pose = (p.x, p.y, yaw_from_quat(msg.pose.pose.orientation))

    def _map_cb(self, msg):
        self.local_map = msg.data

    def _snapshot(self):
        if self.pose is None:
            return
        left, right = [], []
        for line in self.local_map.strip().split('\n'):
            parts = line.strip().split(',')
            if len(parts) == 5:
                try:
                    x, y, z, colour, confidence = map(float, parts)
                except ValueError:
                    continue
                if int(colour) == 0:
                    left.append([round(x, 2), round(y, 2), round(confidence, 2)])
                elif int(colour) == 1:
                    right.append([round(x, 2), round(y, 2), round(confidence, 2)])

        record = {
            't_sim': self.get_clock().now().nanoseconds * 1e-9,
            't_wall': time.time(),
            'pose_xyth': [round(v, 3) for v in self.pose],
            'n_left': len(left),
            'n_right': len(right),
            'left_cones': left,
            'right_cones': right,
            'raw_local_map': self.local_map,
        }
        self._f.write(json.dumps(record) + '\n')
        self._f.flush()
        self.get_logger().info(
            f't={record["t_sim"]:.1f}  pose=({self.pose[0]:.2f},{self.pose[1]:.2f},'
            f'{math.degrees(self.pose[2]):.0f}deg)  left={len(left)} right={len(right)}')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', type=float, default=5.0)
    ap.add_argument('--out', default='/workspace/logs/planner_view.jsonl')
    args = ap.parse_args()

    rclpy.init()
    node = PlannerViewRecorder(args.period, args.out)
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node._f.close()
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
