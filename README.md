# Cardiff Autonomous Racing

**Complete autonomous racing system with perception, path planning, and control**

A comprehensive ROS2-based autonomous racing platform featuring:
- **Real-time cone detection** with YOLOv8
- **Visual SLAM** with ORB-SLAM3
- **Path planning** with RRT* algorithms  
- **Vehicle control** integration
- **EUFS simulation** environment
- **Docker-based development** workflow

## Quick Start for New Contributors

### Prerequisites

**System Requirements:**
- Ubuntu 20.04+ or compatible Linux distribution
- Docker 20.10+ and Docker Compose
- 8GB+ RAM, 4+ CPU cores
- 15GB+ free disk space
- X11 display server for GUI applications

**Install Docker:**
```bash
# Ubuntu/Debian
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
newgrp docker

# Verify installation
docker --version
docker-compose --version
```

### Complete Setup (5 minutes)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/callumacourt/cardiff-autonomous-racing.git
   cd cardiff-autonomous-racing
   ```

2. **Build all Docker images:**
   ```bash
   # Build perception system (includes YOLOv8, ORB-SLAM3, ROS2)
   docker build -f docker/Dockerfile.perception -t car-perception:latest .
   
   # Build EUFS simulation environment
   docker build -f docker/Dockerfile.eufs_simple -t car-eufs-simple .
   ```

3. **Test the complete system:**
   ```bash
   # Start EUFS simulation (Terminal 1)
   docker run -it --name eufs-sim --privileged --net=host \
     --env="DISPLAY" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
     car-eufs-simple
   
   # In the EUFS container, launch simulation:
   ros2 launch eufs_launcher simulation.launch.py use_sim_time:=true track:=small_track gazebo_gui:=true
   
   # Start perception system (Terminal 2)
   docker run -it --name car-perception-dev --privileged --net=host \
     --env="DISPLAY" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
     --volume="$(pwd)/perception_ws:/workspace/perception_ws:rw" \
     car-perception:latest
   
   # In the perception container, run cone detection:
   cd /workspace/perception_ws
   colcon build --packages-select cone_detector
   source install/setup.bash
   ros2 run cone_detector cone_detector_node --ros-args --remap image_raw:=/camera/image_raw
   ```

4. **Visualize the results:**
   ```bash
   # View cone detection with bounding boxes (Terminal 3)
   docker exec car-perception-dev bash -c \
     "source /opt/ros/humble/setup.bash && ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image"
   
   # Monitor cone detection data
   docker exec car-perception-dev bash -c \
     "source /opt/ros/humble/setup.bash && ros2 topic echo /cone_detections"
   ```

** You should now see:**
- Gazebo simulation with a racing car on a track with cones
- Camera feed from the car with bounding boxes around detected cones
- Real-time cone detection data in the terminal

##  System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Cardiff Autonomous Racing                          │
└─────────────────────────────────────────────────────────────────────────────┘
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────┐
│   Perception    │  │ Path Planning   │  │    Control      │  │    EUFS     │
│  (perception_ws)│  │                 │  │                 │  │ Simulation  │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────┘
│                     │                     │                     │
│ • YOLOv8 Cones     │ • RRT* Planning    │ • Vehicle Control  │ • Gazebo Env│
│ • ORB-SLAM3        │ • Path Smoothing   │ • CAN Interface    │ • Track Model│
│ • Sensor Fusion    │ • Obstacle Avoid   │ • Safety Systems   │ • Car Physics│
│ • Real-time Proc   │ • Trajectory Gen   │ • State Machine    │ • Sensors    │
└─────────────────────┴─────────────────────┴─────────────────────┴─────────────┘
```

## Repository Structure

```
cardiff-autonomous-racing/
├── README.md                           # This file
├── docker/                             # Docker environments
│   ├── Dockerfile.perception           # Perception + ML stack
│   ├── Dockerfile.eufs_simple          # EUFS simulation
│   ├── Dockerfile.pathplanning         # Path planning
│   ├── Dockerfile.control              # Vehicle control
│   └── shared.env                      # Shared environment variables
├── perception_ws/                      # Perception workspace
│   ├── src/
│   │   ├── cone_detector/              # YOLOv8 cone detection
│   │   ├── cone_mapper/                # Cone mapping and tracking
│   │   └── slam_example/               # ORB-SLAM3 integration
│   └── README.md                       # Detailed perception docs
├── Path_Planning/                      # Path planning algorithms
│   ├── rrt_star.py                     # RRT* implementation
│   ├── integration.py                  # ROS2 integration
│   └── gui.py                          # Visualization tools
├── Control/                            # Vehicle control system
│   ├── ros_control/                    # ROS2 control nodes
│   ├── ros_can/                        # CAN bus interface
│   └── logs/                           # Control system logs
├── scripts/                            # Utility scripts
│   ├── build_docker.sh                 # Build all Docker images
│   └── run_docker.sh                   # Run development environment
└── test_data/                          # Test data and mock nodes
    ├── mock_pose_publisher.py          # Mock vehicle pose
    └── test_cone_published.py          # Test cone detection
```

##  Development Workflow

### 1. **Perception Development**
```bash
# Start development container with live code mounting
docker run -it --name perception-dev --privileged --net=host \
  --env="DISPLAY" --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
  --volume="$(pwd)/perception_ws:/workspace/perception_ws:rw" \
  car-perception:latest

# Inside container - build and test
cd /workspace/perception_ws
colcon build
source install/setup.bash

# Test cone detection
ros2 launch cone_detector cone_detector.launch.py

# Test with real camera or simulation
ros2 run cone_detector cone_detector_node
```

### 2. **Path Planning Development**
```bash
# Path planning with Python
cd Path_Planning
python3 rrt_star.py  # Test algorithms

# ROS2 integration
ros2 run path_planning path_planner_node
```

### 3. **Control System Development**
```bash
# Start control development
cd Control
./start_control.sh

# Monitor CAN bus
ros2 topic echo /can_tx
ros2 topic echo /can_rx
```

### 4. **Full System Integration**
```bash
# Use docker-compose for full system (future)
docker-compose up
```

##  Component Details

###  Perception System
**Location:** `perception_ws/`
**Purpose:** Real-time environment understanding

**Features:**
- **Cone Detection**: YOLOv8-based real-time cone detection
- **Visual SLAM**: ORB-SLAM3 for localization and mapping  
- **Sensor Fusion**: Combine camera, lidar, and odometry data
- **ROS2 Integration**: Standard ROS2 interfaces

**Key Topics:**
- `/camera/image_raw` → Camera input
- `/cone_detections` → Detected cone positions
- `/slam/pose` → Vehicle pose estimate
- `/cone_detector/debug_image` → Visualization

**Quick Test:**
```bash
# Test cone detection with test image
ros2 run cone_detector test_cone_detection
```

###  Path Planning
**Location:** `Path_Planning/`
**Purpose:** Generate optimal racing trajectories

**Algorithms:**
- **RRT\***: Rapidly-exploring Random Tree with optimization
- **Trajectory Smoothing**: B-spline path smoothing
- **Obstacle Avoidance**: Dynamic obstacle avoidance
- **Racing Line Optimization**: Minimum time path planning

**Quick Test:**
```bash
cd Path_Planning
python3 rrt_star.py --visualize
```

###  Control System
**Location:** `Control/`
**Purpose:** Vehicle control and safety

**Features:**
- **CAN Bus Interface**: Communication with vehicle systems
- **Safety Systems**: Emergency braking and fail-safes
- **State Machine**: Autonomous driving state management
- **Manual Override**: Seamless manual control takeover

**Quick Test:**
```bash
cd Control
./start_control.sh --mock  # Test with mock vehicle
```

###  EUFS Simulation
**Purpose:** Realistic racing simulation environment

## Configuration

### Environment Variables
```bash
# Core settings
export ROS_DOMAIN_ID=42                 # Avoid conflicts
export EUFS_MASTER=/workspace/eufs_sim_humble
export CAMERA_TOPIC=/camera/image_raw

# Perception tuning
export YOLO_MODEL=yolov8n.pt           # Model size: n/s/m/l/x
export DETECTION_CONFIDENCE=0.5        # Detection threshold
export IMAGE_RESOLUTION=640x480        # Processing resolution

# Development settings
export ROS_LOG_LEVEL=INFO              # Logging level
export DISPLAY=:0                      # X11 display
```

### Docker Configuration
**Memory Requirements:**
- **Perception**: 6GB+ RAM (YOLOv8 + ORB-SLAM3)
- **EUFS Simulation**: 4GB+ RAM (Gazebo)
- **Development**: 2GB+ RAM per additional container

**Volume Mounts:**
```bash
# Development workflow
--volume="$(pwd)/perception_ws:/workspace/perception_ws:rw"   # Live code editing
--volume="/tmp/.X11-unix:/tmp/.X11-unix:rw"                  # GUI applications
--volume="$(pwd)/test_data:/workspace/test_data:ro"          # Test data
```

## Testing

### Unit Tests
```bash
# Perception tests
cd perception_ws
colcon test --packages-select cone_detector
colcon test-result --verbose

# Path planning tests
cd Path_Planning
python3 -m pytest tests/

# Control tests
cd Control
python3 -m pytest ros_control/test/
```

### Integration Tests
```bash
# Full perception pipeline
./scripts/test_perception_pipeline.sh

# Simulation integration
./scripts/test_eufs_integration.sh

# End-to-end system test
./scripts/test_full_system.sh
```

### Performance Benchmarks
```bash
# Perception performance
ros2 run cone_detector benchmark_detection --iterations 100

# Path planning performance  
python3 Path_Planning/benchmark_planning.py

# System latency
./scripts/measure_system_latency.sh
```

##  Troubleshooting

### Common Issues

**1. Docker permission denied:**
```bash
sudo usermod -aG docker $USER
newgrp docker
```

**2. GUI applications won't start:**
```bash
xhost +local:docker  # Allow Docker X11 access
```

**3. EUFS simulation crashes:**
```bash
# Check GPU drivers
nvidia-smi  # For NVIDIA
# OR check system resources
htop
```

**4. Perception pipeline slow:**
```bash
# Use smaller YOLO model
export YOLO_MODEL=yolov8n.pt

# Reduce image resolution
export IMAGE_RESOLUTION=320x240
```

**5. ROS2 nodes can't communicate:**
```bash
# Check ROS domain
echo $ROS_DOMAIN_ID

# Check network
ros2 topic list
ros2 node list
```

### Debug Commands
```bash
# Container status
docker ps -a
docker logs container_name

# ROS2 diagnostics  
ros2 doctor
ros2 wtf

# System resources
docker stats
htop
nvidia-smi
```

### Visualization Tools
```bash
# RViz for 3D visualization
rviz2

# Image visualization
ros2 run rqt_image_view rqt_image_view

# Topic monitoring
ros2 run rqt_graph rqt_graph
ros2 run rqt_topic rqt_topic
```

## Contributing

### Getting Started
1. **Fork** the repository
2. **Clone** your fork: `git clone https://github.com/YOUR_USERNAME/cardiff-autonomous-racing.git`
3. **Create a branch**: `git checkout -b feature/your-feature-name`
4. **Set up development environment** (see Quick Start)
5. **Make your changes**
6. **Test thoroughly** 
7. **Submit a pull request**

**Documentation:**
- Update README files for modified components
- Add API documentation for new interfaces
- Include usage examples
- Document configuration changes

### Technical Documentation
- [Perception System Details](perception_ws/README.md)
- [Path Planning Algorithms](Path_Planning/README.md)
- [Control System Architecture](Control/README.md)
- [EUFS Integration Guide](docs/eufs_integration.md)
