#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

# Check whether a venv folder is actually usable
is_valid_venv() {
    local dir="$1"
    [[ -x "$dir/bin/python" && -f "$dir/bin/activate" ]]
}

# Resolve virtual environment location.
# Priority:
#   1) $VENV_DIR if provided
#   2) scripts/venv
#   3) project-root venv
#   4) create scripts/venv
if [[ -n "${VENV_DIR:-}" ]]; then
    if ! is_valid_venv "$VENV_DIR"; then
        echo "Provided VENV_DIR is invalid: $VENV_DIR"
        exit 1
    fi
else
    if is_valid_venv "$SCRIPT_DIR/venv"; then
        VENV_DIR="$SCRIPT_DIR/venv"
    elif is_valid_venv "$PROJECT_DIR/venv"; then
        VENV_DIR="$PROJECT_DIR/venv"
    else
        VENV_DIR="$SCRIPT_DIR/venv"
        echo "Creating virtual environment at: $VENV_DIR"
        python3 -m venv "$VENV_DIR"
    fi
fi

echo "Using virtual environment: $VENV_DIR"
PYTHON_BIN="$VENV_DIR/bin/python"
PIP_BIN="$VENV_DIR/bin/pip"

# Install dependencies if requirements.txt exists
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing dependencies..."
    "$PIP_BIN" install -r "$PROJECT_DIR/requirements.txt"
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
"$PYTHON_BIN" "$SCRIPT_DIR/portfolio_webservice.py" &
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

echo "✓ Webservice stopped cleanly."
