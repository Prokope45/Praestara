#!/bin/bash

# Script to update the PostgreSQL password in the database to match the .env file
# This is useful when you have an existing database but need to sync the password

set -e

echo "PostgreSQL Password Update Script"
echo "=================================="
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please ensure you have a .env file with POSTGRES_PASSWORD set."
    exit 1
fi

# Load environment variables
source .env

# Check if POSTGRES_PASSWORD is set
if [ -z "$POSTGRES_PASSWORD" ]; then
    echo "ERROR: POSTGRES_PASSWORD is not set in .env file!"
    exit 1
fi

# Check if POSTGRES_USER is set
if [ -z "$POSTGRES_USER" ]; then
    echo "ERROR: POSTGRES_USER is not set in .env file!"
    exit 1
fi

# Check if POSTGRES_DB is set
if [ -z "$POSTGRES_DB" ]; then
    echo "ERROR: POSTGRES_DB is not set in .env file!"
    exit 1
fi

echo "This script will update the PostgreSQL password for user '$POSTGRES_USER'"
echo "to match the password in your .env file."
echo ""
echo "WARNING: Make sure you have a backup of your database before proceeding!"
echo ""
read -p "Do you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

# Check if Docker Compose is available
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed or not in PATH!"
    exit 1
fi

# Check if database container is running
echo ""
echo "Checking if database container is running..."
if ! docker compose ps db | grep -q "Up\|running"; then
    echo "Database container is not running. Starting it..."
    docker compose up -d db
    echo "Waiting for database to start..."
    sleep 5
fi

# Wait for database to be healthy
echo "Waiting for database to be ready..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    # Try to connect without password check (using trust or existing password)
    if docker compose exec -T db pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
        echo "Database is ready!"
        break
    fi
    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Waiting for database... ($RETRY_COUNT/$MAX_RETRIES)"
    sleep 2
done

if [ $RETRY_COUNT -eq $MAX_RETRIES ]; then
    echo "ERROR: Database did not become ready in time!"
    exit 1
fi

# Update the password
echo ""
echo "Updating password for user '$POSTGRES_USER'..."

# Escape single quotes in password for SQL
ESCAPED_PASSWORD=$(echo "$POSTGRES_PASSWORD" | sed "s/'/''/g")

# Execute the ALTER USER command
if docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "ALTER USER $POSTGRES_USER WITH PASSWORD '$ESCAPED_PASSWORD';" > /dev/null 2>&1; then
    echo "SUCCESS: Password updated successfully!"
    echo ""
    echo "The database password has been updated to match your .env file."
    echo "You can now restart your services with: docker compose restart"
else
    echo "ERROR: Failed to update password!"
    echo ""
    echo "This might happen if:"
    echo "1. The current password in the database doesn't match what Docker expects"
    echo "2. There are permission issues"
    echo ""
    echo "Try stopping all services and starting just the database:"
    echo "  docker compose down"
    echo "  docker compose up -d db"
    echo "Then run this script again."
    exit 1
fi
