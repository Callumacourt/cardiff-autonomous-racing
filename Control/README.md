please read individual readmes for ros_can and ros_control for installation process

to start car:

cd ros_can/FS-AI-API/setup.sh

./setup.sh

ros2 launch ros_can ros_can.launch.py


then in a seperate terminal:

cd ros_control/launch

export PYTHONPATH=$PYTHONPATH:/"your path to here"/ros_control/ros_control

/\ this only needs to be done once per time you log on to your pc, alternatively add it to your ~/.bashrc

if using eufs sim, first get the sim open, then:

./start_control_eufs

if using actual car:

./start_control_