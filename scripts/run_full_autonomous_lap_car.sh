#!/usr/bin/env bash
# Full autonomy pipeline on the REAL CAR (ZED2 + ros_can, native, no docker):
#   ros_can -> ZED camera -> GPU YOLO -> cone_mapper + landmark_slam
#     -> path planner (/planned_path) -> pure-pursuit follower (/cmd)
#
# The follower runs in --real-car mode: it never calls set_mission — select
# the mission on the car's AMI panel; driving starts when ros_can reports
# AS:DRIVING and stops after [laps] or via EBS/RES as normal.
#
# Camera + perception bringup is delegated to setup_real_car.sh (which also
# health-checks the ZED topics). One-time installs: ON_CAR_SETUP.md steps 2-5.
#
# Usage:  scripts/run_full_autonomous_lap_car.sh [laps] [speed_mps]
#         scripts/run_full_autonomous_lap_car.sh stop

LAPS="${1:-1}"
SPEED="${2:-2.0}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
LOG_DIR="${REPO_ROOT}/logs/real_car_lap_$(date +%Y%m%d_%H%M%S)"

set -o pipefail
source /opt/ros/humble/setup.bash

if [ "${1:-}" = "stop" ]; then
  pkill -f '[p]ath_follower.py'
  pkill -f '[i]ntegration.py'
  "${SCRIPT_DIR}/setup_real_car.sh" stop
  echo "Follower, planner and perception stopped. ros_can left running."
  exit 0
fi

mkdir -p "${LOG_DIR}"

echo "[1/6] Checking dependencies..."
"${SCRIPT_DIR}/check_car_deps.sh" || { echo "ABORT: fix the failed checks first."; exit 1; }

echo "[2/6] Making sure no conflicting controller is running..."
# Control's command_node publishes zero-commands on /cmd with no driveable
# mission branch — it must not run alongside the follower.
if pgrep -f 'ros_control.*command_node|[c]md_node.py' >/dev/null; then
  pkill -f 'ros_control.*command_node|[c]md_node.py'
  echo "  stopped a running command_node (conflicts with the follower on /cmd)"
fi
pkill -f '[p]ath_follower.py' 2>/dev/null
pkill -f '[i]ntegration.py' 2>/dev/null

echo "[3/6] ros_can..."
source "${REPO_ROOT}/Control/install/setup.bash"
if timeout 5 ros2 topic list 2>/dev/null | grep -q '/ros_can/state_str'; then
  echo "  ros_can already running."
else
  nohup ros2 launch ros_can ros_can.launch.py > "${LOG_DIR}/ros_can.log" 2>&1 &
  sleep 5
  timeout 10 ros2 topic list 2>/dev/null | grep -q '/ros_can/state_str' \
    || { echo "ABORT: ros_can did not come up (CAN interface? see ${LOG_DIR}/ros_can.log)"; exit 1; }
fi

echo "[4/6] Camera + perception (setup_real_car.sh)..."
"${SCRIPT_DIR}/setup_real_car.sh" || { echo "ABORT: perception bringup failed."; exit 1; }

echo "[5/6] Path planner (wall clock)..."
python3 "${REPO_ROOT}/Path_Planning/path_planning/integration.py" \
    > "${LOG_DIR}/path_planner.log" 2>&1 &

DEADLINE=$((SECONDS + 120))
until timeout 8 ros2 topic echo /planned_path --once >/dev/null 2>&1; do
  if (( SECONDS > DEADLINE )); then
    echo "ABORT: no /planned_path after 120 s — is the camera seeing cones?"
    exit 1
  fi
  echo "  waiting for /planned_path (point the car at cones)..."
  sleep 5
done
echo "  /planned_path is live."

echo "[6/6] Follower armed — select the mission on the AMI panel and start."
echo "      The car drives when ros_can reports AS:DRIVING; EBS/RES stops it as normal."
python3 "${REPO_ROOT}/scripts/path_follower.py" \
    --real-car --laps "${LAPS}" --speed "${SPEED}" 2>&1 \
  | tee "${LOG_DIR}/follower.log"

grep -q 'FULL AUTONOMOUS LAP COMPLETE' "${LOG_DIR}/follower.log" \
  && echo "RESULT: lap completed and car stopped." \
  || echo "RESULT: follower exited without completing — see ${LOG_DIR}/follower.log"
