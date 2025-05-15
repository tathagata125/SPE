#!/bin/bash

# Create a centralized virtual environment
echo "Creating centralized virtual environment..."
python3.12 -m venv venv
source venv/bin/activate

# Install all dependencies
echo "Installing dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

echo "Setup complete! To activate the environment, run:"
echo "source venv/bin/activate"