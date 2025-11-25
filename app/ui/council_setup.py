"""
Council Setup UI component for Agent Council system.

Allows users to create new council sessions with name, description, and requirements.
"""

import streamlit as st

from app.state.session import get_session_manager
from app.utils.exceptions import AgentCouncilException
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
    st.header("🏛️ Create Agent Council Session")

    with st.form("council_setup_form"):
        # Session metadata
        st.subheader("Session Information")
        session_name = st.text_input(
            "Session Name",
            placeholder="e.g., Customer Portal Integration Design",
            help="Give your session a meaningful name"
        )

        session_description = st.text_area(
            "Description (Optional)",
            placeholder="Brief description of what you're trying to accomplish",
            height=100
        )

        # User requirements
        st.subheader("Requirements")
        user_request = st.text_area(
            "What do you need the Agent Council to help you design?",
            placeholder="Describe your requirements, challenges, or questions...",
            height=200,
            help="Provide as much detail as possible for better results"
        )

        # Context information
        st.subheader("Additional Context (Optional)")

        col1, col2 = st.columns(2)

        with col1:
            industry = st.text_input("Industry", placeholder="e.g., Healthcare, Finance")
            org_size = st.selectbox(
                "Organization Size",
                ["Small (< 100 users)", "Medium (100-1000 users)", "Large (> 1000 users)", "Enterprise"]
            )

        with col2:
            use_case = st.text_input("Use Case", placeholder="e.g., Customer Portal, Data Integration")
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])

        # Additional context
        additional_context = st.text_area(
            "Additional Context",
            placeholder="Any other relevant information (constraints, preferences, existing systems, etc.)",
            height=100
        )

        # Submit button
        submitted = st.form_submit_button("🚀 Start Council Session", type="primary")

        if submitted:
            # Validation
            if not user_request or len(user_request.strip()) < 10:
                st.error("⚠️ Please provide a detailed requirement (at least 10 characters)")
                return

            try:
                # Build context
                context = {
                    "industry": industry if industry else None,
                    "org_size": org_size,
                    "use_case": use_case if use_case else None,
                    "priority": priority,
                    "additional_context": additional_context if additional_context else None,
                }

                # Create session
                session_manager = get_session_manager()
                state = session_manager.create_session(
                    user_request=user_request.strip(),
                    name=session_name.strip() if session_name else None,
                    description=session_description.strip() if session_description else None,
                    user_context=context
                )

                st.success(f"✅ Council session created successfully!")
                st.info(f"**Session ID:** `{state.session_id}`")

                # Store session ID in session state
                st.session_state.current_session_id = state.session_id
                st.session_state.page = "agent_selector"

                logger.info("ui_session_created", session_id=state.session_id, name=session_name)

                st.rerun()

            except AgentCouncilException as e:
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
    st.subheader("📋 Recent Sessions")

    try:
        session_manager = get_session_manager()
        sessions = session_manager.list_sessions(limit=10)

        if not sessions:
            st.info("No sessions yet. Create your first council session above!")
            return

        for session in sessions:
            with st.expander(f"📁 {session.get('name', 'Untitled')} - {session['session_id'][:8]}..."):
                st.write(f"**Status:** {session['status']}")
                st.write(f"**Created:** {session['created_at']}")
                st.write(f"**Updated:** {session['updated_at']}")

                if session.get('description'):
                    st.write(f"**Description:** {session['description']}")

                col1, col2 = st.columns([1, 1])

                with col1:
                    if st.button("📂 Load", key=f"load_{session['session_id']}"):
                        st.session_state.current_session_id = session['session_id']
                        st.session_state.page = "agent_selector"
                        st.rerun()

                with col2:
                    if st.button("🗑️ Delete", key=f"delete_{session['session_id']}"):
                        session_manager.delete_session(session['session_id'])
                        st.success("Session deleted")
                        st.rerun()

    except AgentCouncilException as e:
        st.error(f"Failed to load sessions: {str(e)}")
        logger.error("ui_session_list_failed", error=str(e))

