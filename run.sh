#!/bin/bash
PROJECT_PATH="/home/pi/project/seek_new"
/home/pi/.local/bin/uv run python -m main
# echo "$(date) - Seek - INFO - run.sh started" >> "$PROJECT_PATH/log/default.log"