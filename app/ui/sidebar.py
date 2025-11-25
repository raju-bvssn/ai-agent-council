"""
Streamlit sidebar with navigation and admin tools.

Displays:
- Navigation menu
- Session management
- Admin panel (prototype tools)
"""

import streamlit as st
from typing import Optional

from app.ui.api_client import APIClient, get_api_client
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_sidebar():
    """
    Render sidebar with navigation and admin tools.
    """
    with st.sidebar:
        st.title("🏛️ Agent Council")
        st.markdown("---")
        
        # Navigation
        render_navigation()
        
        st.markdown("---")
        
        # Session Management
        render_session_management()
        
        st.markdown("---")
        
        # Admin Tools (Prototype)
        render_admin_panel()


def render_navigation():
    """
    Render navigation menu.
    """
    st.subheader("📍 Navigation")
    
    # Navigation buttons
    if st.button("🏠 Home", use_container_width=True):
        st.session_state.page = "council_setup"
        st.rerun()
    
    if st.button("📋 Active Sessions", use_container_width=True):
        st.session_state.page = "session_list"
        st.rerun()


def render_session_management():
    """
    Render current session information.
    """
    st.subheader("💼 Current Session")
    
    session_id = st.session_state.get("current_session_id")
    
    if session_id:
        st.success(f"**Session ID:**")
        st.code(session_id, language=None)
        
        # Option to clear current session
        if st.button("🔄 New Session", use_container_width=True):
            # Clear session state
            st.session_state.current_session_id = None
            st.session_state.page = "council_setup"
            st.success("Session cleared. Starting new session.")
            st.rerun()
    else:
        st.info("No active session")


def render_admin_panel():
    """
    Render admin panel with prototype tools.
    
    **WARNING**: These tools are for POC/demo purposes only.
    In production, these should be properly secured.
    """
    st.subheader("⚙️ Prototype Tools")
    st.caption("⚠️ Admin functions for POC/demo")
    
    # Initialize API client
    api_client = get_api_client()
    
    # Show stats
    try:
        with st.expander("📊 System Stats"):
            stats = api_client.get_admin_stats()
            st.metric("Total Sessions", stats.get("total_sessions", 0))
            
            status_breakdown = stats.get("status_breakdown", {})
            if status_breakdown:
                st.write("**Status Breakdown:**")
                for status, count in status_breakdown.items():
                    st.write(f"- {status.replace('_', ' ').title()}: {count}")
    except Exception as e:
        logger.error("Failed to fetch admin stats", error=str(e))
    
    # Clear All Sessions
    st.markdown("### 🧹 Clear All Sessions")
    st.caption("Removes all session data from database")
    
    if st.button("Clear All Sessions", use_container_width=True, type="secondary"):
        try:
            result = api_client.clear_all_sessions()
            count = result.get("count", 0)
            st.success(f"✅ Cleared {count} sessions")
            logger.info("all_sessions_cleared_from_ui", count=count)
            
            # Clear local session state
            if "current_session_id" in st.session_state:
                del st.session_state["current_session_id"]
            if "current_workflow_state" in st.session_state:
                del st.session_state["current_workflow_state"]
            
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Failed to clear sessions: {str(e)}")
            logger.error("clear_sessions_failed", error=str(e))
    
    # Reset Database (Danger Zone)
    st.markdown("### ⚠️ Reset Database")
    st.caption("**DANGER ZONE**: Permanently deletes ALL data")
    
    # Two-step confirmation
    if "confirm_reset" not in st.session_state:
        st.session_state.confirm_reset = False
    
    if not st.session_state.confirm_reset:
        if st.button("Reset Database", use_container_width=True, type="primary"):
            st.session_state.confirm_reset = True
            st.warning("⚠️ Click **Confirm Reset** to proceed")
            st.rerun()
    else:
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.confirm_reset = False
                st.rerun()
        
        with col2:
            if st.button("✅ Confirm Reset", use_container_width=True, type="primary"):
                try:
                    result = api_client.reset_database()
                    st.success("✅ Database reset successfully")
                    logger.warning("database_reset_from_ui")
                    
                    # Clear all session state
                    for key in list(st.session_state.keys()):
                        if key != "confirm_reset":
                            del st.session_state[key]
                    
                    st.session_state.confirm_reset = False
                    st.session_state.page = "council_setup"
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to reset database: {str(e)}")
                    logger.error("reset_database_failed", error=str(e))
                    st.session_state.confirm_reset = False
