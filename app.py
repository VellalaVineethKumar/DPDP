"""
Multi-Regulation Compliance Assessment Tool

This application helps organizations assess their compliance with various 
data protection regulations across different industries.

Main entry point that initializes the application and handles page routing.
"""

import streamlit as st
import logging
import os
import sys
from datetime import datetime
from dotenv import load_dotenv  

# Reduce logging frequency for timer updates
logging.getLogger('__main__').setLevel(logging.WARNING)
logging.getLogger('assessment').setLevel(logging.WARNING)
logging.getLogger('root').setLevel(logging.WARNING)  # Added to suppress root logger

# Setup logging configuration before any other imports
if not os.path.exists('logs'):
    os.makedirs('logs')

# Configure root logger
logging.basicConfig(
    level=logging.WARNING,  # Changed from INFO to WARNING
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f"logs/app_{datetime.now().strftime('%Y%m%d')}.log"),
        logging.StreamHandler(sys.stdout)  # Add StreamHandler for terminal output
    ]
)

# Get logger for this module
logger = logging.getLogger(__name__)

# Add test log message to verify logging is working
logger.info("Application started - Logging initialized")

# Load environment variables silently
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
if os.path.exists(env_path):
    load_dotenv(env_path)

# Check for API key without logging
api_key = os.environ.get("COMPLIANCE_AI_API_KEY")

# Continue with the rest of the imports and application setup
import config
from helpers import initialize_session_state
from assessment import get_questionnaire
from views import (
    render_landing_page,
    render_header, 
    render_sidebar, 
    render_welcome_page, 
    render_dashboard, 
    render_assessment, 
    render_report, 
    render_recommendations,
    render_data_discovery,  # Add this import
    render_admin_page
)


# Set page configuration with custom icon
st.set_page_config(
    page_title=config.APP_TITLE,
    page_icon=config.APP_ICON,
    layout=config.APP_LAYOUT,
    initial_sidebar_state=config.SIDEBAR_STATE
)

# Initialize session state
initialize_session_state()

# Check authentication
if not st.session_state.get('authenticated', False):
    render_landing_page()
else:
    # Main application flow
    if 'current_page' not in st.session_state:
        st.session_state.current_page = 'welcome'
    if 'current_section' not in st.session_state:
        st.session_state.current_section = 0
    if 'responses' not in st.session_state:
        st.session_state.responses = {}
    if 'assessment_complete' not in st.session_state:
        st.session_state.assessment_complete = False
    if 'results' not in st.session_state:
        st.session_state.results = None
    if 'organization_name' not in st.session_state:
        st.session_state.organization_name = ""
    if 'assessment_date' not in st.session_state:
        st.session_state.assessment_date = datetime.now().strftime("%Y-%m-%d")
    if 'selected_regulation' not in st.session_state:
        st.session_state.selected_regulation = "DPDP"
    if 'selected_industry' not in st.session_state:
        st.session_state.selected_industry = "general"

    # Main app logic
    def main():
        """Main application function that renders the appropriate page"""
        try:
            # Add detailed logging for industry changes
            if 'selected_industry' in st.session_state:
                current_industry = st.session_state.selected_industry
                previous_industry = getattr(st.session_state, 'last_checked_industry', None)
                
                if previous_industry and current_industry != previous_industry:
                    logger.info(f"Industry changed from '{previous_industry}' to '{current_industry}'")
                    # Force questionnaire reload on industry change
                    if 'current_questionnaire' in st.session_state:
                        del st.session_state.current_questionnaire
                        logger.info("Cleared questionnaire cache due to industry change")
                
                st.session_state.last_checked_industry = current_industry

            # DEBUGGING: Add questionnaire verification on every page load
            if 'selected_industry' in st.session_state:
                logger.info(f"APP MAIN: Current selected industry is {st.session_state.selected_industry}")
                
                # Check if questionnaire type is locked but doesn't match selected_industry
                if hasattr(st.session_state, 'locked_questionnaire_type'):
                    if (st.session_state.locked_questionnaire_type == "e-commerce" and 
                        st.session_state.selected_industry.lower() != "e-commerce"):
                        logger.warning(f"FIXING MISMATCH: selected_industry={st.session_state.selected_industry} but locked to e-commerce")
                        st.session_state.selected_industry = "e-commerce"
                        st.session_state.clear_questionnaire_cache = True
                
                # Log detailed diagnostic info on change detection
                if hasattr(st.session_state, 'last_checked_industry') and st.session_state.last_checked_industry != st.session_state.selected_industry:
                    logger.warning(f"INDUSTRY CHANGED in app: {st.session_state.last_checked_industry} -> {st.session_state.selected_industry}")
                    
                st.session_state.last_checked_industry = st.session_state.selected_industry
                
                # If E-commerce is selected, lock it to prevent switches
                if st.session_state.selected_industry.lower() == "e-commerce" and not hasattr(st.session_state, 'locked_questionnaire_type'):
                    st.session_state.locked_questionnaire_type = "e-commerce"
                    logger.info("LOCKING to E-commerce questionnaire type")
            
            # Add diagnostics for response issues
            if st.session_state.get('current_page') == 'assessment' and 'responses' in st.session_state:
                logger.info(f"Current responses count: {len(st.session_state.responses)}")
                section_idx = st.session_state.get('current_section', 0)
                questionnaire = get_questionnaire(
                    st.session_state.selected_regulation,
                    st.session_state.selected_industry
                )
                if 'sections' in questionnaire:
                    total_sections = len(questionnaire['sections'])
                    logger.info(f"Questionnaire has {total_sections} total sections")
                    
                    # Log the names of all sections for verification
                    section_names = [s.get('name', f'Section {i+1}') for i, s in enumerate(questionnaire['sections'])]
                    logger.info(f"All section names: {section_names}")
                    
                    # Debug log to see which sections are actually in the questionnaire
                    logger.info(f"Complete questionnaire structure: {len(questionnaire['sections'])} sections")
                    for idx, section in enumerate(questionnaire['sections']):
                        logger.info(f"Section {idx+1}: {section.get('name')} with {len(section.get('questions', []))} questions")
                    
                    if section_idx < total_sections:
                        section = questionnaire['sections'][section_idx]
                        question_count = len(section.get('questions', []))
                        logger.info(f"Current section {section_idx} has {question_count} questions")
                        
                        # Check which questions are answered in this section
                        for q_idx in range(question_count):
                            key = f"s{section_idx}_q{q_idx}"
                            logger.info(f"Question {q_idx+1} response key {key}: {'exists' if key in st.session_state.responses else 'missing'}")
                
            # Check for and fix null responses during startup 
            if st.session_state.get('check_for_nulls', True) and 'responses' in st.session_state:
                from helpers import fix_null_responses
                null_count = sum(1 for v in st.session_state.responses.values() if v is None)
                if null_count > 0:
                    logger.warning(f"Found {null_count} null responses at startup, automatically fixing...")
                    fixed = fix_null_responses("Not applicable")
                    if fixed > 0:
                        logger.info(f"Automatically fixed {fixed} null responses at startup")
                # Only check once per session
                st.session_state.check_for_nulls = False
            
            # Render header
            render_header()
            
            # Render sidebar
            render_sidebar()
            
            # Check if assessment parameters are filled
            assessment_ready = (
                st.session_state.organization_name and 
                st.session_state.organization_name.strip() != "" and
                st.session_state.selected_regulation and
                st.session_state.selected_industry
            )
            
                
            # Render current page
            if st.session_state.current_page == 'welcome':
                render_welcome_page()
            elif st.session_state.current_page == 'assessment' and assessment_ready:
                render_assessment()
            elif st.session_state.current_page == 'dashboard' and st.session_state.get('assessment_complete', False):
                render_dashboard()
            elif st.session_state.current_page == 'report' and st.session_state.get('assessment_complete', False):
                render_report()
            elif st.session_state.current_page == 'recommendations' and st.session_state.get('assessment_complete', False):
                render_recommendations()
            elif st.session_state.current_page == 'discovery' and st.session_state.get('assessment_complete', False):
                render_data_discovery()
            elif st.session_state.current_page == 'admin' and st.session_state.get('is_admin', False):
                render_admin_page()
            else:
                # Default to welcome page
                render_welcome_page()
                
        except Exception as e:
            logger.error(f"Error in main application: {str(e)}", exc_info=True)
            st.error("An unexpected error occurred. Please try refreshing the page.")

    if __name__ == "__main__":
        main()