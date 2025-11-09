#!/bin/bash
# Production Deployment Script for KSEB Dash Application

echo "=== KSEB Dash Application - Production Deployment ==="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing/updating dependencies..."
pip install -r requirements.txt

echo ""
echo "=== Starting Production Server ==="
echo "Using: Gunicorn with 4 workers (gevent)"
echo "Port: 8050"
echo "Access: http://localhost:8050"
echo ""

# Run with gunicorn
gunicorn app_optimized:server \
    --workers 4 \
    --worker-class gevent \
    --worker-connections 1000 \
    --timeout 300 \
    --bind 0.0.0.0:8050 \
    --access-logfile access.log \
    --error-logfile error.log \
    --log-level info \
    --reload

# For more workers (if you have more CPU cores):
# --workers $(nproc)

# For specific IP binding:
# --bind 127.0.0.1:8050  # Localhost only
# --bind 0.0.0.0:8050    # All interfaces

# With SSL/HTTPS:
# --certfile=/path/to/cert.pem --keyfile=/path/to/key.pem
