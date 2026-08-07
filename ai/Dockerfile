# Dockerfile for AI Service
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies including pip
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to avoid compatibility issues
RUN pip3 install --upgrade pip setuptools wheel

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --default-timeout=100 --only-binary=:all:

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8001/health || exit 1

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]