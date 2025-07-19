source ~/cardiff-autonomous-racing/Control/install/setup.bash
./cardiff-autonomous-racing/Control/ros_can/FS-AI-API/setup.bash
date >> ~/cardiff-autonomous-racing/Control/logs/ros_can_output.logs
ros2 launch ros_can ros_can.launch.py >> ~/cardiff-autonomous-racing/Control/logs/ros_can_output.logs 2>&1 &

export PYTHONPATH="$PYTHONPATH:~/cardiff-autonomous-racing/Control/ros_control/ros_control"
date >> ~/cardiff-autonomous-racing/Control/logs/control_output.log
ros2 run ros_control control_node >> ~/cardiff-autonomous-racing/Control/logs/control_output.log