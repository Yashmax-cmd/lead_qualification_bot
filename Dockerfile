FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Run the training script to generate the model and vectorizer during build
# In production, models might be pulled from a registry instead
RUN python generate_mock_data.py
ENV PYTHONPATH=/app
RUN python model_trainer.py

# Expose ports for both FastAPI and Streamlit
EXPOSE 8000
EXPOSE 8501

# Command to run both using a shell script or process manager
# For simplicity in docker, we'll use a shell command to start both
CMD uvicorn main:app --host 0.0.0.0 --port 8000 & streamlit run app.py --server.port 8501 --server.address 0.0.0.0
