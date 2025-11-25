"""
Approval Panel UI component for Agent Council system.

Human-in-the-loop interface for approving or rejecting designs.
"""

import streamlit as st

from app.state.session import get_session_manager
from app.utils.exceptions import AgentCouncilException
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_approval_panel(session_id: str):
    """
    Render human approval interface.

    Args:
        session_id: Session ID
    """
    st.header("✋ Human Approval Required")

    try:
        session_manager = get_session_manager()
        state = session_manager.get_session(session_id)

        # Display current design summary
        st.subheader("📋 Design Summary")

        if state.current_design:
            st.write(f"**Version:** {state.current_design.version}")
            st.write(f"**Title:** {state.current_design.title}")
            st.write(f"**Description:** {state.current_design.description}")

            with st.expander("View Full Design"):
                st.write("**Architecture Overview:**")
                st.write(state.current_design.architecture_overview)

                if state.current_design.components:
                    st.write("**Components:**")
                    for component in state.current_design.components:
                        st.json(component)
        else:
            st.info("Design document not yet generated")

        # Display review summary
        st.divider()
        st.subheader("🔍 Review Summary")

        if state.reviews:
            approval_count = sum(1 for r in state.reviews if r.decision.value == "approve")
            revision_count = sum(1 for r in state.reviews if r.decision.value == "revise")
            reject_count = sum(1 for r in state.reviews if r.decision.value == "reject")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Approvals", approval_count)
            with col2:
                st.metric("🔄 Revisions Requested", revision_count)
            with col3:
                st.metric("❌ Rejections", reject_count)

            # Show individual reviews
            with st.expander("View All Reviews"):
                for review in state.reviews:
                    st.write(f"**{review.reviewer_role.value}:** {review.decision.value}")
                    st.write(f"  Rationale: {review.rationale}")
                    st.divider()
        else:
            st.warning("No reviews available yet")

        # Approval decision
        st.divider()
        st.subheader("🎯 Your Decision")

        decision = st.radio(
            "What would you like to do?",
            ["Approve", "Request Revision", "Reject"],
            help="Approve to proceed, request revision for improvements, or reject to cancel"
        )

        feedback = st.text_area(
            "Your Feedback",
            placeholder="Provide any comments, concerns, or instructions...",
            height=150
        )

        if st.button(f"✓ Confirm {decision}", type="primary"):
            # TODO: Phase 2 - Implement approval workflow
            if decision == "Approve":
                st.success("✅ Design approved! Proceeding to FAQ generation...")
                state.human_approved = True
                state.human_feedback = feedback
            elif decision == "Request Revision":
                st.warning("🔄 Revision requested. Agents will update the design...")
                state.human_feedback = feedback
            else:
                st.error("❌ Design rejected. Session cancelled.")

            # Update state
            session_manager.update_session(state)

            logger.info("ui_human_decision", session_id=session_id, decision=decision)
            st.rerun()

    except AgentCouncilException as e:
        st.error(f"Failed to load approval panel: {str(e)}")
        logger.error("ui_approval_panel_failed", error=str(e), session_id=session_id)


def render_approval_history(session_id: str):
    """
    Render approval history for the session.

    Args:
        session_id: Session ID

    TODO: Phase 2 - Implement approval history tracking
    """
    st.subheader("📜 Approval History")
    st.info("Approval history tracking coming in Phase 2")

