#!/bin/bash

# Frontend startup script for Streamlit

set -e

# Get port from environment or use default
PORT=${STREAMLIT_PORT:-8501}
API_URL=${API_URL:-"http://127.0.0.1:8000/analyze"}

echo "Starting Streamlit frontend on port $PORT..."
echo "Backend API URL: $API_URL"

# Start Streamlit
streamlit run app.py --server.port "$PORT" --server.address 0.0.0.0 --logger.level=info
