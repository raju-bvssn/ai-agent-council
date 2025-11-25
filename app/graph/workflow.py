"""
LangGraph workflow definition for Agent Council system.

Defines the workflow graph with nodes, edges, and conditional routing.
"""

from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.evaluator import WorkflowEvaluator
from app.graph.node_definitions import (
    faq_generation_node,
    finalize_node,
    human_approval_node,
    master_architect_node,
    reviewer_node,
    solution_architect_node,
)
from app.graph.state_models import AgentRole, WorkflowState
from app.utils.logging import get_logger

logger = get_logger(__name__)


def create_workflow_graph() -> StateGraph:
    """
    Create the Agent Council workflow graph.

    Workflow:
    1. Master Architect (initial analysis)
    2. Solution Architect (design document)
    3. Reviewers (parallel evaluation)
    4. Conditional:
       - If revisions needed → Solution Architect (revision loop)
       - If escalation needed → Human Approval
       - If approved → FAQ Generation
    5. Finalize

    Returns:
        Configured StateGraph
    """
    logger.info("creating_workflow_graph")

    # Create graph
    workflow = StateGraph(WorkflowState)

    # Add nodes
    workflow.add_node("master_architect", master_architect_node)
    workflow.add_node("solution_architect", solution_architect_node)

    # Add reviewer nodes
    workflow.add_node(
        "reviewer_nfr",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_NFR)
    )
    workflow.add_node(
        "reviewer_security",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_SECURITY)
    )
    workflow.add_node(
        "reviewer_integration",
        lambda state: reviewer_node(state, AgentRole.REVIEWER_INTEGRATION)
    )

    workflow.add_node("human_approval", human_approval_node)
    workflow.add_node("faq_generation", faq_generation_node)
    workflow.add_node("finalize", finalize_node)

    # Set entry point
    workflow.set_entry_point("master_architect")

    # Add edges
    # Master Architect → Solution Architect
    workflow.add_edge("master_architect", "solution_architect")

    # Solution Architect → All Reviewers (parallel)
    workflow.add_edge("solution_architect", "reviewer_nfr")
    workflow.add_edge("solution_architect", "reviewer_security")
    workflow.add_edge("solution_architect", "reviewer_integration")

    # Reviewers → Conditional routing
    # TODO: Phase 2 - Implement proper parallel reviewer coordination
    # For now, use simple sequential flow

    # After reviews, determine next step
    def route_after_reviews(state: WorkflowState) -> str:
        """Route after all reviews complete."""
        return WorkflowEvaluator.determine_next_step(state)

    # Conditional edges after reviews
    # TODO: Phase 2 - Add proper conditional edge routing
    # workflow.add_conditional_edges(
    #     "reviewer_integration",  # Last reviewer
    #     route_after_reviews,
    #     {
    #         "solution_architect": "solution_architect",  # Revision loop
    #         "human_approval": "human_approval",
    #         "faq_generation": "faq_generation",
    #     }
    # )

    # For Phase 1, use simple edges
    workflow.add_edge("reviewer_nfr", "human_approval")
    workflow.add_edge("reviewer_security", "human_approval")
    workflow.add_edge("reviewer_integration", "human_approval")

    # Human Approval → FAQ Generation
    workflow.add_edge("human_approval", "faq_generation")

    # FAQ Generation → Finalize
    workflow.add_edge("faq_generation", "finalize")

    # Finalize → END
    workflow.add_edge("finalize", END)

    logger.info("workflow_graph_created")

    return workflow


def compile_workflow() -> Any:
    """
    Compile the workflow graph.

    Returns:
        Compiled workflow ready for execution

    TODO: Phase 2 - Add LangSmith tracing configuration
    TODO: Phase 2 - Add checkpointing for state persistence
    """
    logger.info("compiling_workflow")

    graph = create_workflow_graph()
    compiled = graph.compile()

    logger.info("workflow_compiled")

    return compiled


# TODO: Phase 2 - Add workflow execution functions
# TODO: Phase 2 - Add streaming support for UI updates
# TODO: Phase 2 - Add checkpoint management for resuming workflows

