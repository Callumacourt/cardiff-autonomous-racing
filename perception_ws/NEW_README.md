# Cardiff Autonomous Racing - Perception Stack

YOLOv8 cone detection running on EUFS Formula Student simulation.

## Quick Start - Do this in terminal to run YOLO with eufs sim

```bash
# 1. Allow GUI
xhost +local:docker

# 2. Start containers
docker compose up -d base perception eufs_sim

# 3. Start YOLO detector
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run cone_detector YOLO_cone_detector" &

# 4. RVIZ opens automatically showing the track
# Add these displays in RVIZ:
#   - Add → By topic → /ground_truth/cones → ConeArrayWithCovariance (simulator ground truth)
#   - Add → By topic → /yolo_annotated_image → Image (camera feed with bounding boxes)
```

## ORB Vocabulary (required for SLAM)

The ORB-SLAM3 nodes need the 145 MB `ORBvoc.txt` dictionary. Download it once into the repo and either rebuild the perception image or copy it into an already running container:

```bash
cd /home/callum/cardiff-autonomous-racing
./scripts/fetch_orb_vocabulary.sh

# Option A: rebuild the perception image so the new file is baked in
docker compose build perception

# Option B: copy it into the current container without rebuilding
docker cp perception_ws/src/slam_example/config/ORBvoc.txt \
       racing_perception:/workspace/perception_ws/src/slam_example/config/ORBvoc.txt
```

If you update the vocabulary later, rerun the script and rebuild/copy again so the container sees the new file.

## What's Running

- **racing_base** - Base ROS2 Humble container (car-base image)
- **racing_eufs_sim** - EUFS Formula Student track with cones in Gazebo (car-eufs 5.6GB)
- **racing_perception** - YOLOv8 detector container (car-perception 11.6GB)
- **RVIZ** - Opens automatically showing track, car, and ground truth cones
- **ORB-SLAM3** - Pangolin + ORB library built from source, wrapped by `slam_example`

## System Requirements

- Docker and Docker Compose
- X11 display server
- ~20GB disk space for images
- GPU recommended (falls back to CPU automatically)

## Key Topics

- `/ground_truth/cones` - Ground truth cone positions from EUFS simulator
- `/zed/left/image_rect_color` - Camera feed (640x480)
- `/zed/depth/image_raw` - Depth image for 3D positioning
- `/detected_cones` - YOLO detections with 3D coordinates (String format)
- `/yolo_annotated_image` - Camera image with bounding boxes drawn
- `/cone_cloud/local` - Throttled PointCloud2 of planner-friendly cones
- `/perception/cones` - EUFS `ConeArray` published by the detector
- `/odometry/slam` - Pose estimate from ORB-SLAM3 stereo node

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
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /detected_cones --once"

# Check YOLO is running
docker exec racing_perception ps aux | grep YOLO_cone_detector

# Verify topics
docker exec racing_perception bash -c "source /opt/ros/humble/setup.bash && ros2 topic list | grep -E '(yolo|zed|cones)'"
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

## ORB-SLAM3 (Stereo) Workflow

The perception image now installs Pangolin, clones `perception_ws/ORB_SLAM3` from upstream, and compiles the ROS 2 wrapper `slam_example`. Make sure you have run `./scripts/fetch_orb_vocabulary.sh` (see section above) so the launch files can load `config/ORBvoc.txt`.

1. Pangolin dependencies + ROS `message_filters` are installed via `apt`
2. Pangolin is built and installed to `/usr/local/lib/libpangolin.so`
3. `./build.sh` runs inside `perception_ws/ORB_SLAM3`
4. `slam_example` is built against the freshly compiled ORB library

### Launching the stereo pipeline

```bash
# Inside the perception container (after docker compose up)
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 launch slam_example slam_example.launch.py"
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
- Update topic names inside the launch file if your sensor differs

### Topic checks

```bash
# Confirm SLAM odometry is streaming
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic hz /odometry/slam"

# Inspect pose values once
docker exec racing_perception bash -c "source /entrypoint.sh && ros2 topic echo /odometry/slam --once"
```

If the Pangolin window fails to open, rerun `xhost +local:docker` before starting the stack.

If Pangolin stays on “waiting for images” and `ros2 node info /orb_slam3_stereo_inertial` only lists the IMU subscription, rebuild `slam_example` (`colcon build --packages-select slam_example`) to pick up the persistent camera subscription fix introduced in January 2025.

### Pose logging to CSV

```bash
# (Terminal 1) Run SLAM as shown above

# (Terminal 2) Record /odometry/slam into /workspace/logs/slam_poses.csv
docker exec -it racing_perception bash -c "source /entrypoint.sh && ros2 run slam_example slam_pose_logger \\
       --ros-args -p log_path:=/workspace/logs/slam_poses.csv \\
                                           -p odom_topic:=/odometry/slam \\
                                           -p flush_every:=10"

# Inspect the CSV header + first few rows
docker exec racing_perception bash -c "head -n5 /workspace/logs/slam_poses.csv"
```

The logger creates directories automatically, appends if `append:=true`, and flushes every `flush_every` messages (default 10). Combine it with `ros2 topic hz /odometry/slam` to make sure SLAM is publishing before relying on the CSV.

## Architecture

**Docker Images:**
- `car-base` - Base ROS2 Humble with common dependencies (~10GB)
- `car-perception` - YOLOv8 + Pangolin + ORB-SLAM3 + ROS 2 nodes (~12GB)
- `car-eufs` - EUFS sim + RViz plugins for visualization (5.6GB)

**Files explained:**
- `docker/Dockerfile.perception` - Builds YOLO perception stack, Pangolin, ORB-SLAM3, and `slam_example`
- `docker/Dockerfile.eufs_sim` - Builds EUFS simulation with RViz plugins
- `docker/entrypoint_perception.sh` - Sources Humble/workspace and exports ORB paths
- `docker/entrypoint_eufs_sim.sh` - Launches sim with `launch_group:=default`
- `perception_ws/src/cone_detector/cone_detector/YOLO_cone_detector.py` - Main detector node (YOLO + depth)
- `perception_ws/src/slam_example` - ROS 2 wrapper publishing `/odometry/slam`
- `perception_ws/ORB_SLAM3` - Upstream ORB-SLAM3 sources (built via `./build.sh`)
- `perception_ws/src/slam_example/config/ORBvoc.txt` - Vocabulary shipped inside the image
- `best.pt` - Trained YOLOv8 model (copied to `/workspace/perception_ws/models/`)

**Data Flow:**
```
EUFS Sim → Camera/Depth → YOLO Detector → Planner outputs & SLAM
                ↓                               ↓
         Ground Truth Cones            /detected_cones
                                      /yolo_annotated_image
                                      /perception/cones
                                      /cone_cloud/local
                                      /odometry/slam
```
