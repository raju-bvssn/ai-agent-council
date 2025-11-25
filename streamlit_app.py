"""
Streamlit application entry point for Agent Council system.

Run with: streamlit run streamlit_app.py
"""

import streamlit as st

from app.ui.main_view import render_main_view
from app.ui.sidebar import render_sidebar
from app.ui.styles import inject_slds_theme
from app.utils.logging import configure_logging, get_logger
from app.utils.settings import get_settings

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Agent Council",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject Salesforce Lightning Design System theme
inject_slds_theme()


def initialize_session_state():
    """Initialize Streamlit session state variables."""
    if "page" not in st.session_state:
        st.session_state.page = "council_setup"
    
    if "current_session_id" not in st.session_state:
        st.session_state.current_session_id = None
    
    if "session_name" not in st.session_state:
        st.session_state.session_name = None
    
    if "selected_agents" not in st.session_state:
        from app.graph.state_models import AgentRole
        st.session_state.selected_agents = [
            AgentRole.MASTER,
            AgentRole.SOLUTION_ARCHITECT,
            AgentRole.REVIEWER_NFR,
            AgentRole.REVIEWER_SECURITY,
            AgentRole.REVIEWER_INTEGRATION,
            AgentRole.FAQ,
        ]
    
    if "workflow_running" not in st.session_state:
        st.session_state.workflow_running = False


def main():
    """Main application entry point."""
    settings = get_settings()

    try:
        logger.info("streamlit_app_started", env=settings.env)
    except Exception as e:
        # Fallback if logging fails - don't crash the app
        print(f"Streamlit app started (logging error: {e})")

    # Initialize session state
    initialize_session_state()

    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_view()


if __name__ == "__main__":
    main()

