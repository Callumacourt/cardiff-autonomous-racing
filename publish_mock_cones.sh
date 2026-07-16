#!/bin/bash
# Publish mock cone data to test path planning
# Run this in a separate terminal

echo "🚀 Publishing mock cone data..."
echo "This simulates YOLO cone detections"
echo "Press Ctrl+C to stop"
echo ""

# Source ROS
source /opt/ros/humble/setup.bash

# Publish car pose
ros2 topic pub /car_pose geometry_msgs/msg/PoseStamped "{
  header: {stamp: {sec: 0, nanosec: 0}, frame_id: 'map'},
  pose: {
    position: {x: 0.0, y: 0.0, z: 0.0},
    orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}
  }
}" -r 10 &

POSE_PID=$!

# Wait a bit
sleep 1

# Publish cone data (straight track with blue/yellow cones)
ros2 topic pub /detected_cones std_msgs/msg/String "data: '
2.0,2.5,0.0,0
4.0,2.5,0.0,0
6.0,2.5,0.0,0
8.0,2.5,0.0,0
10.0,2.5,0.0,0
12.0,2.5,0.0,0
2.0,-2.5,0.0,1
4.0,-2.5,0.0,1
6.0,-2.5,0.0,1
8.0,-2.5,0.0,1
10.0,-2.5,0.0,1
12.0,-2.5,0.0,1'" -r 5 &

CONE_PID=$!

echo "✅ Publishing mock data..."
echo "   - Car pose at origin"
echo "   - 6 blue cones (left, label=0)"
echo "   - 6 yellow cones (right, label=1)"
echo ""
echo "Check path planning logs: sudo docker logs -f racing_planning"
echo ""
echo "Press Ctrl+C to stop"

# Wait for Ctrl+C
trap "kill $POSE_PID $CONE_PID 2>/dev/null; echo ''; echo '🛑 Stopped'; exit" INT
wait
