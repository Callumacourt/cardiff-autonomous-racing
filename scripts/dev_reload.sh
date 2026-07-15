#!/usr/bin/env bash
# Rebuild and restart one perception package after a code change, without
# restarting the whole stack.

set -euo pipefail

usage() {
  cat <<EOF
Usage:
  $0 [--no-build] run <package> <node_executable> [container]
  $0 [--no-build] launch <package> <launch_file> [container]

Options:
  --no-build    Skip colcon build (useful for Python edits)
  package       ROS package name
  node_executable
                Executable name for 'ros2 run <package> <node_executable>'
  launch_file   Launch filename for 'ros2 launch <package> <launch_file>'
  container     Docker container name (default: racing_perception)
EOF
  exit 1
}

NO_BUILD=false
if [ "${1:-}" == "--no-build" ]; then
  NO_BUILD=true
  shift
fi

[ $# -ge 3 ] || usage

MODE="$1"; shift
PKG="$1"; shift
TARGET="$1"; shift
CONTAINER="${1:-racing_perception}"
WORKSPACE_DIR="/workspace/perception_ws"

echo "Mode: $MODE  Package: $PKG  Target: $TARGET  Container: $CONTAINER  No-build: $NO_BUILD"

if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER}$"; then
  echo "ERROR: container '${CONTAINER}' not running"
  exit 2
fi

if ! $NO_BUILD; then
  echo "Building package ${PKG} inside ${CONTAINER}..."
  docker exec "$CONTAINER" bash -lc "source /opt/ros/humble/setup.bash && cd ${WORKSPACE_DIR} && colcon build --symlink-install --packages-select ${PKG}"
fi

sleep 0.5

if [ "$MODE" = "run" ]; then
  NODE="$TARGET"
  echo "Stopping running processes matching '${NODE}'..."
  docker exec "$CONTAINER" bash -lc "pkill -f \"ros2 run ${PKG} ${NODE}\" || pkill -f \"${NODE}\" || true"
  sleep 0.5
  echo "Starting node: ros2 run ${PKG} ${NODE}"
  docker exec -d "$CONTAINER" bash -lc "source /opt/ros/humble/setup.bash && source ${WORKSPACE_DIR}/install/setup.bash && ros2 run ${PKG} ${NODE}"
  echo "Started."
  exit 0
fi

if [ "$MODE" = "launch" ]; then
  LAUNCH_FILE="$TARGET"
  echo "Stopping any launch matching 'ros2 launch ${PKG} ${LAUNCH_FILE}'..."
  docker exec "$CONTAINER" bash -lc "pkill -f \"ros2 launch ${PKG} ${LAUNCH_FILE}\" || true"
  sleep 0.5
  echo "Starting launch: ros2 launch ${PKG} ${LAUNCH_FILE}"
  docker exec -d "$CONTAINER" bash -lc "source /opt/ros/humble/setup.bash && source ${WORKSPACE_DIR}/install/setup.bash && ros2 launch ${PKG} ${LAUNCH_FILE}"
  echo "Started."
  exit 0
fi

usage