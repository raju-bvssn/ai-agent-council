"""
Council Setup UI component for Agent Council system.

Allows users to create new council sessions with name, description, and requirements.
"""

import streamlit as st

from app.ui.api_client import get_api_client
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
                with st.spinner("Creating council session..."):
                    # Build context
                    context = {
                        "industry": industry if industry else None,
                        "org_size": org_size,
                        "use_case": use_case if use_case else None,
                        "priority": priority,
                        "additional_context": additional_context if additional_context else None,
                    }

                    # Create session via API
                    api_client = get_api_client()
                    response = api_client.create_session(
                        user_request=user_request.strip(),
                        name=session_name.strip() if session_name else None,
                        description=session_description.strip() if session_description else None,
                        user_context=context
                    )

                    session_id = response.get("session_id")
                    
                    if not session_id:
                        st.error("❌ Failed to create session: No session ID returned")
                        return

                    st.success(f"✅ Council session created successfully!")
                    st.info(f"**Session ID:** `{session_id}`")

                    # Store session ID and metadata in session state
                    st.session_state.current_session_id = session_id
                    st.session_state.session_name = session_name
                    st.session_state.session_context = context
                    st.session_state.page = "agent_selector"

                    logger.info("ui_session_created", session_id=session_id, name=session_name)

                    st.rerun()

            except Exception as e:
                st.error(f"❌ Failed to create session: {str(e)}")
                logger.error("ui_session_creation_failed", error=str(e))
    
    close_slds_card()


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

