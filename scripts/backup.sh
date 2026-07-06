#!/bin/bash
# Backup script for Vehicle Detection System

set -e  # Exit on any error

echo "=== Vehicle Detection System Backup ==="
echo "This script will backup the Vehicle Detection System"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Set backup directory and timestamp
BACKUP_DIR="/opt/vehicle-detection/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_NAME="vehicle-detection-backup_$TIMESTAMP"
BACKUP_PATH="$BACKUP_DIR/$BACKUP_NAME"

# Create backup directory if it doesn't exist
mkdir -p "$BACKUP_DIR"

echo "Backup will be stored in: $BACKUP_PATH"

# Stop services temporarily for consistent backup
echo "Stopping services for backup..."
docker-compose stop

# Backup PostgreSQL database
echo "Backing up PostgreSQL database..."
mkdir -p "$BACKUP_PATH/db"
docker exec $(docker-compose ps -q db) pg_dump -U postgres vehicle_detection > "$BACKUP_PATH/db/vehicle_detection.sql"

# Backup Redis data
echo "Backing up Redis data..."
mkdir -p "$BACKUP_PATH/redis"
docker exec $(docker-compose ps -q redis) redis-cli save
docker cp $(docker-compose ps -q redis):/data/dump.rdb "$BACKUP_PATH/redis/"

# Backup application code and configuration
echo "Backing up application code and configuration..."
cp -r . "$BACKUP_PATH/app/"
cp .env.example "$BACKUP_PATH/env.example"  # Template without sensitive data

# Backup logs (optional, can be large)
echo "Backing up logs (last 7 days only)..."
mkdir -p "$BACKUP_PATH/logs"
find ./backend/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_PATH/logs/" \;
find ./ai/logs -name "*.log" -mtime -7 -exec cp {} "$BACKUP_PATH/logs/" \;

# Create backup manifest
echo "Creating backup manifest..."
cat > "$BACKUP_PATH/manifest.txt" << EOF
Vehicle Detection System Backup
===============================
Date: $(date)
Version: 1.0.0
Backup Type: Full
Services Included:
  - PostgreSQL Database
  - Redis Cache
  - Application Code
  - Configuration (template)
  - Logs (last 7 days)
EOF

# Create compressed archive
echo "Creating compressed archive..."
tar -czf "$BACKUP_PATH.tar.gz" -C "$BACKUP_DIR" "$BACKUP_NAME"

# Remove uncompressed backup directory
echo "Cleaning up temporary files..."
rm -rf "$BACKUP_PATH"

# Start services again
echo "Starting services..."
docker-compose start

# Wait for services to start
echo "Waiting for services to start..."
sleep 20

# Check service status
echo "Checking service status..."
docker-compose ps

echo ""
echo "=== Backup Complete ==="
echo "Backup created successfully: $BACKUP_PATH.tar.gz"
echo ""
echo "To restore from this backup, use:"
echo "  tar -xzf $BACKUP_PATH.tar.gz -C /tmp"
echo "  Then follow the restore.sh script instructions"
echo ""
echo "Backup size: $(du -h "$BACKUP_PATH.tar.gz" | cut -f1)"
echo ""
echo "Recommendations:"
echo "1. Store backups in a secure, off-site location"
echo "2. Regularly test your backup restoration process"
echo "3. Consider automating this script with cron for regular backups"