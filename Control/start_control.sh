#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

source $SCRIPT_DIR/install/setup.bash
.$SCRIPT_DIR/ros_can/FS-AI-API/setup.sh
ros2 launch ros_can ros_can.launch.py >> "$SCRIPT_DIR/logs/ros_can_output-$(date +"%d-%m-%Y-%T").log" 2>&1 &

export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR/ros_control/ros_control"
ros2 run ros_control command_node --ros-args -p eufs_simulate:=0 >> "$SCRIPT_DIR/logs/control_output-$(date +"%d-%m-%Y-%T").log" 2>&1