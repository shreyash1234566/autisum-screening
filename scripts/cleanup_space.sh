#!/usr/bin/env bash
echo "Starting cleanup to free up disk space..."

# 1. Remove all unused Docker data (images, containers, volumes, networks)
echo "Cleaning up Docker..."
docker system prune -af --volumes

# 2. Clean up npm cache (common in Codespaces)
echo "Cleaning up npm cache..."
npm cache clean --force

# 3. Remove temporary files
echo "Cleaning up /tmp..."
sudo rm -rf /tmp/*

# 4. Clean up apt cache
echo "Cleaning up apt cache..."
sudo apt-get clean

echo "Cleanup complete! Check space with: df -h"
