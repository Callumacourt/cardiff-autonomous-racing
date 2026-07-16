#!/bin/bash

source /opt/ros/humble/setup.bash
source /workspace/eufs_sim_humble/install/setup.bash
echo $eufs_simulate
echo $RMW_IMPLEMENTATION
export EUFS_MASTER=/workspace/eufs_sim_humble
rqt_graph &
if [ $eufs_simulate = 1 ]; then
    # Skip GUI launcher, directly run simulation with real camera enabled
    # launch_group:=default enables real sensors (camera, depth, lidar)
    # vs launch_group:=no_perception which uses abstract cone detection
    ros2 launch eufs_launcher simulation.launch.py \
        use_sim_time:=true \
        track:=${TRACK_NAME:-small_track} \
        robot_name:=ads-dv \
        rviz:=true \
        launch_group:=default \
        gazebo_gui:=false \
        publish_gt_tf:=false \
        pub_ground_truth:=true
fi