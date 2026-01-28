#!/bin/bash

# Script to restore a database dump into the PostgreSQL container
# Usage: ./scripts/restore-db.sh <path-to-dump-file>

set -e

# Check if dump file argument is provided
if [ $# -eq 0 ]; then
    echo "ERROR: No dump file specified!"
    echo "Usage: $0 <path-to-dump-file>"
    echo "Example: $0 backups/backup_2026-01-27.sql"
    exit 1
fi

DUMP_FILE="$1"

# Check if dump file exists
if [ ! -f "$DUMP_FILE" ]; then
    echo "ERROR: Dump file not found: $DUMP_FILE"
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    echo "ERROR: .env file not found!"
    echo "Please run ./scripts/setup-env.sh first to create the .env file."
    exit 1
fi

# Load environment variables
source .env

echo "Starting database restore process..."
echo "Dump file: $DUMP_FILE"

# Check if Docker Compose is running
if ! docker compose ps db | grep -q "Up\|running"; then
    echo "WARNING: Database container is not running."
    echo "Starting database container..."
    docker compose up -d db
    echo "Waiting for database to be ready..."
    sleep 10
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

# Determine dump file type and restore accordingly
echo "Restoring database from dump file..."

# Check if it's a custom format dump (pg_dump -Fc) or SQL dump
if file "$DUMP_FILE" | grep -q "PostgreSQL custom database dump"; then
    # Custom format - use pg_restore
    echo "Detected custom format dump, using pg_restore..."
    docker compose exec -T db pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --clean --if-exists < "$DUMP_FILE"
else
    # SQL format - use psql
    echo "Detected SQL format dump, using psql..."
    docker compose exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" < "$DUMP_FILE"
fi

echo "SUCCESS: Database restored successfully from $DUMP_FILE"
