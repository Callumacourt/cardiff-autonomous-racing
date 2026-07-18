#!/usr/bin/env bash
# Perception bringup against IPG CarMaker (FSAI comp, office 13 rig).
# Adapted from setup_real_car.sh, MINUS anything camera-driver/dkms specific —
# CarMaker is not a physical camera, so there's no SDK to install here. This
# script assumes CarMaker (and whatever ROS2 bridge it uses) is already
# started by whoever runs the rig; our job is just to build + launch
# perception against whatever topics that bridge publishes.
#
# We don't yet know CarMaker's exact topic names, domain ID, or whether it
# provides simulated camera/depth at all — CONFIRM ALL OF THE BELOW ON THE DAY
# with `ros2 topic list` before trusting this script's defaults.
#
# Usage:
#   ./setup_carmaker_sim.sh          build + launch perception
#   ./setup_carmaker_sim.sh stop     stop perception nodes

set -o pipefail

# ---------------------------------------------------------------------------
# Configuration — CONFIRM ALL OF THIS ON THE DAY (ros2 topic list, ros2 doctor
# --report for domain/RMW). Nothing here is verified against the real rig yet.
# ---------------------------------------------------------------------------
ROS_DOMAIN_ID_VAL=0                 # match whatever the CarMaker bridge uses
RMW_IMPLEMENTATION_VAL=rmw_fastrtps_cpp

# Set to false if CarMaker gives no simulated camera/depth — script will then
# only run landmark_slam + cone_mapper against vehicle state, skipping the
# detector entirely.
RUN_DETECTOR=true

RGB_TOPIC="/zed/zed_node/rgb/image_rect_color"
DEPTH_TOPIC="/zed/zed_node/depth/depth_registered"
CAMERA_INFO_TOPIC="/zed/zed_node/left/camera_info"
VELOCITY_TOPIC="/ros_can/twist"     # or /gps_controller/vel-style topic — confirm
IMU_TOPIC="/ros_can/imu"
CAMERA_X_OFFSET="0.0"
CAMERA_Y_OFFSET="0.0"

TOPIC_WAIT_TIMEOUT=30                # s to wait for upstream topics to appear

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WS="$REPO_ROOT/perception_ws"
LOG_DIR="$REPO_ROOT/logs/carmaker_sim/$(date +%Y%m%d_%H%M%S)"
PKGS="cone_detector cone_mapper landmark_slam"

die()  { echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "==> $*"; }

stop_nodes() {
  pkill -f '[Y]OLO_cone_detector' && echo "  stopped cone_detector" || echo "  cone_detector not running"
  pkill -f '[l]andmark_slam'      && echo "  stopped landmark_slam"  || echo "  landmark_slam not running"
  pkill -f '[c]one_mapper'        && echo "  stopped cone_mapper"    || echo "  cone_mapper not running"
}

if [ "${1:-}" = "stop" ]; then
  step "Stopping perception"
  stop_nodes
  exit 0
fi

# ---------------------------------------------------------------------------
# 1. ROS 2 environment
# ---------------------------------------------------------------------------
step "Sourcing ROS 2 Humble"
[ -f /opt/ros/humble/setup.bash ] || die "ROS 2 Humble not found on this machine"
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID="$ROS_DOMAIN_ID_VAL"
export RMW_IMPLEMENTATION="$RMW_IMPLEMENTATION_VAL"

step "Checking python dependencies"
python3 -c "import torch, ultralytics, cv2, scipy, cv_bridge, message_filters, sensor_msgs_py" 2>/dev/null \
  || die "python deps missing — see ON_CAR_SETUP.md for the offline installer list"

# ---------------------------------------------------------------------------
# 2. Build perception (native colcon build, same as setup_real_car.sh — if
#    the venue rig actually runs perception in Docker instead, swap this
#    section for a `docker compose up` + `docker exec` flow like
#    start_sim_and_log_slam.sh does)
# ---------------------------------------------------------------------------
step "Building perception workspace ($PKGS)"
cd "$WS"
colcon build --symlink-install --packages-select $PKGS || die "colcon build failed"
source "$WS/install/setup.bash"

mkdir -p "$LOG_DIR"
topic_up() { ros2 topic list 2>/dev/null | grep -qx "$1"; }

wait_for_topic() {
  local topic="$1" waited=0
  until topic_up "$topic"; do
    sleep 2; waited=$((waited+2))
    [ "$waited" -ge "$TOPIC_WAIT_TIMEOUT" ] && return 1
    echo "  waiting for $topic (${waited}s)..."
  done
  return 0
}

# ---------------------------------------------------------------------------
# 3. Wait for CarMaker's own topics — this script does NOT start CarMaker or
#    any bridge; that must already be running (rig operator's side).
# ---------------------------------------------------------------------------
step "Waiting for CarMaker vehicle-state topics"
wait_for_topic "$IMU_TOPIC" \
  || die "$IMU_TOPIC never appeared — is CarMaker + its ROS2 bridge running? check ROS_DOMAIN_ID/RMW match"
echo "  IMU topic up"

if [ "$RUN_DETECTOR" = true ]; then
  step "Waiting for CarMaker camera topics"
  wait_for_topic "$RGB_TOPIC" \
    || die "$RGB_TOPIC never appeared — set RUN_DETECTOR=false at the top of this script if CarMaker has no camera sim"
  for t in "$DEPTH_TOPIC" "$CAMERA_INFO_TOPIC"; do
    topic_up "$t" || die "$t not being published — fix the topic name near the top of this script"
  done
  echo "  camera topics up"
fi

# ---------------------------------------------------------------------------
# 4. Launch perception
# ---------------------------------------------------------------------------
step "Restarting perception nodes (logs: $LOG_DIR)"
stop_nodes
sleep 1

if [ "$RUN_DETECTOR" = true ]; then
  nohup ros2 run cone_detector YOLO_cone_detector --ros-args \
      -p rgb_topic:="$RGB_TOPIC" \
      -p depth_topic:="$DEPTH_TOPIC" \
      -p camera_info_topic:="$CAMERA_INFO_TOPIC" \
      >"$LOG_DIR/cone_detector.log" 2>&1 &
  PID_DETECTOR=$!
fi

nohup ros2 run landmark_slam landmark_slam --ros-args \
    -p imu_topic:="$IMU_TOPIC" \
    -p camera_x_offset:="$CAMERA_X_OFFSET" \
    -p camera_y_offset:="$CAMERA_Y_OFFSET" \
    >"$LOG_DIR/landmark_slam.log" 2>&1 &
PID_SLAM=$!

nohup ros2 run cone_mapper cone_mapper \
    >"$LOG_DIR/cone_mapper.log" 2>&1 &
PID_MAPPER=$!

# ---------------------------------------------------------------------------
# 5. Health check
# ---------------------------------------------------------------------------
step "Health check (waiting 10s for nodes to come up)"
sleep 10

FAIL=0
entries=("landmark_slam:$PID_SLAM" "cone_mapper:$PID_MAPPER")
[ "$RUN_DETECTOR" = true ] && entries+=("cone_detector:$PID_DETECTOR")
for entry in "${entries[@]}"; do
  name="${entry%%:*}"; pid="${entry##*:}"
  if kill -0 "$pid" 2>/dev/null; then
    echo "  OK    $name running (pid $pid)"
  else
    echo "  FAIL  $name died — check $LOG_DIR/$name.log"
    FAIL=1
  fi
done

check_topic() {
  if topic_up "$1"; then echo "  OK    $1"; else echo "  WARN  $1 missing — $2"; fi
}
check_topic "$IMU_TOPIC"        "SLAM needs the IMU"
check_topic "$VELOCITY_TOPIC"   "no velocity source: SLAM position will drift while moving"
[ "$RUN_DETECTOR" = true ] && check_topic "/cone_cloud/local" "detector not publishing yet (first YOLO inference can take a moment)"
check_topic "/odometry/slam"    "SLAM not publishing (needs IMU messages first)"

echo
if [ "$FAIL" -eq 0 ]; then
  echo "=== Perception up against CarMaker. Outputs: /odometry/slam, /cone_map/local, /cone_map/global ==="
  echo "=== Logs: $LOG_DIR ==="
else
  echo "=== PROBLEMS FOUND — see logs above ==="
  exit 1
fi
