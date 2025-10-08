#!/bin/bash

# Source ROS2 setup
source /opt/ros/humble/setup.bash

# Source workspace if it exists and is built
if [ -f "/workspace/perception_ws/install/setup.bash" ]; then
    echo "Sourcing perception workspace..."
    source /workspace/perception_ws/install/setup.bash
else
    echo "Perception workspace not built yet. Run 'colcon build' to build it."
fi

# Set up environment variables for ORB-SLAM3
export ORB_SLAM3_ROOT_PATH=/workspace/ORB_SLAM3

# Set up environment for YOLO models (downloaded automatically by ultralytics)
export YOLO_MODELS_DIR=/workspace/.ultralytics

# Create directories if they don't exist
mkdir -p /workspace/.ultralytics

# Set working directory
cd /workspace/perception_ws

echo "=== Cardiff Autonomous Racing - Perception Environment ==="
echo "ROS2 Humble + EUFS Sim + YOLOv8 + ORB-SLAM3"
echo ""
echo "Quick commands:"
echo "  colcon build              # Build the workspace"
echo "  source install/setup.bash # Source built packages"
echo "  ros2 launch cone_detector cone_detector.launch.py  # Start cone detection"
echo "  ros2 launch slam_system slam.launch.py             # Start SLAM"
echo ""

# Execute the command
exec "$@"