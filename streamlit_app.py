"""
Streamlit application entry point for Agent Council system.

Run with: streamlit run streamlit_app.py
"""

import streamlit as st

from app.ui.main_view import render_main_view
from app.ui.sidebar import render_sidebar
from app.utils.logging import configure_logging, get_logger
from app.utils.settings import get_settings

# Configure logging
configure_logging()
logger = get_logger(__name__)

# Page configuration
st.set_page_config(
    page_title="Agent Council",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for dark theme
st.markdown("""
<style>
    .stApp {
        background-color: #0e1117;
    }
    .stButton>button {
        width: 100%;
    }
    .stExpander {
        background-color: #1e2130;
    }
</style>
""", unsafe_allow_html=True)


def main():
    """Main application entry point."""
    settings = get_settings()

    logger.info("streamlit_app_started", env=settings.env)

    # Render sidebar
    render_sidebar()

    # Render main content
    render_main_view()


if __name__ == "__main__":
    main()

