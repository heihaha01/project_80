#!/bin/bash

# 1. Kill existing process
echo "Stopping existing project_80 process..."
pkill -f "python -u run.py"

# Optional: wait a moment for the port to be freed
sleep 1

# 2. Update code (optional, uncomment if you want auto-pull)
# git pull

# 3. Start new process
echo "Starting project_80..."
# Use nohup to run in background, redirect both stdout and stderr (2>&1)
nohup python -u run.py > super_nohup.out 2>&1 &

echo "Project started! Logs are being written to super_nohup.out"
echo "You can view logs with: tail -f super_nohup.out"
