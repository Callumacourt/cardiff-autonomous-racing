#!/bin/bash

# Cardiff Autonomous Racing - System Check
# Run this script to verify your setup before starting

echo "🏎️  Cardiff Autonomous Racing - System Check"
echo "=============================================="

# Check Docker
echo ""
echo "🔍 Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo "✅ Docker found: $DOCKER_VERSION"
else
    echo "❌ Docker not found! Please install Docker Desktop"
    exit 1
fi

# Check Docker Compose
echo ""
echo "🔍 Checking Docker Compose..."
if command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo "✅ Docker Compose found: $COMPOSE_VERSION"
else
    echo "❌ Docker Compose not found! Please install Docker Desktop"
    exit 1
fi

# Check Docker daemon
echo ""
echo "🔍 Checking Docker daemon..."
if docker info &> /dev/null; then
    echo "✅ Docker daemon is running"
else
    echo "❌ Docker daemon not running! Please start Docker Desktop"
    exit 1
fi

# Check disk space
echo ""
echo "🔍 Checking disk space..."
AVAILABLE_SPACE=$(df -h . | awk 'NR==2{print $4}')
echo "✅ Available disk space: $AVAILABLE_SPACE"

# Check for docker-compose.yml
echo ""
echo "🔍 Checking project files..."
if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml found"
else
    echo "❌ docker-compose.yml not found! Are you in the right directory?"
    exit 1
fi

# Check for main directories
DIRS=("Control" "docker" "Path Planning" "perception_ws")
for dir in "${DIRS[@]}"; do
    if [ -d "$dir" ]; then
        echo "✅ Directory found: $dir"
    else
        echo "⚠️  Directory missing: $dir"
    fi
done

echo ""
echo "🎉 System check complete!"
echo ""
echo "🚀 Next steps:"
echo "1. Run: docker-compose build"
echo "2. Run: docker-compose up"
echo "3. Watch the autonomous racing system start!"
echo ""
echo "📚 For detailed instructions, see: QUICK_START.md"
