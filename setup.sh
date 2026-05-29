#!/bin/bash

# Quick setup script for the separated architecture
# Usage: bash setup.sh

set -e

echo "================================================"
echo "Lead Qualification Bot - Quick Setup"
echo "================================================"
echo ""

# Check if Docker and Docker Compose are available
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

echo "✅ Docker and Docker Compose found"
echo ""

# Ask user for port configuration
read -p "Enter FastAPI port (default: 8000): " FASTAPI_PORT
FASTAPI_PORT=${FASTAPI_PORT:-8000}

read -p "Enter Streamlit port (default: 8501): " STREAMLIT_PORT
STREAMLIT_PORT=${STREAMLIT_PORT:-8501}

echo ""
echo "Creating .env file..."
cat > .env << EOF
FASTAPI_PORT=$FASTAPI_PORT
STREAMLIT_PORT=$STREAMLIT_PORT
EOF

echo "✅ .env file created"
echo ""

echo "Building Docker images..."
docker-compose build

echo ""
echo "✅ Setup complete!"
echo ""
echo "Starting services..."
echo "- FastAPI Backend: http://localhost:$FASTAPI_PORT"
echo "- Streamlit Frontend: http://localhost:$STREAMLIT_PORT"
echo ""

docker-compose up -d

echo "✅ Services are starting..."
echo ""
echo "Check status with: docker-compose ps"
echo "View logs with: docker-compose logs -f"
echo ""
echo "For GitHub Codespaces:"
echo "1. Open the Ports tab in Terminal"
echo "2. Find your forwarded URLs"
echo "3. Update API URL in Streamlit sidebar"
