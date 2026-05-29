FROM python:3.10-slim

WORKDIR /app/frontend

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend files
COPY . .

# Expose port (default 8501, can be overridden)
EXPOSE 8501

# Environment variables
ENV PYTHONPATH=/app
ENV STREAMLIT_PORT=8501
ENV API_URL="http://backend:8000/analyze"

# Run Streamlit app
CMD ["streamlit", "run", "app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
