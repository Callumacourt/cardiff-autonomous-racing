#!/bin/bash
# File: scripts/run_docker.sh
set -e

echo "🚀 Starting Cardiff Autonomous Racing System..."

# Create logs directory
mkdir -p logs

# Start the system
docker-compose up --build

echo "🏁 System started! Check logs/ directory for output."