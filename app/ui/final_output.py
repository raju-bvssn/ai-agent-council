"""
Final Output UI component for Agent Council system.

Displays final design document, FAQ, and deliverables.
"""

import streamlit as st
import json

from app.ui.api_client import get_api_client
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
        api_client = get_api_client()
        session_data = api_client.get_session(session_id)
        
        status = session_data.get("status", "unknown")
        
        # Status check
        if status != "completed":
            st.warning(f"⏳ Council session is still in progress (Status: {status.replace('_', ' ').title()})")
            st.info("Final deliverables will be available once the session is completed.")
            
            # Option to go back to feedback panel
            if st.button("← Back to Feedback Panel"):
                st.session_state.page = "feedback_panel"
                st.rerun()
            return

        # Final Design Document
        st.subheader("📄 Final Design Document")

        current_design = session_data.get("current_design")
        
        if current_design:
            # Design header
            st.markdown(f"## {current_design.get('title', 'Solution Design')}")
            st.write(f"**Version:** {current_design.get('version', '1.0')}")

            st.divider()

            # Description
            if current_design.get("description"):
                st.markdown("### Description")
                st.write(current_design["description"])

            # Architecture Overview
            if current_design.get("architecture_overview"):
                st.divider()
                st.markdown("### Architecture Overview")
                st.write(current_design["architecture_overview"])

            # Components
            if current_design.get("components"):
                st.divider()
                st.markdown("### Components")
                for component in current_design["components"]:
                    component_name = component.get('name', 'Component')
                    with st.expander(f"📦 {component_name}"):
                        st.json(component)

            # NFR Considerations
            if current_design.get("nfr_considerations"):
                st.divider()
                st.markdown("### Non-Functional Requirements")
                st.json(current_design["nfr_considerations"])

            # Security Considerations
            if current_design.get("security_considerations"):
                st.divider()
                st.markdown("### Security Considerations")
                st.json(current_design["security_considerations"])

            # Integration Points
            if current_design.get("integration_points"):
                st.divider()
                st.markdown("### Integration Points")
                for integration in current_design["integration_points"]:
                    integration_name = integration.get('name', 'Integration')
                    with st.expander(f"🔗 {integration_name}"):
                        st.json(integration)

            # Deployment Notes
            if current_design.get("deployment_notes"):
                st.divider()
                st.markdown("### Deployment Notes")
                st.write(current_design["deployment_notes"])

            # Diagrams
            if current_design.get("diagrams"):
                st.divider()
                st.markdown("### Diagrams")
                for diagram_url in current_design["diagrams"]:
                    st.image(diagram_url, caption="Architecture Diagram")

        else:
            st.warning("Final design document not available")

        # FAQ Section
        st.divider()
        st.subheader("❓ Frequently Asked Questions")

        faq_entries = session_data.get("faq_entries", [])
        if faq_entries:
            for idx, faq in enumerate(faq_entries, 1):
                with st.expander(f"Q{idx}: {faq.get('question', 'Question')}"):
                    st.write(f"**A:** {faq.get('answer', 'Answer')}")
                    if faq.get('category'):
                        st.caption(f"Category: {faq['category']}")
        else:
            st.info("No FAQ entries generated")

        # Decision Rationale
        decision_rationale = session_data.get("decision_rationale")
        if decision_rationale:
            st.divider()
            st.subheader("📝 Decision Rationale")
            st.write(decision_rationale)

        # Session Summary
        st.divider()
        _render_session_summary(session_data)

        # Export options
        st.divider()
        _render_export_options(session_data)
        
        # Navigation
        st.divider()
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🏠 New Session"):
                st.session_state.current_session_id = None
                st.session_state.page = "council_setup"
                st.rerun()
        with col2:
            if st.button("📋 View All Sessions"):
                st.session_state.page = "council_setup"
                st.rerun()

    except Exception as e:
        st.error(f"Failed to load final output: {str(e)}")
        logger.error("ui_final_output_failed", error=str(e), session_id=session_id)


def _render_export_options(session_data: dict):
    """
    Render export options for deliverables.

    Args:
        session_data: Session data dict

    TODO: Phase 2C - Implement export functionality
    """
    st.subheader("📥 Export Deliverables")

    col1, col2, col3 = st.columns(3)

    with col1:
        # JSON export (functional)
        if st.button("💾 Download JSON", use_container_width=True):
            json_str = json.dumps(session_data, indent=2)
            st.download_button(
                label="⬇️ Download JSON",
                data=json_str,
                file_name=f"council_session_{session_data.get('session_id', 'unknown')}.json",
                mime="application/json"
            )

    with col2:
        if st.button("📊 Export as Markdown", use_container_width=True):
            st.info("Markdown export coming in Phase 2C")

    with col3:
        if st.button("📄 Export as PDF", use_container_width=True):
            st.info("PDF export coming in Phase 2C")


def _render_session_summary(session_data: dict):
    """
    Render session summary statistics.

    Args:
        session_data: Session data dict
    """
    st.subheader("📊 Session Summary")

    col1, col2, col3, col4 = st.columns(4)

    messages = session_data.get("messages", [])
    reviews = session_data.get("reviews", [])
    revision_count = session_data.get("revision_count", 0)
    created_at = session_data.get("created_at", "")
    updated_at = session_data.get("updated_at", "")

    with col1:
        st.metric("Messages", len(messages))

    with col2:
        st.metric("Reviews", len(reviews))

    with col3:
        st.metric("Revisions", revision_count)

    with col4:
        # Calculate duration if timestamps available
        if created_at and updated_at:
            try:
                from datetime import datetime
                created = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                updated = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                duration = (updated - created).total_seconds()
                st.metric("Duration", f"{int(duration // 60)}m")
            except:
                st.metric("Duration", "N/A")
        else:
            st.metric("Duration", "N/A")

