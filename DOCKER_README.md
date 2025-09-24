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

### Before running the system

1. **Run the FSAI-API setup script**
   ```bash
   . /your/path/to/here/Control/ros_can/FS-AI-API/setup.sh
   ```
2. **For guis to work, add docker to the xhost access control**
   ```bash
   xhost +local:docker
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
  - `/racing/control/steering`: Steering commands
  - `/racing/control/throttle`: Throttle commands
  - `/car_pose`: Vehicle position feedback
  - `/can_state`: EUFS autonomous system state
- **Features**: Real EUFS messages, position feedback, vehicle dynamics