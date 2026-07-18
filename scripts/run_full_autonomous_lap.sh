#!/usr/bin/env bash
set -euo pipefail

# Full-stack autonomous lap in the EUFS sim:
#   perception  (YOLO cone_detector + cone_mapper + landmark_slam)
#     -> path_planning  (Path_Planning/path_planning/integration.py -> /planned_path)
#       -> control commands  (scripts/path_follower.py -> /cmd, pure pursuit)
#
# No ground truth is used to drive: pose comes from SLAM, the path from the
# planner. RViz (launched by the sim container) shows the live cone map, the
# SLAM pose and the green /planned_path while the car laps.
#
# Usage:  scripts/run_full_autonomous_lap.sh [laps] [speed_mps]

LAPS="${1:-1}"
SPEED="${2:-2.0}"
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TS="$(date +%Y%m%d_%H%M%S)"
mkdir -p "${ROOT_DIR}/logs"
cd "${ROOT_DIR}"

# [0/7] Prefer the native docker engine: it holds the original car-* images
# and, unlike Docker Desktop's VM, its containers can reach the host X server
# for RViz.
if [ -z "${DOCKER_HOST:-}" ] && [ -S /var/run/docker.sock ] \
   && DOCKER_HOST=unix:///var/run/docker.sock docker image inspect car-eufs >/dev/null 2>&1; then
  export DOCKER_HOST=unix:///var/run/docker.sock
  echo "[0/7] Using native docker engine (car-* images + X display)"
fi

# Reuse previously built images under the names compose expects, so a
# missing tag doesn't trigger a multi-GB rebuild.
for pair in \
    car-perception=cardiff-autonomous-racing-perception \
    car-eufs=cardiff-autonomous-racing-eufs_sim \
    car-control=cardiff-autonomous-racing-control \
    car-planning=cardiff-autonomous-racing-path_planning; do
  want="${pair%%=*}"; src="${pair#*=}"
  if ! docker image inspect "${want}" >/dev/null 2>&1 \
     && docker image inspect "${src}" >/dev/null 2>&1; then
    echo "[0/7] Tagging ${src} as ${want}"
    docker tag "${src}" "${want}"
  fi
done

echo "[1/7] Starting containers..."
docker compose up -d base perception eufs_sim
until docker exec racing_eufs_sim bash -c \
  'source /opt/ros/humble/setup.bash && timeout 5 ros2 topic list 2>/dev/null | grep -q /imu/data'; do
  echo "  waiting for sim topics..."
  sleep 5
done

echo "[2/7] Resetting sim state (non-fatal if freshly started)..."
docker exec racing_eufs_sim bash -c '
  source /opt/ros/humble/setup.bash &&
  source /workspace/eufs_sim_humble/install/setup.bash &&
  ros2 daemon stop >/dev/null 2>&1;
  timeout 15 ros2 service call /ros_can/reset std_srvs/srv/Trigger {} >/dev/null &&
  timeout 15 ros2 service call /ros_can/reset_vehicle_pos std_srvs/srv/Trigger {} >/dev/null' \
  || echo "  (reset skipped — continuing with current sim state)"

echo "[3/7] Building + restarting perception nodes..."
docker exec racing_perception bash -lc \
  'source /opt/ros/humble/setup.bash && cd /workspace/perception_ws &&
   colcon build --symlink-install --packages-select cone_detector cone_mapper landmark_slam' \
  >/dev/null
docker exec racing_perception bash -c \
  "pkill -f '[c]one_detector|[c]one_mapper|[l]andmark_slam|[i]ntegration.py' || true"
sleep 2
for node in "cone_detector YOLO_cone_detector" "cone_mapper cone_mapper" "landmark_slam landmark_slam"; do
  docker exec -d racing_perception bash -lc \
    "source /opt/ros/humble/setup.bash && source /workspace/perception_ws/install/setup.bash && ros2 run ${node} --ros-args -p use_sim_time:=true > /workspace/logs/${node%% *}.log 2>&1"
done
sleep 10

echo "[4/7] Starting path planner..."
docker exec racing_perception mkdir -p /tmp/planner
docker cp "${ROOT_DIR}/Path_Planning/path_planning/integration.py" racing_perception:/tmp/planner/integration.py
docker cp "${ROOT_DIR}/Path_Planning/path_planning/tum_wrapper.py"  racing_perception:/tmp/planner/tum_wrapper.py
# wall clock on purpose: the 5 Hz replan timer must not slow with sim RTF,
# or the follower sees a stale path and brakes
docker exec -d racing_perception bash -lc \
  'source /opt/ros/humble/setup.bash && cd /tmp/planner &&
   python3 integration.py > /workspace/logs/path_planner.log 2>&1'

echo "[5/7] Waiting for /planned_path (perception must map the first cones)..."
DEADLINE=$((SECONDS + 180))
until docker exec racing_perception bash -c \
  'source /opt/ros/humble/setup.bash && timeout 10 ros2 topic echo /planned_path --once >/dev/null 2>&1'; do
  if (( SECONDS > DEADLINE )); then
    echo "ERROR: no /planned_path after 180 s — check logs/cone_detector.log and logs/path_planner.log"
    exit 1
  fi
  echo "  no path yet..."
  sleep 5
done
echo "  /planned_path is live."

echo "[6/7] Driving ${LAPS} lap(s) at ${SPEED} m/s off SLAM + planner (slow at low RTF — be patient)..."
docker cp "${ROOT_DIR}/scripts/path_follower.py" racing_eufs_sim:/tmp/path_follower.py
docker exec racing_eufs_sim bash -c \
  "source /opt/ros/humble/setup.bash && source /workspace/eufs_sim_humble/install/setup.bash &&
   timeout 3000 python3 /tmp/path_follower.py --laps ${LAPS} --speed ${SPEED}" \
  | tee "${ROOT_DIR}/logs/full_lap_${TS}.log"

echo "[7/7] Post-run topic health:"
for t in /odometry/slam /cone_map/local /planned_path; do
  docker exec racing_perception bash -c \
    "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz $t 2>/dev/null | tail -1" \
    | sed "s|^|  $t : |" || true
done

echo
echo "Log: logs/full_lap_${TS}.log"
grep -q 'FULL AUTONOMOUS LAP COMPLETE' "${ROOT_DIR}/logs/full_lap_${TS}.log" \
  && echo "RESULT: lap completed and car stopped." \
  || echo "RESULT: lap did NOT complete — see log."
