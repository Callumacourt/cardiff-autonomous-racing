#!/bin/bash

# Perception module entrypoint script
echo "Starting Perception Module..."

# Source ROS 2
source /opt/ros/humble/setup.bash

# Source our workspace
if [ -f /workspace/perception_ws/install/setup.bash ]; then
    source /workspace/perception_ws/install/setup.bash
    echo "Perception workspace sourced successfully"
else
    echo "Perception workspace not found, building..."
    cd /workspace/perception_ws
    colcon build --symlink-install
    source /workspace/perception_ws/install/setup.bash
fi

echo "Perception system ready. Available nodes:"
echo "  - ros2 run cone_detector YOLO_cone_detector"
echo "  - ros2 run cone_mapper cone_mapper"
echo "  - ros2 run landmark_slam landmark_slam"

# Execute the command passed to docker run
exec "$@"
