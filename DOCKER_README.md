# Cardiff Autonomous Racing - Docker Setup

##  Overview

This repository contains a fully containerized autonomous racing system with three main components:
- **Mock Data Publishers**: Simulates car pose and cone detection data
- **Perception System**: Processes cone data and creates local maps
- **Path Planning System**: Generates optimal racing paths using RRT* algorithm

### Prerequisites
- Docker and Docker Compose installed
- Git (for cloning the repository)

### Running the System

1. **Clone and navigate to the repository**:
   ```bash
   git clone <your-repo-url>
   cd cardiff-autonomous-racing
   ```

2. **Build all containers**:
   ```bash
   docker-compose build
   ```

3. **Start the entire system**:
   ```bash
   docker-compose up
   ```

4. **Start in detached mode** (run in background):
   ```bash
   docker-compose up -d
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
