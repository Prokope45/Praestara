#!/bin/bash

# Script to set up .env file with secure secrets
# This script copies .env.example to .env and generates secure values for SECRET_KEY and POSTGRES_PASSWORD

set -e

echo "Setting up environment file..."

# Check if .env already exists
if [ -f .env ]; then
    echo "WARNING: .env file already exists!"
    read -p "Do you want to overwrite it? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Setup cancelled. Existing .env file preserved."
        exit 0
    fi
fi

# Check if .env.example exists
if [ ! -f .env.example ]; then
    echo "ERROR: .env.example file not found!"
    exit 1
fi

# Check if Python is available
if ! command -v python3 &> /dev/null && ! command -v python &> /dev/null; then
    echo "ERROR: Python is not installed or not in PATH!"
    exit 1
fi

# Determine Python command
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

echo "Copying .env.example to .env..."
cp .env.example .env

echo "Generating secure SECRET_KEY..."
SECRET_KEY=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")

echo "Generating secure POSTGRES_PASSWORD..."
POSTGRES_PASSWORD=$($PYTHON_CMD -c "import secrets; print(secrets.token_urlsafe(32))")

echo "Updating .env file with generated secrets..."

# Use different sed syntax based on OS
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    sed -i '' "s|SECRET_KEY=changethis|SECRET_KEY=${SECRET_KEY}|g" .env
    sed -i '' "s|POSTGRES_PASSWORD=changethis|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|g" .env
else
    # Linux
    sed -i "s|SECRET_KEY=changethis|SECRET_KEY=${SECRET_KEY}|g" .env
    sed -i "s|POSTGRES_PASSWORD=changethis|POSTGRES_PASSWORD=${POSTGRES_PASSWORD}|g" .env
fi

echo "SUCCESS: Environment file setup complete!"
echo ""
echo "Generated credentials:"
echo "   SECRET_KEY: ${SECRET_KEY}"
echo "   POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}"
echo ""
echo "WARNING: Keep these credentials secure and do not commit the .env file to version control!"
