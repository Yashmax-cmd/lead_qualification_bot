FROM python:3.10-slim

WORKDIR /app/backend

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend files
COPY . .

# Create data and models directories
RUN mkdir -p ../data/raw ../models

# Expose port (default 8000, can be overridden)
EXPOSE 8000

# Environment variables
ENV PYTHONPATH=/app
ENV FASTAPI_HOST=0.0.0.0
ENV FASTAPI_PORT=8000

# Generate mock data and train model during build
RUN python generate_mock_data.py
RUN python model_trainer.py

# Run FastAPI server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
