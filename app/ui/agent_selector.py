"""
Agent Selector UI component for Agent Council system.

Allows users to select and configure agents for the council.
"""

import streamlit as st
import time

from app.graph.state_models import AgentRole
from app.ui.api_client import get_api_client
from app.utils.logging import get_logger

logger = get_logger(__name__)


# Agent information for UI
AGENT_INFO = {
    AgentRole.MASTER: {
        "name": "Master Architect",
        "icon": "🎯",
        "description": "Coordinates the council and synthesizes final recommendations",
        "required": True,
    },
    AgentRole.SOLUTION_ARCHITECT: {
        "name": "Solution Architect",
        "icon": "🏗️",
        "description": "Creates and evolves the solution design document",
        "required": True,
    },
    AgentRole.REVIEWER_NFR: {
        "name": "NFR & Performance Reviewer",
        "icon": "⚡",
        "description": "Reviews non-functional requirements, performance, and scalability",
        "required": False,
    },
    AgentRole.REVIEWER_SECURITY: {
        "name": "Security Reviewer",
        "icon": "🔒",
        "description": "Reviews security architecture and compliance requirements",
        "required": False,
    },
    AgentRole.REVIEWER_INTEGRATION: {
        "name": "Integration Reviewer",
        "icon": "🔗",
        "description": "Reviews integration patterns and API design",
        "required": False,
    },
    AgentRole.FAQ: {
        "name": "FAQ Generator",
        "icon": "📚",
        "description": "Generates FAQ and decision rationale documentation",
        "required": False,
    },
}


def render_agent_selector():
    """
    Render agent selection interface.

    Allows users to:
    - View available agents
    - Select/deselect agents
    - View agent descriptions
    - Configure agent parameters
    """
    st.header("🤖 Configure Agent Council")

    # Check if we have a session
    if "current_session_id" not in st.session_state:
        st.warning("⚠️ No active session. Please create a session first.")
        if st.button("← Back to Setup"):
            st.session_state.page = "council_setup"
            st.rerun()
        return

    session_id = st.session_state.current_session_id
    st.info(f"**Session ID:** `{session_id[:16]}...`")

    st.subheader("Select Agents")
    st.write("Choose which specialized agents should participate in this council:")

    # Initialize selected agents in session state
    if "selected_agents" not in st.session_state:
        st.session_state.selected_agents = [
            AgentRole.MASTER,
            AgentRole.SOLUTION_ARCHITECT,
            AgentRole.REVIEWER_NFR,
            AgentRole.REVIEWER_SECURITY,
            AgentRole.REVIEWER_INTEGRATION,
            AgentRole.FAQ,
        ]

    # Render agent selection
    cols = st.columns(2)

    for idx, (role, info) in enumerate(AGENT_INFO.items()):
        with cols[idx % 2]:
            with st.container():
                st.markdown(f"### {info['icon']} {info['name']}")
                st.write(info['description'])

                if info['required']:
                    st.success("✓ Required")
                    # Ensure required agents are always selected
                    if role not in st.session_state.selected_agents:
                        st.session_state.selected_agents.append(role)
                else:
                    is_selected = role in st.session_state.selected_agents
                    selected = st.checkbox(
                        "Include in Council",
                        value=is_selected,
                        key=f"agent_{role.value}"
                    )

                    if selected and role not in st.session_state.selected_agents:
                        st.session_state.selected_agents.append(role)
                    elif not selected and role in st.session_state.selected_agents:
                        st.session_state.selected_agents.remove(role)

                st.divider()

    # Summary
    st.subheader("📊 Council Summary")
    st.write(f"**Selected Agents:** {len(st.session_state.selected_agents)}")

    agent_names = [AGENT_INFO[role]['name'] for role in st.session_state.selected_agents]
    st.write(", ".join(agent_names))

    # Action buttons
    st.divider()
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("← Back to Setup"):
            st.session_state.page = "council_setup"
            st.rerun()

    with col2:
        if st.button("🔄 Reset to Defaults"):
            st.session_state.selected_agents = [
                AgentRole.MASTER,
                AgentRole.SOLUTION_ARCHITECT,
                AgentRole.REVIEWER_NFR,
                AgentRole.REVIEWER_SECURITY,
                AgentRole.REVIEWER_INTEGRATION,
                AgentRole.FAQ,
            ]
            st.rerun()

    with col3:
        if st.button("▶️ Start Council", type="primary"):
            try:
                with st.spinner("🚀 Starting workflow execution..."):
                    api_client = get_api_client()
                    
                    # Execute workflow
                    response = api_client.execute_workflow(
                        session_id=session_id,
                        stream=False
                    )
                    
                    logger.info(
                        "ui_workflow_started",
                        session_id=session_id,
                        agent_count=len(st.session_state.selected_agents)
                    )
                    
                    # Check if workflow started successfully
                    if response.get("status") in ["in_progress", "completed"]:
                        st.success("✅ Workflow started successfully!")
                        st.session_state.page = "feedback_panel"
                        time.sleep(1)  # Brief pause to show success message
                        st.rerun()
                    else:
                        error = response.get("error", "Unknown error")
                        st.error(f"❌ Workflow execution failed: {error}")
                        
            except Exception as e:
                st.error(f"❌ Failed to start workflow: {str(e)}")
                logger.error("ui_workflow_start_failed", error=str(e), session_id=session_id)


def render_suggested_agents():
    """
    Render AI-suggested agents based on requirements.

    TODO: Phase 2 - Implement AI-based agent suggestion
    """
    st.info("💡 **AI Suggestions** - Coming in Phase 2: Based on your requirements, the system will suggest optimal agents.")

