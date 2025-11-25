"""
Feedback Panel UI component for Agent Council system.

Displays agent feedback and allows user interaction with review results.
"""

import streamlit as st
import time

from app.graph.state_models import ReviewDecision
from app.ui.api_client import get_api_client
from app.ui.styles import close_slds_card, render_slds_card, render_status_pill
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_feedback_panel(session_id: str):
    """
    Render feedback panel showing agent outputs and reviews.

    Args:
        session_id: Session ID to display feedback for
    """
    st.markdown("# 💬 Agent Feedback & Reviews")
    st.caption("Real-time updates from your Agent Council")
    
    st.markdown("<br>", unsafe_allow_html=True)

    # Add refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col2:
        if st.button("🔄 Refresh", key="refresh_feedback", use_container_width=True):
            st.rerun()
    with col3:
        auto_refresh = st.checkbox("Auto-refresh", value=False)

    try:
        api_client = get_api_client()
        
        # Get session data
        with st.spinner("Loading session data..."):
            session_data = api_client.get_session(session_id)
        
        status = session_data.get("status", "unknown")
        messages = session_data.get("messages", [])
        reviews = session_data.get("reviews", [])
        current_agent = session_data.get("current_agent")
        revision_count = session_data.get("revision_count", 0)
        max_revisions = session_data.get("max_revisions", 3)

        # Status indicator with SLDS pill
        render_slds_card()
        st.markdown("**Current Status:**")
        render_status_pill(status)
        st.markdown("<br>", unsafe_allow_html=True)
        
        if current_agent:
            st.write(f"📍 **Current Agent:** {current_agent.replace('_', ' ').title()}")
        
        close_slds_card()
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Display messages
        if messages:
            render_slds_card("📝 Agent Messages")

            for idx, message in enumerate(messages):
                agent_role = message.get("agent_role", "unknown")
                timestamp = message.get("timestamp", "")
                content = message.get("content", "")
                metadata = message.get("metadata", {})
                
                # Format timestamp
                if timestamp:
                    try:
                        from datetime import datetime
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        time_str = dt.strftime('%H:%M:%S')
                    except:
                        time_str = timestamp[:19]
                else:
                    time_str = "N/A"
                
                with st.expander(
                    f"{_get_agent_icon(agent_role)} {agent_role.replace('_', ' ').title()} - {time_str}",
                    expanded=(idx == len(messages) - 1)  # Expand latest message
                ):
                    # Try to parse JSON content
                    try:
                        import json
                        content_json = json.loads(content)
                        st.json(content_json)
                    except:
                        st.write(content)

                    if metadata:
                        with st.container():
                            st.caption("**Metadata:**")
                            st.json(metadata)
            
            close_slds_card()
        else:
            st.info("No agent messages yet. Workflow starting...")
            close_slds_card()
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Display reviews
        if reviews:
            render_slds_card("🔍 Review Feedback")

            for review in reviews:
                _render_review_card(review)
            
            close_slds_card()
        else:
            st.info("No reviews yet. Waiting for reviewers...")
            close_slds_card()
        
        st.markdown("<br>", unsafe_allow_html=True)

        # Display revision status
        if revision_count > 0:
            render_slds_card("🔄 Revision Status")
            progress = revision_count / max_revisions
            st.progress(progress)
            st.write(f"**Revisions:** {revision_count} / {max_revisions}")
            close_slds_card()

        # Auto-refresh logic
        if auto_refresh and status == "in_progress":
            time.sleep(2)
            st.rerun()
        
        # Navigation based on status
        st.divider()
        
        if status == "awaiting_human":
            st.info("🟠 **Workflow is waiting for human approval**")
            if st.button("📋 Go to Approval Panel", type="primary"):
                st.session_state.page = "approval_panel"
                st.rerun()
        elif status == "completed":
            st.success("✅ **Workflow completed successfully!**")
            if st.button("🎉 View Final Output", type="primary"):
                st.session_state.page = "final_output"
                st.rerun()
        elif status == "failed":
            errors = session_data.get("errors", [])
            st.error(f"❌ **Workflow failed:** {errors[-1] if errors else 'Unknown error'}")
        elif status == "in_progress":
            st.info("🟡 **Workflow is running...** Enable auto-refresh to see live updates")

    except Exception as e:
        st.error(f"Failed to load feedback: {str(e)}")
        logger.error("ui_feedback_load_failed", error=str(e), session_id=session_id)


def _render_review_card(review):
    """
    Render a single review card.

    Args:
        review: Review dict from API
    """
    decision_colors = {
        "approve": "🟢",
        "reject": "🔴",
        "revise": "🟡",
        "escalate": "🟠",
    }

    severity_colors = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }

    reviewer_role = review.get("reviewer_role", "unknown")
    decision = review.get("decision", "unknown")
    severity = review.get("severity", "medium")
    rationale = review.get("rationale", "No rationale provided")
    concerns = review.get("concerns", [])
    suggestions = review.get("suggestions", [])

    color = decision_colors.get(decision, "⚪")
    severity_icon = severity_colors.get(severity, "⚪")

    with st.container():
        st.markdown(f"### {color} {reviewer_role.replace('_', ' ').title()}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Decision:** {decision.upper()}")

        with col2:
            st.write(f"**Severity:** {severity_icon} {severity}")

        st.write(f"**Rationale:** {rationale}")

        if concerns:
            with st.expander("⚠️ Concerns"):
                for concern in concerns:
                    st.write(f"- {concern}")

        if suggestions:
            with st.expander("💡 Suggestions"):
                for suggestion in suggestions:
                    st.write(f"- {suggestion}")

        st.divider()




def _get_agent_icon(agent_role: str) -> str:
    """
    Get icon for agent role.

    Args:
        agent_role: Agent role string

    Returns:
        Icon emoji
    """
    icons = {
        "master": "🎯",
        "solution_architect": "🏗️",
        "reviewer_nfr": "⚡",
        "reviewer_security": "🔒",
        "reviewer_integration": "🔗",
        "reviewer_domain": "🎓",
        "reviewer_ops": "⚙️",
        "faq": "📚",
        "human": "👤",
    }
    return icons.get(agent_role, "🤖")

