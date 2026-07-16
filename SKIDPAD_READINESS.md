# Skidpad Readiness — 2026-07-16

Findings from a full sweep of perception, Path_Planning (both versions),
Control, and ros_can, plus what was built to close the gaps.

## TL;DR

Perception is figure-8-safe. Path planning and Control are **not** — neither
planner can produce a skidpad path and Control's cmd_node has no
AMI_SKIDPAD branch. A new mission-specific node, `scripts/skidpad_driver.py`,
closes the gap: it drives the regulation figure-8 with pure pursuit off
`/odometry/slam` and talks directly to ros_can. Start everything with
`launch_skidpad_car.sh` (on the car SSD at `~/launch_skidpad_car.sh`).

## Why the existing planner/control chain cannot do skidpad

**Path_Planning, laptop version (RRT*, `Path_Planning/integration.py`)**
- Centerline = unordered nearest blue/yellow pairing. Near the skidpad
  crossing, cones from BOTH circles are in the 6 s local buffer, so blue
  cones of one circle pair with yellow cones of the other → garbage
  midpoints. Order follows map-insertion order, not track order, and
  `last_goal_idx` only ever increases — meaningless on a loop.
- RRT* samples only `x ∈ [0, 500], y ∈ [-20, 500]` (`rrt_star.py:83`).
  Anything behind the start pose or more than 20 m to the right is
  unreachable — half the skidpad, depending on start heading.
- Calls matplotlib `plot()` inside the 5 Hz loop.

**Path_Planning, car SSD version (TUM/GTO, path-planning-development)**
- Does not start: `TUMTrajectoryOptimizer`, `TUM_AVAILABLE`, `np`, and
  `valid_detections` are all referenced but never imported/defined.
- Subscribes to `/car_pose` and `/detected_cones` — topics nothing
  publishes (perception publishes `/odometry/slam` + `/cone_map/local`),
  via a TimeSynchronizer on `std_msgs/String`, which has no header.
- Centerline sorts cones by x-coordinate, assuming the track runs along +x.

**Control (`Control/ros_control/ros_control/cmd_node.py`)**
- Mission branches exist only for ACCELERATION, DDT_INSPECTION_A/B, and
  AUTONOMOUS_DEMO. `AMI_SKIDPAD` (12) falls through — no commands at all.
- Even in the acceleration branch, MPC output is unconditionally
  overwritten with `acceleration = 1.0, steering = 0.0` (lines 248–249)
  and there is no stop condition. The MPC has effectively never driven.
- `self.current_state` passed to the MPC is never updated (the odometry
  callback updates a different object).

## Is perception itself figure-8-safe? Yes, with caveats

- **EKF data association** (`landmark_slam/ekf.py`): color-gated
  nearest-neighbour Mahalanobis (χ², 9.21). Landmarks are points, so
  revisiting cones from the opposite heading is a non-issue. Skidpad's
  constant re-observation of the same ~50 cones is the best case for
  EKF-SLAM — drift stays bounded. Cross-color mismatches at the crossing
  are impossible by construction; same-color neighbours are ~3 m apart, so
  a mismatch needs >1.5 m pose error.
- **Orange is invisible to SLAM** (`landmark_slam_node.py:285` skips
  anything not blue/yellow). At the orange-heavy entry/exit lane the EKF
  runs on IMU + wheel-twist dead reckoning until circle cones are in the
  15 m detection range. Expect slightly degraded pose for the first metres —
  acceptable, but stage with the circles visible if possible.
- **Mapper orange handling**: local map publishes orange at conf ≥ 0.3;
  global promotion needs 6 detections at conf > 0.85. While staged and
  staring at the timing line this is satisfied within ~1 s. Note
  `duplicate_radius = 1.5 m` merges same-color cones closer than 1.5 m —
  closely spaced big timing-line oranges may merge into one map entry. The
  skidpad driver does not use orange cones, so this is cosmetic today.
- **Known unknowns still open**: YOLO never validated on real cones and
  outdoor lighting; GPU inference rate unbenchmarked; camera x/y offsets
  unmeasured (biases the map, mostly self-consistent for this mission);
  `/odometry/slam` twist.angular.z = 0 (irrelevant to the skidpad driver,
  which never reads it).

## What was built (all new files, nothing existing modified)

| File | Purpose |
|---|---|
| `scripts/skidpad_driver.py` (also on SSD repo) | Mission node: anchors regulation figure-8 (entry → right circle ×2 CW → left circle ×2 CCW → exit → stop) at the pose where AS_DRIVING begins; pure pursuit with monotonic path progress (no loop-jumping at the crossing); speed P-control with taper-to-stop; publishes `/cmd`, `/state_machine/driving_flag`, `/ros_can/mission_completed`, `/skidpad/path` (RViz); arms ONLY on ami=AMI_SKIDPAD + AS_DRIVING; brakes if `/odometry/slam` goes stale >0.5 s; 20 Hz (ros_can watchdog is 0.5 s) |
| `scripts/launch_skidpad_car.sh` (SSD: `~/launch_skidpad_car.sh`) | Per-event master script: ros_can → ZED2 → 3 perception nodes → skidpad driver. Intentionally does not start cmd_node or Path_Planning |
| ON_CAR_SETUP.md §10 (SSD) | Skidpad run procedure + parameters to confirm on the day |

**Validation done**: offline kinematic-bicycle self-test
(`python3 scripts/skidpad_driver.py --selftest --plot`): completes the
269 m path, max cross-track error **0.21 m** (lane margin 1.5 m) at
2.5–3.5 m/s, stop overshoot 0.9 m into the 25 m exit lane. **Not yet run in
EUFS sim or on the car.**

**Assumptions to confirm on the day** (parameters in launch_skidpad_car.sh):
<<<<<<< HEAD
- `entry_length` (staged position → circle crossing, default 15 m) — pace it out.
- `exit_length` (crossing → stop zone, default 25 m).
=======
- `entry_length` (SLAM reference point → circle crossing, default 15 m) — pace
  it out; rules stage the *foremost part* 15 m before the line (D4.3.3), so
  add the nose-to-reference distance.
- `exit_length` (crossing → intended stop point, default 20 m). Rules D4.3.6:
  full stop within 25 m or Unsafe Stop = DNF; selftest overshoots ~0.9 m, so
  keep ≤20 for margin.
>>>>>>> path-planning-development
- Car staged on the entry centreline pointing at the crossing — the path is
  anchored to the SLAM pose/heading at the go signal, so a 5° heading error
  displaces the far side of each circle by ~1.6 m. Stage carefully.
- Driving-line radius 9.125 m assumes FS rules geometry (18.25 m circle
  centre spacing).

## Smoke tests before scrutineering (in order)

1. `python3 scripts/skidpad_driver.py --selftest` on the car → PASS.
2. `bash ~/launch_skidpad_car.sh` with car jacked/trestled or E-stopped:
   - `ros2 topic hz /cone_cloud/local` ≥ ~5 Hz (first real GPU benchmark!)
   - `ros2 topic hz /odometry/slam` steady
   - `ros2 topic echo /ros_can/state --once` → ami_state 12 when selector on skidpad
   - `ros2 topic echo /cmd` → zeros while not AS_DRIVING (proves gating)
3. Point camera at real cones: check `/cone_map/local` colors are sane
   (blue=0/yellow=1 not swapped, no phantom cones) — first real-world model
   check.
4. Push the car a few metres by hand (or slow manual mode if allowed):
   `/odometry/slam` position should track distance moved within ~10 %.
5. RViz: confirm `/skidpad/path` figure-8 lands on top of `/cone_map/markers`
   once driving starts — if misaligned, entry_length/staging is wrong.
6. If a practice run is allowed: first run at target_speed 2.0–2.5, walk the
   fallback: EBS/RES stops the car; the driver also brakes itself if SLAM
   output stalls.

## Handoff notes for Control/Planning

- cmd_node needs an AMI_SKIDPAD branch eventually; today the skidpad driver
  bypasses it. Don't run both.
- cmd_node's MPC-override (lines 248–249) and never-updated
  `current_state` mean the acceleration mission would drive at constant
  1 m/s² with no stop — flag before anyone selects ACCELERATION.
- The SSD Path_Planning node needs its imports/topics fixed before it can
  even run; topic contract is `/odometry/slam` + `/cone_map/local`
  (see PERCEPTION_FORMAT.md).
