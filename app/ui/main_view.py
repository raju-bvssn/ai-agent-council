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



