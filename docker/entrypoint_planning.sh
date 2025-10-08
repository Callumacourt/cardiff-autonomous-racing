set -e

# Source ROS2
source /opt/ros/humble/setup.bash
source /workspace/planning_ws/install/setup.bash

echo " Starting Path Planning System..."

# Execute the command passed to docker run
exec "$@"