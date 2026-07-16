# Cardiff Autonomous Racing — Perception Stack

YOLOv8 cone detection + EKF landmark SLAM, running on the EUFS Formula
Student simulator (and, unmodified, on the real car).

For the topic/message contract other teams consume, see
[`../PERCEPTION_FORMAT.md`](../PERCEPTION_FORMAT.md).

## Repository layout

```
perception_ws/src/
  cone_detector/    YOLOv8 + depth -> /cone_cloud/local (3D cone detections)
  landmark_slam/    EKF-SLAM -> /odometry/slam (car pose)
                    ekf.py is pure Python/NumPy, no ROS — fully unit tested
  cone_mapper/      builds /cone_map/local + /cone_map/global from the above

scripts/            dev tools + validation (see "Validating changes" below)
```

Pipeline: `cone_detector` → `landmark_slam` (also reads IMU + velocity) →
`cone_mapper` → path planning.

---

## Run with EUFS sim (Linux)

```bash
# 0. Allow X11 forwarding for RViz
xhost +local:docker

# 1. Build images (first time or after Dockerfile changes)
docker build -f docker/Dockerfile.base       -t car-base       .
docker build -f docker/Dockerfile.perception -t car-perception .
docker build -f docker/Dockerfile.eufs_sim   -t car-eufs       .

# 2. Start containers
docker compose up -d base perception eufs_sim

# 3. Start the three perception nodes (use_sim_time in sim only — omit on the real car)
docker exec -d racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_detector YOLO_cone_detector --ros-args -p use_sim_time:=true"
docker exec -d racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_mapper cone_mapper --ros-args -p use_sim_time:=true"
docker exec -d racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run landmark_slam landmark_slam --ros-args -p use_sim_time:=true"

# 4. Verify topics are flowing
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /odometry/slam"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /cone_cloud/local"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /cone_map/local"
```

**RViz displays to add:**
- `/ground_truth/cones` → ConeArrayWithCovariance (simulator ground truth)
- `/yolo_annotated_image` → Image (camera with bounding boxes)
- `/cone_map/markers` → MarkerArray (built cone map)

---

## Validating changes

Three levels, cheapest first:

**1. Unit tests** (no ROS, no simulator — run these constantly while developing)

```bash
cd perception_ws/src/landmark_slam && pip install pytest numpy && pytest test/ -v   # 71 tests
cd perception_ws/src/cone_mapper   && pytest test/ -v                              # 10 tests
```

**2. Quick smoke test** (stack + node health, ~30s)

```bash
./scripts/start_sim_and_log_slam.sh 20
```

**3. Full-lap regression test** (autonomous lap vs simulator ground truth, ~10 min)

```bash
./scripts/run_lap_validation.sh 1 2.5   # laps, speed m/s
```

Drives a full lap with a test-only pure-pursuit driver (ground truth
centerline — no path planning / control involved), then checks SLAM pose
and the built cone map against ground truth. Run this before trusting any
change to `landmark_slam` or `cone_mapper`.

Dev tools:
- `scripts/dev_reload.sh` — rebuild and restart one package without
  restarting the whole stack (`./scripts/dev_reload.sh run cone_mapper cone_mapper`)
- `scripts/record_planner_view.py` — logs exactly what a path-planning
  subscriber would see on `/odometry/slam` + `/cone_map/local`, useful when
  debugging the interface rather than the algorithms
- `scripts/validate_slam.py` / `scripts/validate_map.py` — the two checks
  `run_lap_validation.sh` runs; callable standalone if you only need one

---

## Landmark SLAM parameters

All tunable via `--ros-args -p <name>:=<value>`:

| Parameter | Default | Description |
|---|---|---|
| `obs_noise_xy` | `0.5` | Std-dev (m) of YOLO cone detection noise |
| `process_noise_xy` | `0.1` | Position prediction noise (m/√s) |
| `process_noise_yaw` | `0.05` | Heading prediction noise (rad/√s) |
| `camera_x_offset` | `0.0` | Camera forward offset from car ref (m) — set once measured |
| `camera_y_offset` | `0.0` | Camera lateral offset (m) |
| `max_cone_range` | `15.0` | Ignore detections beyond this depth (m) |
| `min_cone_range` | `0.5` | Ignore detections closer than this (m) |
| `max_obs_age` | `0.4` | Discard cone detections older than this vs the latest IMU sample (s) |

Real-car example (after measuring camera mount):
```bash
ros2 run landmark_slam landmark_slam \
   --ros-args -p camera_x_offset:=0.35 -p obs_noise_xy:=0.4
```

---

## Troubleshooting

- No `/odometry/slam`: check `landmark_slam` is running and `/imu/data` exists.
- `/odometry/slam` exists but position stays near zero while driving: no
  velocity source — check `/gps_controller/vel` (sim) or `/ros_can/twist`
  (real car) is publishing. The node warns about this at startup.
- No cones: check `/zed/left/image_rect_color`, `/zed/depth/image_raw`, and
  that `best.pt` exists.
- No map output: check `/cone_cloud/local` first, then `/cone_map/local`.

```bash
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 node list | grep -E 'landmark_slam|cone_mapper|yolo'"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /odometry/slam"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /cone_map/local --once"
```
