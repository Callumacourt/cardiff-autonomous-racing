# Cardiff Autonomous Racing - Docker Setup

##  Overview

This repository contains a fully containerized autonomous racing system with three main components:
- **Mock Data Publishers**: Simulates car pose and cone detection data
- **Perception System**: Processes cone data and creates local maps
- **Path Planning System**: Generates optimal racing paths using RRT* algorithm
- **Control system**: Generates inputs for the car to follow

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)
- **NOTE** at present the docker has not been fully tested on a windows machine, using a linux distro that uses X11 for is recommended. Such as Ubuntu or Linux Mint

### Before running the system

1. **Run the FSAI-API setup script**
   ```bash
   . /your/path/to/here/Control/ros_can/FS-AI-API/setup.sh
   ```
2. **For guis to work, add docker to the xhost access control**
   ```bash
   xhost +local:docker
   ```
   - This needs to be done every time you log on, so consider adding it to your .bashrc
3. **For ros communication with the control node**
   - To enable ros communication with the control node you might need to add some rules to your firewall. This is because the control node needs to use `network_mode: host` to access the can bus.
  You can do this on linux with this:
   ```bash
   sudo ufw allow proto udp from any to any port 7400
   sudo ufw allow proto tcp from any to any port 7410:7420
   sudo ufw allow proto udp from any to any port 7410:7420
   sudo ufw reload
   ```

### Running the System

1. **Clone and navigate to the repository**:
   ```bash
   git clone <your-repo-url>
   cd cardiff-autonomous-racing
   ```

2. **Build all containers**:
   ```bash
   sudo docker-compose build
   ```

3. **Start the entire system (without eufs simulation)**:
   ```bash
   sudo docker-compose up
   ```

4. **Start the entire system (with eufs simulation)**:
- set `eufs_simulate=1` in `docker/shared.env`
   ```bash
   sudo docker-compose up
   ```

5. **Start in detached mode** (run in background):
   ```bash
   sudo docker-compose up -d
   ```

## System Components

### Mock Data Publisher (`racing_mock`)
- **Purpose**: Provides simulated sensor data for testing
- **Publishes**:
  - `/car_pose`: Current vehicle position and orientation
  - `/cone_map/local`: Simulated cone positions (blue/yellow racing cones)
- **Data**: Generates realistic racing track data with moving car position

### Perception System (`racing_perception`)
- **Purpose**: Processes incoming cone data and creates environmental maps
- **Subscribes**: Cone detection data
- **Publishes**: Processed cone maps for path planning
- **Features**: Advanced cone mapping and filtering

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