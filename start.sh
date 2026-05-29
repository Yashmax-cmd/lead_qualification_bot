#!/bin/bash
set -e

# Start the FastAPI backend in the background.
uvicorn main:app --host 0.0.0.0 --port 8000 &
UVICORN_PID=$!

# Wait for the backend to become available.
for i in {1..20}; do
  if python -c "import urllib.request, sys; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)" >/dev/null 2>&1; then
    echo "Backend is ready"
    break
  fi
  echo "Waiting for backend... ($i)"
  sleep 1
  if ! kill -0 "$UVICORN_PID" >/dev/null 2>&1; then
    echo "Backend process exited prematurely"
    exit 1
  fi
done

exec streamlit run app.py --server.port 8501 --server.address 0.0.0.0
