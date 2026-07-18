#!/usr/bin/env bash
# Live ZED desk demo of the perception->planning chain, no sim and no car:
#   ZED camera -> GPU YOLO -> cone_mapper + landmark_slam (ZED IMU)
#     -> path planner -> path drawn INSIDE the camera image
#
# Opens an image viewer on /path_overlay_image. Show the camera >=2 blue and
# >=2 yellow cones arranged like a lane and the planned path appears as a
# green line between them.
#
# Usage:  scripts/run_zed_desk_demo.sh          (re)start everything
#         scripts/run_zed_desk_demo.sh stop     stop everything

set -o pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOGS="$ROOT/logs"
CAMERA_MODEL="${CAMERA_MODEL:-zed2i}"

source /opt/ros/humble/setup.bash

echo "[1/4] Stopping previous demo nodes..."
pkill -f '[Y]OLO_cone_detector'
pkill -f '[c]one_mapper'
pkill -f '[l]andmark_slam'
pkill -f '[i]ntegration.py'
pkill -f '[p]ath_image_overlay'
pkill -f '[r]qt_image_view'
if [ "${1:-}" = "stop" ]; then
  pkill -f '[z]ed_camera.launch\|[z]ed_wrapper'
  echo "Demo stopped (ZED node too)."
  exit 0
fi
sleep 2

echo "[2/4] ZED camera..."
if timeout 5 ros2 topic list 2>/dev/null | grep -q '/zed/zed_node/rgb/image_rect_color'; then
  echo "  already running."
else
  ( source "$HOME/zed_ws/install/setup.bash" &&
    nohup ros2 launch zed_wrapper zed_camera.launch.py camera_model:="$CAMERA_MODEL" \
      > "$LOGS/zed_node.log" 2>&1 & )
  until timeout 5 ros2 topic list 2>/dev/null | grep -q '/zed/zed_node/rgb/image_rect_color'; do
    echo "  waiting for ZED topics..."; sleep 3
  done
fi

echo "[3/4] Perception + planner + overlay..."
source "$ROOT/perception_ws/install/setup.bash"
nohup ros2 run cone_detector YOLO_cone_detector --ros-args \
    -p rgb_topic:=/zed/zed_node/rgb/image_rect_color \
    -p depth_topic:=/zed/zed_node/depth/depth_registered \
    -p camera_info_topic:=/zed/zed_node/left/camera_info \
    > "$LOGS/zed_demo_detector.log" 2>&1 &
nohup ros2 run cone_mapper cone_mapper > "$LOGS/zed_demo_mapper.log" 2>&1 &
nohup ros2 run landmark_slam landmark_slam --ros-args \
    -p imu_topic:=/zed/zed_node/imu/data > "$LOGS/zed_demo_slam.log" 2>&1 &
nohup python3 "$ROOT/Path_Planning/path_planning/integration.py" \
    > "$LOGS/zed_demo_planner.log" 2>&1 &
nohup python3 "$SCRIPT_DIR/path_image_overlay.py" > "$LOGS/zed_demo_overlay.log" 2>&1 &
sleep 6

echo "[4/4] Viewer..."
DISPLAY="${DISPLAY:-:0}" nohup ros2 run rqt_image_view rqt_image_view /path_overlay_image \
    >/dev/null 2>&1 &

sleep 3
echo
RATE="$(timeout 10 ros2 topic hz /path_overlay_image 2>/dev/null | grep -m1 rate)"
echo "overlay stream: ${RATE:-no frames yet — check $LOGS/zed_demo_*.log}"
echo "Demo running. Show the camera 2+ blue and 2+ yellow cones in a lane."
