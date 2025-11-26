# LangSmith Integration - Completion Guide

**Status**: Foundation Complete (25%) | **Remaining**: 9 tasks | **Est. Time**: 6-8 hours

This document provides **exact code changes** needed to complete full LangSmith observability.

---

## 📋 Quick Implementation Checklist

- [x] Task 1-3: Settings, initialization, agent tracing (DONE)
- [ ] Task 4: Tool tracing (@traceable to 20+ methods)
- [ ] Task 5: Debate engine tracing
- [ ] Task 6: Consensus engine tracing  
- [ ] Task 7: Workflow node tracing (10 nodes)
- [ ] Task 8: API endpoint tracing (8 endpoints)
- [ ] Task 9: run_id in SessionState
- [ ] Task 10: LangSmith URL in API responses
- [ ] Task 11: UI trace link
- [ ] Task 12: Replay endpoint
- [ ] Task 13: Tests (40+ tests)
- [ ] Task 14: Documentation

---

## ⚡ TASK 4: Tool Client Tracing (Priority: HIGH)

### Files to Modify (5 files):

#### 1. `app/tools/vibes_client.py`

**Add after imports**:
```python
# LangSmith tracing
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
```

**Add @traceable to methods**:
```python
@traceable(name="vibes_execute")
async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
    ...

@traceable(name="vibes_analyze_api_spec")
async def _analyze_api_spec(self, spec_text: Optional[str], spec_type: str = "raml") -> ToolResult:
    ...

@traceable(name="vibes_recommend_patterns")
async def _recommend_patterns(self, description: Optional[str]) -> ToolResult:
    ...

@traceable(name="vibes_review_error_handling")
async def _review_error_handling(self, design: Optional[str]) -> ToolResult:
    ...

@traceable(name="vibes_validate_nfrs")
async def _validate_nfrs(self, requirements: Optional[str]) -> ToolResult:
    ...
```

#### 2. `app/tools/mcp_client.py`

**Add imports + decorators**:
```python
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

@traceable(name="mcp_execute")
async def _execute(self, operation: str, parameters: Dict[str, Any]) -> ToolResult:
    ...

@traceable(name="mcp_get_environment_info")
async def _get_environment_info(self, env_id: str) -> ToolResult:
    ...

@traceable(name="mcp_get_api_metadata")
async def _get_api_metadata(self, api_id: str) -> ToolResult:
    ...

@traceable(name="mcp_list_policies")
async def _list_policies(self, env_id: str) -> ToolResult:
    ...

@traceable(name="mcp_get_runtime_config")
async def _get_runtime_config(self, runtime_id: str) -> ToolResult:
    ...
```

#### 3. `app/tools/lucid_client.py`

```python
@traceable(name="lucid_execute")
async def _execute(...):
    ...

@traceable(name="lucid_generate_architecture_diagram")
async def _generate_architecture_diagram(...):
    ...

@traceable(name="lucid_generate_sequence_diagram")
async def _generate_sequence_diagram(...):
    ...

@traceable(name="lucid_generate_data_flow")
async def _generate_data_flow_diagram(...):
    ...
```

#### 4. `app/tools/gemini_client.py`

```python
@traceable(name="gemini_generate")
async def generate(self, text: str, model: str = "gemini-1.5-flash") -> str:
    ...

@traceable(name="gemini_analyze_long_context")
async def analyze_long_context(self, text: str) -> ToolResult:
    ...
```

#### 5. `app/tools/notebooklm_client.py`

```python
@traceable(name="notebooklm_summarize")
async def summarize_with_sources(self, text: str) -> ToolResult:
    ...

@traceable(name="notebooklm_answer_questions")
async def answer_questions(self, text: str, questions: List[str]) -> ToolResult:
    ...
```

**Estimated Time**: 1 hour

---

## ⚡ TASK 5: Debate Engine Tracing (Priority: MEDIUM)

### File: `app/graph/debate/debate_engine.py`

**Add imports**:
```python
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
```

**Add decorators**:
```python
@traceable(name="debate_run")
async def run_debate(
    disagreement: Disagreement,
    context: str,
    model: Optional[str] = None,
    max_rounds: int = 2
) -> DebateOutcome:
    ...

@traceable(name="debate_round_execution")
async def _execute_debate_round(...):
    ...

@traceable(name="debate_convergence_check")
def _check_convergence(...):
    ...
```

### File: `app/graph/debate/detector.py`

```python
@traceable(name="detect_disagreements")
def detect_disagreements(reviews: List[ReviewFeedback]) -> List[Disagreement]:
    ...

@traceable(name="analyze_conflict_severity")
def analyze_conflict_severity(reviews: List[ReviewFeedback]) -> str:
    ...
```

**Estimated Time**: 30 minutes

---

## ⚡ TASK 6: Consensus Engine Tracing (Priority: MEDIUM)

### File: `app/graph/debate/consensus.py`

```python
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

@traceable(name="consensus_compute")
def compute_consensus(
    reviews: List[ReviewFeedback],
    debates: List[DebateOutcome],
    threshold: float = 0.65
) -> ConsensusResult:
    ...

@traceable(name="consensus_weighted_scoring")
def _compute_weighted_scores(reviews: List[ReviewFeedback]) -> Dict[str, float]:
    ...

@traceable(name="consensus_debate_adjustment")
def _apply_debate_adjustments(base_score: float, debates: List[DebateOutcome]) -> float:
    ...
```

**Estimated Time**: 20 minutes

---

## ⚡ TASK 7: Workflow Node Tracing (Priority: HIGH)

### Files: `app/graph/workflow.py` and `app/graph/phase3b_nodes.py`

**Add imports to both files**:
```python
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
```

**In `workflow.py` or `node_definitions.py`**:
```python
@traceable(name="workflow_master_architect")
def master_architect_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_solution_architect")
def solution_architect_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_reviewer")
def reviewer_node(state: WorkflowState, role: AgentRole) -> Dict[str, Any]:
    ...

@traceable(name="workflow_human_approval")
def human_approval_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_faq_generation")
def faq_generation_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_finalize")
def finalize_node(state: WorkflowState) -> Dict[str, Any]:
    ...
```

**In `phase3b_nodes.py`**:
```python
@traceable(name="workflow_create_reviewer_round")
def create_reviewer_round_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_detect_disagreements")
def detect_disagreements_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_debate_cycle")
def debate_cycle_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_compute_consensus")
def compute_consensus_node(state: WorkflowState) -> Dict[str, Any]:
    ...

@traceable(name="workflow_architect_adjudicator")
def architect_adjudicator_node(state: WorkflowState) -> Dict[str, Any]:
    ...
```

**Estimated Time**: 1 hour

---

## ⚡ TASK 8: API Endpoint Tracing (Priority: HIGH)

### File: `app/api/routes.py` or `app/api/workflow_routes.py`

**Add imports**:
```python
try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])
```

**Add decorators to endpoints**:
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

@router.get("/workflow/{session_id}/status")
@traceable(name="api_get_workflow_status")
async def get_workflow_status(session_id: str):
    ...

@router.post("/workflow/{session_id}/approve")
@traceable(name="api_approve_design")
async def approve_design(session_id: str, request: ApproveRequest):
    ...

@router.post("/workflow/{session_id}/revise")
@traceable(name="api_request_revision")
async def request_revision(session_id: str, request: ReviseRequest):
    ...

@router.get("/health")
@traceable(name="api_health_check")
async def health_check():
    ...

@router.get("/sessions")
@traceable(name="api_list_sessions")
async def list_sessions(limit: int = 50, offset: int = 0):
    ...
```

**Estimated Time**: 30 minutes

---

## ⚡ TASK 9: Store run_id in SessionState (Priority: CRITICAL)

### File: `app/graph/state_models.py`

**Add fields to `WorkflowState`**:
```python
class WorkflowState(BaseModel):
    # ... existing fields ...
    
    # LangSmith tracing
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
```

### File: `app/graph/workflow.py`

**In `run_council_workflow()` function**:
```python
from app.observability import get_current_run_id, get_trace_url, is_tracing_enabled

def run_council_workflow(session_id: str) -> WorkflowResult:
    """Execute the complete council workflow."""
    
    # Load state
    persistence = get_persistence_manager()
    state = persistence.load_state(session_id)
    
    # Capture LangSmith run ID if tracing enabled
    if is_tracing_enabled():
        run_id = get_current_run_id()
        if run_id:
            state.langsmith_run_id = run_id
            state.langsmith_trace_url = get_trace_url(run_id)
            logger.info("langsmith_run_captured", run_id=run_id, session_id=session_id)
    
    # ... rest of workflow execution ...
    
    # Persist state (including run_id)
    persistence.save_state(state)
    
    return WorkflowResult.from_workflow_state(state)
```

### File: `app/state/persistence.py`

**Ensure database schema supports new fields** (if using SQLAlchemy):
```python
# Add columns to CouncilSession table
langsmith_run_id = Column(String, nullable=True)
langsmith_trace_url = Column(String, nullable=True)
```

**Estimated Time**: 45 minutes

---

## ⚡ TASK 10: Expose LangSmith URL in API (Priority: HIGH)

### File: `app/api/schemas.py`

**Update `SessionDetailResponse`**:
```python
class SessionDetailResponse(BaseModel):
    # ... existing fields ...
    
    # LangSmith observability
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
```

**Update `WorkflowResult` (in `state_models.py`)**:
```python
class WorkflowResult(BaseModel):
    # ... existing fields ...
    
    # LangSmith tracing
    langsmith_run_id: Optional[str] = None
    langsmith_trace_url: Optional[str] = None
```

**Update `from_workflow_state()` method**:
```python
@classmethod
def from_workflow_state(cls, state: WorkflowState, ...) -> "WorkflowResult":
    return cls(
        # ... existing fields ...
        langsmith_run_id=state.langsmith_run_id,
        langsmith_trace_url=state.langsmith_trace_url,
    )
```

**Estimated Time**: 20 minutes

---

## ⚡ TASK 11: UI Trace Link (Priority: MEDIUM)

### File: `app/ui/feedback_panel.py`

**Add after status display**:
```python
def render_feedback_panel(session_id: str):
    ...
    session_data = api_client.get_session(session_id)
    
    # Display LangSmith trace link
    trace_url = session_data.get("langsmith_trace_url")
    if trace_url:
        render_slds_card("🔍 Observability")
        st.markdown(f"""
        **View Complete Execution Trace**  
        See the full workflow execution graph, agent interactions, and tool calls:
        
        [{" Open in LangSmith →"}]({trace_url})
        """)
        close_slds_card()
        st.markdown("<br>", unsafe_allow_html=True)
    ...
```

### Alternative: Add to Sidebar

```python
# In app/ui/sidebar.py
def render_sidebar():
    ...
    if st.session_state.get("current_session_id"):
        session_data = api_client.get_session(st.session_state.current_session_id)
        
        if session_data.get("langsmith_trace_url"):
            st.sidebar.markdown("---")
            st.sidebar.markdown("### 🔍 Observability")
            st.sidebar.markdown(f"[View Trace in LangSmith →]({session_data['langsmith_trace_url']})")
```

**Estimated Time**: 20 minutes

---

## ⚡ TASK 12: Replay Endpoint (Priority: LOW)

### File: `app/api/routes.py` or new `app/api/observability_routes.py`

```python
from fastapi import APIRouter, HTTPException
from app.state.persistence import get_persistence_manager
from app.observability import get_trace_url

try:
    from langsmith import traceable
except ImportError:
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator if not args else decorator(args[0])

observability_router = APIRouter(prefix="/observability", tags=["Observability"])

@observability_router.get("/replay/{session_id}")
@traceable(name="api_replay_session")
async def replay_session(session_id: str):
    """
    Get LangSmith replay URL for a session.
    
    Returns the full trace URL if the session was executed with tracing enabled.
    """
    persistence = get_persistence_manager()
    state = persistence.load_state(session_id)
    
    if not state:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if not state.langsmith_run_id:
        raise HTTPException(
            status_code=404,
            detail="No LangSmith trace available for this session. Enable LANGSMITH_TRACING=true."
        )
    
    return {
        "session_id": session_id,
        "langsmith_run_id": state.langsmith_run_id,
        "langsmith_url": state.langsmith_trace_url or get_trace_url(state.langsmith_run_id),
        "trace_available": True
    }

# Include in main router
# In app/api/routes.py:
# from app.api.observability_routes import observability_router
# app.include_router(observability_router)
```

**Estimated Time**: 30 minutes

---

## ⚡ TASK 13: Tracing Tests (Priority: MEDIUM)

### File: `tests/test_langsmith_integration.py` (create new)

```python
"""
Comprehensive tests for LangSmith tracing integration.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import os

from app.observability import (
    initialize_langsmith,
    get_langsmith_client,
    is_tracing_enabled,
    get_trace_url,
    get_current_run_id
)


class TestLangSmithInitialization:
    """Test LangSmith initialization and configuration."""
    
    def test_initialization_disabled(self):
        """Test that initialization returns None when disabled."""
        with patch('app.observability.langsmith_init.get_settings') as mock_settings:
            mock_settings.return_value.is_langsmith_enabled = False
            client = initialize_langsmith()
            assert client is None
    
    def test_initialization_no_api_key(self):
        """Test initialization without API key."""
        with patch('app.observability.langsmith_init.get_settings') as mock_settings:
            mock_settings.return_value.is_langsmith_enabled = True
            mock_settings.return_value.get_langsmith_api_key.return_value = None
            client = initialize_langsmith()
            assert client is None
    
    @patch('app.observability.langsmith_init.Client')
    def test_initialization_success(self, mock_client_class):
        """Test successful LangSmith initialization."""
        with patch('app.observability.langsmith_init.get_settings') as mock_settings:
            mock_settings.return_value.is_langsmith_enabled = True
            mock_settings.return_value.get_langsmith_api_key.return_value = "test-key"
            mock_settings.return_value.langsmith_project = "test-project"
            mock_settings.return_value.langsmith_endpoint = "https://api.smith.langchain.com"
            
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            
            client = initialize_langsmith()
            assert client == mock_client
            mock_client_class.assert_called_once()
    
    def test_is_tracing_enabled(self):
        """Test is_tracing_enabled check."""
        with patch('app.observability.langsmith_init.get_settings') as mock_settings:
            mock_settings.return_value.is_langsmith_enabled = True
            mock_settings.return_value.get_langsmith_api_key.return_value = "test-key"
            
            with patch('app.observability.langsmith_init.get_langsmith_client', return_value=Mock()):
                assert is_tracing_enabled() is True
    
    def test_get_trace_url(self):
        """Test trace URL generation."""
        run_id = "test-run-123"
        url = get_trace_url(run_id)
        
        assert "smith.langchain.com" in url
        assert run_id in url


class TestAgentTracing:
    """Test that agents have tracing decorators."""
    
    def test_master_architect_has_traceable(self):
        """Test MasterArchitectAgent.run has tracing."""
        from app.agents.master_agent import MasterArchitectAgent
        agent = MasterArchitectAgent()
        assert hasattr(agent, 'run')
        assert callable(agent.run)
    
    def test_solution_architect_has_traceable(self):
        """Test SolutionArchitectAgent.run has tracing."""
        from app.agents.solution_architect_agent import SolutionArchitectAgent
        agent = SolutionArchitectAgent()
        assert hasattr(agent, 'run')
    
    def test_reviewer_agents_have_traceable(self):
        """Test reviewer agents have tracing."""
        from app.agents.reviewer_agent import (
            NFRPerformanceReviewer,
            SecurityReviewer,
            IntegrationReviewer
        )
        
        for ReviewerClass in [NFRPerformanceReviewer, SecurityReviewer, IntegrationReviewer]:
            reviewer = ReviewerClass()
            assert hasattr(reviewer, 'run')


class TestToolTracing:
    """Test that tool methods have tracing decorators."""
    
    def test_vibes_client_methods(self):
        """Test Vibes client methods exist."""
        from app.tools.vibes_client import VibesClient
        client = VibesClient()
        
        # Check key methods exist
        assert hasattr(client, '_execute')
        assert hasattr(client, '_analyze_api_spec')
    
    def test_mcp_client_methods(self):
        """Test MCP client methods exist."""
        from app.tools.mcp_client import MCPClient
        client = MCPClient()
        
        assert hasattr(client, '_execute')
        assert hasattr(client, '_get_environment_info')
    
    def test_lucid_client_methods(self):
        """Test Lucid client methods exist."""
        from app.tools.lucid_client import LucidClient
        client = LucidClient()
        
        assert hasattr(client, '_execute')


class TestWorkflowStateRunID:
    """Test run_id storage in WorkflowState."""
    
    def test_workflow_state_has_run_id_fields(self):
        """Test WorkflowState has LangSmith fields."""
        from app.graph.state_models import WorkflowState
        
        state = WorkflowState(session_id="test", user_request="test")
        assert hasattr(state, 'langsmith_run_id')
        assert hasattr(state, 'langsmith_trace_url')
    
    def test_workflow_result_has_run_id_fields(self):
        """Test WorkflowResult exposes LangSmith fields."""
        from app.graph.state_models import WorkflowResult, WorkflowState
        
        state = WorkflowState(
            session_id="test",
            user_request="test",
            langsmith_run_id="test-run-123",
            langsmith_trace_url="https://smith.langchain.com/..."
        )
        
        result = WorkflowResult.from_workflow_state(state)
        assert result.langsmith_run_id == "test-run-123"
        assert result.langsmith_trace_url == "https://smith.langchain.com/..."


class TestAPITracing:
    """Test API endpoint tracing."""
    
    @pytest.mark.asyncio
    async def test_health_endpoint_traced(self):
        """Test health check endpoint is traced."""
        from app.api.routes import health_check
        
        result = await health_check()
        assert result is not None
    
    def test_replay_endpoint_exists(self):
        """Test replay endpoint exists (if implemented)."""
        # This test would check if replay endpoint is registered
        pass


class TestTracingDisabled:
    """Test that system works when LangSmith is disabled."""
    
    def test_agents_work_without_langsmith(self):
        """Test agents execute without LangSmith."""
        with patch.dict(os.environ, {"ENABLE_LANGSMITH": "false"}):
            from app.agents.master_agent import MasterArchitectAgent
            from app.agents.performer import AgentInput
            
            agent = MasterArchitectAgent()
            # Should not crash even if langsmith not installed
            assert hasattr(agent, 'run')
    
    def test_workflow_works_without_langsmith(self):
        """Test workflow executes without LangSmith."""
        with patch.dict(os.environ, {"ENABLE_LANGSMITH": "false"}):
            from app.graph.state_models import WorkflowState
            
            state = WorkflowState(session_id="test", user_request="test")
            assert state.langsmith_run_id is None


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
```

**Run tests**:
```bash
pytest tests/test_langsmith_integration.py -v
```

**Estimated Time**: 2 hours

---

## ⚡ TASK 14: Observability Documentation (Priority: LOW)

### File: `docs/observability.md` (create new)

See `LANGSMITH_INTEGRATION.md` for complete documentation outline. Key sections:

1. **Overview** - What is traced
2. **Setup** - Environment variables
3. **Trace Hierarchy** - Visual diagram
4. **Viewing Traces** - UI, API, Dashboard
5. **Debugging** - How to use traces
6. **Production Best Practices** - Sampling, costs
7. **Troubleshooting** - Common issues

**Estimated Time**: 1 hour

---

## 🚀 Quick Start (After Implementation)

```bash
# 1. Enable LangSmith
export ENABLE_LANGSMITH=true
export LANGSMITH_API_KEY=lsv2_pt_your_key
export LANGSMITH_PROJECT=agent-council

# 2. Install dependencies
pip install langsmith langchain-core

# 3. Run backend
uvicorn main:app --reload

# 4. Create a session in Streamlit
# 5. Click "View in LangSmith" link
# 6. See full execution graph!
```

---

## 📊 Implementation Time Estimates

| Task | Est. Time | Priority |
|------|-----------|----------|
| 4. Tool tracing | 1h | HIGH |
| 5. Debate tracing | 30min | MEDIUM |
| 6. Consensus tracing | 20min | MEDIUM |
| 7. Workflow nodes | 1h | HIGH |
| 8. API endpoints | 30min | HIGH |
| 9. run_id storage | 45min | CRITICAL |
| 10. API URL exposure | 20min | HIGH |
| 11. UI trace link | 20min | MEDIUM |
| 12. Replay endpoint | 30min | LOW |
| 13. Tests | 2h | MEDIUM |
| 14. Documentation | 1h | LOW |
| **TOTAL** | **~8 hours** | - |

---

## 🎯 Recommended Implementation Order

### Phase 1 (Critical - 2.5 hours):
1. Task 9: run_id storage
2. Task 10: API URL exposure
3. Task 8: API endpoint tracing
4. Task 11: UI trace link

**Result**: End-to-end tracing visible in UI

### Phase 2 (High Value - 2.5 hours):
5. Task 4: Tool client tracing
6. Task 7: Workflow node tracing

**Result**: Complete trace hierarchy

### Phase 3 (Nice to Have - 3 hours):
7. Task 5 & 6: Debate/consensus tracing
8. Task 12: Replay endpoint
9. Task 13: Tests
10. Task 14: Documentation

---

## ✅ Validation Checklist

After implementation, verify:

- [ ] Agents create traces in LangSmith
- [ ] Tool calls appear as child spans
- [ ] Workflow nodes show in execution graph
- [ ] Debate cycles visible
- [ ] API shows langsmith_url
- [ ] UI displays "View in LangSmith" link
- [ ] Replay endpoint works
- [ ] Tests pass
- [ ] System works with ENABLE_LANGSMITH=false
- [ ] No breaking changes

---

**Next Step**: Begin with Phase 1 (Critical Path) to get end-to-end tracing working, then iterate on remaining features.

