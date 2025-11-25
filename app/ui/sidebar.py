"""
Sidebar UI component for Agent Council system.

Global navigation and session management.
"""

import streamlit as st

from app.utils.logging import get_logger
from app.utils.settings import get_settings

logger = get_logger(__name__)


def render_sidebar():
    """
    Render application sidebar with navigation and settings.
    """
    with st.sidebar:
        # Logo/Title
        st.title("🏛️ Agent Council")
        st.caption("Multi-Agent Solution Design System")

        st.divider()

        # Navigation
        st.subheader("📍 Navigation")

        # Initialize page in session state
        if "page" not in st.session_state:
            st.session_state.page = "council_setup"

        pages = {
            "council_setup": "🏠 Home / Setup",
            "agent_selector": "🤖 Configure Agents",
            "workflow_execution": "▶️ Execution",
            "feedback_panel": "💬 Feedback",
            "approval_panel": "✋ Approval",
            "final_output": "🎉 Final Output",
        }

        for page_key, page_label in pages.items():
            if st.button(page_label, key=f"nav_{page_key}", use_container_width=True):
                st.session_state.page = page_key
                st.rerun()

        st.divider()

        # Current session info
        if "current_session_id" in st.session_state:
            st.subheader("📋 Current Session")
            st.code(st.session_state.current_session_id[:16] + "...", language=None)

            if st.button("🔄 New Session", use_container_width=True):
                if "current_session_id" in st.session_state:
                    del st.session_state.current_session_id
                st.session_state.page = "council_setup"
                st.rerun()

        st.divider()

        # Settings info
        settings = get_settings()
        st.subheader("⚙️ Settings")
        st.caption(f"Environment: {settings.env}")
        st.caption(f"LLM: {settings.gemini_model}")

        # Debug info
        if settings.debug:
            with st.expander("🐛 Debug Info"):
                st.json({
                    "session_id": st.session_state.get("current_session_id", "None"),
                    "page": st.session_state.page,
                    "selected_agents": len(st.session_state.get("selected_agents", [])),
                })

        st.divider()

        # Footer
        st.caption("Built for Salesforce PS")
        st.caption("Mission Critical Data Compliant")

