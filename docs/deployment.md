# Agent Council - Deployment Guide

Complete guide for deploying the Agent Council system to production environments.

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Environment Configuration](#environment-configuration)
4. [Backend Deployment](#backend-deployment)
5. [Frontend (Streamlit) Deployment](#frontend-deployment)
6. [Demo Mode](#demo-mode)
7. [Health Monitoring](#health-monitoring)
8. [Troubleshooting](#troubleshooting)

---

## Overview

The Agent Council platform consists of two components:

1. **FastAPI Backend** - REST API for workflow orchestration
2. **Streamlit Frontend** - Interactive UI for session management

These can be deployed:
- **Together** on the same server (simple deployment)
- **Separately** on different servers (production deployment)

---

## Architecture

```
┌─────────────────────┐
│  Streamlit UI       │
│  (Port 8501)        │
└──────────┬──────────┘
           │ HTTP
           │ API_BASE_URL
           ▼
┌─────────────────────┐
│  FastAPI Backend    │
│  (Port 8000)        │
│  - Health: /health  │
│  - API: /api/v1/*   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  SQLite Database    │
│  agent_council.db   │
└─────────────────────┘
```

---

## Environment Configuration

### Required Environment Variables

#### Backend (FastAPI)

```bash
# Environment
ENV=production                    # development | staging | production
LOG_LEVEL=INFO                    # DEBUG | INFO | WARNING | ERROR
DEBUG=false                       # Enable debug mode

# API Configuration
API_HOST=0.0.0.0                  # Bind to all interfaces
API_PORT=8000                     # API port
API_BASE_URL=https://your-api.render.com  # Full backend URL
ALLOWED_ORIGINS=*                 # CORS allowed origins (comma-separated)

# Deployment
DEMO_MODE=false                   # Enable demo mode (mocks external tools)
HEALTH_CHECK_ENABLED=true         # Enable /health endpoint

# LLM Provider (Google Gemini)
GOOGLE_API_KEY=your-gemini-key    # Required for agent operations

# Tool Integration (Optional - use DEMO_MODE=true if not available)
VIBES_API_KEY=your-vibes-key      # MuleSoft Vibes (optional)
MCP_API_KEY=your-mcp-key          # MCP Server (optional)
LUCID_API_KEY=your-lucid-key      # Lucid AI (optional)
NOTEBOOKLM_API_KEY=your-nb-key    # NotebookLM (optional)

# Database
DATABASE_URL=sqlite:///./agent_council.db  # SQLite path

# Security
SECRET_KEY=your-secret-key-change-me  # For JWT/sessions (required in production)
```

#### Frontend (Streamlit)

Create `.streamlit/secrets.toml`:

```toml
# Backend API URL
API_BASE_URL = "https://your-api.render.com"
```

Or set environment variable:

```bash
API_BASE_URL=https://your-api.render.com
```

**Priority**: Streamlit secrets > Environment variable > Default (localhost:8000)

---

## Backend Deployment

### Option 1: Render.com

#### 1. Create New Web Service

```yaml
# render.yaml
services:
  - type: web
    name: agent-council-api
    env: python
    buildCommand: "pip install -r requirements.txt"
    startCommand: "uvicorn main:app --host 0.0.0.0 --port $PORT"
    envVars:
      - key: ENV
        value: production
      - key: GOOGLE_API_KEY
        sync: false  # Set in Render dashboard (secret)
      - key: API_BASE_URL
        value: https://agent-council-api.onrender.com
      - key: DEMO_MODE
        value: false
      - key: ALLOWED_ORIGINS
        value: "*"
```

#### 2. Environment Variables in Render Dashboard

Navigate to **Environment** tab and add:
- `GOOGLE_API_KEY` (secret)
- `SECRET_KEY` (secret, generate with `openssl rand -hex 32`)
- Other optional tool API keys

#### 3. Deploy

```bash
git push origin master
```

Render auto-deploys on push.

#### 4. Verify Deployment

```bash
curl https://your-api.onrender.com/health
```

Expected response:
```json
{
  "status": "healthy",
  "timestamp": "2025-11-26T10:00:00Z",
  "version": "1.0.0",
  "environment": "production",
  "demo_mode": false,
  "api_base_url": "https://your-api.onrender.com"
}
```

---

### Option 2: Railway.app

#### 1. Create New Project

```bash
railway login
railway init
```

#### 2. Configure Environment

```bash
railway variables set ENV=production
railway variables set GOOGLE_API_KEY=your-key
railway variables set API_BASE_URL=https://your-app.railway.app
railway variables set DEMO_MODE=false
railway variables set ALLOWED_ORIGINS=*
```

#### 3. Deploy

```bash
railway up
```

#### 4. Get URL

```bash
railway domain
```

---

### Option 3: Docker (Any Platform)

#### Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### Build and Run

```bash
# Build
docker build -t agent-council-api .

# Run
docker run -d \
  -p 8000:8000 \
  -e ENV=production \
  -e GOOGLE_API_KEY=your-key \
  -e API_BASE_URL=http://localhost:8000 \
  -e DEMO_MODE=false \
  --name agent-council-api \
  agent-council-api
```

#### Docker Compose

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ENV=production
      - GOOGLE_API_KEY=${GOOGLE_API_KEY}
      - API_BASE_URL=http://localhost:8000
      - DEMO_MODE=false
      - ALLOWED_ORIGINS=*
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
```

---

## Frontend (Streamlit) Deployment

### Option 1: Streamlit Cloud

#### 1. Connect Repository

1. Go to https://share.streamlit.io
2. Click "New app"
3. Select your GitHub repository
4. Main file: `streamlit_app.py`
5. Python version: 3.11

#### 2. Configure Secrets

In Streamlit Cloud dashboard, go to **Settings** → **Secrets**:

```toml
# .streamlit/secrets.toml
API_BASE_URL = "https://your-backend-api.onrender.com"
```

#### 3. Deploy

Streamlit auto-deploys on push to main branch.

#### 4. Verify

Visit your app URL: `https://your-app.streamlit.app`

---

### Option 2: Self-Hosted Streamlit

#### Run Command

```bash
# Set backend URL
export API_BASE_URL=https://your-backend-api.onrender.com

# Run Streamlit
streamlit run streamlit_app.py --server.port 8501
```

#### With Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

---

## Demo Mode

**DEMO_MODE** allows the system to run without external API keys by mocking all tool responses.

### When to Use Demo Mode

✅ **Use Demo Mode:**
- Presentations and demos
- Development without API keys
- Testing deployment process
- Cost-free exploration

❌ **Don't Use Demo Mode:**
- Production environments
- When real tool integration is needed
- When actual external data is required

### Enabling Demo Mode

#### Backend

```bash
ENV=development
DEMO_MODE=true
```

#### What Gets Mocked

1. **Vibes Client** - Uses Gemini to simulate Vibes recommendations
2. **MCP Client** - Returns structured mock platform metadata
3. **Lucid Client** - Generates Mermaid diagrams instead of Lucid
4. **NotebookLM Client** - Uses Gemini for summarization

#### Verifying Demo Mode

```bash
curl https://your-api.com/health
```

Response:
```json
{
  "status": "healthy",
  "demo_mode": true,  ← Check this field
  ...
}
```

---

## Health Monitoring

### Health Endpoint

```bash
GET /health
```

#### Response

```json
{
  "status": "healthy",
  "timestamp": "2025-11-26T10:00:00.000Z",
  "version": "1.0.0",
  "environment": "production",
  "demo_mode": false,
  "api_base_url": "https://your-api.com"
}
```

### Monitoring Integration

#### Render

Render automatically uses `/health` for health checks.

#### Railway

```bash
railway health-check --path /health
```

#### Uptime Robot

1. Add HTTP(s) monitor
2. URL: `https://your-api.com/health`
3. Keyword to check: `"status":"healthy"`

#### Prometheus

```yaml
scrape_configs:
  - job_name: 'agent-council'
    metrics_path: '/health'
    static_configs:
      - targets: ['your-api.com:443']
```

---

## Troubleshooting

### Common Issues

#### 1. Streamlit Can't Connect to Backend

**Symptoms**: "Backend unreachable" errors in UI

**Solution**:
```bash
# Check backend is running
curl https://your-backend.com/health

# Verify API_BASE_URL in Streamlit secrets
cat .streamlit/secrets.toml

# Check Streamlit logs for URL being used
streamlit run streamlit_app.py
```

#### 2. CORS Errors

**Symptoms**: Browser console shows CORS errors

**Solution**:
```bash
# Add Streamlit domain to ALLOWED_ORIGINS
ALLOWED_ORIGINS=https://your-app.streamlit.app,http://localhost:8501
```

#### 3. LLM API Errors

**Symptoms**: "Agent execution failed" errors

**Solutions**:
```bash
# Verify API key is set
echo $GOOGLE_API_KEY

# Enable DEMO_MODE if API keys unavailable
DEMO_MODE=true

# Check API key quotas/limits
```

#### 4. Database Not Persisting

**Symptoms**: Sessions lost after restart

**Solution**:
```bash
# Ensure DATABASE_URL points to persistent storage
DATABASE_URL=sqlite:///./data/agent_council.db

# Mount volume in Docker
docker run -v $(pwd)/data:/app/data ...
```

#### 5. Health Check Failing

**Symptoms**: Deployment shows unhealthy

**Solutions**:
```bash
# Check health endpoint manually
curl http://localhost:8000/health

# Verify port is exposed
docker ps

# Check logs
docker logs agent-council-api
```

---

## Production Checklist

### Before Deploying

- [ ] Set `ENV=production`
- [ ] Set strong `SECRET_KEY`
- [ ] Configure `GOOGLE_API_KEY`
- [ ] Set correct `API_BASE_URL`
- [ ] Configure `ALLOWED_ORIGINS` restrictively
- [ ] Disable `DEBUG=false`
- [ ] Set `DEMO_MODE=false`
- [ ] Test `/health` endpoint
- [ ] Verify database persistence
- [ ] Test full workflow end-to-end

### After Deploying

- [ ] Monitor `/health` endpoint
- [ ] Check application logs
- [ ] Test UI → API connectivity
- [ ] Verify CORS configuration
- [ ] Test agent workflows
- [ ] Monitor LLM API usage
- [ ] Set up alerting (optional)
- [ ] Document deployment URLs
- [ ] Share access with team

---

## Performance Tuning

### Backend

```bash
# Increase workers for higher concurrency
uvicorn main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Database

For production, consider PostgreSQL:

```bash
DATABASE_URL=postgresql://user:pass@host:5432/agent_council
```

### Caching

Enable caching for frequently accessed data:

```python
# In settings.py
redis_url: str = "redis://localhost:6379"
```

---

## Security Best Practices

1. **Use HTTPS** - Always use TLS in production
2. **Restrict CORS** - Don't use `*` in production
3. **Rotate Keys** - Rotate `SECRET_KEY` periodically
4. **Rate Limiting** - Add rate limiting to API endpoints
5. **Audit Logs** - Enable comprehensive logging
6. **Environment Secrets** - Never commit secrets to git
7. **Principle of Least Privilege** - Limit API key permissions

---

## Scaling

### Horizontal Scaling

```yaml
# Render
services:
  - type: web
    scaling:
      minInstances: 2
      maxInstances: 10
```

### Load Balancing

Use platform's built-in load balancer (Render, Railway) or:

```nginx
upstream agent_council_backend {
    server backend1:8000;
    server backend2:8000;
}
```

---

## Support

For deployment issues:

1. Check logs: `docker logs` or platform dashboard
2. Verify `/health` endpoint
3. Review this deployment guide
4. Check GitHub Issues: https://github.com/raju-bvssn/ai-agent-council/issues
5. Contact: [Your Contact Info]

---

**Deployment Guide Version**: 1.0.0  
**Last Updated**: November 26, 2025  
**Compatibility**: Agent Council v1.0.0+

