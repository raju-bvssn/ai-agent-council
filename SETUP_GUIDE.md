# 🚀 Agent Council - Quick Setup Guide

Complete setup instructions for running Agent Council locally with Google Gemini and LangSmith.

---

## 📋 Prerequisites

- Python 3.9+ (Python 3.10+ recommended)
- Git
- Google Gemini API key
- LangSmith API key (optional, for tracing)

---

## ⚡ Quick Start (5 Minutes)

### **Step 1: Clone and Navigate**

```bash
cd /Users/vbolisetti/AI-Projects/ai-agent-council
```

### **Step 2: Set Up Virtual Environment**

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### **Step 3: Configure API Keys**

**Option A: Edit .env file (already created)**

```bash
# Open .env file in your editor
nano .env
# or
code .env
# or
vim .env
```

**Replace these placeholders with your actual keys:**
- Line 17: `GOOGLE_API_KEY=your_google_api_key_here`
- Line 33: `LANGSMITH_API_KEY=your_langsmith_api_key_here`
- Line 38: `LANGCHAIN_API_KEY=your_langsmith_api_key_here` (same as above)

**Option B: Export variables (temporary, current session only)**

```bash
export GOOGLE_API_KEY="your_actual_google_key"
export ENABLE_LANGSMITH=true
export LANGSMITH_API_KEY="your_actual_langsmith_key"
export LANGCHAIN_TRACING_V2=true
export LANGCHAIN_API_KEY="your_actual_langsmith_key"
```

### **Step 4: Verify Configuration**

```bash
# Test that keys are loaded
python -c "from app.utils.settings import get_settings; s = get_settings(); print(f'✅ Google Key: {s.google_api_key[:10]}...'); print(f'✅ LangSmith: {s.enable_langsmith}')"
```

Expected output:
```
✅ Google Key: AIzaSyXXXX...
✅ LangSmith: True
```

### **Step 5: Start the Backend**

```bash
# In Terminal 1
cd /Users/vbolisetti/AI-Projects/ai-agent-council
source venv/bin/activate
uvicorn main:app --reload
```

Wait for:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

### **Step 6: Test Backend**

```bash
# In a new terminal (Terminal 2)
curl http://localhost:8000/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "environment": "development",
  "demo_mode": false,
  "api_base_url": "http://localhost:8000"
}
```

### **Step 7: Start the UI**

```bash
# In Terminal 2 (or Terminal 3)
cd /Users/vbolisetti/AI-Projects/ai-agent-council
source venv/bin/activate
streamlit run streamlit_app.py
```

Wait for:
```
  You can now view your Streamlit app in your browser.
  
  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

### **Step 8: Access the Application**

Open your browser and go to:
- **UI:** http://localhost:8501
- **API Docs:** http://localhost:8000/docs

---

## ✅ Verify Everything Works

### 1. Health Check (Backend)
```bash
curl http://localhost:8000/api/v1/health
```
✅ Should return: `{"status": "healthy", ...}`

### 2. Create Test Session (API)
```bash
curl -X POST http://localhost:8000/api/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "user_request": "Design a customer portal integration",
    "name": "Test Session"
  }'
```
✅ Should return: `{"session_id": "...", "status": "pending", ...}`

### 3. Open UI (Browser)
- Navigate to http://localhost:8501
- ✅ Should see "🏛️ Create Agent Council Session"

### 4. Create Session (UI)
- Enter session name: "My First Council"
- Enter requirements: "Design a secure API gateway with OAuth"
- ✅ Should see AI-suggested agent roles
- Select agents
- Click "Create Session & Configure Agents"
- ✅ Should navigate to agent selector

### 5. Start Workflow (UI)
- Click "▶️ Start Council"
- ✅ Should see "Workflow started successfully!"
- ✅ Should navigate to feedback panel
- ✅ Should see status indicator

### 6. Check LangSmith (if enabled)
- ✅ Should see "🔍 Execution Trace" card
- ✅ Should see "Open in LangSmith →" link
- Click link
- ✅ Should open LangSmith UI with execution graph

---

## 🔑 Getting API Keys

### **Google Gemini API Key (REQUIRED)**

1. Go to: https://makersuite.google.com/app/apikey
2. Click "Create API Key"
3. Select your Google Cloud project (or create new)
4. Copy the API key
5. Paste into `.env` file at `GOOGLE_API_KEY=`

**Cost:** Free tier available, generous limits

### **LangSmith API Key (OPTIONAL)**

1. Go to: https://smith.langchain.com
2. Sign up or log in
3. Click Settings → API Keys
4. Click "Create API Key"
5. Copy the key (starts with `lsv2_pt_...`)
6. Paste into `.env` file at `LANGSMITH_API_KEY=`

**Cost:** Free tier available, 5K traces/month

**Benefits:**
- Full execution graph visualization
- Agent decision tracing
- LLM call inspection
- Performance monitoring
- Debug tool for complex workflows

---

## 🛠️ Troubleshooting

### Backend won't start?

```bash
# Check if port 8000 is in use
lsof -i :8000

# Kill existing process if needed
kill -9 <PID>

# Or use different port
API_PORT=8001 uvicorn main:app --reload
```

### UI won't start?

```bash
# Check if port 8501 is in use
lsof -i :8501

# Or use different port
streamlit run streamlit_app.py --server.port 8502
```

### Keys not loading?

```bash
# 1. Check .env file exists
ls -la .env

# 2. Verify file has your keys (first 10 chars only)
head -20 .env | grep GOOGLE_API_KEY

# 3. Restart backend (Ctrl+C, then re-run uvicorn command)

# 4. Test in Python
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.getenv('GOOGLE_API_KEY', 'NOT SET')[:10])"
```

### LangSmith not working?

```bash
# Ensure both old and new format are set
grep LANGSMITH .env

# Should see:
# ENABLE_LANGSMITH=true
# LANGSMITH_API_KEY=lsv2_pt_...
# LANGCHAIN_TRACING_V2=true
# LANGCHAIN_API_KEY=lsv2_pt_...
```

### "Module not found" errors?

```bash
# Ensure virtual environment is activated
which python
# Should show: /Users/vbolisetti/AI-Projects/ai-agent-council/venv/bin/python

# If not activated:
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

---

## 🧪 Run Tests

After setup, verify everything works:

```bash
# Activate venv
source venv/bin/activate

# Run all tests
pytest tests/ -v

# Run specific test suites
pytest tests/test_api_comprehensive.py -v
pytest tests/test_ui_integration.py -v

# Run with coverage
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## 📖 Additional Resources

- **API Documentation:** http://localhost:8000/docs
- **API Validation Report:** `API_VALIDATION_REPORT.md`
- **UI Integration Report:** `UI_INTEGRATION_VALIDATION_REPORT.md`
- **Deployment Guide:** `docs/deployment.md`
- **Architecture Docs:** `docs/architecture.md`
- **Workflow Documentation:** `docs/workflow.md`

---

## 🎯 Next Steps After Setup

1. **Create your first session** - Use the UI to create a council session
2. **Configure agents** - Select specialized agents for your use case
3. **Start workflow** - Watch the multi-agent system work
4. **Approve design** - Participate in human-in-the-loop approval
5. **View results** - See final architecture and FAQ

---

## 🚀 You're All Set!

The Agent Council platform is now fully configured and ready to use.

**Terminal 1:** Backend running on http://localhost:8000  
**Terminal 2:** Streamlit UI on http://localhost:8501  
**Status:** ✅ Ready for multi-agent orchestration

Enjoy your AI-powered architecture council! 🎉

