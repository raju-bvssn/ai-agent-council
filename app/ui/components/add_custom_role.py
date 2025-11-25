"""
Add custom role component.

Allows users to add custom agent roles beyond the suggested ones.
"""

import streamlit as st

from app.ui.styles import close_slds_card, render_slds_card


def render_add_custom_role():
    """
    Render UI for adding custom agent roles.
    """
    st.markdown("<br>", unsafe_allow_html=True)
    render_slds_card("➕ Add Custom Role")
    
    st.caption("Create a custom agent role for specialized requirements")
    
    # Initialize session state for custom roles
    if "custom_roles_counter" not in st.session_state:
        st.session_state.custom_roles_counter = 0
    
    # Input for custom role name
    col1, col2 = st.columns([0.85, 0.15])
    
    with col1:
        custom_role_name = st.text_input(
            "Role Name",
            placeholder="e.g., Compliance Officer, DevOps Specialist",
            key="custom_role_input",
            label_visibility="collapsed"
        )
    
    with col2:
        add_button = st.button(
            "➕ Add",
            key="add_custom_role_button",
            use_container_width=True,
            type="primary"
        )
    
    if add_button and custom_role_name.strip():
        # Create unique key for custom role
        custom_role_key = f"custom_role_{st.session_state.custom_roles_counter}"
        st.session_state.custom_roles_counter += 1
        
        # Initialize selected_roles if not exists
        if "selected_roles" not in st.session_state:
            st.session_state.selected_roles = {}
        
        # Add custom role to selected roles
        st.session_state.selected_roles[custom_role_key] = {
            "name": custom_role_name.strip(),
            "description": "Custom user-defined role for this session",
            "responsibilities": "",
            "tools": ["Gemini"],  # Default to Gemini
            "custom_tool": "",
            "category": "custom",
            "is_custom": True
        }
        
        st.success(f"✅ Added custom role: {custom_role_name}")
        
        # Clear input
        st.session_state.custom_role_input = ""
        st.rerun()
    
    elif add_button and not custom_role_name.strip():
        st.warning("⚠️ Please enter a role name")
    
    # Display added custom roles
    if "selected_roles" in st.session_state:
        custom_roles = {
            k: v for k, v in st.session_state.selected_roles.items()
            if v.get("is_custom", False)
        }
        
        if custom_roles:
            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("**Custom Roles Added:**")
            
            for role_key, role_config in custom_roles.items():
                col1, col2 = st.columns([0.85, 0.15])
                
                with col1:
                    role_display = f"""
                    <div style="display: flex; align-items: center;">
                        <span style="font-weight: 500; color: #032D60;">{role_config['name']}</span>
                        <span style="margin-left: 0.5rem; color: #706E6B; cursor: help;" title="{role_config['description']}">ⓘ</span>
                    </div>
                    """
                    st.markdown(role_display, unsafe_allow_html=True)
                
                with col2:
                    if st.button("🗑️", key=f"remove_{role_key}", use_container_width=True):
                        del st.session_state.selected_roles[role_key]
                        st.rerun()
    
    close_slds_card()

