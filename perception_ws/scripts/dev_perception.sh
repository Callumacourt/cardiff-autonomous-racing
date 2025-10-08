set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cardiff Autonomous Racing - Development Mode ===${NC}"
echo ""

# Get directories
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$WORKSPACE_DIR/.." &> /dev/null && pwd )"

# Container settings
CONTAINER_NAME="car-perception-dev"
IMAGE_NAME="car-perception:latest"

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker image '$IMAGE_NAME' not found!${NC}"
    echo -e "${YELLOW}Please build the image first: ./scripts/build_perception.sh${NC}"
    exit 1
fi

# Stop existing container if running
if docker ps -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${YELLOW}Stopping existing container...${NC}"
    docker stop "$CONTAINER_NAME" >/dev/null
fi

# Remove existing container if it exists
if docker ps -a -q -f name="$CONTAINER_NAME" | grep -q .; then
    echo -e "${YELLOW}Removing existing container...${NC}"
    docker rm "$CONTAINER_NAME" >/dev/null
fi

echo -e "${YELLOW}Starting development container...${NC}"
echo -e "${GREEN}Python file changes are live (no rebuild needed)${NC}"
echo -e "${GREEN}Package changes need: colcon build${NC}"
echo -e "${GREEN}Use --symlink-install for faster rebuilds${NC}"
echo ""

# Run development container
docker run -it \
    --name "$CONTAINER_NAME" \
    --rm \
    --privileged \
    --net=host \
    --ipc=host \
    --pid=host \
    -e DISPLAY=$DISPLAY \
    -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
    -v "${WORKSPACE_DIR}:/workspace/perception_ws" \
    -v "${PROJECT_ROOT}/test_data:/workspace/test_data" \
    -w /workspace/perception_ws \
    "$IMAGE_NAME" \
    bash -c "
    echo 'Development Tips:'
    echo '  colcon build --symlink-install  # Fast rebuilds'
    echo '  colcon build --packages-select PKG  # Build single package'
    echo '  source install/setup.bash  # Source after build'
    echo '  ros2 launch cone_detector cone_detector.launch.py'
    echo ''
    exec bash
    "

echo -e "${GREEN}Development session ended.${NC}"