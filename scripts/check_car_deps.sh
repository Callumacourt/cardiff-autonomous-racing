#!/usr/bin/env bash
# Offline dependency check for the FULL autonomy pipeline on the real car:
#   ZED camera -> GPU YOLO -> cone_mapper + landmark_slam -> planner -> follower -> ros_can
#
# Run ON the car machine. No internet needed, nothing is modified.
# Exit 0 = every check passed; nonzero = at least one FAIL (fix before the day).
#
# Usage:  scripts/check_car_deps.sh

set -o pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
ZED_WS="${ZED_WS:-$HOME/zed_ws}"
FAILS=0

pass() { echo "  PASS  $*"; }
fail() { echo "  FAIL  $*"; FAILS=$((FAILS + 1)); }
check() {  # check <description> <command...>
  local desc="$1"; shift
  if "$@" >/dev/null 2>&1; then pass "$desc"; else fail "$desc"; fi
}

echo "== ROS 2 =="
check "/opt/ros/humble exists" test -d /opt/ros/humble
source /opt/ros/humble/setup.bash 2>/dev/null || fail "sourcing ROS setup.bash"
check "ros2 CLI runs" ros2 pkg prefix rclpy
check "ackermann_msgs" python3 -c "import ackermann_msgs.msg"
check "cv_bridge imports" python3 -c "from cv_bridge import CvBridge"

echo "== GPU / YOLO =="
check "NVIDIA driver (nvidia-smi)" nvidia-smi
python3 - <<'EOF' >/dev/null 2>&1 && pass "torch CUDA + GPU kernel run" || fail "torch CUDA + GPU kernel run (wrong wheel for this GPU?)"
import torch
assert torch.cuda.is_available()
x = torch.rand(32, 32, device='cuda') @ torch.rand(32, 32, device='cuda')
assert float(x.sum()) > 0
EOF
check "ultralytics imports" python3 -c "import ultralytics"
python3 -c "import numpy; exit(0 if numpy.__version__.startswith('1.') else 1)" \
  && pass "numpy is 1.x (cv_bridge-compatible)" || fail "numpy is 2.x — breaks cv_bridge, pin 1.26.4"
check "YOLO weights at /workspace/perception_ws/models/best.pt" \
  test -s /workspace/perception_ws/models/best.pt

echo "== ZED =="
lsusb 2>/dev/null | grep -qi stereolabs \
  && pass "ZED camera detected on USB" || fail "ZED camera detected on USB (plug in / check USB3 cable)"
check "ZED SDK installed (/usr/local/zed)" test -d /usr/local/zed/lib
check "zed_ws built" test -f "${ZED_WS}/install/setup.bash"
( source "${ZED_WS}/install/setup.bash" 2>/dev/null && ros2 pkg prefix zed_wrapper >/dev/null 2>&1 ) \
  && pass "zed_wrapper package resolves" || fail "zed_wrapper package resolves"

echo "== Perception workspace =="
check "perception_ws built" test -f "${REPO_ROOT}/perception_ws/install/setup.bash"
for pkg in cone_detector cone_mapper landmark_slam; do
  ( source "${REPO_ROOT}/perception_ws/install/setup.bash" 2>/dev/null \
      && ros2 pkg prefix "$pkg" >/dev/null 2>&1 ) \
    && pass "package $pkg" || fail "package $pkg (rebuild perception_ws)"
done

echo "== Control workspace (ros_can + eufs_msgs) =="
check "Control install exists" test -f "${REPO_ROOT}/Control/install/setup.bash"
( source "${REPO_ROOT}/Control/install/setup.bash" 2>/dev/null \
    && ros2 pkg prefix ros_can >/dev/null 2>&1 ) \
  && pass "ros_can package" || fail "ros_can package (build Control workspace)"
( source "${REPO_ROOT}/Control/install/setup.bash" 2>/dev/null \
    && python3 -c "from eufs_msgs.msg import CanState; from eufs_msgs.srv import SetCanState" ) \
  && pass "eufs_msgs python imports" || fail "eufs_msgs python imports"

echo "== Planner + follower =="
check "planner compiles" python3 -m py_compile "${REPO_ROOT}/Path_Planning/path_planning/integration.py"
check "follower compiles" python3 -m py_compile "${REPO_ROOT}/scripts/path_follower.py"
( source "${REPO_ROOT}/Control/install/setup.bash" 2>/dev/null \
    && python3 -c "
import sys; sys.argv=['x','--help']
import importlib.util
spec = importlib.util.spec_from_file_location('pf', '${REPO_ROOT}/scripts/path_follower.py')
m = importlib.util.module_from_spec(spec)
try:
    spec.loader.exec_module(m)
except SystemExit:
    pass" ) \
  && pass "follower imports resolve (eufs_msgs, ackermann, geometry)" \
  || fail "follower imports resolve"

echo
if [ "${FAILS}" -eq 0 ]; then
  echo "ALL CHECKS PASSED — pipeline dependencies are ready."
else
  echo "${FAILS} CHECK(S) FAILED — fix before running on the car (see ON_CAR_SETUP.md)."
fi
exit "${FAILS}"
