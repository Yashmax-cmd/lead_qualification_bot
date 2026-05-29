#!/bin/bash

# Backend startup script for FastAPI

set -e

# Get port from environment or use default
PORT=${FASTAPI_PORT:-8000}
HOST=${FASTAPI_HOST:-0.0.0.0}

echo "Starting FastAPI backend on $HOST:$PORT..."

# Generate mock data if data doesn't exist
if [ ! -f ../data/raw/lead_scoring_dataset.csv ]; then
    echo "Generating mock data..."
    python generate_mock_data.py
fi

# Train the model if it doesn't exist
if [ ! -f ../models/hybrid_lead_model.pt ]; then
    echo "Training model..."
    python model_trainer.py
fi

# Start FastAPI server with uvicorn
python -m uvicorn main:app --host "$HOST" --port "$PORT" --reload
