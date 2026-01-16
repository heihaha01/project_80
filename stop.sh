#!/bin/bash

echo "Stopping project_80..."
pkill -f "python -u run.py"

if [ $? -eq 0 ]; then
    echo "Process stopped successfully."
else
    echo "No running process found or failed to stop."
fi
