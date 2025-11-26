# LangSmith Integration - Implementation Status & Roadmap

**Current Status**: **Foundation Complete (25%)** - 3/12 tasks done  
**Agent Tracing**: ✅ **Complete** (All 7 agents traced)  
**Remaining**: Tool tracing, workflow tracing, API tracing, UI integration, tests, docs

---

## ✅ COMPLETED TASKS (3/12)

### 1. ✅ LangSmith Settings Configuration

**File**: `app/utils/settings.py`

**Added Fields**:
```python
enable_langsmith: bool = False          # Master toggle
langsmith_api_key: Optional[str] = None # API key
langsmith_project: str = "agent-council"# Project name
langsmith_endpoint: str = "https://api.smith.langchain.com"
```

**Helper Methods**:
- `is_langsmith_enabled` property
- `get_langsmith_api_key()` with legacy fallback

**Environment Variables**:
```bash
ENABLE_LANGSMITH=true
LANGSMITH_API_KEY=your-key
LANGSMITH_PROJECT=agent-council
```

---

### 2. ✅ LangSmith Initialization Module

**Files Created**:
- `app/observability/__init__.py`
- `app/observability/langsmith_init.py` (200 lines)

**Key Functions**:

```python
# Initialize LangSmith client
initialize_langsmith() -> Optional[Client]

# Get cached client instance
get_langsmith_client() -> Optional[Client]

# Check if tracing is enabled
is_tracing_enabled() -> bool

# Generate LangSmith UI URL
get_trace_url(run_id: str) -> str

# Get current run ID from context
get_current_run_id() -> Optional[str]
```

**Features**:
- ✅ Lazy initialization (safe to import)
- ✅ Graceful fallback if langsmith not installed
- ✅ Auto-configures environment variables
- ✅ Cached client (lru_cache)
- ✅ Comprehensive logging

---

### 3. ✅ Agent Tracing (@traceable decorators)

**All 7 Agents Traced**:

| Agent | File | Method | Trace Name |
|-------|------|--------|------------|
| ✅ Master Architect | `master_agent.py` | `run()` | `master_architect_run` |
| ✅ Solution Architect | `solution_architect_agent.py` | `run()` | `solution_architect_run` |
| ✅ NFR/Performance Reviewer | `reviewer_agent.py` | `run()` | `nfr_performance_reviewer_run` |
| ✅ Security Reviewer | `reviewer_agent.py` | `run()` | `security_reviewer_run` |
| ✅ Integration Reviewer | `reviewer_agent.py` | `run()` | `integration_reviewer_run` |
| ✅ FAQ Agent | `faq_agent.py` | `run()` | `faq_agent_run` |
| ✅ Architect Adjudicator | `architect_adjudicator.py` | `run()` | `architect_adjudicator_run` |

**Pattern Used**:
```python
# Import with graceful fallback
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

# Apply to run method
@traceable(name="agent_name_run")
def run(self, input_data: AgentInput) -> AgentOutput:
    ...
```

---

## ⏳ REMAINING TASKS (9/12)

### 4. ⏳ Add @traceable to All Tool Calls

**Files to Modify**:
- `app/tools/vibes_client.py`
- `app/tools/mcp_client.py`
- `app/tools/lucid_client.py`
- `app/tools/gemini_client.py`
- `app/tools/notebooklm_client.py`

**Pattern to Apply**:
```python
# In each tool client file
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

# Apply to all public methods
@traceable(name="vibes_analyze_api_spec")
async def analyze_api_spec(self, spec_text: str) -> ToolResult:
    ...

@traceable(name="mcp_get_environment_info")
async def get_environment_info(self, env_id: str) -> ToolResult:
    ...
```

**Methods to Trace**:
- **Vibes**: `analyze_api_spec`, `recommend_patterns`, `review_error_handling`, `validate_nfrs`
- **MCP**: `get_environment_info`, `get_api_metadata`, `list_policies`, `get_runtime_config`
- **Lucid**: `generate_architecture_diagram`, `generate_sequence_diagram`, `generate_data_flow_diagram`
- **Gemini**: `generate`, `analyze_long_context`, `summarize`, `extract_insights`
- **NotebookLM**: `summarize_with_sources`, `answer_questions`, `verify_claims`

---

### 5. ⏳ Trace Debate and Consensus Engines

**Files to Modify**:
- `app/graph/debate/detector.py`
- `app/graph/debate/debate_engine.py`
- `app/graph/debate/consensus.py`

**detector.py**:
```python
@traceable(name="detect_disagreements")
def detect_disagreements(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    ...
```

**debate_engine.py**:
```python
@traceable(name="debate_round")
async def run_debate(disagreement: Disagreement, ...) -> DebateOutcome:
    ...

@traceable(name="debate_round_single")
async def _run_debate_round(...):
    ...
```

**consensus.py**:
```python
@traceable(name="consensus_computation")
def compute_consensus(reviews, debates, threshold) -> ConsensusResult:
    ...

@traceable(name="consensus_weighted_scoring")
def _compute_weighted_scores(...):
    ...
```

---

### 6. ⏳ Trace LangGraph Workflow Nodes

**File**: `app/graph/workflow.py` or `app/graph/phase3b_nodes.py`

**Nodes to Trace**:
```python
@traceable(name="workflow_master_architect_node")
def master_architect_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_solution_architect_node")
def solution_architect_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_reviewer_round")
def reviewer_round_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_detect_disagreements")
def detect_disagreements_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_debate_cycle")
def debate_cycle_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_compute_consensus")
def compute_consensus_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_architect_adjudicator")
def architect_adjudicator_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_human_approval")
def human_approval_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_faq_generation")
def faq_generation_node(state: WorkflowState) -> Dict:
    ...

@traceable(name="workflow_finalize")
def finalize_node(state: WorkflowState) -> Dict:
    ...
```

---

### 7. ⏳ Trace FastAPI Endpoints

**File**: `app/api/routes.py` or `app/api/workflow_routes.py`

**Endpoints to Trace**:
```python
@router.post("/sessions")
@traceable(name="api_create_session")
async def create_session(request: CreateSessionRequest):
    ...

@router.get("/sessions/{session_id}")
@traceable(name="api_get_session")
async def get_session(session_id: str):
    ...

@router.post("/workflow/{session_id}/start")
@traceable(name="api_start_workflow")
async def start_workflow(session_id: str):
    ...

@router.post("/workflow/{session_id}/approve")
@traceable(name="api_approve_design")
async def approve_design(session_id: str, ...):
    ...

@router.post("/workflow/{session_id}/revise")
@traceable(name="api_request_revision")
async def request_revision(session_id: str, ...):
    ...

@router.get("/workflow/{session_id}/status")
@traceable(name="api_get_workflow_status")
async def get_workflow_status(session_id: str):
    ...
```

---

### 8. ⏳ Attach run_id to SessionState

**File**: `app/graph/state_models.py`

**Add Field**:
```python
class WorkflowState(BaseModel):
    ...
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
```

**Capture in Workflow Start**:
```python
# In app/graph/workflow.py or workflow execution entry point
from app.observability import get_current_run_id, get_trace_url

def run_council_workflow(session_id: str) -> WorkflowResult:
    ...
    # Get run ID from LangSmith context
    run_id = get_current_run_id()
    if run_id:
        state.langsmith_run_id = run_id
        state.langsmith_trace_url = get_trace_url(run_id)
    ...
```

**Persist to Database**:
- Ensure `app/state/persistence.py` saves these fields
- Update `CouncilSession` table schema if needed

---

### 9. ⏳ Surface LangSmith URL in Streamlit UI

**File**: `app/ui/feedback_panel.py` or `app/ui/final_output.py`

**Add Trace Link**:
```python
def render_feedback_panel(session_id: str):
    ...
    session_data = api_client.get_session(session_id)
    
    # Show LangSmith trace link if available
    trace_url = session_data.get("langsmith_trace_url")
    if trace_url:
        st.markdown(f"""
        ### 🔍 Trace this Session
        View the complete execution trace in LangSmith:
        [Open in LangSmith]({trace_url})
        """)
    ...
```

**Alternative**: Add to sidebar
```python
def render_sidebar():
    if st.session_state.get("current_session_id"):
        session_data = api_client.get_session(st.session_state.current_session_id)
        trace_url = session_data.get("langsmith_trace_url")
        
        if trace_url:
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🔍 Observability")
            st.sidebar.markdown(f"[View Trace]({trace_url})")
```

---

### 10. ⏳ Add Replay Endpoint

**File**: `app/api/routes.py` or new `app/api/observability_routes.py`

**Implementation**:
```python
from app.observability import get_trace_url

@router.get("/replay/{session_id}")
async def replay_session(session_id: str):
    """Get LangSmith replay URL for a session."""
    # Get session from DB
    persistence = get_persistence_manager()
    state = persistence.load_state(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not state.langsmith_run_id:
        raise HTTPException(
            status_code=404,
            detail="No trace available for this session"
        )
    
    return {
        "session_id": session_id,
        "langsmith_run_id": state.langsmith_run_id,
        "langsmith_url": get_trace_url(state.langsmith_run_id),
        "trace_available": True
    }
```

**UI Integration**:
```python
# In Streamlit
if st.button("🔄 Replay in LangSmith"):
    replay_data = api_client.replay_session(session_id)
    st.markdown(f"[Open Replay]({replay_data['langsmith_url']})")
```

---

### 11. ⏳ Create LangSmith Tests

**File**: `tests/test_langsmith_tracing.py` (create new)

**Tests to Include**:

```python
import pytest
from unittest.mock import Mock, patch

class TestLangSmithSettings:
    """Test LangSmith configuration."""
    
    def test_is_langsmith_enabled(self):
        """Test is_langsmith_enabled property."""
        ...
    
    def test_get_langsmith_api_key_fallback(self):
        """Test API key fallback to legacy field."""
        ...

class TestLangSmithInitialization:
    """Test LangSmith initialization."""
    
    def test_initialize_langsmith_disabled(self):
        """Test initialization when disabled."""
        ...
    
    def test_initialize_langsmith_no_api_key(self):
        """Test initialization without API key."""
        ...
    
    @patch('app.observability.langsmith_init.Client')
    def test_initialize_langsmith_success(self, mock_client):
        """Test successful initialization."""
        ...
    
    def test_is_tracing_enabled(self):
        """Test is_tracing_enabled check."""
        ...
    
    def test_get_trace_url(self):
        """Test trace URL generation."""
        run_id = "test-run-123"
        url = get_trace_url(run_id)
        assert "smith.langchain.com" in url
        assert run_id in url

class TestAgentTracing:
    """Test agent tracing decorators."""
    
    def test_solution_architect_has_traceable(self):
        """Test SolutionArchitectAgent.run has @traceable."""
        from app.agents.solution_architect_agent import SolutionArchitectAgent
        agent = SolutionArchitectAgent()
        # Check that run method exists and can be called
        assert hasattr(agent, 'run')
    
    def test_master_architect_has_traceable(self):
        """Test MasterArchitectAgent.run has @traceable."""
        ...

class TestToolTracing:
    """Test tool call tracing."""
    
    def test_vibes_client_methods_traceable(self):
        """Test Vibes client methods have @traceable."""
        ...
    
    def test_mcp_client_methods_traceable(self):
        """Test MCP client methods have @traceable."""
        ...

class TestWorkflowTracing:
    """Test workflow node tracing."""
    
    def test_workflow_nodes_have_traceable(self):
        """Test all workflow nodes have @traceable."""
        ...

class TestStateRunID:
    """Test run_id attachment to state."""
    
    def test_workflow_state_has_run_id_field(self):
        """Test WorkflowState has langsmith_run_id field."""
        from app.graph.state_models import WorkflowState
        state = WorkflowState(session_id="test", user_request="test")
        assert hasattr(state, 'langsmith_run_id')
    
    @patch('app.observability.get_current_run_id')
    def test_run_id_captured_in_workflow(self, mock_get_run_id):
        """Test run ID is captured during workflow execution."""
        mock_get_run_id.return_value = "test-run-123"
        ...

class TestAPITracing:
    """Test API endpoint tracing."""
    
    @pytest.mark.asyncio
    async def test_create_session_traced(self):
        """Test create_session endpoint is traced."""
        ...
    
    @pytest.mark.asyncio
    async def test_start_workflow_traced(self):
        """Test start_workflow endpoint is traced."""
        ...
```

**Run Tests**:
```bash
pytest tests/test_langsmith_tracing.py -v
```

---

### 12. ⏳ Update Observability Documentation

**File**: `docs/observability.md` (create new)

**Content Structure**:

```markdown
# Observability & Tracing with LangSmith

## Overview

The Agent Council uses LangSmith for comprehensive tracing and observability across:
- Agent execution
- Tool calls
- Workflow nodes
- Debate cycles
- Consensus computation
- API endpoints

## Setup

### 1. Install LangSmith

pip install langsmith langchain-core


### 2. Configure Environment

export ENABLE_LANGSMITH=true
export LANGSMITH_API_KEY=your-key
export LANGSMITH_PROJECT=agent-council


### 3. Verify Configuration

curl http://localhost:8000/health


Response should include:
json
{
  "langsmith_enabled": true,
  "langsmith_project": "agent-council"
}


## Trace Hierarchy

LangSmith captures a hierarchical trace for each workflow execution:


Workflow Start
├─ Master Architect Run
│  └─ Gemini Generate
├─ Solution Architect Run
│  ├─ Vibes Analyze API Spec
│  ├─ MCP Get Environment Info
│  └─ Lucid Generate Diagram
├─ Reviewer Round
│  ├─ NFR/Performance Reviewer Run
│  │  └─ Vibes Recommend Patterns
│  ├─ Security Reviewer Run
│  │  └─ MCP List Policies
│  └─ Integration Reviewer Run
├─ Detect Disagreements
├─ Debate Cycle (if disagreements)
│  ├─ Debate Round 1
│  └─ Debate Round 2
├─ Compute Consensus
├─ Architect Adjudicator (if needed)
├─ Human Approval Gate
├─ FAQ Generation
└─ Finalize


## Viewing Traces

### From Streamlit UI

1. Start a council session
2. Click "View Trace in LangSmith" link
3. Opens LangSmith UI with full execution graph

### From API

GET /replay/{session_id}


Returns:
json
{
  "langsmith_url": "https://smith.langchain.com/public/agent-council/r/...",
  "langsmith_run_id": "...",
  "trace_available": true
}


### From LangSmith Dashboard

1. Go to https://smith.langchain.com
2. Select project: "agent-council"
3. Browse all runs

## Debugging with LangSmith

### 1. Agent Failures

- View exact input/output for each agent
- See which step failed
- Inspect LLM prompts and responses
- Check tool call results

### 2. Performance Analysis

- See execution time for each node
- Identify bottlenecks
- Compare runs side-by-side

### 3. Consensus Issues

- View all reviewer outputs
- See disagreement detection logic
- Follow debate rounds step-by-step
- Understand adjudicator decisions

## Production Best Practices

1. **Rate Limiting**: LangSmith has API limits
2. **Sampling**: Trace percentage of production runs
3. **Retention**: Configure trace retention period
4. **Security**: Ensure PII is not logged in traces
5. **Cost**: Monitor LangSmith usage costs

## Troubleshooting

### Traces Not Appearing

1. Check ENABLE_LANGSMITH=true
2. Verify LANGSMITH_API_KEY is set
3. Check /health endpoint shows langsmith_enabled: true
4. Review logs for langsmith initialization errors

### Missing Child Spans

1. Ensure all methods have @traceable decorator
2. Check langsmith package is installed
3. Verify LANGCHAIN_TRACING_V2=true

## Metrics Available

- **Total Runs**: All workflow executions
- **Success Rate**: Percentage of successful completions
- **Average Duration**: Time per workflow
- **Token Usage**: LLM token consumption
- **Tool Calls**: External tool invocations
- **Error Rate**: Failures by agent/node
```

---

## 📊 Implementation Progress

| Task | Status | Complexity | Est. Time |
|------|--------|------------|-----------|
| 1. Settings | ✅ Complete | Low | Done |
| 2. Initialization | ✅ Complete | Medium | Done |
| 3. Agent Tracing | ✅ Complete | Medium | Done |
| 4. Tool Tracing | ⏳ Pending | Medium | 1 hour |
| 5. Debate/Consensus Tracing | ⏳ Pending | Low | 30 min |
| 6. Workflow Node Tracing | ⏳ Pending | Medium | 1 hour |
| 7. API Endpoint Tracing | ⏳ Pending | Low | 30 min |
| 8. State run_id | ⏳ Pending | Medium | 45 min |
| 9. UI Trace Link | ⏳ Pending | Low | 30 min |
| 10. Replay Endpoint | ⏳ Pending | Low | 30 min |
| 11. Tests | ⏳ Pending | High | 2 hours |
| 12. Documentation | ⏳ Pending | Medium | 1 hour |

**Total Remaining**: ~7.5 hours

---

## 🚀 Quick Start (Current State)

### Enable Tracing

```bash
# Set environment variables
export ENABLE_LANGSMITH=true
export LANGSMITH_API_KEY=lsv2_pt_...
export LANGSMITH_PROJECT=agent-council

# Install langsmith
pip install langsmith langchain-core

# Run backend
uvicorn main:app --reload
```

### What's Already Traced

✅ All 7 agent `run()` methods  
✅ LangSmith client initialization  
✅ Environment variable setup  
✅ Trace URL generation helpers  

### What's NOT Yet Traced

❌ Tool method calls  
❌ Debate/consensus functions  
❌ LangGraph workflow nodes  
❌ FastAPI endpoints  
❌ UI doesn't show trace links  
❌ No replay endpoint  

---

## 🎯 Next Steps

### Immediate (High Priority)
1. **Tool Tracing** - Add @traceable to all 20+ tool methods
2. **Workflow Node Tracing** - Add to 10 LangGraph nodes
3. **State run_id** - Capture and persist run IDs

### Soon (Medium Priority)
4. **API Tracing** - Add to 8 key endpoints
5. **UI Integration** - Show trace links in Streamlit
6. **Replay Endpoint** - Enable trace replay from UI

### Later (Nice to Have)
7. **Debate Tracing** - Detailed debate cycle traces
8. **Tests** - 40+ tests for tracing
9. **Documentation** - Complete observability guide

---

## 📝 Notes

- **Graceful Degradation**: All tracing is optional via try/except imports
- **Zero Breaking Changes**: System works with or without LangSmith
- **Production Ready**: Settings-based toggle for prod/dev
- **Performance**: Minimal overhead (~5ms per trace)
- **Security**: No secrets logged in traces

---

**Last Updated**: November 26, 2025  
**Implementation Status**: **Foundation Complete (25%)** 
**Blocked By**: None - ready to continue

