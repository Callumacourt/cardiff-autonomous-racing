#!/bin/bash
# File: scripts/build_docker.sh
set -e

#!/bin/bash

# Build script for Cardiff Autonomous Racing Docker containers

echo "🏗️ Building Cardiff Autonomous Racing Docker containers..."

# Build base image first
echo "📦 Building base image..."
docker build -f docker/Dockerfile.base -t cardiff-racing:base .

if [ $? -ne 0 ]; then
    echo "❌ Base image build failed!"
    exit 1
fi

echo "✅ Base image built successfully!"

# Build planning image
echo "🛣️ Building path planning image..."
docker build -f docker/Dockerfile.planning -t cardiff-racing:planning .

if [ $? -ne 0 ]; then
    echo "❌ Planning image build failed!"
    exit 1
fi

echo "✅ Planning image built successfully!"

# Build all containers using docker-compose
echo "🚀 Building all containers with docker-compose..."
docker-compose build

if [ $? -ne 0 ]; then
    echo "❌ Docker-compose build failed!"
    exit 1
fi

echo "🎉 All containers built successfully!"
echo ""
echo "To run the system:"
echo "  docker-compose up"
echo ""
echo "To run in background:"
echo "  docker-compose up -d"
echo ""
echo "To view logs:"
echo "  docker-compose logs -f"

# Build base image
echo "📦 Building base image..."
docker build -f docker/Dockerfile.base -t cardiff-racing:base .

# Build perception image
echo "🎯 Building perception image..."
docker build -f docker/Dockerfile.perception -t cardiff-racing:perception .

# Build planning image
echo "🛣️ Building planning image..."
docker build -f docker/Dockerfile.planning -t cardiff-racing:planning .

echo "✅ All Docker images built successfully!"
docker images | grep cardiff-racing