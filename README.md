# 🏛️ Agent Council

**Multi-Agent Solution Design System for Salesforce Professional Services**

A production-grade, LangGraph-powered orchestration system that coordinates specialized AI agents to collaboratively design and review Salesforce solutions.

## 🎯 Overview

Agent Council brings together multiple specialized AI agents—Master Architect, Solution Architect, and domain-specific Reviewers—to provide comprehensive architectural design and review for Salesforce projects. Built with Mission Critical Data compliance and following Clean Architecture principles.

### Key Features

- **Multi-Agent Collaboration**: Specialized agents work together through LangGraph workflows
- **Human-in-the-Loop**: Approval gates for critical decisions
- **Iterative Refinement**: Automated revision loops based on reviewer feedback
- **Mission Critical Data Compliant**: Uses only approved LLM providers (Google Gemini)
- **Comprehensive Reviews**: NFR/Performance, Security, Integration, and more
- **Knowledge Generation**: Automatic FAQ and decision rationale documentation
- **Clean Architecture**: SOLID principles, fully typed, testable
- **Production-Ready**: FastAPI backend, Streamlit UI, SQLite persistence

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Interface Layer                         │
│  ┌─────────────────────┐    ┌──────────────────────────┐  │
│  │   Streamlit UI      │    │   FastAPI REST API       │  │
│  └─────────────────────┘    └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                         │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Session    │  │    Workflow    │  │     Agent      │ │
│  │   Manager    │  │  Orchestrator  │  │  Controllers   │ │
│  └──────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Domain Layer                            │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │    Agents    │  │   LangGraph    │  │     State      │ │
│  │              │  │    Workflow    │  │    Models      │ │
│  └──────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                Infrastructure Layer                         │
│  ┌──────────────┐  ┌────────────────┐  ┌────────────────┐ │
│  │   Gemini     │  │  External      │  │     SQLite     │ │
│  │   Provider   │  │    Tools       │  │  Persistence   │ │
│  └──────────────┘  └────────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

See [docs/architecture.md](docs/architecture.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Google Gemini API key
- (Optional) API keys for Vibes, MCP Server, NotebookLM, Lucid AI

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd ai-agent-council
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment**
```bash
cp .env.example .env
# Edit .env and add your API keys
```

Minimum required configuration:
```env
GOOGLE_API_KEY=your_gemini_api_key_here
DATABASE_URL=sqlite:///./agent_council.db
```

### Running the Application

**Start the API Backend**
```bash
# Development mode with auto-reload
uvicorn main:app --reload

# Or using Python
python main.py
```

API will be available at: `http://localhost:8000`
- API Docs: http://localhost:8000/docs
- Health Check: http://localhost:8000/api/v1/health

**Start the Streamlit UI**
```bash
streamlit run streamlit_app.py
```

UI will be available at: `http://localhost:8501`

## 📖 Usage

### Creating a Council Session

1. **Open Streamlit UI** (http://localhost:8501)
2. **Fill in session details**:
   - Session name
   - Description
   - Your requirements/request
   - Context (industry, org size, etc.)
3. **Click "Start Council Session"**

### Configuring Agents

1. **Select participating agents**:
   - Master Architect (required)
   - Solution Architect (required)
   - NFR/Performance Reviewer
   - Security Reviewer
   - Integration Reviewer
   - FAQ Generator
2. **Click "Start Council"**

### Workflow Execution (Phase 2)

The council will:
1. Analyze your requirements (Master Architect)
2. Create initial design (Solution Architect)
3. Review in parallel (All Reviewers)
4. Request revision if needed (automatic)
5. Wait for your approval (Human-in-the-Loop)
6. Generate FAQ and documentation
7. Finalize deliverables

### Viewing Results

Navigate to the **Final Output** page to see:
- Complete design document
- Architecture diagrams
- FAQ entries
- Decision rationale
- Review history

### 🔧 Admin Tools (POC/Demo)

The Streamlit UI includes prototype administration tools in the sidebar:

**System Stats**
- View total sessions and status breakdown
- Monitor system health

**Clear All Sessions**
- Removes all session data from the database
- Useful for cleaning up test data during POC/demo
- ⚠️ **WARNING**: This permanently deletes all sessions

**Reset Database (Danger Zone)**
- Drops and recreates all database tables
- Permanently deletes ALL data
- ⚠️ **DANGER**: Use with extreme caution
- Requires two-step confirmation

**API Endpoints**
```bash
# Get system statistics
GET /admin/stats

# Clear all sessions
POST /admin/clear-sessions

# Reset database (DANGER)
POST /admin/reset-database
```

> **Note**: These admin functions are for POC/demo purposes only. In production, these should be properly secured with authentication, authorization, and audit logging.

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_agents.py

# Run with verbose output
pytest -v
```

View coverage report: `open htmlcov/index.html`

## 📚 Documentation

- [Architecture](docs/architecture.md) - System architecture and design principles
- [Workflow](docs/workflow.md) - LangGraph workflow documentation
- [Sequence Diagram](docs/sequence_diagram.md) - Complete interaction flows
- [Component Map](docs/component_map.md) - Component relationships and data flow

## 🛠️ Development

### Project Structure

```
ai-agent-council/
├── app/
│   ├── agents/          # Agent implementations
│   ├── api/             # FastAPI routes and schemas
│   ├── graph/           # LangGraph workflow
│   ├── llm/             # LLM provider abstraction
│   ├── state/           # Session and persistence
│   ├── tools/           # External tool integrations
│   ├── ui/              # Streamlit components
│   └── utils/           # Utilities and helpers
├── tests/               # Test suite
├── docs/                # Documentation
├── main.py              # API entry point
├── streamlit_app.py     # UI entry point
├── requirements.txt     # Dependencies
└── .env.example         # Environment template
```

### Code Quality

```bash
# Format code
black app/ tests/

# Lint code
ruff check app/ tests/

# Type checking
mypy app/
```

### Adding a New Agent

1. Create agent class in `app/agents/`
2. Inherit from `PerformerAgent` or `CriticAgent`
3. Implement `get_system_prompt()` and `run()` methods
4. Add to `AgentRole` enum in `state_models.py`
5. Register in `AgentFactory`
6. Add tests in `tests/test_agents.py`

Example:
```python
from app.agents.performer import PerformerAgent, AgentInput, AgentOutput

class MyCustomAgent(PerformerAgent):
    def __init__(self, llm_provider=None):
        super().__init__(llm_provider=llm_provider, agent_name="MyCustomAgent")
    
    def get_system_prompt(self) -> str:
        return "You are a specialized agent for..."
    
    def run(self, input_data: AgentInput) -> AgentOutput:
        # Implementation
        pass
```

## 🔒 Security & Compliance

### Mission Critical Data Requirements

- ✅ **Approved LLM Provider**: Google Gemini only
- ✅ **Prompt Injection Protection**: Safety wrapper on all inputs
- ✅ **PII Redaction**: Automated in logs
- ✅ **No Customer Data Leakage**: Input sanitization
- ✅ **Audit Logging**: All decisions tracked
- ✅ **Timeout/Retry**: Wrapped external calls

### Best Practices

- Never commit `.env` file
- Rotate API keys regularly
- Review logs for sensitive data
- Use HTTPS in production
- Enable LangSmith tracing for debugging (optional)

## 🌐 API Reference

### Health Check
```bash
GET /api/v1/health
```

### Create Session
```bash
POST /api/v1/sessions
{
  "user_request": "Design a customer portal",
  "name": "Customer Portal",
  "user_context": {}
}
```

### List Sessions
```bash
GET /api/v1/sessions?limit=50&offset=0
```

### Get Session
```bash
GET /api/v1/sessions/{session_id}
```

See API docs at `/docs` for complete reference.

## 🗺️ Roadmap

### Phase 1 (Complete) ✅
- [x] Core architecture and scaffolding
- [x] Agent implementations (base + 6 agents)
- [x] LangGraph workflow foundation
- [x] FastAPI backend
- [x] Streamlit UI
- [x] SQLite persistence
- [x] Safety wrappers
- [x] Documentation

### Phase 2 (Next)
- [ ] Full workflow execution
- [ ] Streaming updates to UI
- [ ] Tool integrations (Vibes, MCP, NotebookLM, Lucid)
- [ ] Diagram generation
- [ ] Export functionality (PDF, Markdown)
- [ ] Domain Expert and Ops reviewers
- [ ] LangSmith integration
- [ ] Comprehensive testing (85%+ coverage)
- [ ] Performance optimization

### Phase 3 (Future)
- [ ] Advanced workflow features (pause, resume, branching)
- [ ] Workflow templates
- [ ] AI-suggested agent selection
- [ ] Analytics and metrics
- [ ] Multi-user support
- [ ] Role-based access control
- [ ] Deployment automation

## 🤝 Contributing

1. Follow project rules in `.cursor/rules/mandatory-project-rules.mdc`
2. Maintain SOLID principles and Clean Architecture
3. Add tests for new features
4. Update documentation
5. Use type hints everywhere
6. Follow existing code style

## 📄 License

[Your License Here]

## 👥 Credits

Built for Salesforce Professional Services with ❤️

## 📞 Support

For issues or questions:
- Create an issue in the repository
- Check documentation in `/docs`
- Review API docs at `/docs`

---

**Mission Critical Data Compliant** | **Built with LangGraph** | **Powered by Google Gemini**

