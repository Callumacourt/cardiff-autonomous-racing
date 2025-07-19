source install/setup.bash
./ros_can/FS-AI-API/setup.sh
date >> logs/ros_can_output.log 
ros2 launch ros_can ros_can.launch.py >> logs/ros_can_output.log 2>&1 &

export PYTHONPATH="$PYTHONPATH:$(pwd)/ros_control/ros_control"
date >> logs/control_output.log
ros2 run ros_control command_node >> logs/control_output.log 2>&1 &
