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

## What's Running

- **racing_base** - Base ROS2 Humble container (car-base image)
- **racing_eufs_sim** - EUFS Formula Student track with cones in Gazebo (car-eufs 5.6GB)
- **racing_perception** - YOLOv8 detector container (car-perception 11.6GB)
- **RVIZ** - Opens automatically showing track, car, and ground truth cones

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

#Check ORB_SLAM3 installed correctly
docker exec -it racing_perception bash -c "cd /workspace/ORB_SLAM3/Examples/Monocular && ./mono_euroc ../../Vocabulary/ORBvoc.txt EuRoC.yaml ../../evaluation/MH_01_easy EuRoC_TimeStamps/MH01.txt"
```
mono_euroc.cc example modified (line 83, true/false) to run offline test on MH_01_easy data with viewer enabled/disabled:
<ol>
<li> Download ASL format for MH_01_easy from [ETHZ](https://projects.asl.ethz.ch/datasets/doku.php?id=kmavvisualinertialdatasets) </li>
<li>Extract and put the MH_01_easy directory in the ORB_SLAM3_src/evaluation directory</li>
<li> in ORB_SLAM3_src/Examples/Monocular, run code above.</li>
</ol>

- With viewer disabled - no errors, no output whilst processing, until creates output files.
- With viewer enabled - some errors, should still process the images.


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

## Architecture

**Docker Images:**
- `car-base` - Base ROS2 Humble with common dependencies (~10GB)
- `car-perception` - YOLOv8 + PyTorch + cone detector node (11.6GB)
- `car-eufs` - EUFS sim + RViz plugins for visualization (5.6GB)

**Files explained:**
- `docker/Dockerfile.perception` - Builds YOLO perception stack
- `docker/Dockerfile.eufs_sim` - Builds EUFS simulation with RViz plugins
- `docker/entrypoint_eufs_sim.sh` - Launches sim with `launch_group:=default` for camera
- `perception_ws/src/cone_detector/cone_detector/YOLO_cone_detector.py` - Main detector node
- `best.pt` - Trained YOLOv8 model (copied to `/workspace/perception_ws/models/` in container)

**Data Flow:**
```
EUFS Sim → Camera/Depth → YOLO Detector → Detections + Annotated Images
                ↓                               ↓
         Ground Truth Cones            /detected_cones
                                      /yolo_annotated_image
```
