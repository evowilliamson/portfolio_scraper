#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Create virtual environment in parent directory if it doesn't exist
if [ ! -d "../venv" ]; then
    echo "Creating virtual environment in parent directory..."
    python3 -m venv ../venv
fi

# Activate virtual environment from parent directory
echo "Activating virtual environment..."
source ../venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "../requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r ../requirements.txt
fi

FLASK_HOST="${FLASK_HOST:-0.0.0.0}"
FLASK_PORT="${FLASK_PORT:-5000}"
HEALTH_HOST="${HEALTH_HOST:-127.0.0.1}"

stop_flask() {
    if [[ -n "${FLASK_PID:-}" ]] && kill -0 "$FLASK_PID" 2>/dev/null; then
        echo "Stopping Flask (PID: $FLASK_PID)..."
        kill -TERM "$FLASK_PID"
        # Wait up to 15 seconds for graceful shutdown
        for _ in {1..15}; do
            if ! kill -0 "$FLASK_PID" 2>/dev/null; then
                echo "Flask stopped gracefully."
                return
            fi
            sleep 1
        done
        echo "Flask did not exit in time; force killing..."
        kill -KILL "$FLASK_PID" || true
    fi
}

trap stop_flask EXIT

echo "Starting Flask webservice..."
python3 portfolio_webservice.py &
FLASK_PID=$!

echo "Waiting for Flask to start (health check)..."
for _ in {1..30}; do
    if curl -sf "http://${HEALTH_HOST}:${FLASK_PORT}/health" >/dev/null 2>&1; then
        echo "✓ Flask is up and running!"
        break
    fi
    sleep 1
done

echo ""
echo "Webservice is running!"
echo "Will automatically stop after 10 minutes..."
echo ""

# Wait for 10 minutes (600 seconds)
sleep 600

echo ""
echo "10 minutes elapsed. Shutting down gracefully..."
stop_flask

# Deactivate virtual environment
deactivate

echo "✓ Webservice stopped cleanly."
