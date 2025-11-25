"""
Graph package for Agent Council workflow.

Provides:
- Workflow state models
- Node definitions
- Workflow evaluator for conditional routing
- Workflow graph builder
"""

from app.graph.evaluator import WorkflowEvaluator, create_routing_function
from app.graph.node_definitions import (
    faq_generation_node,
    finalize_node,
    human_approval_node,
    master_architect_node,
    reviewer_node,
    solution_architect_node,
)
from app.graph.state_models import (
    AgentMessage,
    AgentRole,
    DesignDocument,
    HumanAction,
    ReviewDecision,
    ReviewFeedback,
    WorkflowResult,
    WorkflowState,
    WorkflowStatus,
)
from app.graph.workflow import (
    compile_workflow,
    create_workflow_graph,
    execute_workflow,
    execute_workflow_sync,
    get_workflow_status,
    run_council_workflow,
    step_council_workflow,
)

__all__ = [
    # State Models
    "WorkflowState",
    "WorkflowStatus",
    "AgentRole",
    "ReviewDecision",
    "AgentMessage",
    "ReviewFeedback",
    "DesignDocument",
    "HumanAction",
    "WorkflowResult",
    # Nodes
    "master_architect_node",
    "solution_architect_node",
    "reviewer_node",
    "human_approval_node",
    "faq_generation_node",
    "finalize_node",
    # Evaluator
    "WorkflowEvaluator",
    "create_routing_function",
    # Workflow
    "create_workflow_graph",
    "compile_workflow",
    "execute_workflow",
    "execute_workflow_sync",
    "run_council_workflow",
    "step_council_workflow",
    "get_workflow_status",
]

