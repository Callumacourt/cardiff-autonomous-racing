this module contains the code that sends our instructions to the car,
the cmd message is located in ros_control/cmd_pub.py:ln:34

to install:

cd to control

colcon build --packages-select ros_control

source install/setup.bash 

export PYTHONPATH=$PYTHONPATH:$PWD"/ros_control/ros_control"

/\ add this to ~/.bashrc , replacing $PWD with the path to cardiff-autonomous-racing/Control/