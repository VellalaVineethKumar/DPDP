"""
Multi-Regulation Compliance Assessment Tool

This application helps organizations assess their compliance with various 
data protection regulations across different industries.

Main entry point that initializes the application and handles page routing.
"""

import streamlit as st
import logging
import os
from datetime import datetime

import config
from utils import initialize_session_state
from ui import (
    render_header, 
    render_sidebar, 
    render_welcome_page, 
    render_dashboard, 
    render_assessment, 
    render_report, 
    render_recommendations
)

# Setup logging
if not os.path.exists('logs'):
    os.makedirs('logs')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Set page config
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.APP_LAYOUT,
    initial_sidebar_state=config.SIDEBAR_STATE
)

# Initialize session state
initialize_session_state()

# Main app logic
def main():
    """Main application function that renders the appropriate page"""
    try:
        # Render header
        render_header()
        
        # Render sidebar
        render_sidebar()
        
        # Render current page
        if st.session_state.current_page == 'welcome':
            render_welcome_page()
        elif st.session_state.current_page == 'dashboard':
            render_dashboard()
        elif st.session_state.current_page == 'assessment':
            render_assessment()
        elif st.session_state.current_page == 'report':
            render_report()
        elif st.session_state.current_page == 'recommendations':
            render_recommendations()
        else:
            # Default to welcome page
            render_welcome_page()
            
    except Exception as e:
        logger.error(f"Error in main application: {str(e)}", exc_info=True)
        st.error("An unexpected error occurred. Please try refreshing the page.")

if __name__ == "__main__":
    main()