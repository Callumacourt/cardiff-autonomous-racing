#!/bin/bash
# Complete Path Planning Module Test Script
# Run from: ~/cardiff-autonomous-racing

echo "======================================================================"
echo "🧪 TESTING PATH PLANNING MODULE"
echo "======================================================================"
echo ""

# Check containers are running
echo "1️⃣  Checking Docker containers..."
if sudo docker ps | grep -q "racing_planning"; then
    echo "   ✅ Path planning container running"
else
    echo "   ❌ Path planning container NOT running"
    echo "   Starting containers..."
    sudo docker compose up -d perception path_planning
    sleep 5
fi

if sudo docker ps | grep -q "racing_perception"; then
    echo "   ✅ Perception container running"
else
    echo "   ❌ Perception container NOT running"
fi
echo ""

# Check ROS topics
echo "2️⃣  Checking ROS topics..."
echo "   Available topics:"
sudo docker exec -it racing_planning bash -c "source /opt/ros/humble/setup.bash && ros2 topic list" | grep -E "car_pose|detected_cones|planned_path" || echo "   ⚠️  No relevant topics found"
echo ""

# Check if cone data is being published
echo "3️⃣  Checking cone detection data..."
timeout 5 sudo docker exec -it racing_planning bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /detected_cones" 2>/dev/null && echo "   ✅ Cones being published" || echo "   ⚠️  No cone data (is YOLO running?)"
echo ""

# Check if planned path is being published
echo "4️⃣  Checking planned path output..."
timeout 5 sudo docker exec -it racing_planning bash -c "source /opt/ros/humble/setup.bash && ros2 topic hz /planned_path" 2>/dev/null && echo "   ✅ Path being published" || echo "   ⚠️  No path output"
echo ""

# Sample path data
echo "5️⃣  Sampling published path (one message)..."
timeout 3 sudo docker exec -it racing_planning bash -c "source /opt/ros/humble/setup.bash && ros2 topic echo /planned_path --once" 2>/dev/null | head -20
echo ""

# Check logs for TUM optimization
echo "6️⃣  Checking for TUM optimization in logs..."
sudo docker logs racing_planning 2>&1 | tail -30 | grep -E "TUM|optimization|trajectory|cones" || echo "   ⚠️  No optimization logs found"
echo ""

# Check for errors
echo "7️⃣  Checking for errors in logs..."
if sudo docker logs racing_planning 2>&1 | tail -50 | grep -qi "error\|fail\|traceback"; then
    echo "   ⚠️  Errors found in logs:"
    sudo docker logs racing_planning 2>&1 | tail -30 | grep -i "error\|fail"
else
    echo "   ✅ No recent errors"
fi
echo ""

echo "======================================================================"
echo "📊 SUMMARY"
echo "======================================================================"
echo "To view live logs: sudo docker logs -f racing_planning"
echo "To manually publish test data:"
echo "  ros2 topic pub /car_pose geometry_msgs/PoseStamped '{header: {frame_id: \"map\"}, pose: {position: {x: 0.0, y: 0.0}}}'"
echo "======================================================================"
