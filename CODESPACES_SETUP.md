# GitHub Codespaces Setup Guide

This guide helps you run the separated Lead Qualification Bot (Streamlit + FastAPI) in GitHub Codespaces.

## 🚀 Quick Start in Codespaces

### Step 1: Start Both Services

```bash
docker-compose up --build
```

This will:
- Build the FastAPI backend image
- Build the Streamlit frontend image  
- Start both services on default ports (8000 for FastAPI, 8501 for Streamlit)

### Step 2: Find Your Service URLs

1. Look for the **"Ports"** tab in the Terminal panel
2. You'll see two forwarded ports:
   - Port `8000` → FastAPI Backend (copy the forwarded URL)
   - Port `8501` → Streamlit Frontend (copy the forwarded URL)

### Step 3: Configure the API URL in Streamlit

1. Open the **Streamlit Frontend** URL in your browser
2. In the left sidebar, find the section: **"⚙️ API Configuration"**
3. Copy your FastAPI backend URL from the Ports tab
4. Replace `http://127.0.0.1:8000` in the API URL input field with your actual forwarded URL
5. Format: `https://<codespace-name>-8000.preview.app.github.dev/analyze`

## 🔄 Custom Ports (If Default Ports Don't Work)

If you need different ports, create a `.env` file in the root directory:

```bash
cat > .env << EOF
FASTAPI_PORT=5000
STREAMLIT_PORT=9000
EOF
```

Then rebuild:
```bash
docker-compose up --build
```

## 🐳 Managing Services

### View Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Stop Services
```bash
docker-compose down
```

### Restart Services
```bash
docker-compose restart
```

## 🔍 Troubleshooting in Codespaces

### Issue: Frontend can't connect to backend

**Solution:**
1. Check the **Ports** tab - verify both services are running
2. The API URL must use HTTPS (Codespaces requirement)
3. Example correct URL: `https://codespace-name-8000.preview.app.github.dev/analyze`
4. Update the URL in Streamlit sidebar if needed

### Issue: Port already in use

**Solution:**
- Use the custom ports approach above
- Or kill the conflicting service:
  ```bash
  docker-compose down
  docker-compose up --build
  ```

### Issue: Services not starting

**Solution:**
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose down -v
docker-compose up --build
```

## 📊 Testing the API Directly

You can test the FastAPI backend without Streamlit:

```bash
# Get your backend URL from the Ports tab, then:
curl "https://your-codespace-8000-url.preview.app.github.dev/health"

# Response should be:
# {"status":"healthy","device":"cpu","model_loaded":true}
```

## 🔐 Security Notes for Codespaces

- All connections use HTTPS (forwarded URLs are secure)
- The backend only accepts requests with proper headers
- Firewall rules apply based on Codespaces settings
- Never commit `.env` files with sensitive data

## 📝 Tips for Development

### Live Code Updates
```bash
# Changes to backend Python files:
# Rebuilding required if dependencies change
docker-compose up --build backend

# Changes to frontend Streamlit files:
# Auto-reload enabled, just edit and refresh browser
# No rebuild needed for most changes
```

### Accessing Model Files
Models are stored in the shared `models/` directory:
```bash
ls models/
# Output:
# hybrid_lead_model.pt
# tabular_preprocessor.joblib
# distilbert_lead_classifier/
```

### Checking Model Training Status
```bash
docker-compose logs backend | grep "Epoch"
```

## 🎯 Performance Notes

- Initial startup may take 2-3 minutes (model training)
- Streamlit requires ~500MB RAM
- FastAPI backend requires ~2GB RAM (GPU optional)
- Codespaces provides 4GB RAM by default (usually sufficient)

## 📚 More Information

- [Main SETUP Guide](./SETUP_SEPARATED.md)
- [Backend Documentation](./backend/README.md)
- [Frontend Documentation](./frontend/README.md)
- [Original README](./README.md)

## 🆘 Still Having Issues?

1. Check the logs: `docker-compose logs -f`
2. Verify both services are healthy: `docker-compose ps`
3. Ensure you're using HTTPS URLs in Codespaces
4. Try rebuilding: `docker-compose down -v && docker-compose up --build`

Good luck! 🚀
