#!/bin/bash

# Start the Weather Ops services using the centralized venv
echo "Starting Weather_ops services..."

# Activate the centralized virtual environment
source venv/bin/activate

# Start backend in the background
echo "Starting backend service..."
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!
cd ..

# Wait a moment for backend to initialize
sleep 2

# Start frontend
echo "Starting frontend service..."
cd frontend
streamlit run app.py

# Cleanup when frontend exits
kill $BACKEND_PID