"""
Salesforce Lightning Design System (SLDS) inspired styling for Streamlit UI.

Provides consistent, professional styling matching Salesforce ecosystem.
"""

import streamlit as st


def inject_slds_theme():
    """
    Inject Salesforce Lightning Design System inspired CSS into Streamlit app.
    
    This should be called at the start of the app to apply consistent styling
    across all pages that matches Salesforce Lightning, MuleSoft, and Tableau aesthetics.
    """
    st.markdown("""
    <style>
    /* ================================================
       SALESFORCE LIGHTNING DESIGN SYSTEM - STREAMLIT
       ================================================ */
    
    /* === Global Resets === */
    .stApp {
        background: #FFFFFF !important;
    }
    
    body {
        color: #1A1A1A !important;
        font-family: "Salesforce Sans", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif !important;
        font-size: 0.9375rem;
        line-height: 1.5;
    }
    
    /* === Typography === */
    h1 {
        font-size: 2rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.5px !important;
        color: #032D60 !important;
        margin-bottom: 1rem !important;
        margin-top: 0.5rem !important;
    }
    
    h2 {
        font-size: 1.5rem !important;
        font-weight: 600 !important;
        letter-spacing: -0.3px !important;
        color: #032D60 !important;
        margin-bottom: 0.75rem !important;
        margin-top: 0.5rem !important;
    }
    
    h3 {
        font-size: 1.25rem !important;
        font-weight: 600 !important;
        color: #032D60 !important;
        margin-bottom: 0.5rem !important;
    }
    
    /* === Main Container === */
    .block-container {
        padding-top: 2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1200px !important;
    }
    
    /* === Sidebar Styling === */
    section[data-testid="stSidebar"] {
        background-color: #F4F6F9 !important;
        border-right: 1px solid #D8DDE6 !important;
    }
    
    section[data-testid="stSidebar"] > div {
        padding-top: 1.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
    }
    
    /* Sidebar text */
    section[data-testid="stSidebar"] p,
    section[data-testid="stSidebar"] span,
    section[data-testid="stSidebar"] label {
        color: #1A1A1A !important;
        font-size: 0.9rem !important;
    }
    
    /* Sidebar headers */
    section[data-testid="stSidebar"] h1 {
        color: #032D60 !important;
        font-size: 1.75rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
    }
    
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #032D60 !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        margin-top: 1.5rem !important;
        margin-bottom: 0.75rem !important;
    }
    
    /* === SLDS Cards === */
    .slds-card {
        background: #FFFFFF;
        border-radius: 0.5rem;
        padding: 1.5rem;
        border: 1px solid #D8DDE6;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.07);
        margin-bottom: 1.5rem;
        transition: box-shadow 0.2s ease-in-out;
    }
    
    .slds-card:hover {
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12);
    }
    
    .slds-card-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #032D60;
        margin-bottom: 1rem;
        padding-bottom: 0.75rem;
        border-bottom: 1px solid #E5E7EB;
    }
    
    /* === Buttons === */
    .stButton button {
        background-color: #0176D3 !important;
        color: #FFFFFF !important;
        border-radius: 0.25rem !important;
        border: 1px solid #0176D3 !important;
        padding: 0.625rem 1.25rem !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05) !important;
    }
    
    .stButton button:hover {
        background-color: #014486 !important;
        border-color: #014486 !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
    }
    
    .stButton button:active {
        background-color: #032D60 !important;
        border-color: #032D60 !important;
    }
    
    /* Secondary buttons */
    .stButton button[kind="secondary"] {
        background-color: #FFFFFF !important;
        color: #0176D3 !important;
        border: 1px solid #D8DDE6 !important;
    }
    
    .stButton button[kind="secondary"]:hover {
        background-color: #F4F6F9 !important;
        border-color: #0176D3 !important;
    }
    
    /* === Download Buttons === */
    .stDownloadButton button {
        background-color: #0176D3 !important;
        color: #FFFFFF !important;
        border-radius: 0.25rem !important;
        border: 1px solid #0176D3 !important;
        padding: 0.625rem 1.25rem !important;
        font-size: 0.9375rem !important;
        font-weight: 500 !important;
    }
    
    .stDownloadButton button:hover {
        background-color: #014486 !important;
    }
    
    /* === Input Fields === */
    .stTextInput input,
    .stTextArea textarea,
    .stSelectbox select {
        border-radius: 0.25rem !important;
        border: 1px solid #D8DDE6 !important;
        background: #FFFFFF !important;
        font-size: 0.9375rem !important;
        padding: 0.5rem 0.75rem !important;
        transition: border-color 0.2s ease-in-out !important;
    }
    
    .stTextInput input:focus,
    .stTextArea textarea:focus,
    .stSelectbox select:focus {
        border-color: #0176D3 !important;
        outline: none !important;
        box-shadow: 0 0 0 3px rgba(1, 118, 211, 0.1) !important;
    }
    
    /* Input labels */
    .stTextInput label,
    .stTextArea label,
    .stSelectbox label,
    .stMultiSelect label {
        font-weight: 600 !important;
        color: #032D60 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.375rem !important;
        letter-spacing: 0.01em !important;
    }
    
    /* === Expanders === */
    .streamlit-expanderHeader {
        background-color: #F4F6F9 !important;
        border-radius: 0.25rem !important;
        border: 1px solid #D8DDE6 !important;
        font-weight: 500 !important;
        color: #032D60 !important;
        padding: 0.75rem 1rem !important;
    }
    
    .streamlit-expanderHeader:hover {
        background-color: #E5E7EB !important;
        border-color: #0176D3 !important;
    }
    
    /* === Metrics === */
    [data-testid="stMetricValue"] {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #032D60 !important;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 0.875rem !important;
        font-weight: 500 !important;
        color: #54698D !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }
    
    /* === Info/Warning/Error Boxes === */
    .stAlert {
        border-radius: 0.25rem !important;
        border-left: 4px solid !important;
        padding: 0.75rem 1rem !important;
    }
    
    .stInfo {
        background-color: #E8F4FD !important;
        border-left-color: #0176D3 !important;
        color: #014486 !important;
    }
    
    .stSuccess {
        background-color: #ECFAE8 !important;
        border-left-color: #2E844A !important;
        color: #194E31 !important;
    }
    
    .stWarning {
        background-color: #FFF4E5 !important;
        border-left-color: #FFB75D !important;
        color: #7F4E00 !important;
    }
    
    .stError {
        background-color: #FEECEB !important;
        border-left-color: #BA0517 !important;
        color: #8C001A !important;
    }
    
    /* === Status Pills === */
    .status-pill {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        color: #FFFFFF;
        margin-right: 0.5rem;
        letter-spacing: 0.025em;
        text-transform: uppercase;
    }
    
    .pill-pending {
        background-color: #706E6B;
    }
    
    .pill-in-progress {
        background-color: #0176D3;
    }
    
    .pill-waiting {
        background-color: #FFB75D;
    }
    
    .pill-awaiting-human {
        background-color: #FFB75D;
    }
    
    .pill-completed {
        background-color: #2E844A;
    }
    
    .pill-failed {
        background-color: #BA0517;
    }
    
    .pill-cancelled {
        background-color: #706E6B;
    }
    
    /* === Progress Bar === */
    .stProgress > div > div {
        background-color: #0176D3 !important;
    }
    
    /* === Dividers === */
    hr {
        border-color: #E5E7EB !important;
        margin: 1.5rem 0 !important;
    }
    
    /* === Tabs === */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #D8DDE6;
    }
    
    .stTabs [data-baseweb="tab"] {
        border-radius: 0.25rem 0.25rem 0 0;
        padding: 0.625rem 1rem;
        font-weight: 500;
        color: #54698D;
        border: none;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #0176D3 !important;
        color: #FFFFFF !important;
        font-weight: 600 !important;
    }
    
    /* === Sidebar Buttons === */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        background-color: #FFFFFF !important;
        color: #0176D3 !important;
        border: 1px solid #D8DDE6 !important;
        font-size: 0.875rem !important;
        padding: 0.5rem 1rem !important;
    }
    
    section[data-testid="stSidebar"] .stButton button:hover {
        background-color: #F4F6F9 !important;
        border-color: #0176D3 !important;
    }
    
    /* === Code Blocks === */
    code {
        background-color: #F4F6F9 !important;
        color: #032D60 !important;
        padding: 0.125rem 0.375rem !important;
        border-radius: 0.25rem !important;
        font-family: "Monaco", "Menlo", "Courier New", monospace !important;
        font-size: 0.875em !important;
    }
    
    pre {
        background-color: #F4F6F9 !important;
        border: 1px solid #D8DDE6 !important;
        border-radius: 0.25rem !important;
        padding: 1rem !important;
    }
    
    /* === Links === */
    a {
        color: #0176D3 !important;
        text-decoration: none !important;
        font-weight: 500 !important;
    }
    
    a:hover {
        color: #014486 !important;
        text-decoration: underline !important;
    }
    
    /* === Checkbox/Radio === */
    .stCheckbox label,
    .stRadio label {
        color: #1A1A1A !important;
        font-weight: 400 !important;
    }
    
    /* === Dataframe === */
    .dataframe {
        border: 1px solid #D8DDE6 !important;
        border-radius: 0.25rem !important;
    }
    
    .dataframe th {
        background-color: #F4F6F9 !important;
        color: #032D60 !important;
        font-weight: 600 !important;
        border-bottom: 2px solid #D8DDE6 !important;
    }
    
    /* === Spinner === */
    .stSpinner > div {
        border-top-color: #0176D3 !important;
    }
    
    /* === Responsive Design === */
    @media (max-width: 768px) {
        .block-container {
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        
        .slds-card {
            padding: 1rem !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)


def render_slds_card(title: str = None):
    """
    Render an SLDS-styled card header.
    
    Args:
        title: Optional card title
    """
    if title:
        st.markdown(
            f'<div class="slds-card"><div class="slds-card-header">{title}</div>',
            unsafe_allow_html=True
        )
    else:
        st.markdown('<div class="slds-card">', unsafe_allow_html=True)


def close_slds_card():
    """Close an SLDS card."""
    st.markdown('</div>', unsafe_allow_html=True)


def render_status_pill(status: str, label: str = None):
    """
    Render a status pill with SLDS styling.
    
    Args:
        status: Status key (pending, in_progress, waiting, completed, failed, cancelled)
        label: Display label (defaults to formatted status)
    """
    if label is None:
        label = status.replace('_', ' ').title()
    
    # Map status to pill class
    status_class = status.lower().replace('_', '-')
    
    st.markdown(
        f'<span class="status-pill pill-{status_class}">{label}</span>',
        unsafe_allow_html=True
    )

