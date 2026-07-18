#!/usr/bin/env bash
set -eo pipefail  # no -u: ROS setup.bash trips on unbound variables

# Full-stack autonomous lap in the EUFS sim, running everything NATIVELY
# (no docker): sim with real cameras -> GPU YOLO cone_detector ->
# cone_mapper + landmark_slam -> path planner -> pure-pursuit follower.
#
# Prereqs (already present on this machine):
#   /opt/ros/humble, ~/eufs (eufs_sim workspace), CUDA torch + ultralytics,
#   /workspace/perception_ws/models/best.pt (hardcoded model path)
#
# Usage:  scripts/run_full_autonomous_lap_native.sh [laps] [speed_mps]

LAPS="${1:-1}"
SPEED="${2:-2.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
EUFS_WS="${EUFS_WS:-$HOME/eufs}"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_DIR="${ROOT_DIR}/logs"
mkdir -p "${LOG_DIR}"
cd "${ROOT_DIR}"

source /opt/ros/humble/setup.bash

echo "[1/7] Stopping any previous stack (sim, webcam rig, perception, control, follower)..."
pkill -f 'simulation.launch.py' 2>/dev/null || true
pkill -f '[g]zserver|[g]zclient' 2>/dev/null || true
pkill -f '[e]ufs_launcher' 2>/dev/null || true
pkill -f '[w]ebcam_test_publisher|[w]ebcam_test_viewer' 2>/dev/null || true
pkill -f '[Y]OLO_cone_detector|[c]one_mapper|[l]andmark_slam' 2>/dev/null || true
pkill -f '[i]ntegration.py|[p]ath_follower.py' 2>/dev/null || true
# ros_control's cmd_node streams zero commands on /cmd with no driveable
# mission branch — it would fight the follower, so it must not run during the lap
pkill -f '[r]os_control command_node|ros_control/cmd_node.py' 2>/dev/null || true
pkill -f '[r]viz2' 2>/dev/null || true
sleep 3

echo "[2/7] Building perception workspace..."
(cd "${ROOT_DIR}/perception_ws" && colcon build --symlink-install \
   --packages-select cone_detector cone_mapper landmark_slam) >/dev/null

echo "[3/7] Launching EUFS sim with real cameras (track: ${TRACK_NAME:-small_track})..."
(
  source "${EUFS_WS}/install/setup.bash"
  export EUFS_MASTER="${EUFS_WS}"
  ros2 launch eufs_launcher simulation.launch.py \
      use_sim_time:=true \
      track:="${TRACK_NAME:-small_track}" \
      robot_name:=ads-dv \
      rviz:=false \
      launch_group:=default \
      gazebo_gui:=false \
      publish_gt_tf:=false \
      pub_ground_truth:=true \
      > "${LOG_DIR}/sim_native.log" 2>&1
) &
SIM_PID=$!

until timeout 5 ros2 topic list 2>/dev/null | grep -q '/imu/data'; do
  kill -0 ${SIM_PID} 2>/dev/null || { echo "ERROR: sim died — see logs/sim_native.log"; exit 1; }
  echo "  waiting for sim topics..."
  sleep 5
done
sleep 5

# our own RViz with the racing config — the sim's rviz arg loads its default
# config instead, whose eufs plugin displays aren't built here
rviz2 -d "${ROOT_DIR}/config/racing_visualization.rviz" \
    --ros-args -p use_sim_time:=true > "${LOG_DIR}/rviz_native.log" 2>&1 &

echo "[4/7] Starting perception nodes (GPU YOLO on sim cameras)..."
(
  source "${ROOT_DIR}/perception_ws/install/setup.bash"
  ros2 run cone_detector YOLO_cone_detector --ros-args -p use_sim_time:=true \
      > "${LOG_DIR}/cone_detector.log" 2>&1 &
  ros2 run cone_mapper cone_mapper --ros-args -p use_sim_time:=true \
      > "${LOG_DIR}/cone_mapper.log" 2>&1 &
  ros2 run landmark_slam landmark_slam --ros-args -p use_sim_time:=true \
      > "${LOG_DIR}/landmark_slam.log" 2>&1 &
)
sleep 8

echo "[5/7] Starting path planner (wall clock — replan rate must not follow sim RTF)..."
python3 "${ROOT_DIR}/Path_Planning/path_planning/integration.py" \
    > "${LOG_DIR}/path_planner.log" 2>&1 &

echo "[6/7] Waiting for /planned_path..."
DEADLINE=$((SECONDS + 180))
until timeout 8 ros2 topic echo /planned_path --once >/dev/null 2>&1; do
  if (( SECONDS > DEADLINE )); then
    echo "ERROR: no /planned_path after 180 s — check logs/cone_detector.log / logs/path_planner.log"
    exit 1
  fi
  echo "  no path yet..."
  sleep 5
done
echo "  /planned_path is live."

echo "[7/7] Driving ${LAPS} lap(s) at ${SPEED} m/s off SLAM + planner..."
(
  source "${EUFS_WS}/install/setup.bash"   # eufs_msgs for SetCanState
  timeout 3000 python3 "${ROOT_DIR}/scripts/path_follower.py" \
      --laps "${LAPS}" --speed "${SPEED}" 2>&1
) | tee "${LOG_DIR}/full_lap_native_${TS}.log"

echo
echo "Log: logs/full_lap_native_${TS}.log"
grep -q 'FULL AUTONOMOUS LAP COMPLETE' "${LOG_DIR}/full_lap_native_${TS}.log" \
  && echo "RESULT: lap completed and car stopped." \
  || echo "RESULT: lap did NOT complete — see log."
