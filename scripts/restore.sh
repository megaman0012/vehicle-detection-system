#!/bin/bash
# Restore script for Vehicle Detection System

set -e  # Exit on any error

echo "=== Vehicle Detection System Restore ==="
echo "This script will restore the Vehicle Detection System from a backup"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Check if backup file is provided
if [ $# -eq 0 ]; then
    echo "Usage: $0 <backup-file.tar.gz>"
    echo ""
    echo "Available backups:"
    ls -la /opt/vehicle-detection/backups/*.tar.gz 2>/dev/null || echo "No backups found"
    exit 1
fi

BACKUP_FILE="$1"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Set restore directory
RESTORE_DIR="/tmp/vehicle-detection-restore_$(date +%s)"
BACKUP_DIR="/opt/vehicle-detection/backups"

echo "Restore directory: $RESTORE_DIR"
echo "Backup file: $BACKUP_FILE"

# Create restore directory
mkdir -p "$RESTORE_DIR"

# Extract backup
echo "Extracting backup..."
tar -xzf "$BACKUP_FILE" -C "$RESTORE_DIR"

# Find the extracted directory (should be one with timestamp)
BACKUP_NAME=$(basename "$BACKUP_FILE" .tar.gz)
EXTRACTED_DIR="$RESTORE_DIR/$BACKUP_NAME"

if [ ! -d "$EXTRACTED_DIR" ]; then
    echo "Error: Could not find extracted backup directory"
    exit 1
fi

echo "Found backup: $BACKUP_NAME"

# Stop services
echo "Stopping services..."
docker-compose stop

# Backup current state (just in case)
echo "Creating pre-restore backup..."
./backup.sh

# Restore PostgreSQL database
echo "Restoring PostgreSQL database..."
if [ -f "$EXTRACTED_DIR/db/vehicle_detection.sql" ]; then
    # Drop and recreate database
    docker-compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS vehicle_detection;"
    docker-compose exec -T db psql -U postgres -c "CREATE DATABASE vehicle_detection;"
    
    # Restore data
    cat "$EXTRACTED_DIR/db/vehicle_detection.sql" | docker-compose exec -T db psql -U postgres vehicle_detection
    echo "Database restored successfully"
else
    echo "Warning: No database backup found in $EXTRACTED_DIR/db/vehicle_detection.sql"
fi

# Restore Redis data
echo "Restoring Redis data..."
if [ -f "$EXTRACTED_DIR/redis/dump.rdb" ]; then
    # Stop Redis, replace data, start Redis
    docker-compose stop redis
    docker cp "$EXTRACTED_DIR/redis/dump.rdb" $(docker-compose ps -q redis):/data/dump.rdb
    docker-compose start redis
    echo "Redis data restored successfully"
else
    echo "Warning: No Redis backup found in $EXTRACTED_DIR/redis/dump.rdb"
fi

# Restore application code and configuration
echo "Restoring application code..."
# Note: We don't restore .env to avoid overwriting current configuration
# Only restore the application code
cp -r "$EXTRACTED_DIR/app/"* ./
echo "Application code restored"

# Start services
echo "Starting services..."
docker-compose start

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Run database migrations if needed
echo "Checking for needed migrations..."
# In a real implementation, you would check if migrations are needed
echo "If you updated to a newer version, you may need to run:"
echo "  docker-compose exec backend alembic upgrade head"

# Check service status
echo "Checking service status..."
docker-compose ps

# Clean up
echo "Cleaning up temporary files..."
rm -rf "$RESTORE_DIR"

echo ""
echo "=== Restore Complete ==="
echo "Vehicle Detection System has been restored from: $BACKUP_FILE"
echo ""
echo "Important notes:"
echo "1. Check the logs for any issues: docker-compose logs -f"
echo "2. Verify that all services are running correctly"
echo "3. Test the system functionality"
echo "4. If you restored to a different version, you may need to run database migrations"
echo "5. Review any configuration changes that may be needed"
echo ""
echo "To verify the restoration, check:"
echo "  - Database records: docker-compose exec db psql -U postgres -d vehicle_detection -c \"SELECT COUNT(*) FROM users;\""
echo "  - Redis keys: docker-compose exec redis redis-cli KEYS \"*\" | head -10"