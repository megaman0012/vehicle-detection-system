#!/bin/bash
# Installation script for Vehicle Detection System on CentOS 10

set -e  # Exit on any error

echo "=== Vehicle Detection System Installation ==="
echo "This script will install the Vehicle Detection System on CentOS 10"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Update system
echo "Updating system packages..."
dnf update -y

# Install dependencies
echo "Installing dependencies..."
dnf install -y \
    docker \
    docker-compose \
    git \
    wget \
    curl \
    unzip \
    nginx \
    postgresql15 \
    postgresql15-server \
    redis \
    ffmpeg \
    nvidia-docker2 \
    cuda-toolkit-12-1

# Start and enable services
echo "Starting and enabling services..."
systemctl enable --now docker
systemctl enable --now nginx
systemctl enable --now postgresql
systemctl enable --now redis

# Add current user to docker group
echo "Adding user to docker group..."
usermod -aG docker $USER || echo "User already in docker group or failed to add"

# Configure PostgreSQL
echo "Configuring PostgreSQL..."
/usr/pgsql-15/bin/postgresql-15-setup initdb
systemctl enable --now postgresql-15

# Configure Redis
echo "Configuring Redis..."
systemctl enable --now redis

# Create system user for the application
echo "Creating system user..."
useradd -r -s /bin/false vehicle-detection || echo "User already exists"

# Create application directory
echo "Creating application directory..."
mkdir -p /opt/vehicle-detection
chown -R vehicle-detection:vehicle-detection /opt/vehicle-detection

# Clone repository (if not already present)
if [ ! -d "/opt/vehicle-detection/vehicle-detection-system" ]; then
    echo "Cloning repository..."
    git clone https://github.com/your-repo/vehicle-detection-system.git /opt/vehicle-detection/vehicle-detection-system
else
    echo "Repository already exists, pulling latest changes..."
    cd /opt/vehicle-detection/vehicle-detection-system
    git pull
fi

# Copy environment file
echo "Setting up environment variables..."
cd /opt/vehicle-detection/vehicle-detection-system
cp .env.example .env
echo "Please edit .env file with your configuration values"

# Build and start services
echo "Building and starting services with Docker Compose..."
docker-compose pull || echo "No images to pull, building from scratch"
docker-compose up -d --build

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check service status
echo "Checking service status..."
docker-compose ps

# Configure nginx as reverse proxy (optional)
echo "Configuring nginx as reverse proxy..."
cp ./frontend/nginx.conf /etc/nginx/conf.d/vehicle-detection.conf
nginx -t && systemctl reload nginx

# Setup firewall (if firewalld is active)
if systemctl is-active --quiet firewalld; then
    echo "Configuring firewall..."
    firewall-cmd --permanent --add-service=http
    firewall-cmd --permanent --add-service=https
    firewall-cmd --reload
fi

echo ""
echo "=== Installation Complete ==="
echo "Vehicle Detection System has been installed!"
echo ""
echo "Access the system at: http://your-server-ip"
echo ""
echo "Important next steps:"
echo "1. Edit the .env file with your configuration"
echo "2. Change the default admin password"
echo "3. Configure your Hikvision camera RTSP URLs"
echo "4. Set up SSL certificates for HTTPS (optional but recommended)"
echo "5. Monitor the logs: docker-compose logs -f"
echo ""
echo "For GPU support, ensure NVIDIA drivers are installed and nvidia-docker2 is configured"