"""
Role configuration panel component.

Provides detailed configuration interface for agent roles including
responsibilities and allowed tools.
"""

import streamlit as st
from typing import Dict, Any

from app.agents.suggestion_engine import get_all_available_tools


def render_role_config_panel(role_key: str, role_config: Dict[str, Any]):
    """
    Render configuration panel for a specific role.
    
    Args:
        role_key: Unique identifier for the role
        role_config: Current configuration dictionary
        
    Returns:
        Updated configuration dictionary
    """
    st.markdown("### ⚙️ Configure Role")
    
    # Role name (read-only)
    st.text_input(
        "Role Name",
        value=role_config["name"],
        disabled=True,
        key=f"name_display_{role_key}"
    )
    
    # Responsibilities
    responsibilities = st.text_area(
        "Responsibilities",
        value=role_config.get("responsibilities", ""),
        height=120,
        key=f"responsibilities_panel_{role_key}",
        help="Define what this agent is responsible for in the council"
    )
    
    # Allowed tools
    st.markdown("**Allowed Tools**")
    st.caption("Select which tools this agent can use")
    
    all_tools = get_all_available_tools()
    selected_tools = []
    
    # Display tools in a grid
    cols = st.columns(3)
    for idx, tool in enumerate(all_tools):
        with cols[idx % 3]:
            is_selected = st.checkbox(
                tool,
                value=tool in role_config.get("tools", []),
                key=f"tool_panel_{tool}_{role_key}"
            )
            if is_selected:
                selected_tools.append(tool)
    
    # Custom tool
    custom_tool = st.text_input(
        "Custom Tool (Optional)",
        value=role_config.get("custom_tool", ""),
        key=f"custom_tool_panel_{role_key}",
        placeholder="Enter custom tool name",
        help="Add a custom tool not in the standard list"
    )
    
    # Return updated config
    updated_config = role_config.copy()
    updated_config["responsibilities"] = responsibilities
    updated_config["tools"] = selected_tools
    updated_config["custom_tool"] = custom_tool
    
    return updated_config

