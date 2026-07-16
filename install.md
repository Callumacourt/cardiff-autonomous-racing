# Cardiff Autonomous Racing - Installation Guide

This comprehensive guide will help you set up and run the Cardiff Autonomous Racing perception and path planning systems to reach the Python GUI displaying the optimal path to the goal.

## Prerequisites

- **Operating System**: Ubuntu 22.04 LTS (Required)
- **ROS 2**: Humble Hawksbill distribution
- **Python**: 3.10 or higher

## Table of Contents
1. [System Dependencies](#system-dependencies)
2. [ROS 2 Installation](#ros-2-installation)
3. [Perception Stack Setup](#perception-stack-setup)
4. [Path Planning Setup](#path-planning-setup)
5. [Running the Complete System](#running-the-complete-system)
6. [Troubleshooting](#troubleshooting)

## System Dependencies

First, update your system and install essential packages:

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    git \
    wget \
    curl \
    build-essential \
    cmake \
    pkg-config \
    python3-pip \
    python3-venv \
    python3-tk \
    tk-dev \
    libeigen3-dev \
    libpangolin-dev \
    libopencv-dev
```

## ROS 2 Installation

### Install ROS 2 Humble

1. Set up the ROS 2 repository:
```bash
sudo apt install software-properties-common
sudo add-apt-repository universe
sudo apt update && sudo apt install curl -y
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
```

2. Install ROS 2 Humble:
```bash
sudo apt update
sudo apt install -y ros-humble-desktop
sudo apt install -y ros-dev-tools
```

3. Setup ROS 2 environment (add to your `~/.bashrc`):
```bash
echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
source ~/.bashrc
```

### Install Additional ROS 2 Packages

```bash
sudo apt install -y \
    ros-humble-geometry-msgs \
    ros-humble-std-msgs \
    ros-humble-nav-msgs \
    ros-humble-sensor-msgs \
    ros-humble-cv-bridge \
    ros-humble-image-transport \
    ros-humble-rqt* \
    python3-colcon-common-extensions
```

## Perception Stack Setup

### Install Perception Dependencies

1. **ORB-SLAM3 Dependencies**:
```bash
# Install OpenCV (if not already installed)
sudo apt install -y libopencv-dev python3-opencv

# Install Pangolin dependencies
sudo apt install -y \
    libgl1-mesa-dev \
    libglew-dev \
    libpython3-dev \
    libepoxy-dev \
    libpng-dev \
    libjpeg-dev \
    libtiff5-dev \
    libopenexr-dev \
    liblz4-dev \
    libzstd-dev \
    python3-wheel \
    python3-setuptools

# Install Pangolin (make sure no virtual environment is active)
# Deactivate any virtual environment first
deactivate 2>/dev/null || true
unset VIRTUAL_ENV
unset PYTHONPATH

cd /tmp
git clone https://github.com/stevenlovegrove/Pangolin.git
cd Pangolin
mkdir build && cd build

# Use system Python explicitly to avoid virtual environment conflicts
cmake -DPYTHON_EXECUTABLE=/usr/bin/python3 ..
make -j4
sudo make install
```

2. **Clone and Build ORB-SLAM3**:
```bash
cd /tmp
git clone https://github.com/UZ-SLAMLab/ORB_SLAM3.git
cd ORB_SLAM3
chmod +x build.sh
./build.sh
```

### Build Perception Workspace

1. **Navigate to perception workspace**:
```bash
cd /home/dom/cardiff-autonomous-racing/perception_ws
```

2. **Install Python dependencies for perception**:
```bash
pip3 install \
    opencv-python \
    numpy \
    rclpy \
    sensor-msgs \
    cv-bridge
```

3. **Build the perception workspace**:
```bash
# Make sure ROS 2 is sourced
source /opt/ros/humble/setup.bash

# Build all packages
colcon build --cmake-args -DCMAKE_BUILD_TYPE=Release

# Source the built workspace
source install/setup.bash
```

## Path Planning Setup

### Install Python Dependencies

1. **Navigate to Path Planning directory**:
```bash
cd "/home/dom/cardiff-autonomous-racing/Path Planning"
```

2. **Create and activate Python virtual environment** (recommended):
```bash
python3 -m venv pathplanning_env
source pathplanning_env/bin/activate
```

3. **Install Path Planning dependencies**:
```bash
# Install from requirements.txt
pip install -r requirements.txt

# Install additional required packages
pip install \
    rclpy \
    geometry-msgs \
    std-msgs \
    nav-msgs \
    pillow \
    tkinter
```

### Fix Potential PIL/Pillow Issues

If you encounter `ImportError: cannot import name 'ImageTk' from 'PIL'`, run:

```bash
# Method 1: Reinstall Pillow
pip uninstall pillow -y
pip install --no-cache-dir --force-reinstall pillow

# Method 2: If still having issues
sudo apt update
sudo apt install python3-tk tk-dev
pip uninstall pillow -y
pip install --no-cache-dir --force-reinstall pillow
```

## Running the Complete System

### Step 1: Start ROS 2 Environment

Open a new terminal and source ROS 2:
```bash
source /opt/ros/humble/setup.bash
```

### Step 2: Start Perception Stack (Optional - for real perception data)

If you want to run the full perception pipeline:

**Terminal 1** - Cone Mapper:
```bash
cd /home/dom/cardiff-autonomous-racing/perception_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run cone_mapper cone_mapper
```

**Terminal 2** - SLAM:
```bash
cd /home/dom/cardiff-autonomous-racing/perception_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch slam_example slam_example.launch.py
```

**Terminal 3** - Cone Detector:
```bash
cd /home/dom/cardiff-autonomous-racing/perception_ws
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run cone_detector cone_detector_node
```

### Step 3: Publish Test Data (Alternative to Perception Stack)

If the perception stack is not working or you want to test with dummy data:

**Terminal 4** - Test Data Publisher:
```bash
cd /home/dom/cardiff-autonomous-racing
source /opt/ros/humble/setup.bash
python3 test_cone_publisher.py
```

**OR manually publish test data**:
```bash
# Car pose
ros2 topic pub /car_pose geometry_msgs/PoseStamped '{header: {frame_id: "map"}, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}'

# Cone map data
ros2 topic pub /cone_map/local std_msgs/String "data: '5.0,2.0,0.0,0,0.9\n10.0,2.5,0.0,1,0.8'"
```

### Step 4: Run Path Planning and GUI

**Terminal 5** - Path Planning with GUI:
```bash
cd "/home/dom/cardiff-autonomous-racing/Path Planning"

# If using virtual environment
source pathplanning_env/bin/activate

# Source ROS 2
source /opt/ros/humble/setup.bash

# Run the integration script (this will show the GUI)
python3 integration.py
```

### Step 5: Verify System is Working

**Terminal 6** - Check ROS Topics:
```bash
source /opt/ros/humble/setup.bash

# List all active topics
ros2 topic list

# Monitor specific topics
ros2 topic echo /car_pose
ros2 topic echo /cone_map/local
ros2 topic echo /planned_path
```

Expected topics to see:
- `/car_pose` - Current vehicle position
- `/cone_map/local` - Detected cone positions
- `/planned_path` - Generated optimal path

## Expected Result

When everything is running correctly, you should see:

1. **Console Output**: ROS 2 nodes running and publishing data
2. **GUI Window**: A Python GUI displaying:
   - Current vehicle position
   - Detected cone positions (left/right cones)
   - Generated optimal path using RRT* algorithm
   - Real-time path updates as the vehicle moves

## System Architecture

The complete system works as follows:

1. **Perception Stack** (optional):
   - `cone_detector` - Detects cones from camera feed
   - `slam_example` - Provides vehicle localization
   - `cone_mapper` - Maps detected cones to world coordinates

2. **Test Data** (alternative):
   - `test_cone_publisher.py` - Publishes simulated cone and pose data

3. **Path Planning**:
   - `integration.py` - Main node that:
     - Subscribes to car pose and cone data
     - Runs RRT* path planning algorithm
     - Displays GUI with optimal path visualization
     - Publishes planned path for control systems

## Troubleshooting

### Common Issues

1. **ROS 2 not found**:
   ```bash
   source /opt/ros/humble/setup.bash
   ```

2. **Python import errors**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. **GUI not displaying**:
   ```bash
   sudo apt install python3-tk
   export DISPLAY=:0
   ```

4. **Permission denied errors**:
   ```bash
   sudo chmod +x integration.py
   ```

5. **Colcon build fails**:
   ```bash
   cd perception_ws
   rm -rf build install log
   colcon build --cmake-clean-cache
   ```

6. **Pangolin CMake error - "No module named 'wheel'"**:
   ```bash
   # Install wheel module
   pip3 install wheel setuptools
   # OR if in virtual environment
   pip install wheel setuptools
   ```

7. **Pangolin build issues**:
   ```bash
   # Clean and rebuild Pangolin
   cd /tmp/Pangolin/build
   rm -rf *
   cmake ..
   make -j4
   sudo make install
   ```

### Getting Help

If you encounter issues not covered here, please contact:
- **Path Planning Team Leader**: Dominick George (GeorgeD8@cardiff.ac.uk)

### Logs and Debugging

To debug issues:
```bash
# Check ROS 2 logs
ros2 doctor

# Monitor all topics
rqt_graph

# View topic data
ros2 topic echo /topic_name
```

---

**Success Indicator**: You should see a GUI window with the racing track layout, cone positions, and a green/red path line showing the optimal route calculated by the RRT* algorithm.
