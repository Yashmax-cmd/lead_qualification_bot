# Complete Implementation Guide - Separated Architecture

## 🎯 Overview

This guide shows how to use the refactored Lead Qualification Bot with separated Streamlit (frontend) and FastAPI (backend) services.

## 🏗️ Architecture Components

```
┌─────────────────────────────────────────────────┐
│         User's Browser                          │
│  (Streamlit Frontend on port 8501)              │
└──────────────┬──────────────────────────────────┘
               │ HTTP Requests
               │ (Dynamic API URL)
               ▼
┌─────────────────────────────────────────────────┐
│      FastAPI Backend (port 8000)                │
│  • Model Loading                                │
│  • Lead Prediction                              │
│  • Health Checks                                │
│  • CORS Enabled                                 │
└──────────────┬──────────────────────────────────┘
               │
        ┌──────┴──────┐
        ▼             ▼
    Data Files    Model Files
    (shared/)     (shared/)
```

## 🚀 Implementation Options

### Option 1: Local Development (Recommended for Development)

#### Prerequisites
- Python 3.10+
- pip or conda
- At least 4GB RAM

#### Setup Backend
```bash
cd backend
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

pip install -r requirements.txt

# Generate mock data
python generate_mock_data.py

# Train the model (first time only, ~5-10 minutes)
python model_trainer.py
```

#### Start Backend
```bash
# Terminal 1
cd backend
source venv/bin/activate  # or your OS equivalent
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

#### Setup Frontend
```bash
cd frontend
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # or your OS equivalent

pip install -r requirements.txt
```

#### Start Frontend
```bash
# Terminal 2
cd frontend
source venv/bin/activate  # or your OS equivalent

# For local development with localhost backend:
API_URL="http://127.0.0.1:8000/analyze" streamlit run app.py --server.port 8501

# Or let it use default localhost in sidebar
streamlit run app.py --server.port 8501
```

Access Streamlit at: `http://localhost:8501`

---

### Option 2: Docker Compose (Recommended for Production/Deployment)

#### Prerequisites
- Docker
- Docker Compose
- 4GB available disk space

#### Build and Start
```bash
# From root directory
docker-compose up --build
```

This will:
1. Build backend image from `backend/Dockerfile`
2. Build frontend image from `frontend/Dockerfile`
3. Start both services on default ports (8000, 8501)
4. Create shared network for service-to-service communication

#### Access Services
- **Backend API:** http://localhost:8000
- **Frontend:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

#### Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

#### Stop Services
```bash
docker-compose down
```

---

### Option 3: GitHub Codespaces (Recommended for Collaborative Development)

#### Setup
```bash
# In Codespaces terminal
docker-compose up --build
```

#### Get Service URLs
1. Look for the "**Ports**" tab in the Terminal panel (VS Code)
2. You'll see two forwarded ports:
   - `8000` (Backend) → Copy the forwarded URL
   - `8501` (Frontend) → Copy the forwarded URL

#### Configure API URL
1. Open Frontend URL in browser
2. In left sidebar, find "**⚙️ API Configuration**"
3. Paste your backend's forwarded URL in the text input
4. Format should be: `https://<name>-8000.preview.app.github.dev/analyze`

#### Key Points
- Always use HTTPS in Codespaces
- Ports change per session, update URL each time
- Health check helps manage service dependencies
- Perfect for team collaboration

---

### Option 4: Custom Ports (For Port Conflicts)

#### Local Development
```bash
# Terminal 1 - Backend on port 5000
cd backend
FASTAPI_PORT=5000 python -m uvicorn main:app --host 0.0.0.0 --port 5000

# Terminal 2 - Frontend on port 9000
cd frontend
API_URL="http://127.0.0.1:5000/analyze" streamlit run app.py --server.port 9000
```

#### Docker Compose
```bash
# Create .env file
echo "FASTAPI_PORT=5000" > .env
echo "STREAMLIT_PORT=9000" >> .env

# Start with custom ports
docker-compose up --build
```

Access at:
- Backend: http://localhost:5000
- Frontend: http://localhost:9000

---

## 🔧 Configuration Files

### Root Level: `.env`
```env
# Optional: Only needed for custom ports
FASTAPI_PORT=8000
STREAMLIT_PORT=8501
```

### Backend: `backend/.env`
```env
FASTAPI_HOST=0.0.0.0
FASTAPI_PORT=8000
MLFLOW_TRACKING_URI=sqlite:///mlruns.db
```

### Frontend: `frontend/.env`
```env
STREAMLIT_PORT=8501
# For local dev with localhost
API_URL=http://127.0.0.1:8000/analyze
# For Docker Compose
# API_URL=http://backend:8000/analyze
# For Codespaces (replace with actual URL)
# API_URL=https://your-codespace-8000-url.preview.app.github.dev/analyze
```

---

## 📊 Testing the Services

### Health Check
```bash
curl http://localhost:8000/health
# Response: {"status":"healthy","device":"cpu","model_loaded":true}
```

### Simple Prediction
```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"customer_response":"We need a demo and pricing urgently"}'
```

### Advanced Prediction (With CRM Attributes)
```bash
curl -X POST http://localhost:8000/analyze \
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

---

## 🔄 Development Workflows

### Adding Dependencies

**Backend:**
```bash
cd backend
source venv/bin/activate  # or activate.bat on Windows
pip install new-package
pip freeze > requirements.txt
```

**Frontend:**
```bash
cd frontend
source venv/bin/activate  # or activate.bat on Windows
pip install new-package
pip freeze > requirements.txt
```

### Updating Backend Code
- **Local:** Changes reload automatically with `--reload` flag
- **Docker:** Rebuild with `docker-compose up --build backend`

### Updating Frontend Code
- **Local:** Streamlit auto-reloads on save
- **Docker:** Streamlit auto-reloads in container

### Debugging

**Backend Logs:**
```bash
# Local
python -m uvicorn main:app --log-level debug

# Docker
docker-compose logs -f backend
```

**Frontend Logs:**
```bash
# Local - Visible in terminal
streamlit run app.py --logger.level=debug

# Docker
docker-compose logs -f frontend
```

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| `Port 8000 already in use` | Use custom port: `FASTAPI_PORT=5000` |
| `Port 8501 already in use` | Use custom port: `STREAMLIT_PORT=9000` |
| `Frontend can't reach backend` | Check API URL in sidebar, ensure backend is running |
| `Model training takes too long` | First run trains the model (~10 min), subsequent runs are instant |
| `Docker build fails` | Run `docker-compose down -v` then retry |
| `Codespaces: HTTPS required` | Use URLs from Ports tab, not localhost |
| `API returns 503 error` | Backend model still loading, wait 30-40 seconds |

---

## 📈 Performance Considerations

### Local Development
- Backend RAM: ~2GB (with model loaded)
- Frontend RAM: ~500MB
- CPU: Moderate (model inference is fast)
- Disk: ~3GB for models

### Docker
- Total RAM needed: ~3GB
- CPU: Moderate
- Disk: ~5GB for images + data
- Network: Fast local communication between containers

### Codespaces
- Default 4GB RAM (sufficient)
- CPU: 2-4 cores
- Startup time: ~2-3 minutes (includes model training)
- Network: Good for API communication

---

## 🔐 Security Best Practices

1. **Never commit `.env` files** with actual credentials
2. **Use environment variables** for sensitive data
3. **Enable HTTPS** in production (Codespaces does this automatically)
4. **Validate input** before sending to backend
5. **Use proper authentication** if deployed publicly
6. **Limit CORS origins** in production instead of `*`

---

## 📚 Project Structure

```
backend/
  ├── main.py                 # FastAPI application
  ├── config.py              # Configuration
  ├── data_processor.py      # NLP preprocessing
  ├── model_trainer.py       # Model training
  ├── generate_mock_data.py  # Data generation
  ├── requirements.txt       # Dependencies
  ├── Dockerfile             # Container definition
  ├── start.sh              # Startup script
  └── .env.example          # Config template

frontend/
  ├── app.py                 # Streamlit application
  ├── requirements.txt       # Dependencies
  ├── Dockerfile             # Container definition
  ├── start.sh              # Startup script
  ├── .env.example          # Config template
  └── .streamlit/
      └── config.toml       # Streamlit config

shared/
  ├── data/                  # Datasets
  ├── models/                # Trained models
  └── mlruns.db             # MLflow tracking

root/
  ├── docker-compose.yml     # Service orchestration
  ├── .env.example          # Root env template
  ├── setup.sh              # Quick setup script
  ├── SETUP_SEPARATED.md    # Setup guide
  └── CODESPACES_SETUP.md   # Codespaces guide
```

---

## 🎯 Deployment Checklist

- [ ] Update `docker-compose.yml` for your environment
- [ ] Configure `.env` files with actual values
- [ ] Test backend health endpoint: `/health`
- [ ] Test API with sample request
- [ ] Test Streamlit frontend UI
- [ ] Verify port configurations
- [ ] Check CORS settings for frontend origin
- [ ] Review logs for errors
- [ ] Test with real data samples
- [ ] Document any environment-specific changes

---

## 📞 Support & Resources

- **Setup Guide:** [SETUP_SEPARATED.md](./SETUP_SEPARATED.md)
- **Codespaces Guide:** [CODESPACES_SETUP.md](./CODESPACES_SETUP.md)
- **Quick Reference:** [BRANCH_SUMMARY.md](./BRANCH_SUMMARY.md)
- **FastAPI Docs:** http://localhost:8000/docs (when running)
- **Streamlit Docs:** https://docs.streamlit.io

---

## 🎓 Learning Resources

### Understanding the Architecture
- Read [SETUP_SEPARATED.md](./SETUP_SEPARATED.md) for detailed architecture
- Review Docker Compose configuration
- Check service health endpoints

### Customization
- Modify `backend/main.py` for new API endpoints
- Update `frontend/app.py` for UI changes
- Adjust `backend/config.py` for model parameters

### Deployment
- Review Docker Compose best practices
- Consider using container orchestration (Kubernetes)
- Implement proper monitoring and logging

---

## ✅ Verification Checklist

After setup, verify:

```bash
# 1. Services running
docker-compose ps
# or check processes locally

# 2. Backend health
curl http://localhost:8000/health

# 3. API functional
curl -X POST http://localhost:8000/analyze -H "Content-Type: application/json" \
  -d '{"customer_response":"test","total_visits":0,"time_on_website":0,"page_views":0,"source":"Unknown","last_activity":"Unknown","occupation":"Unknown"}'

# 4. Frontend accessible
curl http://localhost:8501

# 5. Services logged correctly
docker-compose logs | grep "healthy"
```

---

**Happy deploying!** 🚀
