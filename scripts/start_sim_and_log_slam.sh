#!/usr/bin/env bash
set -euo pipefail

# Quick smoke test: start the stack, restart perception nodes, print topic
# rates, sample SLAM error for a few seconds. Use this after a code change
# to check nothing is obviously broken.
#
# For a full accuracy check (autonomous lap + cone map vs ground truth),
# use run_lap_validation.sh instead.
#
# Usage:
#   scripts/start_sim_and_log_slam.sh [duration_seconds]
# Example:
#   scripts/start_sim_and_log_slam.sh 30

DURATION="${1:-20}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="${ROOT_DIR}/logs"
TS="$(date +%Y%m%d_%H%M%S)"
LOG_FILE="${LOG_DIR}/slam_validation_${TS}.log"

mkdir -p "${LOG_DIR}"

cd "${ROOT_DIR}"

echo "[1/5] Starting containers..."
docker compose up -d base perception eufs_sim
sleep 10

echo "[2/5] Restarting perception nodes cleanly..."
docker exec racing_perception bash -lc "ps -eo pid,args | grep -E '[r]os2 run cone_detector YOLO_cone_detector|[r]os2 run cone_mapper cone_mapper|[r]os2 run landmark_slam landmark_slam' | awk '{print \$1}' | xargs -r kill || true"

sleep 1

for node in "cone_detector YOLO_cone_detector" "cone_mapper cone_mapper" "landmark_slam landmark_slam"; do
  docker exec -d racing_perception bash -lc \
    "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run ${node} --ros-args -p use_sim_time:=true"
done

sleep 3

echo "[3/5] Health checks..."
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && ros2 node list | grep -E "landmark_slam|cone_mapper|yolo" || true'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /odometry/slam || true'
docker exec racing_perception bash -lc 'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /cone_map/local || true'

echo "[4/5] Running SLAM validator for ${DURATION}s..."
echo "Logging to: ${LOG_FILE}"
docker exec racing_perception bash -lc "source /opt/ros/humble/setup.bash && timeout ${DURATION} python3 /workspace/scripts/validate_slam.py" | tee "${LOG_FILE}"

echo "[5/5] Done."
echo "Log saved: ${LOG_FILE}"
echo "Tip: grep 'SLAM VALIDATION SUMMARY' -A 8 ${LOG_FILE}"
