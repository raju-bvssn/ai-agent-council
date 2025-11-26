"""
Deliverables generation module.

Transforms completed workflow state into concrete architecture deliverables
for customer presentation.
"""

from app.graph.deliverables.service import (
    build_architecture_summary,
    build_decision_records,
    build_risks_and_mitigations,
    build_faq_items,
    build_diagram_descriptors,
    assemble_markdown_report,
    build_deliverables_bundle,
)

__all__ = [
    "build_architecture_summary",
    "build_decision_records",
    "build_risks_and_mitigations",
    "build_faq_items",
    "build_diagram_descriptors",
    "assemble_markdown_report",
    "build_deliverables_bundle",
]

