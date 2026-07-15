# Perception Outputs (Simple Guide)

What is published, who publishes it, and how to read it. Written for other
teams (path planning, control) consuming perception's topics.

---

## 1) The 3 Topics You Need

| Topic | Type | Published by | Used by |
|---|---|---|---|
| `/odometry/slam` | `nav_msgs/Odometry` | `landmark_slam` | `cone_mapper`, planning, control |
| `/cone_map/local` | `std_msgs/String` | `cone_mapper` | path planning (current) |
| `/cone_map/global` | `std_msgs/String` | `cone_mapper` | debugging / future global planning |

---

## 2) What SLAM Actually Gives You

### Inputs SLAM needs to produce a pose

| Input topic | Type | Source | Required? |
|---|---|---|---|
| `imu_topic` param, default `/imu/data` | `sensor_msgs/Imu` | sim IMU plugin; `/ros_can/imu` on the real car | yes — heading |
| `/ros_can/twist` | `TwistWithCovarianceStamped` | real car (`ros_can`) | one velocity source |
| `/gps_controller/vel` | `Vector3Stamped` | EUFS sim GPS plugin | one velocity source |
| `/cone_cloud/local` | `PointCloud2` | `cone_detector` (YOLO) | yes — position correction |

`landmark_slam` prefers `/ros_can/twist` when it's being received and falls
back to `/gps_controller/vel` otherwise, so the same node works in sim and on
the car unmodified. Without a velocity source the pose cannot translate — the
node logs a warning if neither topic is publishing.

### Reading `/odometry/slam`

- `msg.pose.pose.position.x`, `.y`
- `msg.pose.pose.orientation` (quaternion; yaw is heading)
- `msg.pose.covariance` (uncertainty)

Pose is in the **map frame** — the origin is wherever `landmark_slam` started,
not a GPS-anchored point.

---

## 3) Cone Data Format (what planner uses now)

`/cone_map/local` is CSV text in one string, one cone per line:

```
x,y,z,color,confidence
```

Color IDs:

- `0` = blue (left boundary)
- `1` = yellow (right boundary)
- `2` = orange (start/finish marker; ignore for boundary)
- `3` = unknown

Example line: `5.73,2.69,0.54,0,0.85`

Cones below 0.3 confidence are held back from this topic — everything
published here has been seen enough times to be trusted.

---

## 4) Fastest Way to Reach the Topics

### Quick smoke test

```bash
./scripts/start_sim_and_log_slam.sh 20
```

Starts the stack, restarts the three perception nodes, prints topic health,
samples SLAM error for 20s. Use after a code change to check nothing is
obviously broken.

### Full accuracy check (autonomous lap vs ground truth)

```bash
./scripts/run_lap_validation.sh 1 2.5   # laps, speed m/s
```

Drives a full lap with a test-only pure-pursuit driver, then validates SLAM
pose and the cone map against simulator ground truth. Takes longer but is
the real regression test — run this before trusting a change.

### Manual commands

```bash
# Start stack
docker compose up -d base perception eufs_sim

# Start perception nodes
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_detector YOLO_cone_detector'
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_mapper cone_mapper'
docker exec -d racing_perception bash -lc 'source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run landmark_slam landmark_slam'

# Read one message from each topic
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

Expected rates: `/odometry/slam` 50–90 Hz, `/cone_map/local` 10–20 Hz
(depends on detections).

---

## 6) Real-Car Launch (ZED2)

Sim topic names are the defaults. On the real car, override at launch:

```bash
ros2 run cone_detector YOLO_cone_detector --ros-args \
  -p rgb_topic:=/zed/zed_node/rgb/image_rect_color \
  -p depth_topic:=/zed/zed_node/depth/depth_registered \
  -p camera_info_topic:=/zed/zed_node/left/camera_info

ros2 run landmark_slam landmark_slam --ros-args \
  -p imu_topic:=/ros_can/imu \
  -p camera_x_offset:=<measured> -p camera_y_offset:=<measured>
```

Confirm the exact ZED2 wrapper topic names with `ros2 topic list` once it's
running — they depend on the wrapper's `camera_name` launch param.
`/ros_can/twist` needs no override — same topic name real and sim.

## 7) For Path Planning Team (Minimal)

Subscribe to just these two:

1. `/odometry/slam` for car pose
2. `/cone_map/local` for cones — blue (`color==0`) is left, yellow
   (`color==1`) is right, ignore orange/unknown for boundaries

That's enough for centerline generation, local goal selection, and RRT*.
