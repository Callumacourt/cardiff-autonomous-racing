#!/bin/bash

# Control module entrypoint script
echo "🎮 Starting Control Module..."

# Source ROS 2
source /opt/ros/humble/setup.bash

# Source our workspace
if [ -f /workspace/control_ws/install/setup.bash ]; then
    source /workspace/control_ws/install/setup.bash
    echo "✅ Control workspace sourced successfully"
else
    echo "❌ Control workspace not found, building..."
    cd /workspace/control_ws
    colcon build --symlink-install
    source /workspace/control_ws/install/setup.bash
fi

# Start the control node
echo "🚀 Launching ROS control node..."

# Try to run ros_can first (if eufs_msgs built successfully)
if ros2 run ros_can ros_can_node 2>/dev/null; then
    echo "✅ ROS CAN node started successfully"
elif ros2 run ros_control cmd_node 2>/dev/null; then
    echo "✅ ROS Control cmd_node started successfully"
else
    echo "🎮 Running simple mock control node for complete system simulation..."
    cd /workspace/Control
    python3 simple_mock_control.py
fi
