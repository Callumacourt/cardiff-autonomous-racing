#!/bin/bash
# Setup script to install TUM Global Race Trajectory Optimization

set -e

echo "🏎️  Setting up TUM Global Race Trajectory Optimization..."

# Navigate to Path_Planning directory
cd "$(dirname "$0")"

# Clone TUM optimizer repository as submodule
if [ ! -d "tum_optimizer" ]; then
    echo "📥 Cloning TUM optimizer repository..."
    git clone https://github.com/TUMFTM/global_racetrajectory_optimization tum_optimizer
    echo "✅ TUM optimizer cloned successfully"
else
    echo "✅ TUM optimizer already exists"
    echo "📥 Updating TUM optimizer..."
    cd tum_optimizer
    git pull
    cd ..
fi

echo ""
echo "✅ TUM optimizer setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Rebuild Docker container: sudo docker compose build path_planning"
echo "2. Restart containers: sudo docker compose up -d path_planning"
echo "3. Check logs: sudo docker logs -f racing_planning"
echo ""
echo "💡 Note: Python dependencies will be installed automatically during Docker build"
