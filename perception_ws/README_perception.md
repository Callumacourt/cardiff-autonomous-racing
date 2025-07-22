Cardiff Autonomous Racing FS-AI 2025: Perception Stack

ROS2-based perception pipeline for cone detection, SLAM and cone mapping with the EUFS sim

## Packages:

- `cone_detector/`: Colour based (HSV) cone detection publishing cone position + colour.
- `slam_example/`: Launch files + config to run ORB-SLAM3 using ZED2 camera simulation.
- `eufs_sim/`: Sim environment (Boogiemanc fork with plugins from official EUFS repo).
- `ackermann_msgs/`, `eufs_msgs/`: Dependencies for EUFS sim

## Dependencies

Install these system packages first:

```
sudo apt install libeigen3-dev libpangolin-dev libopencv-dev
```
Need to clone and build:

- Pangolin

Clone into workspace with:

```
cd ~/your_workspace
git clone this repository
git clone https://github.com/stevenlovegrove/Pangolin.git
```

## Running the System

Build the workspace:

```
colcon build --symlink-install
source install/setup.bash
```

In each new terminal:

```
source yourworkspace/install/setup.bash

```
Launch simulation:

```
export EUFS_MASTER=true
ros2 launch eufs_tracks track.launch.py
```
Launch cone detection node:

```
ros2 run cone_detector YOLO_cone_detector
```
Launch SLAM:

```
export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:~/ros2_ws/ORB_SLAM3_mask/lib
ros2 launch slam_example slam_example.launch.py

```

Launch cone mapping node and visuals:

```
ros2 run cone_mapper cone_mapper.py

(optional) ros2 run cone_mapper track_generation.py

ros2 run cone_mapper map_visual.py

```
