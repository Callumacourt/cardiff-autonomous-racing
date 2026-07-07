# Perception Outputs (Simple Guide)

This file shows exactly **what is published**, **who publishes it**, and **how to read it**.

---

## 1) The 3 Topics You Need

| Topic | Type | Published by | Used by |
|---|---|---|---|
| `/odometry/slam` | `nav_msgs/Odometry` | `landmark_slam` | `cone_mapper`, planning, control |
| `/cone_map/local` | `std_msgs/String` | `cone_mapper` | path planning (current) |
| `/cone_map/global` | `std_msgs/String` | `cone_mapper` | debugging / future global planning |

Yes, a **global cone map is being created** and published on `/cone_map/global`.

---

## 2) What SLAM Actually Gives You

### What SLAM needs as input

| Input topic | Type | Where it comes from | Required? |
|---|---|---|---|
| `/imu/data` | `sensor_msgs/Imu` | sim or real IMU | yes — yaw rate for prediction |
| `/ros_can/twist` | `TwistWithCovarianceStamped` | **real car only** (ros_can node) | one velocity source required |
| `/gps_controller/vel` | `Vector3Stamped` | **EUFS sim** GPS plugin | one velocity source required |
| `/cone_cloud/local` | `PointCloud2` | `cone_detector` (YOLO) | yes — position corrections |

`landmark_slam` automatically prefers `/ros_can/twist` when it is being
received and falls back to `/gps_controller/vel` otherwise, so the same node
works in sim and on the car with no remapping.  If neither velocity source is
alive the node logs a warning and position will NOT track — this was the cause
of the original "high SLAM error vs ground truth" issue.

From `/odometry/slam`:

- `msg.pose.pose.position.x`
- `msg.pose.pose.position.y`
- `msg.pose.pose.orientation` (quaternion; yaw is heading)
- `msg.pose.covariance` (uncertainty)

In plain terms: **SLAM gives the car pose in map frame** (where the car is + where it is pointing).

---

## 3) Cone Data Format (what planner uses now)

`/cone_map/local` is CSV text in one string. Each line is:

`x,y,z,color,confidence`

Color IDs:

- `0` = blue (left boundary)
- `1` = yellow (right boundary)
- `2` = orange (marker; usually ignore for boundary)
- `3` = unknown

Example line:

`5.73,2.69,0.54,0,0.85`

---

## 4) Fastest Way to Reach the Topics

### One consistent command (recommended)

From repo root:

```bash
./scripts/start_sim_and_log_slam.sh 20
```

What it does:
- starts `base`, `perception`, `eufs_sim`
- restarts `cone_detector`, `cone_mapper`, `landmark_slam`
- runs quick topic health checks
- runs SLAM validator for 20s and writes a log to `logs/slam_validation_*.log`

---

### Start stack

```bash
docker compose up -d base perception eufs_sim
```

### Start perception nodes

```bash
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_detector YOLO_cone_detector'
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_mapper cone_mapper'
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run landmark_slam landmark_slam'
```

### Read one message from each topic

```bash
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic echo /odometry/slam --once'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic echo /cone_map/local --once'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic echo /cone_map/global --once'
```

---

## 5) Quick Health Check

```bash
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 node list | grep -E "landmark_slam|cone_mapper|yolo"'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /odometry/slam'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /cone_map/local'
```

Expected:

- `/odometry/slam`: roughly 50–90 Hz
- `/cone_map/local`: roughly 10–20 Hz (depends on detections)

---

## 6) For Path Planning Team (Minimal)

Use only these two subscriptions:

1. `/odometry/slam` for car pose
2. `/cone_map/local` for cones

Then:

- take blue (`color==0`) as left cones
- take yellow (`color==1`) as right cones
- ignore orange/unknown for boundaries

That is enough for centerline + local goal + RRT*.

---

## 7) Structured Topic Status

`/cone_map/structured` is **not part of the current production path**.

For now, use `/cone_map/local` as the single cone input for planning.
