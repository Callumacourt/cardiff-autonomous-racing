# Path Planning Package

## Overview
The Path Planning package is a ROS2 Humble node that generates optimal racing lines for autonomous vehicles in real-time. It receives cone detections from the perception system and vehicle pose information, then computes and publishes a drivable path for the control system to follow.

**Platform Requirements:** Ubuntu 22.04 LTS, ROS2 Humble

---

## Table of Contents
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [ROS2 Interface](#ros2-interface)
- [Installation](#installation)
- [Running the System](#running-the-system)
- [Visualization](#visualization)
- [Algorithm Details](#algorithm-details)
- [Future Improvements](#future-improvements)
- [Troubleshooting](#troubleshooting)
- [Support](#support)

---

## Architecture

### System Overview
```
┌─────────────────┐         ┌──────────────────┐         ┌──────────────┐
│  Perception     │────────▶│  Path Planning   │────────▶│   Control    │
│  (YOLO + SLAM)  │         │  (This Package)  │         │   System     │
└─────────────────┘         └──────────────────┘         └──────────────┘
      │                              │
      │ /detected_cones              │ /planned_path
      │ /car_pose                    │
      └──────────────────────────────┘
```

### Data Flow
1. **Perception System** detects cones using YOLO and publishes to `/detected_cones`
2. **SLAM/Localization** tracks vehicle position and publishes to `/car_pose`
3. **Path Planner** synchronizes both inputs using `message_filters`
4. **Centerline Generation** calculates optimal racing line from cone boundaries
5. **Path Publishing** sends waypoints to `/planned_path` at 5 Hz
6. **Control System** follows the published path

---

## Project Structure

```
Path_Planning/
├── path_planning/              # Main package directory
│   ├── __init__.py            # Package initialisation
│   └── integration.py         # Main path planning node (PathPlannerNode)
├── launch/
│   └── launch.py              # ROS2 launch file for full system
├── resource/                   # Package resource files
│   └── path_planning
├── package.xml                 # ROS2 package dependencies
├── setup.py                    # Python package configuration
└── pathPlanningREADME.md      # This file
```

### Key Files

#### `path_planning/integration.py`
The main ROS2 node implementing the `PathPlannerNode` class. Contains:
- **Subscribers:** Synchronized `/car_pose` and `/detected_cones` listeners
- **Publisher:** Publishes `nav_msgs/Path` to `/planned_path`
- **Callbacks:** Processes cone detections and vehicle pose updates
- **Planning Loop:** Runs at 5 Hz to generate and publish paths
- **Algorithms:** Centerline generation and cone categorisation

#### `launch/launch.py`
Launch file that starts:
1. `cone_mapper` node from perception package
2. `path_planner` node from this package

---

## How It Works

### 1. Node Initialisation
```python
PathPlannerNode()
├── Subscribes to /car_pose (geometry_msgs/PoseStamped)
├── Subscribes to /detected_cones (std_msgs/String)
├── Creates publisher for /planned_path (nav_msgs/Path)
└── Starts 5 Hz timer for main planning loop
```

### 2. Cone Detection Processing

**Input Format:** `/detected_cones` message contains newline-separated cone data:
```
x,y,z,label
x,y,z,label
...
```

**Label Classification:**
| Label | Color  | Meaning         | Action                    |
|-------|--------|-----------------|---------------------------|
| 0     | Blue   | Left boundary   | Add to `left_cones[]`     |
| 1     | Yellow | Right boundary  | Add to `right_cones[]`    |
| 2     | Orange | Special marker  | Add to `orange_cones[]`   |
| 3     | Unknown| Invalid         | Filter out                |
| -1    | N/A    | Error           | Filter out                |

### 3. Message Synchronisation

Uses ROS2 `message_filters.TimeSynchronizer` to align:
- Vehicle pose updates from `/car_pose`
- Cone detections from `/detected_cones`

**Why?** Ensures spatial consistency between where the vehicle is and which cones it sees.

### 4. Centerline Generation Algorithm

```python
generate_centerline():
    if both left and right cones exist:
        # Sort cones by x-coordinate (forward direction)
        for each left_cone:
            find closest_right_cone by x-coordinate
            calculate midpoint between pair
            add to centerline
    
    elif only left_cones:
        # Estimate centerline with 1.5m offset
        centerline = [(x + 1.5, y) for (x, y) in left_cones]
    
    elif only right_cones:
        # Estimate centerline with 1.5m offset
        centerline = [(x - 1.5, y) for (x, y) in right_cones]
```

**Algorithm Characteristics:**
- **Simple & Fast:** O(n*m) where n=left cones, m=right cones
- **Robust:** Handles partial cone detection (one side only)
- **Assumption:** Track width ≈ 3 meters (1.5m from boundary to center)

### 5. Path Publishing

Converts centerline points to ROS2 `nav_msgs/Path`:
```python
Path message:
├── header.frame_id = 'map'
├── header.stamp = current_time
└── poses[] = [
    PoseStamped(x, y, z=0.0, orientation=neutral)
    for each centerline point
]
```

**Update Rate:** 5 Hz (200ms interval)

---

## ROS2 Interface

### Subscribed Topics

| Topic             | Type                        | Description                          |
|-------------------|-----------------------------|--------------------------------------|
| `/car_pose`       | `geometry_msgs/PoseStamped` | Vehicle position and orientation     |
| `/detected_cones` | `std_msgs/String`           | Cone detections from YOLO (x,y,z,label) |

### Published Topics

| Topic            | Type              | Frequency | Description                    |
|------------------|-------------------|-----------|--------------------------------|
| `/planned_path`  | `nav_msgs/Path`   | 5 Hz      | Waypoints for vehicle to follow |

### Parameters
Currently none (hardcoded constants in node).

### Node Name
`path_planner`

---

## Installation

### Prerequisites
```bash
# ROS2 Humble installation
sudo apt update
sudo apt install ros-humble-desktop

# Python dependencies
sudo apt install python3-pip python3-dev

# Required ROS2 packages
sudo apt install ros-humble-geometry-msgs \
                 ros-humble-nav-msgs \
                 ros-humble-std-msgs \
                 ros-humble-message-filters
```

### Build Instructions

1. **Navigate to workspace:**
```bash
cd ~/cardiff-autonomous-racing
```

2. **Install Python dependencies:**
```bash
pip install numpy scipy
```

3. **Build the package:**
```bash
cd Path_Planning
colcon build --packages-select path_planning
```

4. **Source the workspace:**
```bash
source install/setup.bash
```

### Verify Installation
```bash
# Check if package is recognized
ros2 pkg list | grep path_planning

# Check available executables
ros2 pkg executables path_planning
# Expected output: path_planning path_planner
```

---

## Running the System

### Method 1: Launch Full System (Recommended)

Starts both perception and path planning:
```bash
cd ~/cardiff-autonomous-racing/Path_Planning
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 launch path_planning launch.py
```

### Method 2: Run Path Planner Only

For testing or if perception is running separately:
```bash
source /opt/ros/humble/setup.bash
source install/setup.bash

ros2 run path_planning path_planner
```

### Method 3: Docker Environment

```bash
cd ~/cardiff-autonomous-racing
docker-compose up planning
```

---

## Testing & Debugging

### Test with Mock Data

**Terminal 1:** Run path planner
```bash
ros2 run path_planning path_planner
```

**Terminal 2:** Publish test pose
```bash
ros2 topic pub /car_pose geometry_msgs/PoseStamped '{
  header: {frame_id: "map"}, 
  pose: {
    position: {x: 0.0, y: 0.0, z: 0.0}, 
    orientation: {w: 1.0}
  }
}'
```

**Terminal 3:** Publish test cone detections
```bash
ros2 topic pub /detected_cones std_msgs/String "data: '5.0,2.0,0.0,0
10.0,2.5,0.0,0
15.0,2.0,0.0,0
5.0,-2.0,0.0,1
10.0,-2.5,0.0,1
15.0,-2.0,0.0,1'"
```

### Monitor Output

**Check planned path:**
```bash
ros2 topic echo /planned_path
```

**Check node logs:**
```bash
ros2 node info /path_planner
```

**List all active topics:**
```bash
ros2 topic list
```

---

## Visualization

### Option 1: RViz2 (Recommended)

```bash
# Start RViz2
rviz2

# In RViz:
# 1. Set "Fixed Frame" to "map"
# 2. Click "Add" → "By topic" → /planned_path → Path
# 3. Adjust path color/width in Display panel
```

**Display Configuration:**
- Path: Green line, width 0.05m
- Pose: Blue arrow
- Frame: map

### Option 2: Plotjuggler

For real-time 2D plotting:
```bash
ros2 run plotjuggler plotjuggler
# Select /planned_path/poses[]/pose/position/x and y
```

### Option 3: Command Line

```bash
# Watch path updates
ros2 topic echo /planned_path --no-arr

# Monitor update frequency
ros2 topic hz /planned_path
# Expected: ~5 Hz
```

---

## Algorithm Details

### Current Implementation: Centerline Following

**Algorithm:** Midpoint-based geometric centerline
**Complexity:** O(n*m) where n, m are left/right cone counts
**Latency:** ~1-5ms per update
**Pros:**
- Fast and deterministic
- Works with partial cone detection
- Suitable for real-time (5 Hz)

**Cons:**
- No optimization (e.g., minimum curvature)
- No obstacle avoidance
- Assumes straight-line cone pairing

### Cone Pairing Strategy

```
Left cones:  ●────────●────────●
                 ╲       ╲       ╲
Centerline:       ×────────×────────×
                 ╱       ╱       ╱
Right cones: ●────────●────────●
```

For each left cone, find the right cone with the closest x-coordinate, then compute midpoint.

### Edge Cases Handled

1. **Only left cones detected:** Offset +1.5m to the right
2. **Only right cones detected:** Offset -1.5m to the left
3. **No cones detected:** Empty path (no output)
4. **Invalid labels:** Filtered out before processing
5. **Malformed data:** Try-except with warning logs

---

## Future Improvements

### Planned Enhancements

1. **Global Trajectory Optimsation** (Priority: High)
   - Gives us fastest line
   - Well optimised for our use case
   - Makes us more competitive at competition.

2. **Path Smoothing** (Priority: Medium)
   - Bezier curve interpolation
   - Spline fitting for smoother trajectories
   - Reduce waypoint jitter

3. **Lookahead Control** (Priority: Medium)
   - Pure pursuit controller integration
   - Dynamic lookahead distance based on speed
   - Goal point selection along centerline

4. **Advanced Centerline Generation** (Priority: Low)
   - Delaunay triangulation for better pairing
   - Minimum curvature optimization
   - Racing line optimization (maximize corner speed)

5. **Parameter Configuration** (Priority: Low)
   - ROS2 parameters for track width, update rate
   - Dynamic reconfigure support
   - Tuning interface

---

## Troubleshooting

### Problem: Node doesn't receive cone detections

**Solution:**
```bash
# Check if perception is publishing
ros2 topic list | grep detected_cones
ros2 topic hz /detected_cones

# Check topic data format
ros2 topic echo /detected_cones
```

### Problem: Path not published

**Solution:**
```bash
# Check node is running
ros2 node list | grep path_planner

# Check for errors in logs
ros2 run path_planning path_planner --ros-args --log-level debug

# Verify centerline is generated (check logs for "Generated centerline with X points")
```

### Problem: Build errors

**Solution:**
```bash
# Clean build
rm -rf build install log
colcon build --packages-select path_planning --cmake-clean-cache

# Check dependencies
rosdep install --from-paths . --ignore-src -r -y
```

### Problem: Import errors (numpy, scipy)

**Solution:**
```bash
# Install in ROS2 Python environment
pip3 install numpy scipy --user

# Or use system packages
sudo apt install python3-numpy python3-scipy
```

---

## Performance Metrics

| Metric                    | Value      |
|---------------------------|------------|
| Update Rate               | 5 Hz       |
| Processing Latency        | 1-5 ms     |
| Max Cone Count            | ~100       |
| Memory Usage              | ~50 MB     |
| CPU Usage                 | <5%        |

---

## Code Quality

- **Type Hints:** Full type annotations for all functions
- **Documentation:** Comprehensive docstrings
- **Error Handling:** Try-except blocks with logging
- **ROS2 Best Practices:** Proper node lifecycle management
- **Modularity:** Separate methods for each concern

---

## Support

### Primary Contact
**Dominick George** - Path Planning Team Leader  
📧 Email: GeorgeD8@cardiff.ac.uk

### Team Members
- Dominick George (Team Lead)
- Akshay Karsan (Developer)
- Ayush Yellembalse(Developer)
- Callum A'court (Developer)
- Victor Romero Cano (Academic Supervisor)

### Additional Resources
- [ROS2 Humble Documentation](https://docs.ros.org/en/humble/)
- [Global Race Trajectory Optimisation](https://github.com/TUMFTM/global_racetrajectory_optimization)
- WhatsApp: Contact Team Principle for invite
- Teams: Contact Team Lead for invite

---

## License
MIT License - See repository root for details

---

**Last Updated:** March 2026  
**Package Version:** 0.0.0  
**ROS2 Distribution:** Humble