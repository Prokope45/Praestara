#!/bin/bash

# Script to create a database dump from the PostgreSQL container
# The dump will be saved in the backups/ directory with a timestamp

set -e

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please run ./scripts/setup-env.sh first to create the .env file."
    exit 1
fi

# Load environment variables
source .env

# Create backups directory if it doesn't exist
BACKUP_DIR="backups"
if [ ! -d "$BACKUP_DIR" ]; then
    echo "Creating backups directory..."
    mkdir -p "$BACKUP_DIR"
fi

# Generate timestamp for backup filename
TIMESTAMP=$(date +"%Y-%m-%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${TIMESTAMP}.sql"

echo "Starting database backup process..."

# Check if Docker Compose is running
if ! docker compose ps db | grep -q "Up\|running"; then
    echo "ERROR: Database container is not running!"
    echo "Please start the database with: docker compose up -d db"
    exit 1
fi

# Wait for database to be healthy
echo "Checking database health..."
MAX_RETRIES=30
RETRY_COUNT=0

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
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

# Create database dump
echo "Creating database dump..."
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists > "$BACKUP_FILE"

# Check if dump was successful
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "SUCCESS: Database backup created successfully!"
    echo "Backup file: $BACKUP_FILE"
    echo "File size: $FILE_SIZE"
else
    echo "ERROR: Backup file was not created or is empty!"
    exit 1
fi
