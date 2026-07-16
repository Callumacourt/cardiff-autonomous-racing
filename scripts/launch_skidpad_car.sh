#!/usr/bin/env bash
# SKIDPAD mission master script — starts everything the mission needs:
#   ros_can -> ZED2 camera -> perception (detector, SLAM, mapper) -> skidpad_driver
#
# Run on the car after setup_on_car.sh has completed once.  Ctrl+C stops all.
#
# Deliberately NOT started: Control's cmd_node (no AMI_SKIDPAD branch, and it
# publishes /cmd + a constant mission_completed=False that would fight the
# skidpad driver) and the Path_Planning node (can't handle a figure-8).
set -uo pipefail

REPO="$HOME/cardiff-autonomous-racing"
source /opt/ros/humble/setup.bash

cleanup() { kill 0 2>/dev/null; }
trap cleanup EXIT INT TERM

echo "[1/4] ros_can (CAN bridge — mission state, IMU, twist)"
( cd "$REPO/Control" &&
  source install/setup.bash &&
  ./ros_can/FS-AI-API/setup.sh &&
  ros2 launch ros_can ros_can.launch.py ) &
sleep 3

echo "[2/4] ZED2 camera driver"
( source "$HOME/zed_ws/install/setup.bash" &&
  ros2 launch zed_wrapper zed_camera.launch.py camera_model:=zed2 ) &
sleep 8

echo "      Verifying camera topics (adjust this script if names differ)"
timeout 10 ros2 topic list | grep -E "zed" | head -8 || echo "  WARNING: no /zed topics yet"

echo "[3/4] Perception nodes"
source "$REPO/perception_ws/install/setup.bash"

ros2 run cone_detector YOLO_cone_detector --ros-args \
  -p rgb_topic:=/zed/zed_node/rgb/image_rect_color \
  -p depth_topic:=/zed/zed_node/depth/depth_registered \
  -p camera_info_topic:=/zed/zed_node/left/camera_info &

ros2 run landmark_slam landmark_slam --ros-args \
  -p imu_topic:=/ros_can/imu &
  # add once measured:  -p camera_x_offset:=<m> -p camera_y_offset:=<m>

ros2 run cone_mapper cone_mapper &

echo "[4/4] Skidpad driver (arms only on AMI_SKIDPAD + AS_DRIVING)"
# entry_length/exit_length: CONFIRM against the actual track before running.
( source "$REPO/Control/install/setup.bash" &&
  python3 "$REPO/scripts/skidpad_driver.py" --ros-args \
    -p entry_length:=15.0 \
    -p exit_length:=25.0 \
    -p target_speed:=2.5 ) &

echo
echo "Running. Health checks in another terminal:"
echo "  ros2 topic echo /ros_can/state --once    (mission = 12 for skidpad)"
echo "  ros2 topic hz /cone_cloud/local          (detections)"
echo "  ros2 topic hz /odometry/slam             (SLAM pose)"
echo "  ros2 topic echo /cone_map/local --once   (map feed)"
echo "  ros2 topic echo /cmd                     (driver output — zeros until AS_DRIVING)"
wait
