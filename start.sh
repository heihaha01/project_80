#!/bin/bash

# Check if project is already running
if pgrep -f "python -u run.py" > /dev/null
then
    echo "Project is already running."
    exit 1
fi

echo "Starting project_80..."
nohup python -u run.py > super_nohup.out 2>&1 &
echo "Project started with PID $!"
echo "Logs: tail -f super_nohup.out"
