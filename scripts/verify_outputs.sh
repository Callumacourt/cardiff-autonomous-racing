#!/bin/bash

echo "========================================="
echo "CARDIFF AUTONOMOUS RACING - SYSTEM CHECK"
echo "========================================="
echo ""

# Function to check topic
check_topic() {
    local topic=$1
    local description=$2
    local container=$3
    
    echo "Checking: $description"
    echo "Topic: $topic"
    
    # Check if topic exists
    result=$(docker exec $container bash -c "source /opt/ros/humble/setup.bash && ros2 topic list 2>/dev/null | grep -c '^${topic}$'")
    
    if [ "$result" -eq "1" ]; then
        # Get publish rate
        hz=$(docker exec $container bash -c "source /opt/ros/humble/setup.bash && timeout 3 ros2 topic hz $topic 2>/dev/null | grep 'average rate' | awk '{print \$3}'")
        
        if [ -z "$hz" ]; then
            echo "  ✗ TOPIC EXISTS BUT NO DATA (0 Hz)"
        else
            echo "  ✓ PUBLISHING at ${hz} Hz"
        fi
        
        # Get message type
        msg_type=$(docker exec $container bash -c "source /opt/ros/humble/setup.bash && ros2 topic info $topic 2>/dev/null | grep 'Type:' | awk '{print \$2}'")
        echo "  Message Type: $msg_type"
    else
        echo "  ✗ NOT FOUND"
    fi
    echo ""
}

echo "=== SIMULATOR OUTPUTS ==="
check_topic "/ground_truth/cones" "Ground Truth Cones (EUFS Sim)" "racing_eufs_sim"
check_topic "/zed/left/image_rect_color" "Left Camera RGB" "racing_eufs_sim"
check_topic "/zed/right/image_rect_color" "Right Camera RGB" "racing_eufs_sim"
check_topic "/zed/depth/image_raw" "Depth Image" "racing_eufs_sim"
check_topic "/imu/data" "IMU Data" "racing_eufs_sim"

echo "=== PERCEPTION OUTPUTS ==="
check_topic "/detected_cones" "YOLO Detections (String)" "racing_perception"
check_topic "cone_detection_image" "Annotated Image" "racing_perception"
check_topic "/perception/cones" "Cone Array" "racing_perception"
check_topic "/cone_cloud/local" "Point Cloud" "racing_perception"

echo "=== SLAM OUTPUTS ==="
check_topic "/odometry/slam" "SLAM Odometry" "racing_perception"

echo "=== SUMMARY ==="
echo "All topics above should be publishing for other teams to access."
echo ""
echo "To view a specific topic's data:"
echo "  docker exec racing_perception bash -c \"source /opt/ros/humble/setup.bash && ros2 topic echo /TOPIC_NAME --once\""
echo ""
echo "To record all topics for analysis:"
echo "  docker exec racing_perception bash -c \"source /opt/ros/humble/setup.bash && ros2 bag record -a -o /workspace/test_recording\""