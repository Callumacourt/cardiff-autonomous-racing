# Run script for Cardiff Autonomous Racing Perception Docker container
# This script runs the perception Docker environment with proper volume mounts

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cardiff Autonomous Racing - Perception Docker Run ===${NC}"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$WORKSPACE_DIR/.." &> /dev/null && pwd )"

# Container and image settings
CONTAINER_NAME="car-perception-dev"
IMAGE_NAME="car-perception:latest"

# Check if image exists
if ! docker image inspect "$IMAGE_NAME" >/dev/null 2>&1; then
    echo -e "${RED}Error: Docker image '$IMAGE_NAME' not found!${NC}"
    echo -e "${YELLOW}Please build the image first: ./scripts/build_perception.sh${NC}"
    exit 1
fi

# Stop and remove existing container if it exists
if docker ps -a --format 'table {{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo -e "${YELLOW}Stopping and removing existing container...${NC}"
    docker stop "$CONTAINER_NAME" >/dev/null 2>&1 || true
    docker rm "$CONTAINER_NAME" >/dev/null 2>&1 || true
fi

echo -e "${YELLOW}Starting perception container...${NC}"
echo -e "${YELLOW}Container: ${CONTAINER_NAME}${NC}"
echo -e "${YELLOW}Image: ${IMAGE_NAME}${NC}"
echo ""

# Run the container with volume mounts
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
    bash

echo -e "${GREEN}Container exited.${NC}"