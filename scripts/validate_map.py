#!/usr/bin/env python3
"""
Validate the built cone map against the simulator's ground-truth track.

Checks two things:

1. /cone_map/global vs the track CSV: coverage (how many real cones were
   mapped), position error of matched cones, ghosts (mapped cones matching
   no real cone) and duplicates (two mapped cones claiming the same real
   cone).  A small 2-D ICP removes any SLAM-frame offset first, so the
   numbers reflect map quality rather than global frame drift.

2. /cone_map/local parses with EXACTLY the logic Path_Planning uses
   (integration.py): 5 comma-separated floats per line, colour 0 -> left,
   colour 1 -> right.

Run inside the sim container after a lap:
    python3 validate_map.py [--track .../small_track.csv] [--match-radius 1.5]

Only standard messages are used (std_msgs/String).
"""
import argparse
import csv
import math

import numpy as np
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

BLUE, YELLOW = 0, 1


def load_gt_cones(track_csv):
    """Ground-truth blue/yellow cones in the ground-truth-odom frame."""
    cones, start = [], None
    with open(track_csv) as f:
        for row in csv.DictReader(f):
            x, y = float(row['x']), float(row['y'])
            if row['tag'] == 'blue':
                cones.append((x, y, BLUE))
            elif row['tag'] == 'yellow':
                cones.append((x, y, YELLOW))
            elif row['tag'] == 'car_start':
                start = (x, y, float(row['direction']))
    sx, sy, syaw = start
    c, s = math.cos(-syaw), math.sin(-syaw)
    return [(c * (x - sx) - s * (y - sy), s * (x - sx) + c * (y - sy), col)
            for x, y, col in cones]


def icp_align_2d(src, dst, iterations=10):
    """Rigid SE(2) transform aligning point set *src* to *dst* (both Nx2)."""
    src = np.asarray(src, dtype=float)
    dst = np.asarray(dst, dtype=float)
    R_total = np.eye(2)
    t_total = np.zeros(2)
    cur = src.copy()
    for _ in range(iterations):
        # nearest-neighbour correspondence
        d2 = ((cur[:, None, :] - dst[None, :, :]) ** 2).sum(axis=2)
        nn = d2.argmin(axis=1)
        matched = d2[np.arange(len(cur)), nn] < 3.0 ** 2
        if matched.sum() < 3:
            break
        a, b = cur[matched], dst[nn[matched]]
        ca, cb = a.mean(axis=0), b.mean(axis=0)
        H = (a - ca).T @ (b - cb)
        U, _, Vt = np.linalg.svd(H)
        R = Vt.T @ U.T
        if np.linalg.det(R) < 0:
            Vt[1] *= -1
            R = Vt.T @ U.T
        t = cb - R @ ca
        cur = cur @ R.T + t
        R_total = R @ R_total
        t_total = R @ t_total + t
    return R_total, t_total


def parse_map_string(data, expected_fields):
    """Parse a cone_mapper CSV String message; returns (cones, bad_lines)."""
    cones, bad = [], 0
    for line in data.strip().split('\n'):
        parts = line.strip().split(',')
        if len(parts) != expected_fields:
            bad += 1
            continue
        try:
            vals = [float(p) for p in parts]
        except ValueError:
            bad += 1
            continue
        cones.append(vals)
    return cones, bad


class MapValidator(Node):
    def __init__(self):
        super().__init__('map_validator')
        self.global_msg = None
        self.local_msg = None
        self.create_subscription(String, '/cone_map/global', self._global_cb, 1)
        self.create_subscription(String, '/cone_map/local', self._local_cb, 1)

    def _global_cb(self, msg):
        self.global_msg = msg.data

    def _local_cb(self, msg):
        self.local_msg = msg.data


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--track', default='/workspace/eufs_sim_humble/eufs_tracks/csv/small_track.csv')
    ap.add_argument('--match-radius', type=float, default=1.5)
    ap.add_argument('--wait', type=float, default=15.0, help='seconds to wait for messages')
    args = ap.parse_args()

    gt = load_gt_cones(args.track)

    rclpy.init()
    node = MapValidator()
    import time
    deadline = time.time() + args.wait
    while time.time() < deadline and (node.global_msg is None or node.local_msg is None):
        rclpy.spin_once(node, timeout_sec=0.5)
    node.destroy_node()
    rclpy.try_shutdown()

    print('\n' + '=' * 62)
    print('CONE MAP VALIDATION')
    print('=' * 62)

    # ── 1. Global map vs ground truth ────────────────────────────────────
    if node.global_msg is None:
        print('FAIL: no /cone_map/global message received')
        return
    mapped, bad = parse_map_string(node.global_msg, expected_fields=4)  # x,y,z,color
    mapped_bw = [(x, y, int(col)) for x, y, z, col in mapped if int(col) in (BLUE, YELLOW)]
    print(f'/cone_map/global: {len(mapped)} cones '
          f'({len(mapped_bw)} blue/yellow), {bad} malformed lines')

    if len(mapped_bw) >= 3:
        R, t = icp_align_2d([(x, y) for x, y, _ in mapped_bw],
                            [(x, y) for x, y, _ in gt])
        aligned = [(*(R @ np.array([x, y]) + t), col) for x, y, col in mapped_bw]

        matches = {}   # gt index -> list of (mapped idx, err)
        ghosts = 0
        errs = []
        for mi, (x, y, col) in enumerate(aligned):
            best_gi, best_d = None, args.match_radius
            for gi, (gx, gy, gcol) in enumerate(gt):
                if gcol != col:
                    continue
                d = math.hypot(gx - x, gy - y)
                if d < best_d:
                    best_gi, best_d = gi, d
            if best_gi is None:
                ghosts += 1
            else:
                matches.setdefault(best_gi, []).append((mi, best_d))
                errs.append(best_d)

        duplicates = sum(len(v) - 1 for v in matches.values())
        coverage = 100.0 * len(matches) / len(gt)
        print(f'  ground-truth cones:   {len(gt)}')
        print(f'  coverage:             {len(matches)}/{len(gt)}  ({coverage:.0f}%)')
        if errs:
            print(f'  match error mean/max: {np.mean(errs):.3f} / {max(errs):.3f} m '
                  f'(after SE2 alignment)')
        print(f'  ghosts (no gt match): {ghosts}')
        print(f'  duplicates:           {duplicates}')
    else:
        print('  too few blue/yellow cones to evaluate')

    # ── 2. Planner-format check (mirrors Path_Planning/integration.py) ──
    print()
    if node.local_msg is None:
        print('FAIL: no /cone_map/local message received')
        return
    left, right, bad_local = [], [], 0
    for line in node.local_msg.strip().split('\n'):
        parts = line.strip().split(',')
        if len(parts) == 5:  # x,y,z,color,confidence — integration.py contract
            try:
                x, y, z, colour, confidence = map(float, parts)
            except ValueError:
                bad_local += 1
                continue
            if int(colour) == 0:
                left.append((x, y))
            elif int(colour) == 1:
                right.append((x, y))
        else:
            bad_local += 1
    status = 'OK' if (left or right) and bad_local == 0 else 'CHECK'
    print(f'/cone_map/local planner-format check: {status}')
    print(f'  parsed as integration.py would: {len(left)} left (blue), '
          f'{len(right)} right (yellow), {bad_local} unparseable lines')
    print('=' * 62)


if __name__ == '__main__':
    main()
