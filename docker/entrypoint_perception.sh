#!/bin/bash

# Perception module entrypoint script
echo " Starting Perception Module..."

# Source ROS 2
source /opt/ros/humble/setup.bash

# Set ORB_SLAM3 environment variables
export ORB_SLAM3_ROOT_DIR=/workspace/perception_ws/ORB_SLAM3
export PYTHONPATH="${PYTHONPATH}:${ORB_SLAM3_ROOT_DIR}/lib"

# Source our workspace
if [ -f /workspace/perception_ws/install/setup.bash ]; then
    source /workspace/perception_ws/install/setup.bash
    echo " Perception workspace sourced successfully"
else
    echo " Perception workspace not found, building..."
    cd /workspace/perception_ws
    colcon build --symlink-install
    source /workspace/perception_ws/install/setup.bash
fi

echo " Perception system ready. Available nodes:"
echo "  - ros2 run cone_detector cone_detector_node"
echo "  - ros2 run cone_mapper cone_mapper_node"
echo "  - ros2 run slam_example orb_slam3_stereo"
echo "  - ros2 run slam_example orb_slam3_stereo_inertial"

# Execute the command passed to docker run
exec "$@"