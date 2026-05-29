# Lead Qualification Bot - Separated Streamlit & FastAPI Architecture

This refactored version separates the Streamlit frontend and FastAPI backend into independent services with **configurable ports** - perfect for GitHub Codespaces where ports are dynamically assigned.

## 🏗️ Architecture

```
lead_qualification_bot/
├── backend/                           # FastAPI Backend Service
│   ├── main.py                       # FastAPI application with CORS enabled
│   ├── config.py                     # Configuration & hyperparameters
│   ├── data_processor.py             # Data preprocessing & tokenization
│   ├── model_trainer.py              # Model training with MLflow
│   ├── generate_mock_data.py         # Mock data generation
│   ├── requirements.txt              # Backend dependencies
│   ├── Dockerfile                    # Docker image for backend
│   ├── start.sh                      # Backend startup script
│   └── .env.example                  # Environment variables template
│
├── frontend/                          # Streamlit Frontend Service
│   ├── app.py                        # Streamlit application
│   ├── requirements.txt              # Frontend dependencies
│   ├── Dockerfile                    # Docker image for frontend
│   ├── start.sh                      # Frontend startup script
│   ├── .env.example                  # Environment variables template
│   └── .streamlit/
│       └── config.toml              # Streamlit configuration
│
├── data/                             # Shared data directory
│   └── raw/
│       └── lead_scoring_dataset.csv
│
├── models/                           # Shared models directory
│   ├── hybrid_lead_model.pt
│   ├── tabular_preprocessor.joblib
│   └── distilbert_lead_classifier/
│
├── docker-compose.yml                # Orchestrates both services
├── README.md                         # Main project documentation
└── SETUP.md                         # Detailed setup instructions
```

## ✨ Key Features

### 1. **Configurable Ports**
- **FastAPI Backend:** Default `8000`, configurable via `FASTAPI_PORT` env var
- **Streamlit Frontend:** Default `8501`, configurable via `STREAMLIT_PORT` env var
- Perfect for **GitHub Codespaces** where ports are randomly assigned

### 2. **Separate Services**
- Independent deployments
- Isolated dependencies
- Easy to scale horizontally
- Flexible development workflow

### 3. **Smart API URL Configuration**
The Streamlit app loads the API URL in this order:
1. Streamlit secrets (`.streamlit/secrets.toml`)
2. Environment variables (`API_URL`)
3. User input in sidebar
4. Default (`http://127.0.0.1:8000/analyze`)

### 4. **CORS Enabled**
FastAPI backend has CORS middleware for cross-origin requests from Streamlit frontend.

### 5. **Health Checks**
Docker Compose includes health checks for robust service orchestration.

## 🚀 Quick Start

### Option 1: Local Development (Without Docker)

#### Setup Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Generate mock data and train model
python generate_mock_data.py
python model_trainer.py

# Start FastAPI server (port 8000)
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Setup Frontend (New Terminal)
```bash
cd frontend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Set API URL (localhost for local development)
export API_URL="http://127.0.0.1:8000/analyze"

# Start Streamlit (port 8501)
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
```

### Option 2: Docker Compose (Recommended)

```bash
# Build and start both services
docker-compose up --build

# Services will be available at:
# - Backend: http://localhost:8000
# - Frontend: http://localhost:8501
```

### Option 3: GitHub Codespaces

```bash
# Start both services
docker-compose up --build

# Get your Codespace URL from the "Ports" tab in the Terminal panel
# Update the API URL in the Streamlit sidebar:
# https://<your-codespace-name>-8000.preview.app.github.dev/analyze
```

## 🔧 Configuration

### Backend Environment Variables

Create `backend/.env`:
```env
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
MLFLOW_TRACKING_URI=sqlite:///mlruns.db
```

Run with custom port:
```bash
FASTAPI_PORT=5000 python -m uvicorn main:app --host 0.0.0.0 --port 5000
```

### Frontend Environment Variables

Create `frontend/.env`:
```env
STREAMLIT_PORT=8501
API_URL=http://127.0.0.1:8000/analyze
```

Run with custom port:
```bash
STREAMLIT_PORT=9000 streamlit run app.py --server.port 9000
```

### Docker Compose Custom Ports

Create `.env` in root directory:
```env
FASTAPI_PORT=5000
STREAMLIT_PORT=9000
```

Then run:
```bash
docker-compose up --build
```

## 📊 API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Simple Prediction (Text Only)
```bash
curl -X POST "http://localhost:8000/predict" \
  -H "Content-Type: application/json" \
  -d '{"customer_response": "We need a demo and pricing urgently"}'
```

### Advanced Prediction (With CRM Attributes)
```bash
curl -X POST "http://localhost:8000/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "customer_response": "We need a demo and pricing urgently",
    "total_visits": 15,
    "time_on_website": 2000,
    "page_views": 5.5,
    "source": "Google Campaigns",
    "last_activity": "Email Opened",
    "occupation": "Working Professional"
  }'
```

## 📁 Directory Structure

### Shared Directories
- **`data/raw/`** - Raw dataset (shared between backend and frontend)
- **`models/`** - Trained models (shared between backend and frontend)
- **`mlruns/`** - MLflow tracking data (created by backend)

### Isolated Directories
- **`backend/`** - FastAPI source code & dependencies
- **`frontend/`** - Streamlit source code & dependencies

## 🐳 Docker Compose Services

### Backend Service
- **Image:** `lead_qualification_bot-backend:latest`
- **Port:** `8000` (configurable via `FASTAPI_PORT`)
- **Health Check:** `/health` endpoint
- **Volumes:** `./data`, `./models`
- **Network:** `lead_network`

### Frontend Service
- **Image:** `lead_qualification_bot-frontend:latest`
- **Port:** `8501` (configurable via `STREAMLIT_PORT`)
- **Environment:** `API_URL=http://backend:8000/analyze`
- **Depends On:** Backend (waits for health check)
- **Network:** `lead_network`

## 🔄 Development Workflow

### Adding Dependencies

**Backend:**
```bash
cd backend
pip install new-package
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
pip install new-package
pip freeze > requirements.txt
```

### Rebuilding Docker Images

```bash
# Rebuild all services
docker-compose up --build

# Rebuild specific service
docker-compose up --build backend
docker-compose up --build frontend
```

### Viewing Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 🚨 Troubleshooting

### Frontend Can't Connect to Backend

1. **Check API URL Configuration:**
   - Look at Streamlit sidebar for "Backend API Endpoint URL"
   - Verify it matches your actual backend URL

2. **Local Development:**
   ```bash
   # Ensure backend is running
   curl http://localhost:8000/health
   # Should return: {"status":"healthy",...}
   ```

3. **Docker Compose:**
   ```bash
   # Check service status
   docker-compose ps
   
   # View logs
   docker-compose logs backend
   docker-compose logs frontend
   ```

4. **GitHub Codespaces:**
   - Click "Ports" tab in terminal
   - Find your forwarded port numbers
   - Update API URL in Streamlit sidebar with HTTPS URLs

### Port Already in Use

```bash
# Find process using port
lsof -i :8000  # For port 8000
lsof -i :8501  # For port 8501

# Kill process
kill -9 <PID>
```

Or use different ports:
```bash
FASTAPI_PORT=5000 STREAMLIT_PORT=9000 docker-compose up --build
```

### Model Training Issues

```bash
# Rebuild backend to retrain
docker-compose up --build backend

# Or manually in backend directory
cd backend
python generate_mock_data.py
python model_trainer.py
```

## 📚 Additional Documentation

- [SETUP.md](./SETUP.md) - Detailed setup instructions
- [Backend README](./backend/README.md) - Backend-specific documentation
- [Frontend README](./frontend/README.md) - Frontend-specific documentation

## 🎯 Next Steps

1. **Test locally** with `docker-compose up --build`
2. **Customize ports** in `.env` file
3. **Deploy** to production environment
4. **Monitor** with logs and health checks

## 📝 License

This project maintains the same license as the parent repository.

## 🤝 Contributing

When contributing:
1. Update both backend and frontend as needed
2. Update `requirements.txt` in respective directories
3. Test with Docker Compose before committing
4. Update documentation accordingly
