export PYTHONPATH="$PYTHONPATH:$(pwd)/ros_control/ros_control"
date >> logs/control_output.log
ros2 run ros_control command_node --ros-args -p eufs_simulate:=true >> logs/control_output.log 2>&1
