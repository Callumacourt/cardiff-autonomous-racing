source ~/cardiff-autonomous-racing/Control/install/setup.bash
sh ~/cardiff-autonomous-racing/Control/ros_can/FS-AI-API/setup.sh
date >> ~/cardiff-autonomous-racing/Control/logs/ros_can_output.logs
ros2 launch ros_can ros_can.launch.py >> ~/cardiff-autonomous-racing/Control/logs/ros_can_output.logs 2>&1 &

export PYTHONPATH="$PYTHONPATH:/home/cardiff/cardiff-autonomous-racing/Control/ros_control/ros_control"
date >> ~/cardiff-autonomous-racing/Control/logs/control_output.log
ros2 run ros_control command_node >> ~/cardiff-autonomous-racing/Control/logs/control_output.log 2>&1 &
