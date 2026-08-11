# Dockerfile for AI Service
FROM nvidia/cuda:12.1.1-runtime-ubuntu22.04

# Set working directory
WORKDIR /app

# Install system dependencies: build tools (needed by some Python wheels),
# OpenCV runtime libs and PaddleOCR shared libraries.
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-numpy \
    python3-dev \
    build-essential \
    swig \
    libgl1 \
    libglib2.0-0 \
    libglib2.0-dev \
    libgomp1 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools to avoid compatibility issues
RUN pip3 install --upgrade pip setuptools wheel

# Install CPU builds of PyTorch first (smaller image, works without a GPU);
# `-r requirements.txt` then skips torch because it is already satisfied.
RUN pip3 install --no-cache-dir \
    torch==2.4.0 \
    --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --default-timeout=100

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos '' appuser
USER appuser

# Expose port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://127.0.0.1:8001/health', timeout=5).status == 200 else sys.exit(1)"

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
