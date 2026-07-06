#!/bin/bash
# Update script for Vehicle Detection System

set -e  # Exit on any error

echo "=== Vehicle Detection System Update ==="
echo "This script will update the Vehicle Detection System"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Change to application directory
cd /opt/vehicle-detection/vehicle-detection-system || {
    echo "Application directory not found. Please check installation."
    exit 1
}

# Pull latest changes
echo "Pulling latest changes from repository..."
git pull

# Update Python dependencies (backend)
echo "Updating backend dependencies..."
cd backend
pip install --upgrade -r requirements.txt
cd ..

# Update Python dependencies (AI service)
echo "Updating AI service dependencies..."
cd ai
pip install --upgrade -r requirements.txt
cd ..

# Update Node.js dependencies (frontend)
echo "Updating frontend dependencies..."
cd frontend
npm update
cd ..

# Pull latest Docker images
echo "Pulling latest Docker images..."
docker-compose pull

# Recreate containers with updated images
echo "Updating services..."
docker-compose up -d --build --remove-orphans

# Run database migrations (if any)
echo "Checking for database migrations..."
# In a real implementation, you would run alembic upgrade head here
echo "Skipping automatic migrations - please run manually if needed:"
echo "  docker-compose exec backend alembic upgrade head"

# Restart services
echo "Restarting services..."
docker-compose restart

# Wait for services to start
echo "Waiting for services to start..."
sleep 20

# Check service status
echo "Checking service status..."
docker-compose ps

echo ""
echo "=== Update Complete ==="
echo "Vehicle Detection System has been updated!"
echo ""
echo "Recommendations:"
echo "1. Check the logs for any issues: docker-compose logs -f"
echo "2. Verify that all services are running correctly"
echo "3. Test the system functionality"
echo "4. Review the changelog for any breaking changes"