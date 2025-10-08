# Cardiff Autonomous Racing - Quick Visualization Launcher
# Launches visual tools to see cone detection in action

echo "Cardiff Autonomous Racing - Visual Verification"
echo "================================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE} Launching visualization tools...${NC}"

# Check if perception container is running
PERCEPTION_RUNNING=$(docker ps --filter "name=car-perception" --filter "status=running" -q)

if [ -z "$PERCEPTION_RUNNING" ]; then
    echo -e "${RED} Perception container not running${NC}"
    echo "Please start the perception container first."
    exit 1
fi

echo -e "${GREEN} Starting cone detection visualization...${NC}"

# Launch image viewer for debug images (shows bounding boxes)
echo "Opening cone detection view (with bounding boxes)..."
docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && ros2 run rqt_image_view rqt_image_view /cone_detector/debug_image" &

sleep 2

# Launch image viewer for raw camera feed
echo "Opening raw camera view..."
docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && ros2 run rqt_image_view rqt_image_view /camera/image_raw" &

sleep 2

# Launch RViz for 3D visualization
echo "Opening RViz for 3D visualization..."
docker exec car-perception-dev bash -c "source /opt/ros/humble/setup.bash && rviz2" &

echo -e "\n${GREEN} Visualization tools launched!${NC}"
echo -e "${YELLOW}You should now see:${NC}"
echo "1.  Cone detection view - Camera feed with bounding boxes around detected cones"
echo "2.  Raw camera view - Direct feed from EUFS simulation camera"
echo "3.   RViz - 3D visualization tool (add topics: /cone_detections, /cone_detector/debug_image)"
echo ""
echo -e "${BLUE} Tips:${NC}"
echo "- In RViz, click 'Add' and add the following topics:"
echo "  /cone_detections (geometry_msgs/PointStamped)"
echo "  /cone_detector/debug_image (sensor_msgs/Image)"
echo "- Move the car in Gazebo to see different cone detection views"
echo "- Check the terminal running cone_detector for detection statistics"
echo ""
echo -e "${GREEN}Press Ctrl+C to close all visualization windows${NC}"

# Wait for user to press Ctrl+C
trap 'echo -e "\n${BLUE}Closing visualization tools...${NC}"; pkill -f rqt_image_view; pkill -f rviz2; exit 0' INT

echo "Visualization running... Press Ctrl+C to stop."
while true; do
    sleep 1
done