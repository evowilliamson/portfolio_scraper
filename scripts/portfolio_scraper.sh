#!/bin/bash

# Create virtual environment in parent directory if it doesn't exist
if [ ! -d "../.venv" ]; then
    echo "Creating virtual environment in parent directory..."
    python3 -m venv ../.venv
fi

# Activate virtual environment from parent directory
echo "Activating virtual environment..."
source ../.venv/bin/activate

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the portfolio scraper
echo "Running portfolio_scraper.py..."
python3 portfolio_scraper.py

# Deactivate virtual environment
deactivate