#!/bin/bash
SCRIPT_DIR="$(dirname "$(readlink -f "$0")")"

export PYTHONPATH="$PYTHONPATH:$SCRIPT_DIR/ros_control/ros_control"
ros2 run ros_control command_node --ros-args -p eufs_simulate:=1 >> "$SCRIPT_DIR/logs/control_output-$(date +"%d-%m-%Y-%T").log" 2>&1
