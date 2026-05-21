# Cardiff Autonomous Racing - Perception Stack

YOLOv8 cone detection running on EUFS Formula Student simulation.

# ----- Linux ----- #
## Follow this to run the perception stack with eufs sim

```bash
# 1. Allow GUI
xhost +local:docker

# 2. Start containers
docker compose up -d base perception eufs_sim

# 3. Launch full perception stack (all nodes in one command)
docker exec -it racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 launch slam_example perception_full.launch.py"

# Optional: enable Pangolin SLAM viewer (requires DISPLAY)
# ros2 launch slam_example perception_full.launch.py viewer:=true

# Optional: run without SLAM (cone detection only, car-frame output)
# ros2 launch slam_example perception_full.launch.py use_slam:=false odom_topic:=/odom

#   (EUFS publishes IMU data on `/imu/data`; if you need to double-check, run
#    `docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 topic hz /imu/data --window 5'` before launching SLAM.)

# 6. RVIZ opens automatically showing the track
# Add these displays in RVIZ:
#   - Add → By topic → /ground_truth/cones → ConeArrayWithCovariance (simulator ground truth)
#   - Add → By topic → /yolo_annotated_image → Image (camera feed with bounding boxes)
```

# ----- WSL (Windows) ----- #
## Prerequisites for WSL Users

Before running the perception stack on WSL, ensure you have:

1. **WSL2 installed** (Windows 10 or 11)
   ```powershell
   # In PowerShell (Admin)
   wsl --install
   wsl --set-default-version 2
   ```

2. **Docker Desktop for Windows** with WSL2 backend enabled
   - Install Docker Desktop
   - Settings → General → "Use the WSL 2 based engine" (enabled)
   - Settings → Resources → WSL Integration → Enable for your distro (Ubuntu)

3. **Clone this repo inside WSL** (not Windows filesystem)
   ```bash
   # Inside WSL
   cd ~
   git clone <repo-url> cardiff-autonomous-racing
   cd cardiff-autonomous-racing
   ```

4. **Initialize submodules (required)**
   ```bash
   git submodule update --init --recursive
   ```

5. **Fix Docker permissions (if you see "permission denied")**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

6. **(Optional) WSLg for GUI** — Windows 11 only
   - WSLg comes with Windows 11 by default (GUI apps work out of the box)
   - Check: `echo $DISPLAY` should show `:0` or similar
   - If not set, update WSL: `wsl --update`

---

## Run with GUI (Windows 11 + WSLg)

For Windows 11 users. Pangolin viewer and RViz will open in Windows.

```bash
# 0. Build images (first time only, or after Dockerfile changes)
docker build -f docker/Dockerfile.base -t car-base:latest .
docker build -f docker/Dockerfile.control -t car-control:latest .
docker build -f docker/Dockerfile.eufs_sim -t car-eufs:latest .
docker build -f docker/Dockerfile.perception -t car-perception:latest . --progress=plain

# 1. Start containers
docker compose up -d base perception eufs_sim

# 2. Launch full perception stack
docker exec -it racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 launch slam_example perception_full.launch.py viewer:=true"

# 3. Verify it's working (in another terminal)
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /odometry/slam"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /cone_map/car_frame --once"
```

---

## Run Headless (Windows 10 or no GUI)

For Windows 10 or when you don't need visualisation. All processing runs; topics publish normally.

```bash
# 0. Build images (first time only, or after Dockerfile changes)
docker build -f docker/Dockerfile.base -t car-base:latest .
docker build -f docker/Dockerfile.control -t car-control:latest .
docker build -f docker/Dockerfile.eufs_sim -t car-eufs:latest .
docker build -f docker/Dockerfile.perception -t car-perception:latest . --progress=plain

# 1. Start containers
docker compose up -d base perception eufs_sim

# 2. Launch full perception stack (headless)
docker exec -it racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 launch slam_example perception_full.launch.py viewer:=false"

# 3. Verify it's working (in another terminal)
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /odometry/slam"
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /cone_cloud/local --once"
```

**What works headless:**
- Full perception pipeline (YOLO, cone mapper, SLAM)
- All ROS2 topics publish normally
- Recording/playback with `ros2 bag`
- Topic inspection, logging, and tests

**What doesn't work:**
- Pangolin viewer window
- RViz visualization
- Interactive GUI tools (`rqt_image_view`, etc.)

---

## What's Running

- **racing_base** - Base ROS2 Humble container (car-base image)
- **racing_eufs_sim** - EUFS Formula Student track with cones in Gazebo (car-eufs 5.6GB)
- **racing_perception** - YOLOv8 detector container (car-perception 11.6GB)
- **RVIZ** - Opens automatically showing track, car, and ground truth cones
- **ORB-SLAM3** - Pangolin + ORB library built from source, wrapped by `slam_example`


## Key Topics

### Perception inputs (from EUFS sim / real car)
- `/zed/left/image_rect_color` — left camera feed (640×480)
- `/zed/right/image_rect_color` — right camera feed (stereo, for SLAM)
- `/zed/depth/image_raw` — depth image for 3-D cone positioning
- `/zed/left/camera_info` — camera intrinsics (consumed automatically)
- `/imu/data` — IMU at ~70 Hz (for stereo-inertial SLAM)
- `/ground_truth/cones` — EUFS ground truth (visualisation only)

### Primary perception outputs
- `/cone_map/car_frame` — **PointCloud2 in `base_link`** — cone positions relative to the car; primary input for path planner and future landmark SLAM observations
- `/cone_map/local` — same data as String CSV `x,y,z,color,confidence` in `base_link`
- `/cone_map/orange` — PointCloud2 in `base_link` — start/finish line cones only
- `/car_pose` — `geometry_msgs/PoseStamped` in `odom` frame — republished from SLAM for path planner
- `/odometry/slam` — `nav_msgs/Odometry` — raw SLAM odometry

### Secondary / visualisation
- `/cone_map/global` — String CSV in `odom` frame — accumulated global map
- `/cone_map/markers` — MarkerArray for RViz
- `/track/centerline` — `nav_msgs/Path` for RViz
- `/yolo_annotated_image` — camera feed with bounding boxes
- `/mapping/diagnostics` — DiagnosticArray health monitor

## Troubleshooting

**RVIZ doesn't show cones:**
- Add `/ground_truth/cones` display: Add → By topic → ConeArrayWithCovariance
- Requires `eufs_rviz_plugins` (built into car-eufs image)

**YOLO not detecting:**
- Check if running: `docker exec racing_perception ps aux | grep YOLO`
- Manually start with step 3 command above
- Verify model: `docker exec racing_perception ls /workspace/perception_ws/models/best.pt`

**Camera not publishing:**
- Check: `docker exec racing_eufs_sim bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /zed/left/image_rect_color"`
- Should be ~30Hz

**Display issues:**
- Run `xhost +local:docker` before starting containers
- Check `echo $DISPLAY` shows `:0` or `:1`

## Check It's Working

```bash
# See YOLO detections (should show cone positions)
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /cone_map/car_frame --once"

# Check YOLO is running
docker exec racing_perception ps aux | grep YOLO_cone_detector

# Verify topics
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic list | grep -E '(yolo|zed|cone|slam)'"
```

## Rebuilding After Code Changes

```bash
# Rebuild perception (if you modified YOLO detector)
docker build -f docker/Dockerfile.perception -t car-perception:latest .

# Rebuild EUFS sim (if you modified simulation)
docker build -f docker/Dockerfile.eufs_sim -t car-eufs:latest .

# Restart containers
docker compose down
docker compose up -d base perception eufs_sim
```

## Stopping Everything

```bash
# Stop all containers
docker compose down

# Stop and remove images (clean slate)
docker compose down --rmi all

```
### Launching the full perception stack (preferred)

```bash
# Starts SLAM + YOLO detector + cone mapper in one command
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 launch slam_example perception_full.launch.py"
```

- Subscribes to `/zed/left/right/image_rect_color`
- Loads `slam_example/config/ORBvoc.txt` and `camera_and_slam_settings.yaml`
- Publishes `nav_msgs/Odometry` on `/odometry/slam`
- Pangolin viewer can be toggled via the `viewer` parameter

### Stereo-inertial variant

```bash
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 launch slam_example slam_stereo_inertial.launch.py"
```

- Adds `/zed/imu/data` to the subscriptions
- Defaults to `/imu/data` (EUFS publishes here); override with `imu_topic:=/zed/imu/data` if you have a ZED IMU stream
- Update topic names inside the launch file if your sensor differs

### Topic checks

```bash
# Confirm SLAM odometry is streaming
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic hz /odometry/slam"

# Inspect pose values once
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic echo /odometry/slam --once"
```

If the Pangolin window fails to open, rerun `xhost +local:docker` before starting the stack.

### Visualising cones & SLAM

Quick commands to inspect cone publishing and SLAM (run inside the perception container):

```bash
# start an interactive shell in the perception container
docker exec -it racing_perception bash -c "source /entrypoint.sh && bash"

# Echo the latest detected cones once
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic echo /cone_map/car_frame --once"

# See publish rates for key topics
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic hz /cone_map/car_frame /cone_cloud/local /odometry/slam"

# View the YOLO annotated camera feed
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 run rqt_image_view rqt_image_view /yolo_annotated_image"

# Visualise node/topic graph
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 run rqt_graph rqt_graph"

# Launch RViz (then add displays listed below)
docker exec -it racing_perception bash -c "source /entrypoint.sh && rviz2"
```

**Build time note:** `car-perception` can take 20-60+ minutes. To verify it is still working, use `docker stats` or check Docker Desktop's Build view.