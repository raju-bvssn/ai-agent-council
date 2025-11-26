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
        
        # Phase 3B: Final Architecture Rationale (from Adjudicator)
        final_architecture_rationale = session_data.get("final_architecture_rationale")
        if final_architecture_rationale:
            st.divider()
            st.subheader("⚖️ Architect Adjudicator's Final Rationale")
            st.info("This section contains the Architect Adjudicator's final decisions and comprehensive rationale for resolving any conflicts.")
            
            try:
                # Try to parse as JSON for structured display
                rationale_json = json.loads(final_architecture_rationale)
                
                # Display final decisions
                if rationale_json.get("final_decisions"):
                    st.markdown("### Final Decisions")
                    for decision in rationale_json["final_decisions"]:
                        with st.expander(f"🎯 {decision.get('disagreement_topic', 'Decision')}"):
                            st.markdown(f"**Decision:** {decision.get('decision', 'N/A')}")
                            st.markdown(f"**Rationale:** {decision.get('rationale', 'N/A')}")
                
                # Display architecture rationale
                if rationale_json.get("architecture_rationale"):
                    st.markdown("### Overall Architecture Rationale")
                    st.write(rationale_json["architecture_rationale"])
                
                # Display design updates
                if rationale_json.get("design_updates"):
                    st.markdown("### Required Design Updates")
                    for update in rationale_json["design_updates"]:
                        st.markdown(f"- {update}")
            
            except json.JSONDecodeError:
                # If not JSON, display as plain text
                st.write(final_architecture_rationale)

        # Phase 3C: Architecture Deliverables Bundle
        st.divider()
        _render_deliverables_bundle(session_id, session_data)

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


def _render_deliverables_bundle(session_id: str, session_data: dict):
    """
    Render Phase 3C deliverables bundle.
    
    Displays architecture summary, decision records, risks, FAQs, and diagrams
    from the comprehensive deliverables bundle.
    
    Args:
        session_id: Session ID
        session_data: Session data dict
    """
    st.subheader("📄 Final Architecture Deliverables")
    
    # Check if deliverables are available
    deliverables = session_data.get("deliverables")
    
    if not deliverables:
        st.info("⏳ Deliverables are being generated... They will appear once the workflow completes.")
        return
    
    # Tab layout for deliverables sections
    tabs = st.tabs([
        "📋 Summary",
        "🎯 Decisions",
        "⚠️ Risks",
        "❓ FAQ",
        "📊 Diagrams",
        "📄 Full Report"
    ])
    
    # Tab 1: Architecture Summary
    with tabs[0]:
        arch_summary = deliverables.get("architecture_summary", {})
        
        st.markdown("### Architecture Overview")
        st.write(arch_summary.get("overview", "No overview available"))
        
        st.markdown("### Key Capabilities")
        capabilities = arch_summary.get("key_capabilities", [])
        if capabilities:
            for cap in capabilities:
                st.markdown(f"- ✅ {cap}")
        else:
            st.info("No key capabilities documented")
        
        st.markdown("### Non-Functional Highlights")
        nfr_highlights = arch_summary.get("non_functional_highlights", [])
        if nfr_highlights:
            for nfr in nfr_highlights:
                st.markdown(f"- 🎯 {nfr}")
        else:
            st.info("No NFR highlights documented")
    
    # Tab 2: Key Design Decisions (ADR-style)
    with tabs[1]:
        st.markdown("### Architecture Decision Records")
        decisions = deliverables.get("decisions", [])
        
        if decisions:
            for decision in decisions:
                with st.expander(f"**{decision.get('id')}**: {decision.get('title')}", expanded=False):
                    st.markdown("**Context:**")
                    st.write(decision.get("context", "N/A"))
                    
                    st.markdown("**Decision:**")
                    st.info(decision.get("decision", "N/A"))
                    
                    st.markdown("**Rationale:**")
                    st.write(decision.get("rationale", "N/A"))
                    
                    st.markdown("**Consequences:**")
                    st.write(decision.get("consequences", "N/A"))
        else:
            st.info("No decision records available")
    
    # Tab 3: Risks & Mitigations
    with tabs[2]:
        st.markdown("### Technical Risks & Mitigation Strategies")
        risks = deliverables.get("risks", [])
        
        if risks:
            # Create a table for risks
            risk_data = []
            for risk in risks:
                risk_data.append({
                    "ID": risk.get("id", "N/A"),
                    "Description": risk.get("description", "N/A")[:60] + "...",
                    "Impact": risk.get("impact", "N/A").upper(),
                    "Likelihood": risk.get("likelihood", "N/A").upper(),
                })
            
            # Display table
            st.table(risk_data)
            
            # Display detailed view
            st.markdown("#### Detailed Mitigation Plans")
            for risk in risks:
                with st.expander(f"{risk.get('id')}: {risk.get('description', 'Risk')[:50]}..."):
                    col1, col2 = st.columns(2)
                    with col1:
                        impact_color = {
                            "low": "🟢",
                            "medium": "🟡",
                            "high": "🟠",
                            "critical": "🔴"
                        }.get(risk.get("impact", "").lower(), "⚪")
                        st.metric("Impact", f"{impact_color} {risk.get('impact', 'N/A').title()}")
                    with col2:
                        likelihood_color = {
                            "low": "🟢",
                            "medium": "🟡",
                            "high": "🔴"
                        }.get(risk.get("likelihood", "").lower(), "⚪")
                        st.metric("Likelihood", f"{likelihood_color} {risk.get('likelihood', 'N/A').title()}")
                    
                    st.markdown("**Full Description:**")
                    st.write(risk.get("description", "N/A"))
                    
                    st.markdown("**Mitigation Strategy:**")
                    st.success(risk.get("mitigation", "N/A"))
                    
                    if risk.get("owner"):
                        st.caption(f"Owner: {risk['owner']}")
        else:
            st.info("No risks documented")
    
    # Tab 4: FAQ
    with tabs[3]:
        st.markdown("### Frequently Asked Questions for Architecture Review")
        faqs = deliverables.get("faqs", [])
        
        if faqs:
            for idx, faq in enumerate(faqs, 1):
                with st.expander(f"**Q{idx}:** {faq.get('question', 'Question')}"):
                    st.write(faq.get("answer", "N/A"))
                    if faq.get("source"):
                        st.caption(f"Source: {faq['source']}")
        else:
            st.info("No FAQ entries available")
    
    # Tab 5: Diagrams
    with tabs[4]:
        st.markdown("### Architecture Diagrams")
        diagrams = deliverables.get("diagrams", [])
        
        if diagrams:
            for diagram in diagrams:
                st.markdown(f"#### {diagram.get('title', 'Diagram')}")
                st.caption(f"Type: {diagram.get('diagram_type', 'unknown')}")
                st.write(diagram.get("description", ""))
                
                # Show Lucid link if available
                if diagram.get("lucid_url"):
                    st.markdown(f"[🔗 Open in Lucid]({diagram['lucid_url']})")
                
                # Show Mermaid source if available
                elif diagram.get("mermaid_source"):
                    st.markdown("**Diagram Source (Mermaid):**")
                    st.code(diagram.get("mermaid_source"), language="mermaid")
                    st.caption("💡 Copy this code to visualize in Mermaid Live Editor or documentation")
                else:
                    st.info("Diagram source not available")
                
                st.divider()
        else:
            st.info("No diagrams available")
    
    # Tab 6: Full Markdown Report
    with tabs[5]:
        st.markdown("### Complete Markdown Report")
        markdown_report = deliverables.get("markdown_report", "")
        
        if markdown_report:
            # Display report in code block
            st.code(markdown_report, language="markdown")
            
            # Download button
            st.download_button(
                label="📥 Download Markdown Report",
                data=markdown_report,
                file_name=f"architecture_deliverables_{session_id}.md",
                mime="text/markdown",
                use_container_width=True
            )
        else:
            st.warning("Markdown report not generated")


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

