"""
UI package for Agent Council Streamlit application.

Provides modular UI components following Clean Architecture principles.
All business logic is delegated to the application layer.
"""

from app.ui.agent_selector import render_agent_selector
from app.ui.api_client import APIClient, get_api_client
from app.ui.approval_panel import render_approval_panel
from app.ui.council_setup import render_council_setup, render_session_list
from app.ui.feedback_panel import render_feedback_panel
from app.ui.final_output import render_final_output
from app.ui.main_view import render_main_view
from app.ui.sidebar import render_sidebar

__all__ = [
    "render_sidebar",
    "render_main_view",
    "render_council_setup",
    "render_session_list",
    "render_agent_selector",
    "render_feedback_panel",
    "render_approval_panel",
    "render_final_output",
    "APIClient",
    "get_api_client",
]

