#!/usr/bin/env bash
set -euo pipefail

# Full-lap perception validation in the EUFS sim, no path planning / control
# involved: a test driver follows the ground-truth centerline while the SLAM
# validator and cone-map validator measure the perception stack.
#
# Usage:  scripts/run_lap_validation.sh [laps] [speed_mps]
#
# Produces:  logs/lap_slam_<ts>.log   (pose error vs ground truth)
#            logs/lap_map_<ts>.log    (cone map vs ground-truth track)

LAPS="${1:-1}"
SPEED="${2:-2.5}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
SLAM_LOG="${ROOT_DIR}/logs/lap_slam_${TS}.log"
MAP_LOG="${ROOT_DIR}/logs/lap_map_${TS}.log"
mkdir -p "${ROOT_DIR}/logs"
cd "${ROOT_DIR}"

echo "[1/6] Starting containers..."
docker compose up -d base perception eufs_sim
until docker exec racing_eufs_sim bash -c \
  'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic list 2>/dev/null | grep -q /imu/data'; do
  sleep 5
done

echo "[2/6] Resetting sim state..."
docker exec racing_eufs_sim bash -c '
  source /opt/ros/humble/setup.bash &&
  source /workspace/eufs_sim_humble/install/setup.bash &&
  timeout 10 ros2 service call /ros_can/reset std_srvs/srv/Trigger {} >/dev/null &&
  timeout 10 ros2 service call /ros_can/reset_vehicle_pos std_srvs/srv/Trigger {} >/dev/null'

echo "[3/6] Restarting perception nodes..."
# bracket trick: pattern must not match this command's own cmdline
docker exec racing_perception bash -c \
  "pkill -f '[c]one_detector|[c]one_mapper|[l]andmark_slam|[v]alidate_slam' || true"
sleep 2
# use_sim_time so node clocks (buffer aging etc.) follow the sim clock
for node in "cone_detector YOLO_cone_detector" "cone_mapper cone_mapper" "landmark_slam landmark_slam"; do
  docker exec -d racing_perception bash -lc \
    "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run ${node} --ros-args -p use_sim_time:=true > /workspace/logs/${node%% *}.log 2>&1"
done
sleep 12

echo "[4/6] Copying test scripts into sim container..."
docker cp "${ROOT_DIR}/scripts/lap_test_driver.py" racing_eufs_sim:/tmp/lap_test_driver.py
docker cp "${ROOT_DIR}/scripts/validate_map.py"    racing_eufs_sim:/tmp/validate_map.py
docker cp "${ROOT_DIR}/scripts/validate_slam.py"   racing_perception:/workspace/scripts/validate_slam.py

echo "[5/6] Driving ${LAPS} lap(s) at ${SPEED} m/s (slow at low RTF — be patient)..."
docker exec -d racing_perception bash -c \
  "source /opt/ros/humble/setup.bash && timeout 3600 python3 /workspace/scripts/validate_slam.py > /workspace/logs/lap_slam_current.log 2>&1"
docker exec racing_eufs_sim bash -c \
  "source /opt/ros/humble/setup.bash && source /workspace/eufs_sim_humble/install/setup.bash &&
   timeout 3000 python3 /tmp/lap_test_driver.py --laps ${LAPS} --speed ${SPEED}"
docker exec racing_perception bash -c 'pkill -INT -f validate_slam.py || true'
sleep 3
cp "${ROOT_DIR}/logs/lap_slam_current.log" "${SLAM_LOG}"

echo "[6/6] Validating cone map against ground truth..."
docker exec racing_eufs_sim bash -c \
  "source /opt/ros/humble/setup.bash && python3 /tmp/validate_map.py" | tee "${MAP_LOG}"

echo
echo "SLAM summary:"
grep -A 8 "SLAM VALIDATION SUMMARY" "${SLAM_LOG}" || echo "  (no summary — check ${SLAM_LOG})"
echo "Logs: ${SLAM_LOG}"
echo "      ${MAP_LOG}"
