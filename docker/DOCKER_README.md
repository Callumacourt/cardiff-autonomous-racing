# Cardiff Autonomous Racing - Docker Setup

##  Overview

This repository contains a fully containerized autonomous racing system with three main components:
- **Perception System**: Camera-based cone detection, EKF-SLAM localisation, and cone mapping
- **Path Planning System**: Generates optimal racing paths using RRT* algorithm
- **Control system**: Generates inputs for the car to follow

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)
- If on windows, you will need wsl 2 using the Ubuntu-22.04 distro

If on windows, run all the following steps from within wsl.

### Before running the system

1. **Clone and navigate to the repository**:
   ```bash
   git clone <your-repo-url>
   cd cardiff-autonomous-racing
   git submodule init
   git submodule update
```

2. **Run the FSAI-API setup script**
   ```bash
   . /your/path/to/here/Control/ros_can/FS-AI-API/setup.sh
   ```
3. **For guis to work, add docker to the xhost access control**
   ```bash
   xhost +local:docker
   ```
   - This needs to be done every time you log on, so consider adding it to your .bashrc
   - This does not need to be done on windows using wsl.

4. **For ros communication with the control node**
   - To enable ros communication with the control node you might need to add some rules to your firewall. This is because the control node needs to use `network_mode: host` to access the can bus.
  You can do this on linux with this:
   ```bash
   sudo ufw allow proto udp from any to any port 7400
   sudo ufw allow proto tcp from any to any port 7410:7420
   sudo ufw allow proto udp from any to any port 7410:7420
   sudo ufw reload
   ```
   - This also does not need to be done on windows

### Running the System

If on windows, run from within wsl.

1. **Navigate to the repository**:
   ```bash
   cd cardiff-autonomous-racing
   ```

2. **Build all containers**:
   ```bash
   sudo docker compose build
   ```

-  **First time build**

   On the very first build you may get an error like this: `ERROR [eufs_sim internal] load metadata for docker.io/library/cardiff-autonomous-racing-control:latest`

   To fix this you can build each container individually like this
   ```bash
   sudo docker compose build base
   sudo docker compose build perception
   sudo docker compose build path_planning
   sudo docker compose build control
   sudo docker compose build eufs_sim
   ```
   Remember, this is only necesary the first time you ever build this system.

3. **Start the entire system (without eufs simulation)**:
   ```bash
   sudo docker compose up
   ```

4. **Start the entire system (with eufs simulation)**:
- set `eufs_simulate=1` in `docker/shared.env`
   ```bash
   sudo docker compose up
   ```

5. **Start in detached mode** (run in background):
   ```bash
   sudo docker compose up -d
   ```

## System Components

### Perception System (`racing_perception`)
- **Purpose**: Camera-based cone detection, localisation, and cone mapping
- **Nodes**: `cone_detector` (YOLOv8 + depth), `landmark_slam` (EKF-SLAM),
  `cone_mapper` (builds the track map)
- **Publishes**: `/odometry/slam` (car pose), `/cone_map/local` +
  `/cone_map/global` (cone positions)
- **Details**: see [`../perception_ws/README.md`](../perception_ws/README.md)
  and [`../PERCEPTION_FORMAT.md`](../PERCEPTION_FORMAT.md)

### Path Planning System (`racing_planning`)
- **Purpose**: Generates optimal racing paths using RRT* algorithm
- **Subscribes**: 
  - `/car_pose`: Current vehicle position
  - `/cone_map/local`: Cone positions from perception
- **Publishes**: 
  - `/planned_path`: Optimal racing path
- **Algorithm**: RRT* with dynamic obstacle avoidance

### Control System (`racing_control`)
- **Purpose**: Vehicle control with real EUFS message integration
- **Subscribes**:
  - `/planned_path`: Racing path from planning
- **Publishes**:
  - `/cmd`: steering and acceleration commands (if eufs_simulate=0, this is picked up by ros_can and converted into torque requests, which are sent down the can bus)
  - `/state_machine/driving_flag`: flag saying wether the car is in driving mode, instructions from /cmd will only be recieved if this is true
  - `/ros_can/mission_completed`: flag saying wether the mission has been completed, car will only recieve instructions if this is false
  - `/car_pose`: Vehicle position feedback
  - `/can_state`: EUFS autonomous system state
- **Features**: Real EUFS messages, position feedback, vehicle dynamics