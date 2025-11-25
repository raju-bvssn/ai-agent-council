"""
Feedback Panel UI component for Agent Council system.

Displays agent feedback and allows user interaction with review results.
"""

import streamlit as st

from app.graph.state_models import ReviewDecision
from app.state.session import get_session_manager
from app.utils.exceptions import AgentCouncilException
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_feedback_panel(session_id: str):
    """
    Render feedback panel showing agent outputs and reviews.

    Args:
        session_id: Session ID to display feedback for
    """
    st.header("💬 Agent Feedback & Reviews")

    try:
        session_manager = get_session_manager()
        state = session_manager.get_session(session_id)

        # Display messages
        if state.messages:
            st.subheader("📝 Agent Messages")

            for message in state.messages:
                with st.expander(
                    f"{_get_agent_icon(message.agent_role)} {message.agent_role.value.replace('_', ' ').title()} - "
                    f"{message.timestamp.strftime('%H:%M:%S')}"
                ):
                    st.write(message.content)

                    if message.metadata:
                        with st.container():
                            st.caption("**Metadata:**")
                            st.json(message.metadata)
        else:
            st.info("No agent messages yet. Workflow execution pending.")

        # Display reviews
        if state.reviews:
            st.divider()
            st.subheader("🔍 Review Feedback")

            for review in state.reviews:
                _render_review_card(review)
        else:
            st.info("No reviews yet. Agents are still working...")

        # Display revision status
        if state.revision_count > 0:
            st.divider()
            st.subheader("🔄 Revision Status")
            progress = state.revision_count / state.max_revisions
            st.progress(progress)
            st.write(f"**Revisions:** {state.revision_count} / {state.max_revisions}")

        # Action buttons
        st.divider()
        _render_action_buttons(state)

    except AgentCouncilException as e:
        st.error(f"Failed to load feedback: {str(e)}")
        logger.error("ui_feedback_load_failed", error=str(e), session_id=session_id)


def _render_review_card(review):
    """
    Render a single review card.

    Args:
        review: ReviewFeedback object
    """
    decision_colors = {
        ReviewDecision.APPROVE: "🟢",
        ReviewDecision.REJECT: "🔴",
        ReviewDecision.REVISE: "🟡",
        ReviewDecision.ESCALATE: "🟠",
    }

    severity_colors = {
        "low": "🟢",
        "medium": "🟡",
        "high": "🟠",
        "critical": "🔴",
    }

    color = decision_colors.get(review.decision, "⚪")
    severity = severity_colors.get(review.severity, "⚪")

    with st.container():
        st.markdown(f"### {color} {review.reviewer_role.value.replace('_', ' ').title()}")

        col1, col2 = st.columns([3, 1])

        with col1:
            st.write(f"**Decision:** {review.decision.value.upper()}")

        with col2:
            st.write(f"**Severity:** {severity} {review.severity}")

        st.write(f"**Rationale:** {review.rationale}")

        if review.concerns:
            with st.expander("⚠️ Concerns"):
                for concern in review.concerns:
                    st.write(f"- {concern}")

        if review.suggestions:
            with st.expander("💡 Suggestions"):
                for suggestion in review.suggestions:
                    st.write(f"- {suggestion}")

        st.divider()


def _render_action_buttons(state):
    """
    Render action buttons for user interaction.

    Args:
        state: WorkflowState object
    """
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("✅ Approve Design", type="primary", disabled=state.status.value != "awaiting_human"):
            st.success("Design approved! Proceeding to finalization...")
            # TODO: Phase 2 - Implement approval workflow
            logger.info("ui_design_approved", session_id=state.session_id)

    with col2:
        if st.button("🔄 Request Revision", disabled=not state.can_proceed()):
            st.warning("Requesting revision from agents...")
            # TODO: Phase 2 - Implement revision request
            logger.info("ui_revision_requested", session_id=state.session_id)

    with col3:
        if st.button("❌ Reject Design", disabled=state.status.value != "awaiting_human"):
            st.error("Design rejected. Please provide feedback.")
            # TODO: Phase 2 - Implement rejection workflow
            logger.info("ui_design_rejected", session_id=state.session_id)

    # Feedback text area
    if state.status.value == "awaiting_human":
        st.text_area(
            "💬 Your Feedback (Optional)",
            placeholder="Provide additional guidance for the council...",
            key="human_feedback"
        )


def _get_agent_icon(agent_role) -> str:
    """
    Get icon for agent role.

    Args:
        agent_role: AgentRole enum

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
    return icons.get(agent_role.value, "🤖")

