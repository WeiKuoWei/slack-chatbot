#!/bin/bash

# Remove old virtual environment if it exists
echo "Removing existing virtual environment..."
rm -rf .venv

# Verify Python installation
echo "Checking Python version..."
python3 --version

# Create new virtual environment
echo "Creating new virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install required packages
echo "Installing required packages..."
pip install -r requirements.txt

echo "Setup complete!"
