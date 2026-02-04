# Path Planning Module

## Overview
The Path Planning module generates optimal racing trajectories for the Cardiff autonomous racing vehicle. It integrates the **TUM Global Race Trajectory Optimization** framework with ROS 2 to produce minimum curvature or minimum time racing lines based on real-time cone detections from the perception system.

**Requirements: Ubuntu 22.04 LTS + ROS 2 Humble**

## Architecture

### ROS 2 Package Structure
```
Path_Planning/
├── path_planning/              # Main Python package
│   ├── __init__.py
│   ├── integration.py          # ROS 2 node (PathPlannerNode)
│   └── tum_wrapper.py          # TUM optimizer wrapper
├── tum_optimizer/              # TUM global trajectory optimization (submodule)
├── launch/
│   └── launch.py               # ROS 2 launch file
├── Legacy code/                # Deprecated RRT* implementation
├── package.xml                 # ROS 2 package manifest
├── setup.py                    # Python package setup
├── requirements.txt            # Python dependencies
├── setup_tum.sh               # TUM optimizer installation script
├── test_tum_integration.py    # Integration test script
└── INTEGRATION_GUIDE.md       # Detailed TUM integration guide
```

### Core Components

#### 1. PathPlannerNode (`path_planning/integration.py`)
ROS 2 node that:
- Subscribes to `/detected_cones` (YOLO cone detections: x,y,z,label format)
- Subscribes to `/car_pose` (vehicle pose)
- Publishes to `/planned_path` (optimized trajectory as nav_msgs/Path)
- Runs at 5 Hz
- Supports both TUM optimized trajectories and fallback centerline generation

**Cone Label Mapping:**
- Label 0: Blue cones (left track boundary)
- Label 1: Yellow cones (right track boundary)
- Label 2: Orange cones (special markers/boundaries)
- Label 3: Unknown cones (filtered out)

#### 2. TUMTrajectoryOptimizer (`path_planning/tum_wrapper.py`)
Wrapper class for TUM optimizer that:
- Converts cone detections to TUM reference track format `[x, y, w_tr_right, w_tr_left]`
- Optimizes trajectory using minimum curvature or shortest path algorithms
- Returns trajectory: `[x, y, heading, curvature, velocity]`

#### 3. TUM Global Race Trajectory Optimization (`tum_optimizer/`)
Git submodule from [TUMFTM/global_racetrajectory_optimization](https://github.com/TUMFTM/global_racetrajectory_optimization)
- Implements minimum time and minimum curvature optimization
- Uses CasADi for nonlinear optimization
- Provides trajectory planning helpers library

## Installation

### 1. Install System Dependencies
```bash
# ROS 2 Humble (if not already installed)
sudo apt update
sudo apt install ros-humble-desktop python3-colcon-common-extensions

# Python development tools
sudo apt install python3-pip python3-venv
```

### 2. Install Python Dependencies
```bash
cd /your/dir/structure/cardiff-autonomous-racing/Path_Planning
pip3 install -r requirements.txt
```

**Key dependencies:**
- `numpy` - Numerical computations
- `scipy` - Scientific computing
- `trajectory-planning-helpers` - TUM trajectory planning library
- `casadi` - Optimization framework
- `cvxpy` - Convex optimization
- `quadprog` - Quadratic programming solver

### 3. Setup TUM Optimizer (Git Submodule)
```bash
# Run the automated setup script
cd /your/dir/structure/cardiff-autonomous-racing/Path_Planning
./setup_tum.sh

# Or manually:
git clone https://github.com/TUMFTM/global_racetrajectory_optimization tum_optimizer
cd tum_optimizer
pip3 install -r requirements.txt
```

### 4. Build ROS 2 Package
```bash
# Navigate to workspace root
cd /your/dir/structure/cardiff-autonomous-racing

# Build the path_planning package
colcon build --packages-select path_planning

# Source the workspace
source install/setup.bash
```

## Usage

### Running with Docker (Recommended)
```bash
# Build the planning container
sudo docker compose build path_planning

# Start the container
sudo docker compose up -d path_planning

# Check logs
sudo docker logs -f racing_planning
```

### Running Locally

#### Option 1: Using ROS 2 Launch File
```bash
# Source ROS 2 and workspace
source /opt/ros/humble/setup.bash
source /your/dir/structure/cardiff-autonomous-racing/install/setup.bash

# Launch path planner (and optionally cone_mapper)
ros2 launch path_planning launch.py
```

#### Option 2: Running Node Directly
```bash
# Source environment
source /opt/ros/humble/setup.bash
source /your/dir/structure/cardiff-autonomous-racing/install/setup.bash

# Run the path planner node
ros2 run path_planning path_planner
```

#### Option 3: Development/Testing
```bash
cd /your/dir/structure/cardiff-autonomous-racing/Path_Planning

# Run integration test
python3 test_tum_integration.py

# Or run directly (for debugging)
python3 path_planning/integration.py
```

### Testing with Mock Data

**Terminal 1: Start Path Planner**
```bash
source /opt/ros/humble/setup.bash
cd /your/dir/structure/cardiff-autonomous-racing/Path_Planning
python3 path_planning/integration.py
```

**Terminal 2: Publish Mock Cone Data**
```bash
source /opt/ros/humble/setup.bash

# Publish vehicle pose
ros2 topic pub /car_pose geometry_msgs/PoseStamped '{header: {frame_id: "map"}, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}'

# Publish cone detections (x,y,z,label format)
ros2 topic pub /detected_cones std_msgs/String "data: '2.0,2.5,0.0,0
4.0,2.5,0.0,0
6.0,2.5,0.0,0
8.0,2.5,0.0,0
10.0,2.5,0.0,0
2.0,-2.5,0.0,1
4.0,-2.5,0.0,1
6.0,-2.5,0.0,1
8.0,-2.5,0.0,1
10.0,-2.5,0.0,1'"
```

**Terminal 3: Monitor Output**
```bash
# List active topics
ros2 topic list

# Echo planned path
ros2 topic echo /planned_path

# Echo cone detections
ros2 topic echo /detected_cones
```

## How It Works

### 1. Data Flow
```
[Perception] → /detected_cones → [PathPlannerNode] → /planned_path → [Control]
                                         ↑
                                   /car_pose
```

### 2. Optimization Pipeline
1. **Cone Detection:** YOLO detector publishes cone positions with labels
2. **Cone Categorization:** PathPlannerNode separates blue (left) and yellow (right) cones
3. **Reference Track Generation:** TUM wrapper converts cones to reference track format
4. **Trajectory Optimization:** TUM optimizer computes minimum curvature racing line
5. **Path Publication:** Optimized trajectory published as ROS 2 Path message

### 3. Optimization Types
- **`mincurv`** (default): Minimum curvature - smoother, safer trajectories
- **`shortest_path`**: Shortest geometric path through track
- **`mintime`**: Minimum lap time (requires vehicle dynamics model and GGV diagram)

### 4. Fallback Behavior
If TUM optimization fails (insufficient cones, errors), the node falls back to simple centerline generation by averaging left and right cone positions.

## Configuration

### Key Parameters (in `integration.py`)
```python
# Vehicle dimensions
vehicle_width = 1.5    # meters
vehicle_length = 2.5   # meters

# Minimum cones required for optimization
min_cones_left = 5
min_cones_right = 5

# Publishing rate
timer_period = 0.2     # 5 Hz
```

## Troubleshooting

### TUM Optimizer Not Available
**Symptom:** Log message "TUM optimizer not available"
```bash
# Verify installation
python3 -c "import trajectory_planning_helpers; print('TUM OK')"

# Reinstall if needed
pip3 install --upgrade trajectory-planning-helpers casadi
```

### No Path Published
**Check:**
1. Are cones being received? `ros2 topic echo /detected_cones`
2. Are there enough cones? (Need ≥5 left and ≥5 right)
3. Check node logs: `ros2 node info /path_planner`

### Import Errors
```bash
# Ensure workspace is sourced
source /your/dir/structure/cardiff-autonomous-racing/install/setup.bash

# Rebuild if package structure changed
colcon build --packages-select path_planning --symlink-install
```

## Legacy Code

The `Legacy code/` directory contains the original RRT* implementation and earlier integration attempts. This is kept for reference but is not part of the current system.

## Documentation

- [INTEGRATION_GUIDE.md](INTEGRATION_GUIDE.md) - Detailed TUM integration guide
- [TUM Repository](https://github.com/TUMFTM/global_racetrajectory_optimization) - Upstream documentation
- [trajectory_planning_helpers docs](https://github.com/TUMFTM/trajectory_planning_helpers) - Python library docs

## Support

For questions or issues with the path planning module, contact:

**Path Planning Team Lead:** Dominick George  
**Email:** GeorgeD8@cardiff.ac.uk

## Contributors

- Dominick George - Project Lead, TUM Integration
- Callum A'court - ROS 2 Integration, Package Structure