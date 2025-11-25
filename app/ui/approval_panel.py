"""
Approval Panel UI component for Agent Council system.

Human-in-the-loop interface for approving or rejecting designs.
"""

import streamlit as st

from app.ui.api_client import get_api_client
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
        api_client = get_api_client()
        session_data = api_client.get_session(session_id)
        
        status = session_data.get("status", "unknown")
        current_design = session_data.get("current_design")
        reviews = session_data.get("reviews", [])

        # Display current design summary
        st.subheader("📋 Design Summary")

        if current_design:
            st.write(f"**Version:** {current_design.get('version', '1.0')}")
            st.write(f"**Title:** {current_design.get('title', 'Untitled')}")
            st.write(f"**Description:** {current_design.get('description', 'No description')}")

            with st.expander("View Full Design"):
                st.json(current_design)
        else:
            st.info("Design document not yet generated")

        # Display review summary
        st.divider()
        st.subheader("🔍 Review Summary")

        if reviews:
            approval_count = sum(1 for r in reviews if r.get("decision") == "approve")
            revision_count = sum(1 for r in reviews if r.get("decision") == "revise")
            reject_count = sum(1 for r in reviews if r.get("decision") == "reject")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("✅ Approvals", approval_count)
            with col2:
                st.metric("🔄 Revisions Requested", revision_count)
            with col3:
                st.metric("❌ Rejections", reject_count)

            # Show individual reviews
            with st.expander("View All Reviews"):
                for review in reviews:
                    reviewer_role = review.get("reviewer_role", "unknown")
                    decision = review.get("decision", "unknown")
                    rationale = review.get("rationale", "No rationale")
                    st.write(f"**{reviewer_role.replace('_', ' ').title()}:** {decision}")
                    st.write(f"  Rationale: {rationale}")
                    
                    if review.get("concerns"):
                        st.write("  Concerns:")
                        for concern in review["concerns"]:
                            st.write(f"    - {concern}")
                    
                    if review.get("suggestions"):
                        st.write("  Suggestions:")
                        for suggestion in review["suggestions"]:
                            st.write(f"    - {suggestion}")
                    
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
            with st.spinner(f"Processing {decision.lower()}..."):
                try:
                    if decision == "Approve":
                        result = api_client.approve_design(session_id, feedback)
                        st.success("✅ Design approved! Proceeding to FAQ generation...")
                        logger.info("ui_human_approved", session_id=session_id)
                        # Navigate to feedback panel to see FAQ generation
                        st.session_state.page = "feedback_panel"
                        
                    elif decision == "Request Revision":
                        result = api_client.request_revision(session_id, feedback)
                        st.warning("🔄 Revision requested. Agents will update the design...")
                        logger.info("ui_revision_requested", session_id=session_id)
                        # Navigate to feedback panel to see revision
                        st.session_state.page = "feedback_panel"
                        
                    else:  # Reject
                        # TODO: Implement reject endpoint
                        st.error("❌ Design rejected. Session cancelled.")
                        logger.info("ui_design_rejected", session_id=session_id)
                        # Navigate back to home
                        st.session_state.page = "council_setup"
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"Failed to process decision: {str(e)}")
                    logger.error("ui_approval_decision_failed", error=str(e), session_id=session_id)

    except Exception as e:
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

