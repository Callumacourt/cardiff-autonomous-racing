#!/bin/bash
set -e

# Source ROS2
source /opt/ros/humble/setup.bash
source /workspace/perception_ws/install/setup.bash

echo "🎯 Starting Perception System..."

# Execute the command passed to docker run
exec "$@"