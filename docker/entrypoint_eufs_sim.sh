#!/bin/bash

source /opt/ros/humble/setup.bash
source /workspace/eufs_sim_humble/install/setup.bash
echo $eufs_simulate
echo $RMW_IMPLEMENTATION
export EUFS_MASTER=/workspace/eufs_sim_humble
rqt_graph &
if [ $eufs_simulate = 1 ]; then
    ros2 launch eufs_launcher eufs_launcher.launch.py
fi