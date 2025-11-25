"""
Final Output UI component for Agent Council system.

Displays final design document, FAQ, and deliverables.
"""

import streamlit as st

from app.state.session import get_session_manager
from app.utils.exceptions import AgentCouncilException
from app.utils.logging import get_logger

logger = get_logger(__name__)


def render_final_output(session_id: str):
    """
    Render final output and deliverables.

    Args:
        session_id: Session ID
    """
    st.header("🎉 Final Design & Deliverables")

    try:
        session_manager = get_session_manager()
        state = session_manager.get_session(session_id)

        # Status check
        if state.status.value != "completed":
            st.warning(f"⏳ Council session is still in progress (Status: {state.status.value})")
            st.info("Final deliverables will be available once the session is completed.")
            return

        # Final Design Document
        st.subheader("📄 Final Design Document")

        if state.final_design:
            design = state.final_design

            # Design header
            st.markdown(f"## {design.title}")
            st.write(f"**Version:** {design.version}")
            st.write(f"**Last Updated:** {design.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")

            st.divider()

            # Description
            st.markdown("### Description")
            st.write(design.description)

            # Architecture Overview
            st.divider()
            st.markdown("### Architecture Overview")
            st.write(design.architecture_overview)

            # Components
            if design.components:
                st.divider()
                st.markdown("### Components")
                for component in design.components:
                    with st.expander(f"📦 {component.get('name', 'Component')}"):
                        st.json(component)

            # NFR Considerations
            if design.nfr_considerations:
                st.divider()
                st.markdown("### Non-Functional Requirements")
                for nfr_type, nfr_detail in design.nfr_considerations.items():
                    st.write(f"**{nfr_type}:** {nfr_detail}")

            # Security Considerations
            if design.security_considerations:
                st.divider()
                st.markdown("### Security Considerations")
                for sec_type, sec_detail in design.security_considerations.items():
                    st.write(f"**{sec_type}:** {sec_detail}")

            # Integration Points
            if design.integration_points:
                st.divider()
                st.markdown("### Integration Points")
                for integration in design.integration_points:
                    with st.expander(f"🔗 {integration.get('name', 'Integration')}"):
                        st.json(integration)

            # Deployment Notes
            if design.deployment_notes:
                st.divider()
                st.markdown("### Deployment Notes")
                st.write(design.deployment_notes)

            # Diagrams
            if design.diagrams:
                st.divider()
                st.markdown("### Diagrams")
                for diagram_url in design.diagrams:
                    st.image(diagram_url, caption="Architecture Diagram")

        else:
            st.warning("Final design document not available")

        # FAQ Section
        st.divider()
        st.subheader("❓ Frequently Asked Questions")

        if state.faq_entries:
            for idx, faq in enumerate(state.faq_entries, 1):
                with st.expander(f"Q{idx}: {faq.get('question', 'Question')}"):
                    st.write(f"**A:** {faq.get('answer', 'Answer')}")
                    if faq.get('category'):
                        st.caption(f"Category: {faq['category']}")
        else:
            st.info("No FAQ entries generated")

        # Decision Rationale
        if state.decision_rationale:
            st.divider()
            st.subheader("📝 Decision Rationale")
            st.write(state.decision_rationale)

        # Export options
        st.divider()
        _render_export_options(state)

    except AgentCouncilException as e:
        st.error(f"Failed to load final output: {str(e)}")
        logger.error("ui_final_output_failed", error=str(e), session_id=session_id)


def _render_export_options(state):
    """
    Render export options for deliverables.

    Args:
        state: WorkflowState object

    TODO: Phase 2 - Implement export functionality
    """
    st.subheader("📥 Export Deliverables")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📄 Export as PDF"):
            st.info("PDF export coming in Phase 2")

    with col2:
        if st.button("📊 Export as Markdown"):
            st.info("Markdown export coming in Phase 2")

    with col3:
        if st.button("💾 Download JSON"):
            st.info("JSON export coming in Phase 2")


def render_session_summary(session_id: str):
    """
    Render session summary statistics.

    Args:
        session_id: Session ID
    """
    try:
        session_manager = get_session_manager()
        state = session_manager.get_session(session_id)

        st.subheader("📊 Session Summary")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Messages", len(state.messages))

        with col2:
            st.metric("Reviews", len(state.reviews))

        with col3:
            st.metric("Revisions", state.revision_count)

        with col4:
            duration = (state.updated_at - state.created_at).total_seconds()
            st.metric("Duration", f"{int(duration // 60)}m")

    except AgentCouncilException as e:
        logger.error("ui_session_summary_failed", error=str(e), session_id=session_id)

