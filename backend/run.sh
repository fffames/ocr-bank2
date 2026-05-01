#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}")" && pwd )"

# Activate venv
source "$SCRIPT_DIR/venv/bin/activate"

# Set PYTHONPATH to include backend directory
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# Change to script directory
cd "$SCRIPT_DIR"

# Start server
echo "Starting server from: $SCRIPT_DIR"
echo "Python path: $PYTHONPATH"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
