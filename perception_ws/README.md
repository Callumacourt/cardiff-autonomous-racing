ROS2 workspace that detects cones and tracks the car's position in real time:
-  **Cone Detection** - Find racing cones using computer vision
-  **Visual SLAM** - Track car position and build maps
-  **EUFS Integration** - Works with racing simulation
-  **Docker Ready** - One-command setup

## Quick Start

**Prerequisites**: Docker installed ([install guide](https://docs.docker.com/get-docker/))

```bash
# 1. Build perception system (might be a little long first time)
docker build -f ../docker/Dockerfile.perception -t car-perception:latest ..

# 2. Start development container
docker run -it --name perception-dev --privileged --net=host \
  --env="DISPLAY" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --volume="$(pwd):/workspace/perception_ws:rw" car-perception:latest

# 3. Build and test (inside container)
colcon build && source install/setup.bash
ros2 run cone_detector cone_detector_node
```

**You should see**: `Loaded YOLO model: yolov8n.pt` and `Cone detector node initialized`

## What's Inside

### Cone Detector (`src/cone_detector/`)
**Finds racing cones in camera images**

**What it does**: Uses YOLOv8 AI to detect orange/yellow/blue racing cones
**Input**: Camera images (`/camera/image_raw`)  
**Output**: Cone positions (`/cone_detections`) + debug images with boxes

**Try it**:
```bash
# See cone detection working
ros2 run cone_detector cone_detector_node
ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image
```

### SLAM System (`src/slam_system/`)  
**Tracks where the car is and builds maps**

**What it does**: Uses camera to figure out car position and create maps
**Status**:  Template ready - needs ORB-SLAM3 C++ integration
**Input**: Camera images + calibration data
**Output**: Car pose (`/slam/pose`) + trajectory (`/slam/path`)

**Try it**:
```bash
# See placeholder SLAM (publishes demo trajectory)
ros2 run slam_system slam_node
rviz2  # Add /slam/path topic to see trajectory
```
## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Container                         │
│  ┌─────────────────────────────────────────────────────────┴─┐
│  │ ROS2 Humble + YOLOv8 + ORB-SLAM3 + EUFS                 │
│  └─────────────────────────────────────────────────────────┬─┘
│                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ │
│  │  Cone Detector  │  │  SLAM System    │  │ Integration  │ │
│  │   (YOLOv8)      │  │  (ORB-SLAM3)    │  │   Module (TODO)    │ │
│  └─────────────────┘  └─────────────────┘  └──────────────┘ │
│           │                     │                    │      │
│           └─────────────────────┼────────────────────┘      │
│                                 │                           │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │              EUFS Simulation                            │ │
│  └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Docker Environment

The perception workspace runs in Docker environment:

**Base:** ROS2 Humble Desktop Full
**Includes:**
- Python 3.10+ with scientific stack
- OpenCV 4.8+ with Python bindings
- YOLOv8 (ultralytics) with PyTorch
- ORB-SLAM3 dependencies (Eigen, Pangolin, etc.)
- EUFS simulation dependencies
- Development tools (colcon, vcstool, etc.)

**Ports:** 11311 (ROS Master), 8080 (Web interfaces)

## Directory Structure

```
perception_ws/
├── README.md                           # This file
├── src/                                # ROS2 packages
│   ├── cone_detector/                  # YOLOv8 cone detection
│   │   ├── cone_detector/              # Python package
│   │   ├── launch/                     # Launch files
│   │   ├── README.md                   # Package documentation
│   │   └── package.xml                 # Package metadata
│   ├── slam_system/                    # ORB-SLAM3 integration
│   │   ├── slam_system/                # Python package
│   │   ├── launch/                     # Launch files
│   │   ├── README.md                   # Package documentation
│   │   └── package.xml                 # Package metadata
│   └── perception_integration/         # System coordination
├── scripts/                            # Utility scripts
│   ├── build_perception.sh             # Build Docker image
│   └── run_perception.sh               # Run container
├── build/                              # Build artifacts (auto-generated)
├── install/                            # Installed packages (auto-generated)
└── log/                                # Build logs (auto-generated)
```

## Testing with EUFS Racing Simulation

### Start Racing Simulation
```bash
# Terminal 1: Start EUFS simulation  
docker run -it --name eufs-sim --privileged --net=host \
  --env="DISPLAY" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  car-eufs-simple

# Inside EUFS container:
ros2 launch eufs_launcher simulation.launch.py use_sim_time:=true track:=small_track gazebo_gui:=true
```

### Connect Perception System
```bash
# Terminal 2: Start perception
docker exec -it perception-dev bash
cd /workspace/perception_ws && source install/setup.bash

# Run cone detection on EUFS camera
ros2 run cone_detector cone_detector_node --ros-args --remap image_raw:=/camera/image_raw

# Run SLAM system  
ros2 run slam_system slam_node --ros-args --remap image_raw:=/camera/image_raw
```

### See Results
```bash
# Terminal 3: Visualize everything
docker exec perception-dev bash -c "ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image"
docker exec perception-dev bash -c "rviz2"

# In RViz: Add these topics
# - /cone_detections (geometry_msgs/PointStamped)  
# - /slam/path (nav_msgs/Path)
# - /cone_detector/debug_image (sensor_msgs/Image)
```
### Recommended Hardware
**CPU**: 4+ cores, 2.5GHz+
**Memory**: 8GB+ RAM
**GPU**: Optional but recommended for YOLOv8
**Storage**: 10GB+ free space

## Troubleshooting

### Common Issues

1. **Docker build fails**:
   ```bash
   # Clean Docker build cache
   docker system prune -a
   
   # Check available space
   df -h
   ```

2. **Container won't start**:
   ```bash
   # Check Docker daemon
   sudo systemctl status docker
   
   # Verify image exists
   docker images | grep car-perception
   ```

3. **No camera data**:
   ```bash
   # Check available topics
   ros2 topic list | grep camera
   
   # Test camera feed
   ros2 run rqt_image_view rqt_image_view /camera/image_raw
   ```

4. **Build errors**:
   ```bash
   # Clean workspace
   rm -rf build install log
   
   # Check dependencies
   rosdep install --from-paths src --ignore-src -r -y
   
   # Rebuild
   colcon build
   ```
   
### Debug Commands

```bash
# Container info
docker ps -a
docker logs car-perception-dev

# ROS2 diagnostics
ros2 doctor
ros2 wtf

# Network connectivity
ros2 topic list
ros2 service list
ros2 node list

# Performance monitoring
htop
nvidia-smi  # if GPU available
```

### Immediate TODOs
- [ ] Complete ORB-SLAM3 C++ integration
- [ ] Add camera calibration tools
- [ ] Implement coordinate transformations
- [ ] Add cone color classification
- [ ] Create integration tests

## Documentation

[Cone Detector Documentation](src/cone_detector/README.md)
[SLAM System Documentation](src/slam_system/README.md)
[Docker Environment Details](../docker/README.md)
[EUFS Integration Guide](docs/eufs_integration.md)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request
