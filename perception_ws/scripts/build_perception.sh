# Build script for Cardiff Autonomous Racing Perception Docker image
# This script builds the perception Docker environment with all dependencies

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Cardiff Autonomous Racing - Perception Docker Build ===${NC}"
echo ""

# Get the directory of this script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
WORKSPACE_DIR="$( cd "$SCRIPT_DIR/.." &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "$WORKSPACE_DIR/.." &> /dev/null && pwd )"

# Image name and tag
IMAGE_NAME="car-perception"
IMAGE_TAG="latest"
FULL_IMAGE_NAME="${IMAGE_NAME}:${IMAGE_TAG}"

echo -e "${YELLOW}Building Docker image: ${FULL_IMAGE_NAME}${NC}"
echo -e "${YELLOW}Workspace: ${WORKSPACE_DIR}${NC}"
echo -e "${YELLOW}Project root: ${PROJECT_ROOT}${NC}"
echo ""

# Check if Dockerfile exists
DOCKERFILE_PATH="${PROJECT_ROOT}/docker/Dockerfile.perception"
if [ ! -f "$DOCKERFILE_PATH" ]; then
    echo -e "${RED}Error: Dockerfile.perception not found at ${DOCKERFILE_PATH}${NC}"
    exit 1
fi

# Build the Docker image
echo -e "${YELLOW}Building Docker image...${NC}"
cd "$PROJECT_ROOT"

docker build \
    -f docker/Dockerfile.perception \
    -t "$FULL_IMAGE_NAME" \
    --build-arg BUILDKIT_INLINE_CACHE=1 \
    .

if [ $? -eq 0 ]; then
    echo ""
    echo -e "${GREEN} Docker image built successfully!${NC}"
    echo -e "${GREEN}Image: ${FULL_IMAGE_NAME}${NC}"
    echo ""
    echo -e "${YELLOW}Next steps:${NC}"
    echo "  1. Run the container: ./scripts/run_perception.sh"
    echo "  2. Build the workspace: colcon build"
    echo "  3. Start perception: ros2 launch cone_detector cone_detector.launch.py"
    echo ""
else
    echo -e "${RED}Docker build failed!${NC}"
    exit 1
fi