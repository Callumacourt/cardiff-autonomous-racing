# SLAM System Package

ORB-SLAM3 visual SLAM implementation for autonomous racing.

## Overview

This package provides a ROS2 interface to ORB-SLAM3 for visual Simultaneous Localization and Mapping (SLAM). It processes camera images to estimate the vehicle's pose and build a map of the environment.

**Note**: This package currently provides a template structure. Full ORB-SLAM3 integration requires compilation of the C++ library and Python bindings.

## Current Status

**Development Status**: Template Implementation

The current implementation provides:
* ROS2 node structure and interfaces
* Parameter configuration
* Topic publishers and subscribers
* Mock pose generation for testing
* Actual ORB-SLAM3 integration (requires C++ compilation)

## Usage

### Quick Start

1. Launch the SLAM system:
   ```bash
   ros2 launch slam_system slam.launch.py
   ```

2. View the trajectory:
   ```bash
   rviz2 -d src/slam_system/config/slam_viz.rviz
   ```

3. Monitor pose estimates:
   ```bash
   ros2 topic echo /slam/pose
   ```

### Configuration

```bash
ros2 launch slam_system slam.launch.py \
    slam_mode:=monocular \
    camera_topic:=/camera/image_raw \
    vocabulary_path:=/workspace/ORB_SLAM3/Vocabulary/ORBvoc.txt
```

#### Parameters

- `slam_mode` (string, default: `monocular`): SLAM mode (monocular, stereo, rgbd)
- `camera_topic` (string, default: `/camera/image_raw`): Input camera topic
- `camera_info_topic` (string, default: `/camera/camera_info`): Camera calibration topic
- `pose_topic` (string, default: `/slam/pose`): Output pose topic
- `path_topic` (string, default: `/slam/path`): Output trajectory topic
- `map_topic` (string, default: `/slam/map`): Output map topic
- `vocabulary_path` (string): Path to ORB vocabulary file
- `settings_path` (string): Path to SLAM settings file

## Topics

### Subscribed Topics

- `/camera/image_raw` (sensor_msgs/Image): Input camera images
- `/camera/camera_info` (sensor_msgs/CameraInfo): Camera calibration data

### Published Topics

- `/slam/pose` (geometry_msgs/PoseStamped): Current camera pose estimate
- `/slam/path` (nav_msgs/Path): Camera trajectory
- `/slam/map` (nav_msgs/OccupancyGrid): Generated occupancy grid map

### TF Frames

* `map` to `camera_link`: Camera pose in the map frame

## ORB-SLAM3 Integration

To complete the ORB-SLAM3 integration:

### Prerequisites

1. **Install ORB-SLAM3 dependencies**:
   ```bash
   # Eigen3
   sudo apt install libeigen3-dev
   
   # Pangolin
   git clone https://github.com/stevenlovegrove/Pangolin.git
   cd Pangolin && mkdir build && cd build
   cmake .. && make -j4 && sudo make install
   
   # OpenCV (already included in Docker)
   ```

2. **Build ORB-SLAM3**:
   ```bash
   git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
   cd ORB_SLAM3
   chmod +x build.sh && ./build.sh
   ```

3. **Create Python bindings**:
   ```bash
   # Option 1: Use existing bindings
   git clone https://github.com/ydsf16/ORB_SLAM3_Python
   
   # Option 2: Create custom bindings with pybind11
   pip install pybind11
   ```

### Implementation Steps

1. **Update the slam_node.py**:
   - Import ORB-SLAM3 Python bindings
   - Initialize SLAM system in `__init__`
   - Process images with actual SLAM in `image_callback`

2. **Configuration files**:
   - Add camera calibration YAML files
   - Configure ORB-SLAM3 parameters
   - Set vocabulary path

3. **Build integration**:
   - Update CMakeLists.txt for C++ dependencies
   - Add ORB-SLAM3 libraries to package

## Development

### File Structure

```
slam_system/
├── slam_system/
│   ├── __init__.py
│   └── slam_node.py              # Main SLAM node
├── launch/
│   └── slam.launch.py            # Launch configuration
├── config/                       # Configuration files
│   ├── camera_calibration.yaml   # Camera parameters
│   └── slam_settings.yaml        # SLAM parameters
├── test/                         # Unit tests
├── package.xml                   # Package metadata
└── setup.py                      # Python setup
```

### Testing with Mock Data

The current implementation provides mock pose data for testing:

```python
# Mock trajectory (sinusoidal pattern)
time_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
x = math.sin(time_sec * 0.1) * 2.0
y = math.cos(time_sec * 0.1) * 2.0
```

### Camera Calibration

Proper SLAM requires accurate camera calibration:

```bash
# Calibrate camera using ROS2 tools
ros2 run camera_calibration cameracalibrator.py \
    --size 8x6 --square 0.108 \
    image:=/camera/image_raw \
    camera:=/camera
```

## Integration Examples

### With EUFS Simulation

```bash
# Terminal 1: EUFS simulation
ros2 launch eufs_launcher eufs_launcher.launch.py

# Terminal 2: SLAM system
ros2 launch slam_system slam.launch.py \
    camera_topic:=/camera/image_raw \
    camera_info_topic:=/camera/camera_info

# Terminal 3: Visualization
rviz2
```


## Troubleshooting

### Common Issues

1. **No pose output**:
   - Check camera topics: `ros2 topic list | grep camera`
   - Verify image format and camera info
   - Ensure proper lighting and texture in the scene

2. **Poor tracking**:
   - Check camera calibration
   - Ensure sufficient visual features
   - Adjust ORB-SLAM3 parameters

3. **Build errors**:
   - Install all dependencies
   - Check ORB-SLAM3 compilation
   - Verify Python bindings

### Performance Optimization

- **Reduce image resolution** for faster processing
- **Adjust ORB parameters** for feature extraction
- **Use GPU acceleration** if available
- **Tune SLAM parameters** for your specific environment

## Future Work

- [ ] Complete ORB-SLAM3 C++ integration
- [ ] Add Python bindings compilation
- [ ] Implement proper coordinate transformations
- [ ] Add loop closure detection
- [ ] Support for map saving/loading
- [ ] Multi-session SLAM capability
- [ ] IMU integration for visual-inertial SLAM
