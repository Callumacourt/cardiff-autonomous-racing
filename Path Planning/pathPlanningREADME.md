# Path Planning Section

## Description
This section of the codebase is the path planning algorithm that uses the RRT* approach to generate an optimised path for an autonomous vehicle. This will interpret data from the perception team, process a path and send it to the control team.

#Must use Ubuntu 22.04 LTS

## Project Structure
Here is the structure of the project:
 - **main.py** - The main file which runs the project and links all the parts of the project.
 - **dummyInputs.py** - This generates the initial dummy data that we needed before we had the outputs from perception.
 - **inputs.txt** - This file stores the input data that the algorithm needs to run.
 - **rrt(star).py** - This code contains the RRT* algorithm that we are using to generate the path.
 - **gui.py** - This code generates the GUI allowing for easy visualisation of the path.

**Follow the structure of this repository as it is fundamental for it to work.**


## Getting started

**Installing Dependencies**
```
pip install -r requirements.txt
```

#Numpy
```
pip install numpy
```

#ROS2
```
pip install ros
```

#MatPlotLib
```
pip install matplotlib
```

#Python Virtual Environment
```
sudo apt install python3-venv
```

#Tkinter
```
sudo apt install python3-tk -y
```

If you encounter the following error:
```
Import Error: cannot import name 'ImageTk' from 'PIL'
```
Run the following commands:
```
python3 -m venv myenv
source myenv/bin/activate
pip install --upgrade pip
pip uninstall pillow
pip install pillow
```

If you are still encountering the same error, run the following commands:
```
sudo apt update
sudo apt install python3-tk tk-dev
pip uninstall pillow -y
pip install --no-cache-dir --force-reinstall pillow
```

#PyGame
```
pip install pygame
```

## Running The Program

To run integration.py which is the main file that runs the path planning and perception.

1. Ensure ROS 2 is installed and sourced.
```
source /opt/ros/humble/setup.bash
```

2. Manually Publish Test Data (Only required to do if Perception section is broken)
```
ros2 topic pub /car_pose geometry_msgs/PoseStamped '{header: {frame_id: "map"}, pose: {position: {x: 0.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}}'
ros2 topic pub /cone_map/local std_msgs/String "data: '5.0,2.0,0.0,0,0.9\n10.0,2.5,0.0,1,0.8'"
```

3. Build Perception Section (If available)
```
cd /home/user/cardiff-autonomous-racing/perception_ws
colcon build
```

4. Source Section after building
```
source install/setup.bash
```

5. Run Perception Section
```
ros2 run cone_mapper cone_mapper
ros2 launch slam_example slam_example.launch.py
ros2 run cone_detector cone_detector_node
```

3. Run a Publisher Node
```
python3 test_cone_publisher.py
```

4. Verify ROS Topics
```
ros2 topic list
ros2 topic echo /car_pose
ros2 topic echo /cone_map/local
```

5. Navigate to the workspace
```
cd /home/user/cardiff-autonomous-racing/Path\ Planning
```

6. Run the script
```
python3 integration.py
```

## Visuals

## How the Code works

## Usage

## FAQ

## Support

If there is something wrong with the code or you need help, please reach out to the **Path Planning Team Leader, Dominick George**. I would be happy to help you. My email is **GeorgeD8@cardiff.ac.uk**.

## Contributors

- Dominick George
- Harley Doe
- Callum A'court