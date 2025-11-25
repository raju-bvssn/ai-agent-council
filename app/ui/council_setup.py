"""
Council Setup UI component for Agent Council system.

Allows users to create new council sessions with name, description, and requirements.
"""

import streamlit as st

from app.agents.suggestion_engine import suggest_roles
from app.ui.api_client import get_api_client
from app.ui.components import render_add_custom_role, render_agent_suggestions
from app.ui.styles import close_slds_card, render_slds_card, render_status_pill
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_council_setup():
    """
    Render council setup form.

    Allows users to:
    - Enter session name and description
    - Provide requirements/request
    - Add context information
    - Create new session
    """
    st.markdown("# 🏛️ Create Agent Council Session")
    st.caption("Start a new multi-agent design collaboration")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    render_slds_card("Session Configuration")

    # Session name (required)
    session_name = st.text_input(
        "Session Name *",
        placeholder="e.g., Customer Portal Integration Design",
        help="Give your session a meaningful name",
        key="session_name_input"
    )

    # Description/Requirements (required)
    user_request = st.text_area(
        "Description / Requirements *",
        placeholder="Describe what you need the Agent Council to help you design...\n\nExample: Design a secure customer portal integration using MuleSoft that handles 10k+ transactions per day with OAuth authentication and real-time data sync.",
        height=150,
        help="Provide detailed requirements for AI-powered agent suggestions",
        key="user_request_input"
    )
    
    close_slds_card()

    # AI-suggested agent roles
    if user_request and len(user_request.strip()) > 10:
        suggested_roles = suggest_roles(user_request)
        render_agent_suggestions(suggested_roles)
    else:
        st.info("💡 Enter your requirements above to see AI-suggested agent roles")

    # Add custom role component
    render_add_custom_role()
    
    # Submit button (outside form for better UX)
    st.markdown("<br>", unsafe_allow_html=True)
    submitted = st.button("🚀 Create Session & Configure Agents", type="primary", use_container_width=True)

    if submitted:
        # Validation
        if not session_name or len(session_name.strip()) < 3:
            st.error("⚠️ Please provide a session name (at least 3 characters)")
            return
            
        if not user_request or len(user_request.strip()) < 10:
            st.error("⚠️ Please provide detailed requirements (at least 10 characters)")
            return
        
        # Check if at least one role is selected
        selected_roles_config = st.session_state.get("selected_roles", {})
        if not selected_roles_config:
            st.warning("⚠️ Please select at least one agent role for your council")
            return

        try:
            with st.spinner("Creating council session..."):
                # Build context with selected roles
                context = {
                    "selected_roles": selected_roles_config,
                    "session_description": session_name.strip()
                }

                # Create session via API
                api_client = get_api_client()
                response = api_client.create_session(
                    user_request=user_request.strip(),
                    name=session_name.strip(),
                    description=None,  # Not using separate description field anymore
                    user_context=context
                )

                session_id = response.get("session_id")
                
                if not session_id:
                    st.error("❌ Failed to create session: No session ID returned")
                    return

                st.success(f"✅ Council session created successfully!")
                st.info(f"**Session ID:** `{session_id}`")
                
                # Show selected roles summary
                st.markdown("**Selected Agents:**")
                for role_config in selected_roles_config.values():
                    st.write(f"• {role_config['name']}")

                # Store session ID and metadata in session state
                st.session_state.current_session_id = session_id
                st.session_state.session_name = session_name
                
                # Navigate directly to feedback panel (skip old agent selector)
                st.session_state.page = "feedback_panel"

                logger.info(
                    "ui_session_created",
                    session_id=session_id,
                    name=session_name,
                    agent_count=len(selected_roles_config)
                )

                # Wait a moment to show success message
                import time
                time.sleep(1)
                st.rerun()

        except Exception as e:
            st.error(f"❌ Failed to create session: {str(e)}")
            logger.error("ui_session_creation_failed", error=str(e))


def render_session_list():
    """
    Render list of existing sessions.

    Allows users to:
    - View recent sessions
    - Load an existing session
    - Delete sessions
    """
    st.markdown("<br><br>", unsafe_allow_html=True)
    render_slds_card("📋 Recent Sessions")

    try:
        api_client = get_api_client()
        response = api_client.list_sessions(limit=10)
        sessions = response.get("sessions", [])

        if not sessions:
            st.info("No sessions yet. Create your first council session above!")
            return

        for session in sessions:
            session_id = session.get('session_id', '')
            name = session.get('name', 'Untitled')
            status = session.get('status', 'unknown')
            
            with st.expander(f"{name} - {session_id[:8]}...", expanded=False):
                # Render status pill
                render_status_pill(status)
                st.write(f"**Status:** {status}")
                st.write(f"**Created:** {session.get('created_at', 'N/A')}")
                st.write(f"**Updated:** {session.get('updated_at', 'N/A')}")

                if session.get('description'):
                    st.write(f"**Description:** {session['description']}")

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("📂 Load", key=f"load_{session_id}"):
                        st.session_state.current_session_id = session_id
                        st.session_state.session_name = name
                        
                        # Determine which page to show based on status
                        if status in ["completed", "failed", "cancelled"]:
                            st.session_state.page = "final_output"
                        elif status == "awaiting_human":
                            st.session_state.page = "approval_panel"
                        elif status == "in_progress":
                            st.session_state.page = "feedback_panel"
                        else:
                            st.session_state.page = "agent_selector"
                        
                        st.rerun()

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{session_id}"):
                        try:
                            api_client.delete_session(session_id)
                            st.success("Session deleted")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to delete: {str(e)}")

    except Exception as e:
        st.error(f"Failed to load sessions: {str(e)}")
        logger.error("ui_session_list_failed", error=str(e))
    
    close_slds_card()

