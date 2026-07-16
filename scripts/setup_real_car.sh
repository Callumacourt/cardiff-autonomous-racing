#!/usr/bin/env bash
# One-press perception bringup for the FS-AI car — native, no Docker.
# Automates ON_CAR_SETUP.md steps 1-8: ZED SDK, wrapper build, model path,
# perception build, ZED camera + perception launch, health check.
#
# Usage:
#   ./setup_real_car.sh          set everything up and launch
#   ./setup_real_car.sh stop     stop perception + camera
#
# Only run this ON the car, booted from the SSD — the ZED SDK step installs
# kernel-linked components (dkms) that must target the running kernel.
# ros_can is Control's node — launch it per ON_CAR_SETUP.md step 7B;
# this script only checks that its topics are alive.

set -o pipefail

# ---------------------------------------------------------------------------
# Configuration — confirm topic names on the day (ros2 topic list | grep zed)
# ---------------------------------------------------------------------------
RGB_TOPIC="/zed/zed_node/rgb/image_rect_color"
DEPTH_TOPIC="/zed/zed_node/depth/depth_registered"
CAMERA_INFO_TOPIC="/zed/zed_node/left/camera_info"
IMU_TOPIC="/ros_can/imu"          # ADS-DV onboard IMU via ros_can
CAMERA_X_OFFSET="0.0"             # metres forward of car reference — measure
CAMERA_Y_OFFSET="0.0"             # metres left of car reference   — and edit!
CAMERA_MODEL="zed2"
ZED_WS="$HOME/zed_ws"
INSTALLERS_DIR="$HOME/installers"
CAMERA_STARTUP_TIMEOUT=45         # s to wait for ZED topics after launch

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
WS="$REPO_ROOT/perception_ws"
MODEL_SRC="$WS/models/best.pt"
MODEL_DST="/workspace/perception_ws/models/best.pt"   # fixed path in detector
LOG_DIR="$REPO_ROOT/logs/real_car/$(date +%Y%m%d_%H%M%S)"
PKGS="cone_detector cone_mapper landmark_slam"

die()  { echo "ERROR: $*" >&2; exit 1; }
step() { echo; echo "==> $*"; }

stop_nodes() {
  pkill -f '[Y]OLO_cone_detector' && echo "  stopped cone_detector" || echo "  cone_detector not running"
  pkill -f '[l]andmark_slam'      && echo "  stopped landmark_slam"  || echo "  landmark_slam not running"
  pkill -f '[c]one_mapper'        && echo "  stopped cone_mapper"    || echo "  cone_mapper not running"
}

if [ "${1:-}" = "stop" ]; then
  step "Stopping perception + camera"
  stop_nodes
  pkill -f '[z]ed_camera.launch.py' && echo "  stopped zed camera" || echo "  zed camera not running"
  exit 0
fi

# ---------------------------------------------------------------------------
# 1. ROS 2 environment
# ---------------------------------------------------------------------------
step "Sourcing ROS 2 Humble"
[ -f /opt/ros/humble/setup.bash ] \
  || die "ROS 2 Humble missing — this SSD should have it preinstalled, see ON_CAR_SETUP.md"
source /opt/ros/humble/setup.bash
export ROS_DOMAIN_ID=0
export RMW_IMPLEMENTATION=rmw_fastrtps_cpp

step "Checking python dependencies"
python3 -c "import torch, ultralytics, cv2, scipy, cv_bridge, message_filters, sensor_msgs_py" 2>/dev/null \
  || die "python deps missing — install offline from ~/installers per ON_CAR_SETUP.md"
python3 - <<'EOF'
import torch
print(f"  torch {torch.__version__}, CUDA available: {torch.cuda.is_available()}"
      + (f" ({torch.cuda.get_device_name(0)})" if torch.cuda.is_available() else " — YOLO will be SLOW on CPU"))
EOF

# ---------------------------------------------------------------------------
# 2. ZED SDK (ON_CAR_SETUP.md steps 2-4) — one-time. Installs dkms/kernel-linked
#    components, so this must run on the car's actual booted kernel, not a
#    chroot. Skips the NVIDIA driver (580 is already installed) and the AI
#    object-detection module downloads (we run our own YOLO).
# ---------------------------------------------------------------------------
step "ZED SDK"
if [ -d /usr/local/zed ]; then
  echo "  already installed"
else
  echo "  installing ZED wrapper .debs..."
  if ls "$INSTALLERS_DIR"/wrapper_debs/*.deb >/dev/null 2>&1; then
    sudo dpkg -i "$INSTALLERS_DIR"/wrapper_debs/*.deb \
      || { echo "  dpkg reported missing deps, trying apt -f install (needs internet)..."; sudo apt -f install -y; }
  else
    echo "  no wrapper .debs found in $INSTALLERS_DIR/wrapper_debs — skipping"
  fi

  ZED_INSTALLER=$(ls "$INSTALLERS_DIR"/ZED_SDK_*cuda12.8*.run 2>/dev/null | head -1)
  [ -n "$ZED_INSTALLER" ] || ZED_INSTALLER=$(ls "$INSTALLERS_DIR"/ZED_SDK_*.run 2>/dev/null | head -1)
  [ -n "$ZED_INSTALLER" ] || die "no ZED SDK installer (.run) found in $INSTALLERS_DIR"

  echo "  running $(basename "$ZED_INSTALLER")"
  echo "  (skipping driver reinstall — 580 is already installed; skipping AI-module download)"
  chmod +x "$ZED_INSTALLER"
  "$ZED_INSTALLER" -- silent skip_drivers skip_od_module
  if [ ! -d /usr/local/zed ]; then
    die "ZED SDK install did not produce /usr/local/zed — rerun interactively (./$( basename "$ZED_INSTALLER" )) to see the failure, or try the fallback installer per ON_CAR_SETUP.md step 4"
  fi
  echo "  installed"
fi

# ---------------------------------------------------------------------------
# 3. YOLO weights at the detector's fixed path (ON_CAR_SETUP.md step 1)
# ---------------------------------------------------------------------------
step "YOLO weights -> $MODEL_DST"
[ -f "$MODEL_SRC" ] || die "weights not found at $MODEL_SRC"
if [ -f "$MODEL_DST" ] && cmp -s "$MODEL_SRC" "$MODEL_DST"; then
  echo "  already up to date"
else
  { mkdir -p "$(dirname "$MODEL_DST")" && cp "$MODEL_SRC" "$MODEL_DST"; } 2>/dev/null \
    || { echo "  needs sudo:"; sudo mkdir -p "$(dirname "$MODEL_DST")" && sudo cp "$MODEL_SRC" "$MODEL_DST"; } \
    || die "could not copy weights to $MODEL_DST"
  echo "  copied"
fi

# ---------------------------------------------------------------------------
# 4. Build perception (ON_CAR_SETUP.md step 6; incremental, fast if unchanged)
# ---------------------------------------------------------------------------
step "Building perception workspace ($PKGS)"
cd "$WS"
colcon build --symlink-install --packages-select $PKGS || die "colcon build failed"
source "$WS/install/setup.bash"

# ---------------------------------------------------------------------------
# 5. ZED camera (ON_CAR_SETUP.md step 5 + 7A) — build wrapper if needed,
#    launch only if not already up
# ---------------------------------------------------------------------------
mkdir -p "$LOG_DIR"
topic_up() { ros2 topic list 2>/dev/null | grep -qx "$1"; }

step "ZED camera"
if topic_up "$RGB_TOPIC"; then
  echo "  already publishing"
else
  if [ ! -f "$ZED_WS/install/setup.bash" ]; then
    echo "  wrapper not built yet — building (ON_CAR_SETUP.md step 5)..."
    [ -d "$ZED_WS/src/zed-ros2-wrapper" ] \
      || die "$ZED_WS/src has no zed-ros2-wrapper — clone it per ON_CAR_SETUP.md step 5 first"
    ( cd "$ZED_WS" && colcon build --symlink-install --cmake-args=-DCMAKE_BUILD_TYPE=Release ) \
      || die "zed_wrapper build failed"
  fi
  echo "  launching zed_wrapper ($CAMERA_MODEL)..."
  source "$ZED_WS/install/setup.bash"
  nohup ros2 launch zed_wrapper zed_camera.launch.py camera_model:="$CAMERA_MODEL" \
    >"$LOG_DIR/zed_camera.log" 2>&1 &
  waited=0
  until topic_up "$RGB_TOPIC"; do
    sleep 3; waited=$((waited+3))
    [ "$waited" -ge "$CAMERA_STARTUP_TIMEOUT" ] \
      && die "camera topics not up after ${CAMERA_STARTUP_TIMEOUT}s — check $LOG_DIR/zed_camera.log and that the ZED is plugged into USB3"
    echo "  waiting for $RGB_TOPIC (${waited}s)..."
  done
  echo "  camera up"
fi

# ---------------------------------------------------------------------------
# 6. Launch perception (ON_CAR_SETUP.md step 7C)
# ---------------------------------------------------------------------------
step "Restarting perception nodes (logs: $LOG_DIR)"
stop_nodes
sleep 1

nohup ros2 run cone_detector YOLO_cone_detector --ros-args \
    -p rgb_topic:="$RGB_TOPIC" \
    -p depth_topic:="$DEPTH_TOPIC" \
    -p camera_info_topic:="$CAMERA_INFO_TOPIC" \
    >"$LOG_DIR/cone_detector.log" 2>&1 &
PID_DETECTOR=$!

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
# 7. Health check (ON_CAR_SETUP.md step 8)
# ---------------------------------------------------------------------------
step "Health check (waiting 10s for nodes to come up)"
sleep 10

FAIL=0
for entry in "cone_detector:$PID_DETECTOR" "landmark_slam:$PID_SLAM" "cone_mapper:$PID_MAPPER"; do
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
check_topic "$RGB_TOPIC"        "camera not publishing"
check_topic "/ros_can/imu"      "launch ros_can (ON_CAR_SETUP.md step 7B) — SLAM needs the IMU"
check_topic "/ros_can/twist"    "no velocity source: SLAM position will drift while moving"
check_topic "/cone_cloud/local" "detector not publishing yet (first YOLO inference can take a moment)"
check_topic "/odometry/slam"    "SLAM not publishing (needs IMU messages first)"

echo
if [ "$FAIL" -eq 0 ]; then
  echo "=== Perception up. Outputs: /odometry/slam, /cone_map/local, /cone_map/global ==="
  echo "=== Logs: $LOG_DIR ==="
  echo "=== Rates: ros2 topic hz /cone_cloud/local ; ros2 topic hz /odometry/slam ==="
  echo "=== Between runs: scripts/wipe_run_data.sh ==="
else
  echo "=== PROBLEMS FOUND — see logs above ==="
  exit 1
fi
