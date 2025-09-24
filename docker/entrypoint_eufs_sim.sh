#!/bin/bash

source /opt/ros/humble/setup.bash
source /workspace/eufs_sim_humble/install/setup.bash

export EUFS_MASTER=/workspace/eufs_sim_humble

ros2 launch eufs_launcher eufs_launcher.launch.py