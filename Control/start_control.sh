source install/setup.bash
./ros_can/FS-AI-API/setup.sh
ros2 launch ros_can ros_can.launch.py > ros_can_output.log 2>&1 &

export PYTHONPATH="$PYTHONPATH:$(pwd)/ros_control/ros_control"
ros2 run ros_control command_node > control_output.log 2>&1 &
