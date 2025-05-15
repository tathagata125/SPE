#!/bin/bash

# Navigate to the frontend directory
cd "$(dirname "$0")"

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Check if dependencies are installed
if ! pip list | grep -q streamlit; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

# Run the Streamlit application
echo "Starting frontend server..."
streamlit run app.py