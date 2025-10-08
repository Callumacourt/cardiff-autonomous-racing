# Cardiff Autonomous Racing - Quick Setup Script
# One-command setup for new contributors

set -e  # Exit on any error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  Cardiff Autonomous Racing - Quick Setup"
echo "=========================================="
echo -e "${NC}"

# Check prerequisites
echo -e "${BLUE} Checking prerequisites...${NC}"

# Check Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED} Docker not found${NC}"
    echo "Please install Docker first:"
    echo "  curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh"
    exit 1
else
    echo -e "${GREEN} Docker found: $(docker --version | cut -d' ' -f3)${NC}"
fi

# Check Docker permissions
if ! docker ps &> /dev/null; then
    echo -e "${YELLOW}  Docker permission issue${NC}"
    echo "Adding user to docker group..."
    sudo usermod -aG docker $USER
    echo "Please log out and log back in, then run this script again."
    exit 1
fi

# Check X11
if [ -z "$DISPLAY" ]; then
    echo -e "${YELLOW}  No display detected, GUI applications may not work${NC}"
else
    echo -e "${GREEN} Display available: $DISPLAY${NC}"
fi

# Check disk space (need ~15GB)
AVAILABLE_SPACE=$(df . | tail -1 | awk '{print $4}')
REQUIRED_SPACE=15000000  # 15GB in KB

if [ "$AVAILABLE_SPACE" -lt "$REQUIRED_SPACE" ]; then
    echo -e "${RED} Insufficient disk space${NC}"
    echo "Required: 15GB, Available: $(($AVAILABLE_SPACE / 1000000))GB"
    exit 1
else
    echo -e "${GREEN} Sufficient disk space: $(($AVAILABLE_SPACE / 1000000))GB available${NC}"
fi

# Build Docker images
echo -e "\n${BLUE}Building Docker images...${NC}"

echo -e "${YELLOW}Building perception system (includes YOLOv8, ORB-SLAM3, ROS2)...${NC}"
echo "This may take 10-15 minutes on first build..."

if docker build -f docker/Dockerfile.perception -t car-perception:latest .; then
    echo -e "${GREEN}Perception image built successfully${NC}"
else
    echo -e "${RED}Failed to build perception image${NC}"
    exit 1
fi

echo -e "${YELLOW}Building EUFS simulation environment...${NC}"
echo "This may take 5-10 minutes..."

if docker build -f docker/Dockerfile.eufs_simple -t car-eufs-simple .; then
    echo -e "${GREEN}EUFS simulation image built successfully${NC}"
else
    echo -e "${RED}Failed to build EUFS image${NC}"
    exit 1
fi

# Verify images
echo -e "\n${BLUE} Verifying built images...${NC}"
PERCEPTION_SIZE=$(docker images car-perception:latest --format "table {{.Size}}" | tail -1)
EUFS_SIZE=$(docker images car-eufs-simple --format "table {{.Size}}" | tail -1)

echo -e "${GREEN} Perception image: $PERCEPTION_SIZE${NC}"
echo -e "${GREEN} EUFS simulation image: $EUFS_SIZE${NC}"

# Test basic functionality
echo -e "\n${BLUE} Testing basic functionality...${NC}"

echo "Testing perception container..."
if docker run --rm car-perception:latest bash -c "source /opt/ros/humble/setup.bash && ros2 --version"; then
    echo -e "${GREEN} Perception container works${NC}"
else
    echo -e "${RED} Perception container test failed${NC}"
    exit 1
fi

echo "Testing EUFS container..."
if docker run --rm car-eufs-simple bash -c "source /opt/ros/humble/setup.bash && ros2 --version"; then
    echo -e "${GREEN} EUFS container works${NC}"
else
    echo -e "${RED} EUFS container test failed${NC}"
    exit 1
fi

# Setup complete
echo -e "\n${GREEN} Setup Complete!${NC}"
echo -e "${CYAN}=================${NC}"

echo -e "\n${BLUE} Quick Start Commands:${NC}"
echo ""
echo -e "${YELLOW}1. Start EUFS Simulation (Terminal 1):${NC}"
echo "   docker run -it --name eufs-sim --privileged --net=host \\"
echo "     --env=\"DISPLAY\" --volume=\"/tmp/.X11-unix:/tmp/.X11-unix:rw\" \\"
echo "     car-eufs-simple"
echo ""
echo "   # Then inside the container:"
echo "   ros2 launch eufs_launcher simulation.launch.py use_sim_time:=true track:=small_track gazebo_gui:=true"
echo ""
echo -e "${YELLOW}2. Start Perception System (Terminal 2):${NC}"
echo "   docker run -it --name car-perception-dev --privileged --net=host \\"
echo "     --env=\"DISPLAY\" --volume=\"/tmp/.X11-unix:/tmp/.X11-unix:rw\" \\"
echo "     --volume=\"\$(pwd)/perception_ws:/workspace/perception_ws:rw\" \\"
echo "     car-perception:latest"
echo ""
echo "   # Then inside the container:"
echo "   cd /workspace/perception_ws"
echo "   colcon build --packages-select cone_detector"
echo "   source install/setup.bash"
echo "   ros2 run cone_detector cone_detector_node --ros-args --remap image_raw:=/camera/image_raw"
echo ""
echo -e "${YELLOW}3. Visualize Results (Terminal 3):${NC}"
echo "   ./scripts/launch_visualization.sh"
echo ""
echo -e "${BLUE} System Verification:${NC}"
echo "   ./scripts/verify_system.sh"
echo ""
echo -e "${BLUE} Full Documentation:${NC}"
echo "   • Main README: ./README.md"
echo "   • Perception Docs: ./perception_ws/README.md"
echo "   • Path Planning: ./Path_Planning/README.md"
echo "   • Control System: ./Control/README.md"
echo ""
echo -e "${GREEN}Happy Racing! 🏁${NC}"