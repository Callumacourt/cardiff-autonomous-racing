# Cardiff Autonomous Racing - Visual Verification Script
# This script helps new users verify their perception system is working correctly

echo "Cardiff Autonomous Racing - System Verification"
echo "=================================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if containers are running
echo -e "\n${BLUE}Checking System Status...${NC}"

EUFS_RUNNING=$(docker ps --filter "name=eufs-sim" --filter "status=running" -q)
PERCEPTION_RUNNING=$(docker ps --filter "name=car-perception" --filter "status=running" -q)

if [ -z "$EUFS_RUNNING" ]; then
    echo -e "${RED}EUFS simulation not running${NC}"
    echo "   Start with: docker run -it --name eufs-sim --privileged --net=host --env=\"DISPLAY\" --volume=\"/tmp/.X11-unix:/tmp/.X11-unix:rw\" car-eufs-simple"
    exit 1
else
    echo -e "${GREEN}EUFS simulation running${NC}"
fi

if [ -z "$PERCEPTION_RUNNING" ]; then
    echo -e "${RED}Perception container not running${NC}"
    echo "   Start with: docker run -it --name car-perception-dev --privileged --net=host --env=\"DISPLAY\" --volume=\"/tmp/.X11-unix:/tmp/.X11-unix:rw\" --volume=\"$(pwd)/perception_ws:/workspace/perception_ws:rw\" car-perception:latest"
    exit 1
else
    echo -e "${GREEN}Perception container running${NC}"
fi

# Check ROS2 topics
echo -e "\n${BLUE}Checking ROS2 Topics...${NC}"

CAMERA_TOPIC=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic list | grep '/camera/image_raw'" 2>/dev/null)
CONE_TOPIC=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic list | grep '/cone_detections'" 2>/dev/null)
DEBUG_TOPIC=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic list | grep '/cone_detector/debug_image'" 2>/dev/null)

if [ -n "$CAMERA_TOPIC" ]; then
    echo -e "${GREEN}Camera topic available: $CAMERA_TOPIC${NC}"
else
    echo -e "${RED} Camera topic not found${NC}"
fi

if [ -n "$CONE_TOPIC" ]; then
    echo -e "${GREEN}Cone detection topic available: $CONE_TOPIC${NC}"
else
    echo -e "${YELLOW} Cone detection topic not found (cone detector may not be running)${NC}"
fi

if [ -n "$DEBUG_TOPIC" ]; then
    echo -e "${GREEN}Debug image topic available: $DEBUG_TOPIC${NC}"
else
    echo -e "${YELLOW}Debug image topic not found${NC}"
fi

# Check if cone detector is running
echo -e "\n${BLUE}Checking Cone Detector Status...${NC}"

CONE_DETECTOR_NODE=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 node list | grep cone_detector" 2>/dev/null)

if [ -n "$CONE_DETECTOR_NODE" ]; then
    echo -e "${GREEN}Cone detector node running${NC}"
    
    # Check message rate
    echo -e "\n${BLUE}Checking Topic Rates...${NC}"
    echo "Testing camera feed rate (5 seconds)..."
    
    CAMERA_RATE=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /camera/image_raw" 2>/dev/null | tail -1)
    if [ -n "$CAMERA_RATE" ]; then
        echo -e "${GREEN} Camera feed: $CAMERA_RATE${NC}"
    else
        echo -e "${RED} No camera data received${NC}"
    fi
    
    CONE_RATE=$(docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && timeout 5 ros2 topic hz /cone_detections" 2>/dev/null | tail -1)
    if [ -n "$CONE_RATE" ]; then
        echo -e "${GREEN} Cone detections: $CONE_RATE${NC}"
    else
        echo -e "${YELLOW}  No cone detections (may be normal if no cones visible)${NC}"
    fi
    
else
    echo -e "${RED} Cone detector node not running${NC}"
    echo -e "${BLUE} To start cone detector:${NC}"
    echo "   docker exec -it car-perception-dev bash"
    echo "   cd /workspace/perception_ws"
    echo "   source /opt/ros/humble/setup.bash && source install/setup.bash"
    echo "   ros2 run cone_detector cone_detector_node --ros-args --remap image_raw:=/camera/image_raw"
fi

# Visualization options
echo -e "\n${BLUE} Visual Verification Options:${NC}"
echo "1. View cone detection with bounding boxes:"
echo "   docker exec car-perception-dev bash -c \"source /opt/ros/humble/setup.bash && ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image\""
echo ""
echo "2. View raw camera feed:"
echo "   docker exec car-perception-dev bash -c \"source /opt/ros/humble/setup.bash && ros2 run rqt_image_view rqt_image_view /camera/image_raw\""
echo ""
echo "3. Launch RViz for 3D visualization:"
echo "   docker exec car-perception-dev bash -c \"source /opt/ros/humble/setup.bash && rviz2\""
echo ""
echo "4. Monitor cone detection data:"
echo "   docker exec car-perception-dev bash -c \"source /opt/ros/humble/setup.bash && ros2 topic echo /cone_detections\""

# Quick test option
echo -e "\n${BLUE} Quick Visual Test:${NC}"
echo "Run this command to launch image viewer automatically:"
echo -e "${GREEN}./scripts/launch_visualization.sh${NC}"

echo -e "\n${GREEN}System verification complete!${NC}"
echo "If you see green checkmarks above, your perception system is working correctly."
echo "Open Gazebo to see the racing simulation and use the visualization commands above to see cone detection in action."