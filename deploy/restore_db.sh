#!/bin/bash

# Database Restore Script for ClimateAI
# This script restores PostgreSQL database from backup

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup_file>"
    echo "Available backups:"
    ls -la /opt/climateai/backups/climateai_backup_*.sql 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file $BACKUP_FILE does not exist"
    exit 1
fi

echo "Restoring database from: $BACKUP_FILE"
echo "WARNING: This will overwrite the current database!"
read -p "Are you sure you want to continue? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Stop the backend service to prevent data corruption
echo "Stopping backend service..."
docker-compose -f docker-compose.prod.yml stop backend

# Restore the database
echo "Restoring database..."
PGPASSWORD=$DB_PASSWORD pg_restore \
    -h db \
    -U climateai_user \
    -d climateai \
    --no-password \
    --clean \
    --if-exists \
    --create \
    --verbose \
    "$BACKUP_FILE"

# Start the backend service
echo "Starting backend service..."
docker-compose -f docker-compose.prod.yml start backend

echo "Database restore completed."
