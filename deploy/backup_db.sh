#!/bin/bash

# Database Backup Script for ClimateAI
# This script creates backups of PostgreSQL database

set -e

BACKUP_DIR="/opt/climateai/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/climateai_backup_$TIMESTAMP.sql"

# Create backup directory if it doesn't exist
mkdir -p $BACKUP_DIR

echo "Creating database backup: $BACKUP_FILE"

# Create backup using pg_dump
PGPASSWORD=$DB_PASSWORD pg_dump \
    -h db \
    -U climateai_user \
    -d climateai \
    --no-password \
    --format=custom \
    --compress=9 \
    --verbose \
    > "$BACKUP_FILE"

echo "Backup completed: $BACKUP_FILE"

# Keep only last 7 days of backups
find $BACKUP_DIR -name "climateai_backup_*.sql" -mtime +7 -delete

echo "Cleanup completed. Kept only last 7 days of backups."