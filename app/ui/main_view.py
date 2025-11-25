"""
Main View UI component for Agent Council system.

Main content area router based on current page.
"""

import streamlit as st

from app.ui.agent_selector import render_agent_selector
from app.ui.approval_panel import render_approval_panel
from app.ui.council_setup import render_council_setup, render_session_list
from app.ui.feedback_panel import render_feedback_panel
from app.ui.final_output import render_final_output
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_main_view():
    """
    Render main content area based on current page.
    """
    # Get current page from session state
    current_page = st.session_state.get("page", "council_setup")
    session_id = st.session_state.get("current_session_id")

    # Route to appropriate page
    if current_page == "council_setup":
        render_council_setup()
        st.divider()
        render_session_list()

    elif current_page == "agent_selector":
        render_agent_selector()

    elif current_page == "workflow_execution":
        _render_workflow_execution()

    elif current_page == "feedback_panel":
        if session_id:
            render_feedback_panel(session_id)
        else:
            st.warning("No active session")

    elif current_page == "approval_panel":
        if session_id:
            render_approval_panel(session_id)
        else:
            st.warning("No active session")

    elif current_page == "final_output":
        if session_id:
            render_final_output(session_id)
        else:
            st.warning("No active session")

    else:
        st.error(f"Unknown page: {current_page}")


def _render_workflow_execution():
    """
    Render workflow execution page.

    TODO: Phase 2 - Implement live workflow execution with streaming updates
    """
    st.header("▶️ Workflow Execution")

    if "current_session_id" not in st.session_state:
        st.warning("No active session")
        return

    session_id = st.session_state.current_session_id

    st.info(f"**Session ID:** `{session_id[:16]}...`")

    # Workflow status
    st.subheader("🔄 Workflow Status")

    # Placeholder for workflow execution
    st.info("⏳ Workflow execution interface coming in Phase 2")

    # Show workflow steps
    steps = [
        "Master Architect Analysis",
        "Solution Architect Design",
        "NFR Review",
        "Security Review",
        "Integration Review",
        "Human Approval",
        "FAQ Generation",
        "Finalization",
    ]

    for idx, step in enumerate(steps, 1):
        st.write(f"{idx}. {step}")

    st.divider()

    # Action buttons
    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("▶️ Start Execution", type="primary"):
            st.success("Starting workflow execution...")
            # TODO: Phase 2 - Trigger workflow execution
            logger.info("ui_workflow_started", session_id=session_id)

    with col2:
        if st.button("⏸️ Pause Execution"):
            st.warning("Pausing workflow...")
            # TODO: Phase 2 - Implement pause
            logger.info("ui_workflow_paused", session_id=session_id)

    # Progress indicator
    st.divider()
    st.subheader("📊 Progress")
    st.progress(0)
    st.caption("Waiting to start...")

