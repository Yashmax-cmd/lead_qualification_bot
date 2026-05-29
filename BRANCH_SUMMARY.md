# Architecture Refactor - Quick Reference

## 📦 Branch Information

**Branch Name:** `streamlit-fastapi-split`

This branch contains the refactored code with separated Streamlit frontend and FastAPI backend services.

## 📁 What's New

### Directory Structure
```
backend/          ← FastAPI backend service (port 8000)
frontend/         ← Streamlit frontend service (port 8501)
data/            ← Shared data directory
models/          ← Shared models directory
docker-compose.yml ← Orchestrates both services
.env.example     ← Port configuration template
```

### New Features
✅ Separate backend and frontend code  
✅ Configurable ports (great for Codespaces)  
✅ CORS enabled for frontend-backend communication  
✅ Independent scaling and deployment  
✅ Docker Compose orchestration  
✅ Health checks and robust error handling  
✅ Improved Streamlit API error messages  

## 🚀 Quick Commands

### Start Everything
```bash
# Docker Compose (recommended)
docker-compose up --build

# Or use setup script
bash setup.sh
```

### Local Development
```bash
# Terminal 1 - Backend
cd backend
python -m uvicorn main:app --port 8000 --reload

# Terminal 2 - Frontend
cd frontend
streamlit run app.py --server.port 8501
```

### Custom Ports
```bash
# Create .env file
echo "FASTAPI_PORT=5000" > .env
echo "STREAMLIT_PORT=9000" >> .env

# Start with custom ports
docker-compose up --build
```

### GitHub Codespaces
```bash
docker-compose up --build
# Then update API URL in Streamlit sidebar with your Codespaces URLs
```

## 📊 Service Ports

| Service | Default Port | Environment Variable | Docker Network URL |
|---------|-------------|---------------------|-------------------|
| FastAPI Backend | 8000 | `FASTAPI_PORT` | `http://backend:8000` |
| Streamlit Frontend | 8501 | `STREAMLIT_PORT` | `http://frontend:8501` |

## 🔗 API Configuration

Streamlit automatically tries to find the API in this order:
1. `.streamlit/secrets.toml` → `API_URL`
2. Environment variable → `API_URL`
3. Sidebar text input
4. Default → `http://127.0.0.1:8000/analyze`

## 📚 Documentation Files

- **SETUP_SEPARATED.md** - Complete setup and configuration guide
- **CODESPACES_SETUP.md** - GitHub Codespaces specific instructions
- **backend/.env.example** - Backend environment variables
- **frontend/.env.example** - Frontend environment variables
- **.env.example** - Root level Docker Compose variables

## 🔄 Common Tasks

### Update Backend Dependencies
```bash
cd backend
pip install new-package
pip freeze > requirements.txt
```

### Update Frontend Dependencies
```bash
cd frontend
pip install new-package
pip freeze > requirements.txt
```

### Rebuild Backend Only
```bash
docker-compose up --build backend
```

### Rebuild Frontend Only
```bash
docker-compose up --build frontend
```

### View Logs
```bash
docker-compose logs -f          # All services
docker-compose logs -f backend  # Just backend
docker-compose logs -f frontend # Just frontend
```

### Stop Services
```bash
docker-compose down
```

## ✅ Verification

### Check Backend Health
```bash
curl http://localhost:8000/health
# Expected: {"status":"healthy","model_loaded":true,...}
```

### Check Services Running
```bash
docker-compose ps
```

### Test API Endpoint
```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"customer_response":"We need a demo urgently","total_visits":10,"time_on_website":1500,"page_views":3.0,"source":"Google Campaigns","last_activity":"Email Opened","occupation":"Working Professional"}'
```

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port already in use | Use custom ports (create `.env` file) |
| Frontend can't reach backend | Update API URL in Streamlit sidebar |
| Docker build fails | Run `docker-compose down -v` then retry |
| Model training too slow | Wait for initial startup (builds on first run) |
| Codespaces port issues | Use HTTPS URLs from Ports tab |

## 📝 Key Files

### Backend
- `backend/main.py` - FastAPI application with CORS
- `backend/config.py` - Configuration with parent directory support
- `backend/Dockerfile` - Backend container definition
- `backend/requirements.txt` - Backend dependencies

### Frontend
- `frontend/app.py` - Streamlit application with improved error handling
- `frontend/.streamlit/config.toml` - Streamlit theme and settings
- `frontend/Dockerfile` - Frontend container definition
- `frontend/requirements.txt` - Frontend dependencies

### Root
- `docker-compose.yml` - Service orchestration
- `.env.example` - Port configuration template

## 🎯 Next Steps

1. ✅ Review the branch structure
2. ✅ Test locally with `docker-compose up --build`
3. ✅ Try custom ports with `.env` file
4. ✅ Test in Codespaces (if applicable)
5. ✅ Read full documentation in `SETUP_SEPARATED.md`
6. ✅ Deploy to your environment

## 📞 Support

For detailed instructions, see:
- **Quick Start:** SETUP_SEPARATED.md
- **Codespaces:** CODESPACES_SETUP.md
- **Troubleshooting:** SETUP_SEPARATED.md#troubleshooting

---

**Branch:** `streamlit-fastapi-split`  
**Created:** Latest refactor  
**Status:** Ready for testing & deployment ✅
