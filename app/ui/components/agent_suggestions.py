"""
Agent suggestions UI component.

Displays AI-suggested agent roles with selection checkboxes,
info tooltips, and expandable configuration panels.
"""

import streamlit as st
from typing import List

from app.agents.suggestion_engine import SuggestedRole, get_all_available_tools
from app.ui.styles import close_slds_card, render_slds_card


def render_agent_suggestions(suggested_roles: List[SuggestedRole]):
    """
    Render suggested agent roles with selection interface.
    
    Args:
        suggested_roles: List of suggested roles from suggestion engine
    """
    st.markdown("<br>", unsafe_allow_html=True)
    render_slds_card("🤖 Suggested Agent Roles")
    
    st.caption("Select agents to include in your council. Click a selected agent to configure.")
    
    # Initialize session state for selected roles
    if "selected_roles" not in st.session_state:
        st.session_state.selected_roles = {}
    
    if "expanded_role" not in st.session_state:
        st.session_state.expanded_role = None
    
    # Display each suggested role
    for idx, role in enumerate(suggested_roles):
        role_key = f"role_{role.name.replace(' ', '_')}"
        
        # Create a container for each role
        col1, col2 = st.columns([0.05, 0.95])
        
        with col1:
            # Checkbox for selection
            is_selected = st.checkbox(
                "",
                value=role_key in st.session_state.selected_roles,
                key=f"checkbox_{role_key}_{idx}",
                label_visibility="collapsed"
            )
        
        with col2:
            # Role name with info icon and tooltip
            role_header = f"""
            <div style="display: flex; align-items: center; margin-bottom: 0.5rem;">
                <span style="font-weight: 600; color: #032D60; font-size: 1rem;">{role.name}</span>
                <span style="margin-left: 0.5rem; color: #706E6B; cursor: help;" title="{role.description}">ⓘ</span>
            </div>
            <div style="font-size: 0.875rem; color: #54698D; margin-bottom: 0.5rem;">
                {role.description}
            </div>
            """
            st.markdown(role_header, unsafe_allow_html=True)
            
            # Update selected roles in session state
            if is_selected:
                if role_key not in st.session_state.selected_roles:
                    # Initialize with default values
                    st.session_state.selected_roles[role_key] = {
                        "name": role.name,
                        "description": role.description,
                        "responsibilities": role.default_responsibilities,
                        "tools": role.recommended_tools.copy(),
                        "custom_tool": "",
                        "category": role.category
                    }
                
                # Show "Configure" button
                if st.button(
                    "⚙️ Configure",
                    key=f"configure_{role_key}_{idx}",
                    use_container_width=False
                ):
                    st.session_state.expanded_role = role_key if st.session_state.expanded_role != role_key else None
                    st.rerun()
                
                # Show configuration panel if this role is expanded
                if st.session_state.expanded_role == role_key:
                    render_role_config_inline(role_key, role)
            
            else:
                # Remove from selected roles if unchecked
                if role_key in st.session_state.selected_roles:
                    del st.session_state.selected_roles[role_key]
                if st.session_state.expanded_role == role_key:
                    st.session_state.expanded_role = None
        
        st.markdown("<hr style='margin: 1rem 0; border-color: #E5E7EB;'>", unsafe_allow_html=True)
    
    close_slds_card()


def render_role_config_inline(role_key: str, role: SuggestedRole):
    """
    Render inline configuration panel for a selected role.
    
    Args:
        role_key: Unique key for the role
        role: SuggestedRole object with defaults
    """
    st.markdown("""
    <div style="background-color: #F4F6F9; padding: 1rem; border-radius: 0.25rem; margin-top: 0.5rem; margin-bottom: 1rem;">
    """, unsafe_allow_html=True)
    
    st.markdown("**Configure Role**")
    
    # Get current config
    current_config = st.session_state.selected_roles[role_key]
    
    # Responsibilities textarea
    responsibilities = st.text_area(
        "Responsibilities",
        value=current_config["responsibilities"],
        height=100,
        key=f"responsibilities_{role_key}",
        help="Define what this agent is responsible for in the council"
    )
    
    # Update responsibilities
    st.session_state.selected_roles[role_key]["responsibilities"] = responsibilities
    
    # Allowed tools
    st.markdown("**Allowed Tools**")
    
    all_tools = get_all_available_tools()
    selected_tools = []
    
    cols = st.columns(3)
    for idx, tool in enumerate(all_tools):
        with cols[idx % 3]:
            is_tool_selected = st.checkbox(
                tool,
                value=tool in current_config["tools"],
                key=f"tool_{tool}_{role_key}"
            )
            if is_tool_selected:
                selected_tools.append(tool)
    
    # Update tools
    st.session_state.selected_roles[role_key]["tools"] = selected_tools
    
    # Custom tool input
    custom_tool = st.text_input(
        "Custom Tool",
        value=current_config.get("custom_tool", ""),
        key=f"custom_tool_{role_key}",
        placeholder="Enter custom tool name (optional)"
    )
    
    # Update custom tool
    st.session_state.selected_roles[role_key]["custom_tool"] = custom_tool
    
    st.markdown("</div>", unsafe_allow_html=True)

