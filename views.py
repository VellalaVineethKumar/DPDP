"""User interface rendering functions for the Compliance Assessment Tool.
This module contains all the Streamlit UI components and page rendering.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import logging
import os
import time
import base64
import json
import traceback  # Add this import at the top
from typing import Dict, List, Any, Optional, Tuple  # Add typing imports
import tempfile
import re # Add re import
from markdown_pdf import MarkdownPdf, Section # Add markdown-pdf imports
import requests

import config
# Update import: get reg/ind functions from config instead of assessment
from config import get_available_regulations, get_available_industries
from assessment import get_questionnaire, calculate_compliance_score
# Import from new recommendation engine instead of assessment
from recommendation_engine import get_recommendation_priority, organize_recommendations_by_priority
from helpers import (
    go_to_page, 
    save_response, 
    generate_excel_download_link,
    track_event,
    get_section_progress_percentage,  # Use this instead of local implementation
    format_regulation_name,
    validate_token
)
from token_storage import generate_token, cleanup_expired_tokens, revoke_token, get_organization_for_token, TOKENS_FILE

# Import the newly created styles
from styles import (
    get_landing_page_css, 
    get_sidebar_css, 
    get_radio_button_css,
    get_print_export_css,
    get_print_button_html,
    get_expiry_box_css,
    get_section_navigation_css,
    get_common_button_css,
    get_informatica_solution_css,
    get_section_header_css,
    get_progress_metrics_css,
    get_penalties_table_css,
    get_discovery_button_css,
    get_faq_css,
    get_input_label_css,
    get_app_header_css,
    get_contact_link_css,
    get_ai_analysis_css,
    get_penalties_section_css,
    get_countdown_section_css,
    get_logo_css,
    get_spacing_css,
    get_data_discovery_css,
    get_magic_quadrant_css,
    get_ai_report_css,
    get_penalties_note_css
)

from faq import FAQ_DATA  # Add this import at the top

# Add import at the top with other imports

# Setup logging
logger = logging.getLogger(__name__)

def render_header():
    """Render the application header"""
    # Show organization name only if it exists and isn't empty
    org_name = st.session_state.organization_name if st.session_state.organization_name and st.session_state.organization_name.strip() else None
    
    # Add CSS for header layout with logo
    st.markdown(get_app_header_css(), unsafe_allow_html=True)
    
    # Construct logo path
    logo_path = os.path.join(config.BASE_DIR, "Assets", "@logo.png")
    
    # Create header HTML with logo
    header_html = '<div class="app-header">'
    
    # Add logo if exists
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            logo_base64 = base64.b64encode(f.read()).decode()
        header_html += f'<img src="data:image/png;base64,{logo_base64}" class="header-logo" alt="Logo">'
    
    # Add header text
    header_html += '<div class="header-text">'
    header_html += f'<h1>{config.APP_TITLE}</h1>'
    if org_name:
        header_html += f'<p>Organization: {org_name}</p>'
    header_html += '</div></div>'
    
    st.markdown(header_html, unsafe_allow_html=True)

# Landing page function (moved from landing.py)
def render_landing_page():
    """Render the landing page with token authentication"""
    # Add admin navigation button if user has admin privileges
    if st.session_state.get('is_admin', False):
        if st.button("Admin Dashboard", key="admin_nav"):
            st.session_state.current_page = 'admin'
            st.rerun()
            
    # Apply custom CSS
    st.markdown(get_landing_page_css(), unsafe_allow_html=True)
    st.markdown(get_contact_link_css(), unsafe_allow_html=True)
    
    # Add CSS to center the main content block
    st.markdown("""
        <style>
        /* Target the main block containing landing page elements */
        div[data-testid="stVerticalBlock"] > div.stHorizontalBlock > div[data-testid="stVerticalBlock"] {
            align-items: center;
        }
        /* Optional: Add margin below logo if needed */
        div[data-testid="stImage"] {
            margin-bottom: 25px;
        }
        </style>
        """, unsafe_allow_html=True)

    # Logo - Display using columns and centered text within middle column
    if os.path.exists(config.LOGO_PATH):
        col1, col2, col3 = st.columns([1, 1, 1]) # Equal ratios
        with col2:
            # Inject CSS specifically for this column
            st.markdown("""
                <style>
                    div[data-testid="stHorizontalBlock"] > div:nth-child(2) {
                        text-align: center;
                        display: flex; /* Use flexbox for centering */
                        justify-content: center; /* Center horizontally */
                        align-items: center; /* Center vertically if needed */
                    }

                </style>
            """, unsafe_allow_html=True)
            st.image(config.LOGO_PATH, width=300) # Increased width from 200 to 300
    else:
        st.warning(f"Logo not found at path: {config.LOGO_PATH}")
    
    # Title
    st.markdown(f"""
        <div class="title-container">
            <h1>{config.APP_TITLE}</h1>
            <p>Enter your access token to begin the assessment</p>
            <p class="contact-link">If you do not have a token, please <a href="mailto:info@datainfa.com?subject=Requesting%20Access%20token%20for%20my%20organisation">contact us</a> to get your access token.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Token input with centered container
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        token = st.text_input("Access Token", type="password")
        if st.button("Access Assessment", type="primary", use_container_width=True):
            if validate_token(token):
                st.session_state.authenticated = True
                st.session_state.current_page = 'welcome'
                st.rerun()
            else:
                st.error("Invalid token. Please try again or contact support.")
    
    # Footer
    st.markdown("""
        <div class="footer">
            &copy; 2023 Compliance Assessment Tool | All Rights Reserved
        </div>
    """, unsafe_allow_html=True)

def render_assessment():
    """Render the assessment questionnaire"""
    # Create a top anchor to scroll to
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)

    # Add custom CSS to highlight "Informatica Solution:"
    st.markdown(get_informatica_solution_css(), unsafe_allow_html=True)

    # DEBUGGING: Log entry to assessment page with full context
    logger.info(f"ENTERING render_assessment: industry={st.session_state.get('selected_industry', 'UNKNOWN')}")
    logger.info(f"Session state keys: {list(st.session_state.keys())}")
    
    # Try to fix questionnaire selection before continuing
    from helpers import fix_questionnaire_selection, clear_questionnaire_cache
    fixed_questionnaire = fix_questionnaire_selection()
    
    # CRITICAL FIX: Force a check for incorrect industry/questionnaire mismatch
    if 'selected_industry' in st.session_state and st.session_state.selected_industry.lower() == 'e-commerce':
        logger.info("VERIFYING E-commerce questionnaire integrity")
        
        # If we have current_questionnaire, ensure it has 4 sections for E-commerce
        if 'current_questionnaire' in st.session_state:
            sections = st.session_state.current_questionnaire.get('sections', [])
            section_count = len(sections)
            logger.info(f"Current questionnaire has {section_count} sections")
            
            if section_count < 4:
                logger.warning(f"INTEGRITY ERROR: E-commerce questionnaire has only {section_count} sections, forcing reload")
                # Get full stack trace to see where this is happening
                logger.warning(f"Stack trace:\n{''.join(traceback.format_stack())}")
                clear_questionnaire_cache()
                fixed_questionnaire = True
                # Lock to E-commerce
                st.session_state.locked_questionnaire_type = "e-commerce"
                st.session_state.locked_section_count = 4
        else:
            logger.info("No current_questionnaire in session state")
    
    # Create a top anchor to scroll to
    st.markdown('<div id="top-of-form"></div>', unsafe_allow_html=True)
    
    # Add JavaScript to scroll to top when loading a new section
    st.markdown("""
    <script>
        // Automatically scroll to top when this component loads
        window.scrollTo(0, 0);
        
        // Alternative method that may work better in some Streamlit versions
        window.addEventListener('load', function() {
            setTimeout(function() {
                window.scrollTo(0, 0);
            }, 100);
        });
    </script>
    """, unsafe_allow_html=True)
    
    # Cache the questionnaire in session state, with preservation of "new banking fin"
    if 'current_questionnaire' not in st.session_state:    
        st.session_state.current_questionnaire = get_questionnaire(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
    
    # Use the cached questionnaire
    questionnaire = st.session_state.current_questionnaire
    
    # Show questionnaire debug info in sidebar with more details
    with st.sidebar.expander("Navigation panel", expanded=False):
        st.markdown("""
            <style>
            div.stExpander {
                background-color: #0e1117;
                border: 1px solid rgba(49, 51, 63, 0.2);
            }
            /* Dark theme buttons */
            div.stButton > button {
                width: 100%;
                padding: 0.5rem;
                margin: 0.25rem 0;
                background-color: #1e1e1e !important;
                color: #fafafa;
                border: 1px solid #333333 !important;
                border-radius: 0.3rem;
                transition: all 0.2s;
            }
            /* Hover effect */
            div.stButton > button:hover:not(:disabled) {
                background-color: #2d2d2d !important;
                border-color: #404040 !important;
            }
            /* Disabled button */
            div.stButton > button:disabled {
                background-color: #161616 !important;
                color: #666666;
                border-color: #292929 !important;
            }
            /* Current section highlight */
            div.stButton > button.current {
                border-left: 3px solid #666666 !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        
        if "sections" in questionnaire:
            st.write("Jump to section:")
            
            # Create list of sections with completion status
            for i, section in enumerate(questionnaire["sections"]):
                section_name = section.get("name", f"Section {i+1}")
                
                # Calculate if section is complete
                questions = section.get("questions", [])
                answered = sum(1 for q_idx in range(len(questions)) 
                             if f"s{i}_q{q_idx}" in st.session_state.responses)
                complete = answered == len(questions)
                
                # Create button with status indicator
                button_label = f"{i+1}. {section_name} [{answered}/{len(questions)}]"
                if st.button(button_label, key=f"nav_section_{i}", 
                           disabled=i == st.session_state.current_section,
                           use_container_width=True):
                    st.session_state.current_section = i
                    st.rerun()
    
    # TESTING ONLY - TO BE REMOVED BEFORE PRODUCTION
    # Add quick-fill testing option in sidebar for faster testing
    if st.session_state.get('is_admin', False):
        st.markdown("""
            <style>
            /* Expander styling */
            .streamlit-expanderHeader {
                background-color: #262730 !important;
                border: none !important;
                border-radius: 4px !important;
                color: #fafafa !important;
                font-size: 14px !important;
            }
            .streamlit-expanderHeader:hover {
                background-color: #1E1E1E !important;
            }
            /* Testing tools container */
            div.stExpander {
                border: none !important;
                background-color: transparent !important;
            }
            /* Radio buttons in testing tools */
            div.stExpander div[data-testid="stRadio"] > div {
                display: flex !important;
                flex-direction: column !important;
                gap: 8px !important;
            }
            div.stExpander div[data-testid="stRadio"] label {
                background-color: #262730 !important;
                padding: 8px 12px !important;
                border-radius: 4px !important;
                color: #fafafa !important;
                transition: all 0.2s !important;
            }
            div.stExpander div[data-testid="stRadio"] label:hover {
                background-color: #1E1E1E !important;
                color: #6fa8dc !important;
            }
            /* Button styling */
            div.stExpander div[data-testid="stButton"] > button {
                width: 100% !important;
                padding: 8px 12px !important;
                margin: 4px 0 !important;
                background-color: #262730 !important;
                color: #fafafa !important;
                border: none !important;
                border-radius: 4px !important;
                text-align: left !important;
                transition: all 0.2s !important;
            }
            div.stExpander div[data-testid="stButton"] > button:hover {
                background-color: #1E1E1E !important;
                color: #6fa8dc !important;
            }
            div.stExpander div[data-testid="stButton"] > button:active {
                border-left: 3px solid #6fa8dc !important;
            }
            </style>
        """, unsafe_allow_html=True)
        
        with st.sidebar.expander("TESTING TOOLS", expanded=False):
            auto_fill_option = st.radio(
            "Auto-fill responses with:",
            ["None", "All Yes/Positive", "All Partial/Medium", "All No/Negative", "Random Mix"],
            key="auto_fill_option"
        )
            if st.button("Apply Auto-Fill", key="apply_auto_fill", type="primary"):
                sections = questionnaire["sections"]
                current_section = st.session_state.current_section
                
                if current_section < len(sections):
                    section = sections[current_section]
                    questions = section.get("questions", [])
                    
                    import random
                    responses_updated = False
                
                    for q_idx, question in enumerate(questions):
                        # Create the response key in the correct format
                        response_key = f"s{current_section}_q{q_idx}"
                        # Get options for the question
                        if isinstance(question, dict):
                            options = question.get("options", [])
                        else:
                            try:
                                options = section.get("options", [])[q_idx]
                            except (IndexError, KeyError):
                                options = ["Yes", "No", "Not applicable"]
                        
                        # Select option based on auto-fill choice
                        selected_option = None
                        if auto_fill_option == "All Yes/Positive":
                            selected_option = options[0]  # First option (Yes/Positive)
                        elif auto_fill_option == "All Partial/Medium":
                            selected_option = options[1] if len(options) > 2 else options[0]  # Middle option if available
                        elif auto_fill_option == "All No/Negative":
                            selected_option = options[-1]  # Last option (No/Negative)
                        elif auto_fill_option == "Random Mix":
                            selected_option = random.choice(options)  # Random choice
                        
                        # Update session state responses
                        if selected_option:
                            st.session_state.responses[response_key] = selected_option
                            responses_updated = True
                    
                    if responses_updated:
                        st.rerun()
                else:
                    st.error("No section available for auto-fill")
    
    # END OF TESTING CODE
    
    # Add debug info to see which questionnaire we're using
    if fixed_questionnaire:
        st.info("Questionnaire selection has been fixed. Please review your responses.")
       
    sections = questionnaire["sections"]
    
    # Check if questionnaire has any sections
    if not sections:
        st.error("No assessment questions found for the selected regulation and industry. Please select a different combination.")
        if st.button("Back to Welcome"):
            st.session_state.current_page = 'welcome'
            st.rerun()
        return
    
    # Debug display to show section progress
    st.sidebar.write(f"Current Section: {st.session_state.current_section + 1} of {len(sections)}")
    st.sidebar.write(f"Total Sections: {len(sections)}")
    
    if st.session_state.current_section >= len(sections):
        st.session_state.assessment_complete = True
        # Force recalculation of results
        st.session_state.results = calculate_compliance_score(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
        
        # Redirect to report page
        st.session_state.current_page = 'report'
        st.rerun()
        return
    
    # Get current section
    current_section = sections[st.session_state.current_section]
    section_name = current_section["name"]
    questions = current_section["questions"]
    
    # Calculate overall progress across all sections
    total_questions = sum(len(section["questions"]) for section in sections)
    answered_questions = sum(1 for key in st.session_state.responses.keys() if key.startswith('s'))
    overall_progress = (answered_questions / total_questions) * 100 if total_questions > 0 else 0
    
    # Show section header with both section and overall progress
    st.markdown(get_section_header_css(), unsafe_allow_html=True)
    st.markdown(f"""
        <div class="section-header">
            <h2 class="section-title">Part {st.session_state.current_section + 1}: {section_name}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    # Show current section progress
    section_progress = get_section_progress_percentage()
    st.progress(overall_progress / 100)
    
    # Show both progress metrics with consistent spacing
    st.markdown(get_progress_metrics_css(), unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f'<p class="progress-metric">Part progress: {section_progress:.1f}%</p>', unsafe_allow_html=True)
    with col2:
        st.markdown(f'<p class="progress-metric">Overall progress: {overall_progress:.1f}% ({answered_questions}/{total_questions} questions)</p>', unsafe_allow_html=True)
    
    # Apply radio button styling
    st.markdown(get_radio_button_css(), unsafe_allow_html=True)
    
    # Add this near where questions are rendered
    st.markdown("""
        <style>
        .informatica-solution {
            color: #FF4B4B !important;
            font-weight: bold;
        }
        .question-text a {
            color: #FF4B4B;
            text-decoration: none;
            border-bottom: 1px dashed #FF4B4B;
        }
        .question-text a:hover {
            color: #ff7575;
            border-bottom: 1px solid #ff7575;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Create a form for the section
    with st.form(key=f"section_form_{st.session_state.current_section}"):
        # Display questions
        for q_idx, question in enumerate(questions):
            # Handle both string and dict question formats
            if isinstance(question, dict):
                q_id = question.get("id", q_idx + 1)
                q_text = question.get("text", f"Question {q_idx + 1}")
                options = question.get("options", [])
            else:
                # Legacy format where question is a string
                q_id = q_idx + 1
                q_text = question
                # Try to find options from section["options"] if it exists
                try:
                    options = current_section.get("options", [])[q_idx]
                except (IndexError, KeyError):
                    options = ["Yes", "No", "Not applicable"]
                    logger.warning(f"No options found for question {q_id}, using default options")
            
            st.subheader(f"Question {q_id}")
            st.markdown(f"""
                <div class="question-text">
                    {q_text}
                </div>
            """, unsafe_allow_html=True)
            
            # Create a unique key for this question that we'll use to access response
            response_key = f"q_{st.session_state.current_section}_{q_idx}"
            
            # Get current response if any
            saved_response_key = f"s{st.session_state.current_section}_q{q_idx}"
            current_value = st.session_state.responses.get(saved_response_key)
            
            # Style the radio buttons with a better color scheme
            st.markdown("""
            <style>
            div.row-widget.stRadio > div {
                flex-direction: column;
                gap: 10px;
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label {
                padding: 10px;
                background: #262730;  /* Changed to darker background to match Streamlit's theme */
                border: 1px solid #4e4e61;  /* Added border for better visibility */
                border-radius: 5px;
                width: 100%;
                transition: background-color 0.3s;
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
                background: #3b3b49;  /* Slightly lighter on hover */
                border-color: #6e6e80;  /* Brighter border on hover */
            }
            div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
                margin-right: 10px;
            }
            </style>
            """, unsafe_allow_html=True)
            
            # Use radio instead of selectbox
            selected_option = st.radio(
                "Select your answer:",
                options=options,
                key=response_key,
                index=options.index(current_value) if current_value in options else None
            )
        
        # Add some space before buttons
        st.write("")
        
        # Navigation buttons with consistent styling
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            prev_disabled = st.session_state.current_section <= 0
            if st.form_submit_button(
                "Previous Section", 
                disabled=prev_disabled, 
                use_container_width=True,
                type="secondary"
            ):
                # Force scroll to top
                st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
                # Turn off validation flag when going backwards
                st.session_state.form_validation_attempted = False
                
                # Set flag to ensure we focus on the top element in the next render
                st.session_state.scroll_to_top = True
                
                # Save responses first - explicitly save here instead of relying on session state
                for q_idx in range(len(current_section["questions"])):
                    response_key = f"q_{st.session_state.current_section}_{q_idx}"
                    if response_key in st.session_state:
                        response = st.session_state[response_key]
                        save_response(st.session_state.current_section, q_idx, response)
                
                # Go to previous section with a direct rerun flag
                next_section = st.session_state.current_section - 1
                st.session_state.current_section = next_section
                st.session_state.current_page = 'assessment'
                st.rerun()
        
        with col3:
            next_button_label = "Next Section" if st.session_state.current_section < len(sections) - 1 else "Complete Assessment"
            
            if st.form_submit_button(
                next_button_label, 
                type="primary", 
                use_container_width=True
            ):
                # Force scroll to top
                st.markdown('<script>window.scrollTo(0, 0);</script>', unsafe_allow_html=True)
                # Set flag to ensure we focus on the top element in the next render
                st.session_state.scroll_to_top = True
                
                # Save all responses from form state to session state - without debug output
                for q_idx in range(len(current_section["questions"])):
                    response_key = f"q_{st.session_state.current_section}_{q_idx}"
                    answer_key = f"s{st.session_state.current_section}_q{q_idx}"
                    
                    if response_key in st.session_state:
                        response = st.session_state[response_key]
                        if response is not None:
                            # Directly save to session state to bypass helper functions
                            st.session_state.responses[answer_key] = response
                
                # Clear validation flag initially - will be set only if validation fails
                st.session_state.form_validation_attempted = False
                
                # Check which questions are answered in this section without debug output
                all_answered = True
                unanswered = []
                
                for q_idx in range(len(current_section["questions"])):
                    key = f"s{st.session_state.current_section}_q{q_idx}"
                    if key not in st.session_state.responses:
                        all_answered = False
                        unanswered.append(q_idx + 1)
                
                # Only show the error message if there are unanswered questions
                if not all_answered:
                    # Set validation flag to show warnings
                    st.session_state.form_validation_attempted = True
                    question_list = ", ".join(map(str, unanswered))
                    st.error(f"⚠️ Please answer all questions before proceeding. Missing answers for question(s): {question_list}")
                    # Use st.stop() instead of return to preserve form state
                    st.stop()
                
                # If we get here, all questions are answered
                # Go to next section
                next_section = st.session_state.current_section + 1
                
                # Check if we're at the last section
                if next_section >= len(sections):
                    # Final check for all questions across all sections
                    all_sections_complete = True
                    missing_sections = set()
                    
                    for section_idx, section in enumerate(sections):
                        for q_idx, question in enumerate(section["questions"]):
                            response_key = f"s{section_idx}_q{q_idx}"
                            if response_key not in st.session_state.responses:
                                all_sections_complete = False
                                missing_sections.add(section_idx + 1)
                    
                    if not all_sections_complete:
                        st.error("⚠️ Please answer all questions before completing the assessment.")
                        with st.expander("View Missing Sections", expanded=True):
                            st.write("The following sections have unanswered questions:")
                            for section_num in sorted(missing_sections):
                                st.write(f"• Section {section_num}")
                        st.stop()
                    
                    # If we get here, all questions are answered
                    st.session_state.assessment_complete = True
                    st.session_state.results = calculate_compliance_score(
                        st.session_state.selected_regulation,
                        st.session_state.selected_industry
                    )
                    st.session_state.current_page = 'report'
                else:
                    st.session_state.current_section = next_section
                    st.session_state.current_page = 'assessment'
                
                track_event("section_completed", {"section": current_section['name']})
                st.rerun()


from nlg_report import generate_report

def generate_natural_language_report(results: Dict[str, Any]) -> str:
    """
    Generate human-readable report using AI
    """
    logger.info("Requesting AI report generation with the following configuration:")
    logger.info(f"AI enabled: {config.get_ai_enabled()}")
    logger.info(f"API key available: {'Yes' if config.get_ai_api_key() else 'No'}")
    logger.info(f"API provider: {config.get_ai_provider()}")
    
    # Record timing information
    start_time = time.time()
    try:
        report = generate_report(results, use_external_api=config.get_ai_enabled())
        if not report:
            logger.error("Report generation failed - no content returned")
            return "Error: Failed to generate report. Please try again or contact support."
    except Exception as e:
        logger.error(f"Error in report generation: {e}")
        return "Error: Failed to generate report. Please try again or contact support."
        
    duration = time.time() - start_time
    logger.info(f"Report generation completed in {duration:.2f} seconds")
    logger.info(f"Report length: {len(report)} characters")
    
    return report

def render_report():
    """Render the compliance report"""
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to view your compliance report")
        if st.button("Go to Assessment", type="primary"):
            st.session_state.current_page = 'assessment'
            st.rerun()
        return

    
    results = st.session_state.results
    
    st.header(f"{format_regulation_name(st.session_state.selected_regulation)} Compliance Report")
    # st.subheader(f"For: {st.session_state.organization_name}")
    # st.write(f"Assessment Date: {st.session_state.assessment_date}")
    
    # Get questionnaire to check how many sections it has vs how many have scores
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    expected_section_count = len(questionnaire.get("sections", []))
    actual_section_count = len(results.get("section_scores", {}))
    
    # Add a recalculate button at the top when we're missing sections
    if actual_section_count < expected_section_count:
        st.warning(f"⚠️ Note: Only {actual_section_count} of {expected_section_count} sections are showing in the report. Click the button below to ensure all sections are included.")
        if st.button("Process All Sections", type="primary"):
            # Force recreation of the results
            st.session_state.process_all_sections = True
            st.session_state.results = calculate_compliance_score(
                st.session_state.selected_regulation,
                st.session_state.selected_industry
            )
            st.success(f"Processed all {expected_section_count} sections. Refreshing the report to show updated results.")
            st.rerun()
    
    # Summary section
    st.markdown(f"""
    ### Overall Compliance: {results['overall_score']:.1f}% - {results['compliance_level']}
    This report provides a detailed assessment of your organization's compliance with the {format_regulation_name(st.session_state.selected_regulation)}
    across key areas. Review the section scores and recommendations below to identify areas
    for improvement.
    """)
    
    # Create two columns for charts with 1:2 ratio
    col1, col2 = st.columns([1, 2])
    
    # Add gauge chart in the first column
    with col1:
        # Create gauge chart
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=results['overall_score'],
            number={'suffix': '%', 'valueformat': '.0f'},
            domain={'x': [0.1, 0.9], 'y': [0, 0.9]},
            gauge={
                'axis': {'range': [0, 100], 'tickvals': [0, 25, 50, 75, 100], 'ticktext': ['0%', '25%', '50%', '75%', '100%']},
                'bar': {'color': "#1f77b4"},
                'steps': [
                    {'range': [0, 50], 'color': "#ff4b4b"},
                    {'range': [50, 75], 'color': "#ffa64b"},
                    {'range': [75, 100], 'color': "#4bff4b"}
                ]
            },
            title={'text': "Overall Compliance Score"}
        ))
        fig.update_layout(height=300, margin=dict(t=40, b=20, l=20, r=20))
        st.plotly_chart(fig, use_container_width=True)
    
    # Add horizontal bar chart in the second column
    with col2:
        # Get all sections from questionnaire
        questionnaire = st.session_state.current_questionnaire
        all_sections = [section["name"] for section in questionnaire["sections"]]
        
        # Create section scores dataframe with percentage scores and weights, including all sections
        df = pd.DataFrame([
            {
                "Section": section,
                "Score": max(0.1, round(results["section_scores"].get(section, 0) * 100)),
                "Weight": round(next((s['weight'] * 100 for s in questionnaire['sections'] if s['name'] == section), 0), 1)
            }
            for section in all_sections
        ])
        df = df.sort_values(by="Score", ascending=True)
        
        # Create horizontal bar chart with improved color scheme and hover template
        fig = px.bar(
            df, 
            x="Score", 
            y="Section", 
            orientation='h',
            color="Score",
            color_continuous_scale=[[0, "#FF4B4B"], [0.5, "#FF4B4B"], [0.5, "#FFA500"], [0.75, "#FFA500"], [0.75, "#00CC96"], [1, "#00CC96"]],
            range_color=[0, 100],
            labels={"Score": "Compliance Score (%)"}
        )
        fig.update_layout(
            height=400,
            margin=dict(l=10, r=10, t=10, b=10),
            yaxis=dict(automargin=True)
        )
        # Add custom hover template to show weight
        fig.update_traces(
            hovertemplate="<b>%{y}</b><br>Score: %{x:.1f}%<br>Weight: %{customdata:.1f}%<extra></extra>",
            customdata=df["Weight"]
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Add verification for perfect scores
    all_perfect = True
    all_section_scores = []
    
    for section_name, score in results["section_scores"].items():
        if score is not None:  # Skip sections with no applicable questions
            all_section_scores.append(score)
            if score < 1.0:
                all_perfect = False
                break
    
    if all_perfect and results['overall_score'] < 100:
        st.warning("""
        **Note:** All your section scores show full compliance, but the overall score may be slightly below 100% 
        due to weighting factors or rounding. Your organization has effectively achieved full compliance.
        """)

    # Create dataframe for section scores table
    section_data = []
    none_score_sections = []
    
    for section, score in results["section_scores"].items():
        if score is not None:  # Skip sections with no applicable questions
            status = "High Risk" if score < 0.6 else ("Moderate Risk" if score < 0.75 else "Compliant")
            section_data.append({
                "Section": section,
                "Score (%)": f"{score * 100:.1f}%",
                "Weight": f"{next((s['weight'] * 100 for s in get_questionnaire(st.session_state.selected_regulation, st.session_state.selected_industry)['sections'] if s['name'] == section), 0):.1f}%",
                "Status": status
            })
        else:
            none_score_sections.append(section)
    
    df = pd.DataFrame(section_data)
    
    # Display sections with None scores
    if none_score_sections:
        st.info("The following sections have no score because all questions were marked as 'Not applicable' or had no responses:")
        for section in none_score_sections:
            st.write(f"• {section}")
    
    # Add Recommended Actions section here
    st.subheader("Recommended Actions")
    if results.get("improvement_priorities"):
        for i, area in enumerate(results["improvement_priorities"][:3]):
            with st.expander(f"Priority {i+1}: {area}"):
                if area in results["recommendations"] and results["recommendations"][area]:
                    for rec in results["recommendations"][area]:
                        st.write(f"• {rec}")
                else:
                    st.write("No specific recommendations available for this area.")
    else:
        st.info("No specific priority actions identified based on your assessment results.")
    
    # Add INFA Diagram
    st.subheader("DPDP Implementation Framework")
    html_path = os.path.join(config.BASE_DIR, "Assets", "INFA.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        # Use CSS for responsive scaling with container adjustments
        centered_html = f"""
        <style>
        .diagram-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 10px;
            margin-bottom: -60px;
            overflow: auto;
            min-height: 500px;
        }}
        .diagram-content {{
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .diagram-content svg {{
            max-width: 100%;
            height: auto;
            transform-origin: center;
            transition: transform 0.3s ease;
        }}
        @media (max-width: 1200px) {{
            .diagram-container {{
                min-height: 450px;
            }}
            .diagram-content svg {{
                transform: scale(0.85);
            }}
        }}
        @media (max-width: 992px) {{
            .diagram-container {{
                min-height: 400px;
            }}
            .diagram-content svg {{
                transform: scale(0.75);
            }}
        }}
        @media (max-width: 768px) {{
            .diagram-container {{
                min-height: 350px;
            }}
            .diagram-content svg {{
                transform: scale(0.65);
            }}
        }}
        @media (max-width: 576px) {{
            .diagram-container {{
                min-height: 300px;
            }}
            .diagram-content svg {{
                transform: scale(0.5);
            }}
        }}
        </style>
        <div class="diagram-container">
            <div class="diagram-content">
                {html_content}
            </div>
        </div>
        """
        st.components.v1.html(centered_html, height=700, scrolling=True)
    else:
        st.warning("DPDP Implementation Framework diagram not found.")
    
    # Add CLAIRE Diagram with reduced spacing
    st.markdown('<div style="margin-top: -60px;"></div>', unsafe_allow_html=True)
    st.subheader("Informatica CLAIRE Framework")
    claire_path = os.path.join(config.BASE_DIR, "Assets", "CLAIRE.html")
    if os.path.exists(claire_path):
        with open(claire_path, "r", encoding="utf-8") as f:
            claire_content = f.read()
        # Use modified styling for CLAIRE diagram with responsive scaling
        centered_html = f"""
        <style>
        .claire-container {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            padding: 10px;
            margin-top: -40px;
            overflow: auto;
            min-height: 500px;
        }}
        .claire-content {{
            position: relative;
            width: 100%;
            height: 100%;
            display: flex;
            justify-content: center;
            align-items: center;
        }}
        .claire-content svg {{
            max-width: 100%;
            height: auto;
            transform-origin: center;
            transition: transform 0.3s ease;
        }}
        @media (max-width: 1200px) {{
            .claire-container {{
                min-height: 450px;
            }}
            .claire-content svg {{
                transform: scale(0.85);
            }}
        }}
        @media (max-width: 992px) {{
            .claire-container {{
                min-height: 400px;
            }}
            .claire-content svg {{
                transform: scale(0.75);
            }}
        }}
        @media (max-width: 768px) {{
            .claire-container {{
                min-height: 350px;
            }}
            .claire-content svg {{
                transform: scale(0.65);
            }}
        }}
        @media (max-width: 576px) {{
            .claire-container {{
                min-height: 300px;
            }}
            .claire-content svg {{
                transform: scale(0.5);
            }}
        }}
        </style>
        <div class="claire-container">
            <div class="claire-content">
                {claire_content}
            </div>
        </div>
        """
        st.components.v1.html(centered_html, height=600, scrolling=True)
    else:
        st.warning("CLAIRE Framework diagram not found.")
    # --- End of commented out section ---

    # Add Not Applicable answers section
    st.markdown('<div style="margin-top: -60px;"></div>', unsafe_allow_html=True)
    st.subheader("Answers Marked as \"Not Applicable\"")
    
    # Get questionnaire for reference
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    
    # Find all "Not applicable" responses
    na_responses = []
    for section_idx, section in enumerate(questionnaire["sections"]):
        for q_idx, question in enumerate(section["questions"]):
            response_key = f"s{section_idx}_q{q_idx}"
            response = st.session_state.responses.get(response_key)
            
            if isinstance(response, str) and "not applicable" in response.lower():
                # Get question text
                q_text = question.get("text", question) if isinstance(question, dict) else question
                na_responses.append({
                    "section": section["name"],
                    "question": q_text,
                    "question_number": f"Q{q_idx + 1}"
                })
    
    if na_responses:
        with st.expander("View Not Applicable Responses", expanded=False):
            for item in na_responses:
                # Strip HTML links from question text
                clean_question = re.sub(r'\s*\[<a.*?</a>\]', '', item['question']).strip()
                st.markdown(f"""
                **{item['section']} - {item['question_number']}**  
                {clean_question}
                """)
                st.markdown("---")
    else:
        with st.expander("View Not Applicable Responses", expanded=False):
            st.info("No questions were marked as Not Applicable.")
    
    # Add AI Analysis section header/intro
    st.markdown(get_ai_analysis_css(), unsafe_allow_html=True)
    st.markdown("""
        <div class="ai-analysis-container-header"> <!-- Use a different class if needed -->
            <h3 class="ai-analysis-header">🤖 AI Analysis Summary</h3>
            <p class="ai-analysis-text">
                AI-powered analysis of your compliance assessment:
            </p>
        </div>
    """, unsafe_allow_html=True)

    # --- AI Report Generation and Display ---
    ai_report_content_placeholder = st.empty() # Create a placeholder

    # Initialize cached report key if not exists
    if 'cached_ai_report' not in st.session_state:
        st.session_state.cached_ai_report = None

    # Check if we should regenerate the report
    should_regenerate = (
        st.session_state.cached_ai_report is None or
        st.session_state.get('ai_report_generated') is False
    )

    ai_report = None # Ensure ai_report is defined

    with st.spinner("🔄 Generating detailed AI analysis...") if should_regenerate else st.container():
        try:
            if should_regenerate:
                generated_report = generate_natural_language_report(st.session_state.results)
                if generated_report and not generated_report.startswith("Error:"):
                    # Clean up the report text
                    cleaned_report = generated_report.strip()
                    cleaned_report = cleaned_report.replace("```markdown", "").replace("```", "")
                    cleaned_report = re.sub(r'</?div[^>]*>', '', cleaned_report, flags=re.IGNORECASE)
                    cleaned_report = cleaned_report.replace("[Insert Date]", st.session_state.get('assessment_date', 'Unknown Date'))
                    cleaned_report = cleaned_report.replace("[Insert Organization Name]", st.session_state.get('organization_name', 'Unknown Organization'))

                    st.session_state.cached_ai_report = cleaned_report
                    st.session_state.ai_report_generated = True
                    ai_report = cleaned_report # Use the newly generated report
                else:
                    st.error("Failed to generate AI analysis. Please try again.")
                    st.session_state.cached_ai_report = None
            else:
                 ai_report = st.session_state.cached_ai_report # Use cached report

            # Display the report content in the placeholder
            if ai_report:
                # Add the previous CSS styling
                st.markdown("""
                    <style>
                    .ai-analysis-container {
                        background: rgba(255, 255, 255, 0.05);
                        padding: 20px;
                        border-radius: 10px;
                        margin: 20px 0;
                    }
                    .ai-analysis-container h1 {
                        font-size: 1.8em;
                        font-weight: bold;
                        color: white;
                        margin-bottom: 25px;
                        padding-bottom: 15px;
                        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                    }
                    .ai-analysis-container .report-header {
                        font-size: 1.8em;
                        font-weight: bold;
                        color: white;
                        margin-bottom: 25px;
                        padding-bottom: 15px;
                        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
                    }
                    .ai-analysis-container h2 {
                        color: #6fa8dc;
                        font-size: 1.5em;
                        margin-top: 20px;
                        margin-bottom: 15px;
                    }
                    .ai-analysis-container h3 {
                        color: #6fa8dc;
                        font-size: 1.3em;
                        margin-top: 20px;
                        margin-bottom: 15px;
                    }
                    .ai-analysis-container strong {
                        color: #f8aeae;
                    }
                    .ai-analysis-container ul {
                        margin-left: 20px;
                        margin-bottom: 15px;
                    }
                    .ai-analysis-container li {
                        margin-bottom: 10px;
                        line-height: 1.6;
                    }
                    .ai-analysis-container p {
                        line-height: 1.6;
                        margin-bottom: 15px;
                    }
                    </style>
                """, unsafe_allow_html=True)
                    
                # Process the report to fix the first line
                lines = ai_report.split('\n')
                processed_lines = []
                
                # Check if the first line starts with # and contains compliance scores
                if lines and lines[0].startswith('# '):
                    # Extract the header text and handle special formatting
                    header_line = lines[0].replace('# ', '')
                    
                    # Extract title and scores
                    if "**Overall Compliance Score:" in header_line:
                        # Split into title and scores
                        parts = header_line.split("**Overall")
                        title = parts[0].strip()
                        scores_part = "Overall" + parts[1]
                        
                        # Format scores with better styling
                        scores_part = scores_part.replace("**Overall Compliance Score:", "<span style='color: #FF6B6B'>Overall Compliance Score:")
                        scores_part = scores_part.replace("**Compliance Level:", "<span style='color: #FF6B6B'>Compliance Level:")
                        scores_part = scores_part.replace("**Non-Compliant**", "<span style='color: #FF4B4B; font-weight: bold'>Non-Compliant</span>")
                        scores_part = scores_part.replace("**", "</span>")
                        
                        # Create formatted header with proper styling
                        formatted_header = f"""<div class="report-header">
                            <div style="font-size: 1.8em; color: white; margin-bottom: 15px;">{title}</div>
                            <div style="font-size: 1.1em; line-height: 1.6;">{scores_part}</div>
                        </div>"""
                        
                        # Add the formatted header first
                        processed_lines.append(formatted_header)
                        # Then add the remaining lines
                        processed_lines.extend(lines[1:])
                    else:
                        # Fallback for other header formats
                        processed_lines.append(f'<div class="report-header">{header_line}</div>')
                        # Add the remaining lines
                        processed_lines.extend(lines[1:])
                else:
                    # If it doesn't start with #, use the original lines
                    processed_lines.extend(lines)
                
                # Join the processed lines
                processed_report = '\n'.join(processed_lines)
                processed_report = '\n'.join(processed_lines)
                # Wrap the report in the styled container
                st.markdown(f'<div class="ai-analysis-container">{processed_report}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="ai-analysis-container">AI report not available.</div>', unsafe_allow_html=True)


        except Exception as e:
            logger.error(f"Error rendering AI report: {e}")
            st.error("An error occurred while generating the analysis. Please try again.")
            ai_report_content_placeholder.markdown('<div class="ai-analysis-container"><p>Error generating report.</p></div>', unsafe_allow_html=True)
            ai_report = None # Ensure report is None on error


    # --- Download/Regenerate Buttons ---
    if ai_report: # Only show buttons if report exists
        col1, col2 = st.columns([3, 1])
        with col1:
            # Create a row for the buttons with more space between them
            col1, spacer, col2 = st.columns([1, 2, 1])
            
            with col1:
                # Store the report content in session state if not already there
                if 'cached_ai_report' not in st.session_state:
                    st.session_state.cached_ai_report = ai_report

                # Function to generate PDF when download button is clicked
                def get_pdf_data():
                    if 'pdf_data' not in st.session_state:
                        with st.spinner("Generating PDF report..."):
                            try:
                                # Get the original AI report content
                                original_report_content = st.session_state.cached_ai_report
                                if not original_report_content:
                                    st.error("No report content available. Please generate a report first.")
                                    return None
                                
                                # Get organization name, default if not found
                                org_name = st.session_state.get('organization_name', 'Unknown Organization')
                                current_date = datetime.now().strftime("%B %d, %Y")
                                
                                # Get the logo path and verify it exists
                                logo_path = os.path.join(config.BASE_DIR, "Assets", "@logo.png")
                                logger.info(f"Looking for logo at: {logo_path}")
                                
                                # Create header content
                                header_content = ""
                                if os.path.exists(logo_path):
                                    with open(logo_path, "rb") as f:
                                        logo_base64 = base64.b64encode(f.read()).decode()
                                    
                                    header_content = f"""
<div style="text-align: center; margin-bottom: 30px;">
    <img src="data:image/png;base64,{logo_base64}" style="max-width: 200px; margin-bottom: 20px;">
    <h1 style="color: #333; margin: 0;">{org_name}</h1>
    <p style="color: #666; margin: 5px 0;">Compliance Assessment Report</p>
    <p style="color: #666; margin: 5px 0;">Generated on: {current_date} by DataINFA</p>
</div>

---

"""
                                else:
                                    # Create header without logo
                                    header_content = f"""
<div style="text-align: center; margin-bottom: 30px;">
    <h1 style="color: #333; margin: 0;">{org_name}</h1>
    <p style="color: #666; margin: 5px 0;">Compliance Assessment Report</p>
    <p style="color: #666; margin: 5px 0;">Generated on: {current_date} by DataINFA</p>
</div>

---

"""
                                
                                # Combine header with the report content
                                report_with_header = f"{header_content}{original_report_content}"
                                
                                # Generate PDF
                                pdf_data = convert_markdown_to_pdf(report_with_header, org_name)
                                if pdf_data:
                                    st.session_state.pdf_data = pdf_data
                                    return pdf_data
                            except Exception as e:
                                logger.error(f"Error generating PDF: {e}")
                                st.error("An error occurred while generating the PDF. Please try again.")
                                return None
                    return st.session_state.get('pdf_data')

                # Download button that triggers PDF generation only when clicked
                if st.download_button(
                    label="📥 Download Report (PDF)",
                    data=get_pdf_data(),
                    file_name=f"Questionnaire_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                    mime="application/pdf",
                    help="Download the AI-generated analysis as a PDF document",
                    use_container_width=False,
                    key="download_pdf_button",
                    disabled=not st.session_state.get('cached_ai_report')
                ):
                    # Clear the cached PDF data after successful download
                    if 'pdf_data' in st.session_state:
                        del st.session_state.pdf_data
            
            with col2:
                if st.button("🔄 Regenerate", help="Generate a new AI analysis", use_container_width=False):
                    st.session_state.ai_report_generated = False
                    st.rerun()
    else:
        # Show retry button if generation failed or report is None
        if st.button("🔄 Retry Analysis Generation"):
            st.session_state.ai_report_generated = False
            st.rerun()


   
    def get_image_base64(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    # Get all image data first
    img1_base64 = get_image_base64(os.path.join(config.BASE_DIR, "Assets", "data-integration-tools-mq.jpg"))
    img2_base64 = get_image_base64(os.path.join(config.BASE_DIR, "Assets", "ipaas-mq.jpg"))
    img3_base64 = get_image_base64(os.path.join(config.BASE_DIR, "Assets", "data-governance-mq.jpg"))
    img4_base64 = get_image_base64(os.path.join(config.BASE_DIR, "Assets", "data-quality-mq.png"))
    # Add Gartner Magic Quadrant section with hover effect
    st.markdown("""
        <style>
        .magic-quadrant-section {
            background: #1E1E1E;
            padding: 20px;
                        border-radius: 10px;
            margin: 40px 0;
                    }
        .magic-quadrant-header {
                        color: white;
            text-align: center;
            font-size: 24px;
            font-weight: bold;
            margin-bottom: 20px;
        }
        .magic-quadrant-grid {
            display: flex;
            justify-content: space-between;
            gap: 20px;
                        padding: 10px;
            flex-wrap: nowrap;
        }
        .quadrant-item {
            flex: 1;
            min-width: 200px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }
        .magic-quadrant-title {
            color: white;
            text-align: center;
            margin-bottom: 10px;
            font-size: 14px;
            font-weight: 500;
            height: 40px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
        }
        .new-badge {
            background: #8A2BE2;
            color: white;
            padding: 2px 8px;
            border-radius: 15px;
            font-size: 10px;
            font-weight: bold;
            margin-left: 6px;
        }
        /* Image container styles */
        .image-container {
            position: relative;
            width: 220px;
            height: 220px;
            transition: transform 0.3s ease;
            cursor: pointer;
        }
        .image-container img {
            width: 100%;
            height: 100%;
            object-fit: contain;
            transition: all 0.3s ease;
            background: white;
            border-radius: 8px;
        }
        .image-container:hover {
            position: relative;
            z-index: 1000;
        }
        .image-container:hover img {
            transform: scale(2.5);
            box-shadow: 0 0 30px rgba(0,0,0,0.7);
        }
        /* Add styles for the link */
        .quadrant-link {
            text-decoration: none;
                        display: block;
        }
        </style>
    """, unsafe_allow_html=True)

    # Render the Magic Quadrant section
    st.markdown(f"""
        <div class="magic-quadrant-section">
            <div class="magic-quadrant-header">
                <span style="color: #FFA500;">Informatica Leadership in Gartner Magic Quadrant</span>
            </div>
            <div class="magic-quadrant-grid">
                <div class="quadrant-item">
                    <div class="magic-quadrant-title">Data Integration Tools</div>
                    <a href="https://www.informatica.com/lp/gartner-leadership.html" target="_blank" class="quadrant-link">
                        <div class="image-container">
                            <img src="data:image/jpeg;base64,{img1_base64}" alt="Data Integration Tools">
                        </div>
                    </a>
                </div>
                <div class="quadrant-item">
                    <div class="magic-quadrant-title">Integration Platform as a Service (iPaaS)</div>
                    <a href="https://www.informatica.com/lp/gartner-leadership.html" target="_blank" class="quadrant-link">
                        <div class="image-container">
                            <img src="data:image/jpeg;base64,{img2_base64}" alt="iPaaS">
                        </div>
                    </a>
                </div>
                <div class="quadrant-item">
                    <div class="magic-quadrant-title">Data and Analytics Governance Platforms<span class="new-badge">NEW</span></div>
                    <a href="https://www.informatica.com/lp/gartner-leadership.html" target="_blank" class="quadrant-link">
                        <div class="image-container">
                            <img src="data:image/jpeg;base64,{img3_base64}" alt="Data Governance">
                        </div>
                    </a>
                </div>
                <div class="quadrant-item">
                    <div class="magic-quadrant-title">Augmented Data Quality Solutions<span class="new-badge">NEW</span></div>
                    <a href="https://www.informatica.com/lp/gartner-leadership.html" target="_blank" class="quadrant-link">
                        <div class="image-container">
                            <img src="data:image/jpeg;base64,{img4_base64}" alt="Data Quality">
                        </div>
                    </a>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    # Add penalties section with header
    st.markdown(get_penalties_section_css(), unsafe_allow_html=True)
    st.markdown("""
        <div class="penalties-container">
            <h4 class="penalties-header">🚨 Potential Penalties Under DPDP</h4>
            <p class="penalties-text">
                The Digital Personal Data Protection Act, 2023 prescribes significant penalties for non-compliance:
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Create the penalties data with enhanced styling
    penalties_data = {
        "Nature of violation/breach": [
            "Failure of data fiduciary to take reasonable security safeguards to prevent personal data breach",
            "Failure to notify Data Protection Board of India and affected data principals in case of personal data breach",
            "Non-fulfilment of additional obligations in relation to personal data of children",
            "Non-fulfilment of additional obligations by significant data fiduciaries",
            "Non-compliance with duties of data principals",
            "Breach of any term of voluntary undertaking accepted by the Data Protection Board",
            "Residuary penalty"
        ],
        "Penalty": [
            "May extend to INR 250 crores",
            "May extend to INR 200 crores",
            "May extend to INR 200 crores",
            "May extend to INR 150 crores",
            "May extend to INR 10,000",
            "Up to the extent applicable",
            "May extend to INR 50 crores"
        ]
    }
    # Create DataFrame
    penalties_df = pd.DataFrame(penalties_data)
    
    # Apply custom styling with improved aesthetics
    st.markdown(get_penalties_table_css(), unsafe_allow_html=True)
    
    # Display the table with custom formatting
    st.markdown(penalties_df.to_html(classes='penalties-table', escape=False, index=False), unsafe_allow_html=True)
    
    # Add enhanced note about penalties and FAQ section
    st.markdown("""
        <div class='penalties-note'>
            These penalties are prescribed under the Digital Personal Data Protection Act, 2023. 
        </div>
    """, unsafe_allow_html=True)
    # --- End of commented out section ---
    
    # --- Temporarily comment out Countdown section for debugging ---
    # Add the countdown timer with reloader
    st.markdown(get_countdown_section_css(), unsafe_allow_html=True)
    st.markdown("""
        <div class="countdown-container">
            <h3 class="countdown-header">⏰ Time Left to Achieve DPDP Compliance</h3>
            <p class="countdown-text">
                Your organization must achieve compliance before the tentative deadline: December 31, 2025
            </p>
        </div>
    """, unsafe_allow_html=True)
    # --- End of commented out section ---
    
    # --- End of commented out section ---

    # --- Temporarily comment out final columns/buttons for debugging ---
    col1, col2, col3 = st.columns(3)
    
    with col2:
        # Add Quick AI Data Discovery button
        st.markdown(get_discovery_button_css(), unsafe_allow_html=True)
        
        if st.button("🔍 Ready for a Quick AI Data Discovery ?", use_container_width=True):
            st.session_state.current_page = 'discovery'
            st.rerun()
        
        st.write("")
        st.write("")
        
    with col1: 
        # Download buttons - only show Excel download for admin users
        if st.session_state.get('is_admin', False):
            # Initialize assessment_type if not present
            if 'assessment_type' not in st.session_state:
                st.session_state.assessment_type = 'DPDP'  # Default to DPDP assessment type
            
        excel_link = generate_excel_download_link(
            results,
            st.session_state.organization_name,
            st.session_state.assessment_date,
                st.session_state.assessment_type,
                st.session_state.selected_industry  # Add the missing industry parameter
        )
        st.markdown(excel_link, unsafe_allow_html=True)

def render_recommendations():
    """Render the detailed recommendations page"""
    if not st.session_state.assessment_complete or not st.session_state.results:
        st.warning("Please complete the assessment to view recommendations")
        if st.button("Go to Assessment", type="primary"):
            st.session_state.current_page = 'assessment'
            st.rerun()
        return
    
    results = st.session_state.results
    
    st.header(f"{format_regulation_name(st.session_state.selected_regulation)} Recommendations")
    st.subheader(f"For: {st.session_state.organization_name}")
    
    # Use the consolidated recommendation organization function
    from recommendation_engine import organize_recommendations_by_priority
    recommendations_by_priority = organize_recommendations_by_priority(results)
    
    # Display recommendations by priority
    if recommendations_by_priority['high']:
        st.subheader("High Priority Recommendations", anchor="high-priority")
        st.markdown("These areas require immediate attention to address significant compliance gaps.")
        for item in recommendations_by_priority['high']:
            with st.expander(f"{item['section']} (Score: {item['score']:.1f}%)"):
                for rec in item["recommendations"]:
                    st.write(f"• {rec}")
    
    if recommendations_by_priority['medium']:
        st.subheader("Medium Priority Recommendations", anchor="medium-priority")
        st.markdown("These areas should be addressed after high priority items to improve compliance.")
        for item in recommendations_by_priority['medium']:
            with st.expander(f"{item['section']} (Score: {item['score']:.1f}%)"):
                for rec in item["recommendations"]:
                    st.write(f"• {rec}")
    
    if recommendations_by_priority['low']:
        st.subheader("Low Priority Recommendations", anchor="low-priority")
        st.markdown("These areas are mostly compliant but could benefit from minor improvements.")
        for item in recommendations_by_priority['low']:
            with st.expander(f"{item['section']} (Score: {item['score']:.1f}%)"):
                for rec in item["recommendations"]:
                    st.write(f"• {rec}")
    
    if not (recommendations_by_priority['high'] or recommendations_by_priority['medium'] or recommendations_by_priority['low']):
        st.info("No specific recommendations available based on your assessment responses.")
    
    # Add detailed context for recommendations if available
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    # Import and use the enhanced recommendations functionality
    from recommendation_engine import get_recommendation_context
    recommendation_context = get_recommendation_context(questionnaire, st.session_state.responses)
    
    if recommendation_context:
        st.subheader("Recommendation Context")
        st.write("Expand each section to see detailed context for the recommendations")
        
        for section, contexts in recommendation_context.items():
            score = results["section_scores"].get(section)
            
            if score is None:
                continue
                
            priority = "high" if score < 0.6 else ("medium" if score < 0.75 else "low")
            priority_emoji = "🔴" if priority == "high" else ("🟠" if priority == "medium" else "🟢")
            
            with st.expander(f"{priority_emoji} {section} - {len(contexts)} recommendations"):
                for context in contexts:  # Fixed missing 'in contexts'
                    st.markdown(f"##### Question {context['question_id']}")
                    st.write(f"**Q:** {context['question_text']}")
                    st.write(f"**Your Response:** {context['response']}")
                    st.markdown(f"**Recommendation:** {context['recommendation']}")
                    st.markdown("---")
    
    # The AI Analysis section previously here has been removed.

def convert_markdown_to_pdf(markdown_content: str, organization_name: str = "Report") -> bytes | None:
    """Convert markdown content to PDF format using the markdown-pdf library."""
    output_file = None
    try:
        # Initialize PDF object with TOC level 2 (headings ##)
        pdf = MarkdownPdf(toc_level=2)

        # Get the logo path and verify it exists
        logo_path = os.path.join(config.BASE_DIR, "Assets", "@logo.png")
        logger.info(f"Looking for logo at: {logo_path}")
        
        # Create a header with the logo if it exists
        header_content = ""
        if os.path.exists(logo_path):
            # Convert logo to base64
            with open(logo_path, "rb") as f:
                logo_base64 = base64.b64encode(f.read()).decode()
            
            # Add header with logo and styling
            header_content = f"""
<div style="text-align: center; margin-bottom: 30px;">
    <img src="data:image/png;base64,{logo_base64}" style="max-width: 200px; margin-bottom: 20px;">
    <h1 style="color: #333; margin: 0;">{organization_name}</h1>
    <p style="color: #666; margin: 5px 0;">AI Analysis Report</p>
    <p style="color: #666; margin: 5px 0;">Generated on: {datetime.now().strftime('%B %d, %Y')} by DataINFA</p>
</div>

---

"""
        # Combine header with the main content
        full_content = header_content + markdown_content

        # Add the entire markdown content as one section
        pdf.add_section(Section(full_content, toc=True))

        # Set PDF metadata
        pdf.meta["title"] = f"{organization_name} - AI Analysis Report"
        pdf.meta["author"] = config.APP_TITLE
        pdf.meta["subject"] = "DPDP Compliance Assessment Report"
        pdf.meta["keywords"] = "compliance, DPDP, assessment, analysis"
        pdf.meta["creator"] = "DataInfa Assessment Tool"

        # Create a temporary file path for the PDF output
        with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as temp_pdf_file:
            output_file = temp_pdf_file.name
            logger.info(f"Temporary PDF output path: {output_file}")

        # Save the PDF to the temporary file
        logger.info(f"Attempting conversion and save to: {output_file}")
        pdf.save(output_file)
        logger.info(f"markdown-pdf save operation completed for {output_file}")

        # Check if the output file was created and read it
        if os.path.exists(output_file):
            logger.info(f"Output PDF file exists: {output_file}")
            with open(output_file, 'rb') as f:
                pdf_content = f.read()
            logger.info(f"Successfully read {len(pdf_content)} bytes from {output_file}")
            return pdf_content
        else:
            logger.error(f"Conversion failed. Output PDF file not found: {output_file}")
            st.error("Error: Failed to generate PDF file.")
            return None

    except Exception as e:
            # Catching a general exception as specific errors from markdown-pdf might vary
            logger.error(f"Error during markdown-pdf generation: {e}", exc_info=True)
            st.error(f"An error occurred during PDF generation: {e}")
            return None
    finally:
        # Clean up temporary PDF file
        if output_file and os.path.exists(output_file):
            try:
                os.unlink(output_file)
                logger.info(f"Cleaned up temporary PDF file: {output_file}")
            except Exception as e:
                logger.error(f"Error deleting temporary PDF file {output_file}: {e}")

def render_admin_page():
    """Render the admin page"""
    st.title("Admin Dashboard")
    if not st.session_state.get('is_admin', False):
        st.error("Access denied. Admin privileges required.")
        return
    
    st.subheader("Token Management")
    token_tabs = st.tabs(["Generate Token", "View Tokens", "Revoke Token"])
    
    # Generate Token Tab
    with token_tabs[0]:
        st.write("Create a new access token for an organization")
        
        # Organization name with clear label
        st.markdown("#### Organization Details")
        org_name = st.text_input(
            "Organization Name *", 
            key="new_org_name", 
            placeholder="Enter organization name",
            help="The organization this token will be issued to"
        )
        
        # Add Generated By field
        generated_by = st.text_input(
            "Generated By *", 
            key="generated_by",
            value=st.session_state.get("admin_user", "Admin"),
            placeholder="Enter your name",
            help="Your name or identifier as the token generator"
        )
        
        # Expiry date settings with better alignment
        st.markdown("#### Token Expiration")
        
        # Apply custom CSS for expiry box
        st.markdown(get_expiry_box_css(), unsafe_allow_html=True)
        
        # Force single line with container_width and custom height
        container = st.container()
        with container:
            col1, col2 = st.columns([1, 1])
            
            with col1:
                expiry_days = st.number_input(
                    "Token validity (days)", 
                    min_value=1, 
                    max_value=365, 
                    value=5, 
                    key="expiry_days",
                    help="Number of days this token will remain valid"
                )
            
            with col2:
                expiry_date = (datetime.now() + timedelta(days=expiry_days)).strftime("%Y-%m-%d")
                st.markdown(f"""
                <div class="expiry-box">
                    <span style="font-weight: bold;">Expiry date:</span> {expiry_date}
                </div>
                """, unsafe_allow_html=True)
        
        # Generate token button
        if st.button("Generate Token", key="gen_token_btn", type="primary", use_container_width=True):
            if org_name:
                try:
                    # Set token expiry in session state for token_storage to use
                    import token_storage
                    token_storage.TOKEN_EXPIRY_DAYS = expiry_days
                    
                    # Create secure directory if it doesn't exist
                    if not os.path.exists('secure'):
                        os.makedirs('secure', exist_ok=True)
                    
                    # Generate token with the organization name and generated by info
                    new_token = generate_token(org_name, generated_by)
                    if new_token:
                        st.success(f"Token successfully generated for {org_name}!")
                        
                        # Get current timestamp and format it
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
                        # Display the token in a more prominent way with updated styling
                        st.markdown(f"""
                        <style>
                        .token-box {{
                            padding: 20px;
                            background: linear-gradient(135deg, #1a2980, #26d0ce);
                            border: 1px solid #4a90e2;
                            border-radius: 8px;
                            margin: 15px 0;
                            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                        }}
                        .token-box h3 {{
                            color: white;
                            margin-bottom: 15px;
                            font-size: 1.4rem;
                            text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
                        }}
                        .token-value {{
                            font-family: monospace;
                            font-size: 1.2em;
                            font-weight: bold;
                            padding: 15px;
                            background-color: rgba(255, 255, 255, 0.9);
                            color: #1a2980;
                            border-radius: 5px;
                            word-wrap: break-word;
                            margin-bottom: 15px;
                            border-left: 4px solid #26d0ce;
                        }}
                        .token-details {{
                            margin-top: 15px;
                            font-size: 1em;
                        }}
                        .token-details table {{
                            width: 100%;
                        }}
                        .token-details td {{
                            padding: 6px 0;
                        }}
                        .token-details td:first-child {{
                            font-weight: bold;
                            width: 40%;
                            color: #1a2980;
                        }}
                        </style>
                        <div class="token-box">
                            <h3>🔑 Token Generated</h3>
                            <div class="token-value">{new_token}</div>
                            <div class="token-details">
                                <table>
                                    <tr>
                                        <td>Organization:</td>
                                        <td>{org_name}</td>
                                    </tr>
                                    <tr>
                                        <td>Generated By:</td>
                                        <td>{generated_by}</td>
                                    </tr>
                                    <tr>
                                        <td>Generated on:</td>
                                        <td>{current_time}</td>
                                    </tr>
                                    <tr>
                                        <td>Expires on:</td>
                                        <td>{expiry_date}</td>
                                    </tr>
                                    <tr>
                                        <td>Valid for:</td>
                                        <td>{expiry_days} days</td>
                                    </tr>
                                </table>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # Add copy instructions and security notice below
                        st.info("⚠️ **Copy this token now.** For security reasons, it cannot be retrieved later.")
                        st.warning("**Security Notice:** This token grants access to the assessment platform. Store and transmit it securely.")
                    else:
                        st.error("Failed to generate token. Check logs for details.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter an organization name")

    # View Tokens Tab
    with token_tabs[1]:
        st.write("View existing access tokens")
        if st.button("Refresh Token List", key="refresh_tokens"):
            st.rerun()
        try:
            # Get tokens from secure/tokens.csv
            from token_storage import TOKENS_FILE
            if os.path.exists(TOKENS_FILE):
                # Read the actual CSV structure first to determine the column format
                with open(TOKENS_FILE, 'r') as f:
                    first_line = f.readline().strip()
                    logger.info(f"CSV Header: {first_line}")
                # Read CSV file with correct columns
                tokens_df = pd.read_csv(TOKENS_FILE)
                logger.info(f"CSV columns detected: {list(tokens_df.columns)}")
                
                if not tokens_df.empty:
                    # Rename columns if needed for display consistency
                    column_mapping = {}
                    if 'organization_name' in tokens_df.columns:
                        column_mapping['organization_name'] = 'organization'
                    # Apply column renames if any mappings exist
                    if column_mapping:
                        tokens_df = tokens_df.rename(columns=column_mapping)
                    
                    # Format dates for better readability
                    date_columns = ['created_at', 'expires_at']
                    for col in date_columns:
                        if col in tokens_df.columns:
                            try:
                                # Convert to datetime with flexible parsing
                                tokens_df[col] = pd.to_datetime(tokens_df[col], errors='coerce')
                            except Exception as e:
                                logger.warning(f"Error formatting {col}: {e}")
                    
                    # Add days remaining column
                    if 'expires_at' in tokens_df.columns:
                        current_time = datetime.now()
                        days_remaining = []
                        
                        # Process each row individually
                        for _, row in tokens_df.iterrows():
                            try:
                                if pd.notna(row['expires_at']):
                                    expires = pd.to_datetime(row['expires_at'], errors='coerce')
                                    if pd.notna(expires):
                                        delta = expires - current_time
                                        days = delta.days
                                        days_remaining.append("Expired" if days < 0 else f"{days} days")
                                    else:
                                        days_remaining.append("Unknown")
                                else:
                                    days_remaining.append("Unknown")
                            except Exception as e:
                                logger.warning(f"Error calculating days remaining: {e}")
                                days_remaining.append("Unknown")
                                
                        tokens_df['Days Remaining'] = days_remaining
                    
                    # Define columns to display, make sure they exist in the dataframe
                    preferred_columns = ['organization', 'token', 'generated_by', 'created_at', 'expires_at', 'Days Remaining']
                    display_columns = [col for col in preferred_columns if col in tokens_df.columns]
                    
                    # Final display column renames for better presentation
                    column_renames = {
                        'organization': 'Organization',
                        'token': 'Token',
                        'generated_by': 'Generated By',
                        'created_at': 'Created At',
                        'expires_at': 'Expires At'
                    }
                    # Only select and rename columns that exist
                    tokens_df = tokens_df[display_columns].rename(columns={col: column_renames.get(col, col) for col in display_columns})
                    st.dataframe(tokens_df, use_container_width=True)
                else:
                    st.info("No tokens found")
            else:
                st.info("No tokens have been created yet")
        except Exception as e:
            st.error(f"Error loading tokens: {str(e)}")
            logger.error(f"Token loading error: {str(e)}", exc_info=True)

    # Revoke Token Tab
    with token_tabs[2]:
        st.write("Revoke an existing access token")
        token_to_revoke = st.text_input("Enter token to revoke", key="revoke_token_input")
        if st.button("Revoke Token", key="revoke_btn", type="primary"):
            if token_to_revoke:
                try:
                    # Use imported function
                    if revoke_token(token_to_revoke):
                        st.success(f"Token revoked successfully!")
                    else:
                        st.error("Failed to revoke token. Token may not exist.")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
            else:
                st.warning("Please enter a token to revoke")

    # Token Maintenance Section
    st.subheader("Maintenance")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Clean up expired tokens", key="cleanup_btn"):
            try:
                count = cleanup_expired_tokens()
                if count > 0:
                    st.success(f"Removed {count} expired tokens")
                else:
                    st.info("No expired tokens found")
            except Exception as e:
                st.error(f"Error during cleanup: {str(e)}")
    with col2:
        if st.button("Export Token Database", key="export_btn"):
            from token_storage import TOKENS_FILE
            if os.path.exists(TOKENS_FILE):
                import base64
                with open(TOKENS_FILE, 'rb') as f:
                    b64 = base64.b64encode(f.read()).decode()
                    href = f'<a href="data:file/csv;base64,{b64}" download="tokens_export.csv">Download CSV</a>'
                    st.markdown(href, unsafe_allow_html=True)
            else:
                st.info("No token database found to export")

    

def auto_fill_responses(auto_fill_type):
    """Auto-fill responses based on the selected type"""
    if not st.session_state.get('responses'):
        st.session_state.responses = {}
    
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    
    for section_idx, section in enumerate(questionnaire["sections"]):
        for q_idx, question in enumerate(section["questions"]):
            response_key = f"s{section_idx}_q{q_idx}"
            
            if auto_fill_type == "All Compliant":
                st.session_state.responses[response_key] = "Yes"
            elif auto_fill_type == "All Non-Compliant":
                st.session_state.responses[response_key] = "No"
            elif auto_fill_type == "All Partially Compliant":
                st.session_state.responses[response_key] = "Partially"
            elif auto_fill_type == "Random Mix":
                import random
                options = ["Yes", "No", "Partially", "Not applicable"]
                st.session_state.responses[response_key] = random.choice(options)

def render_sidebar():
    """Render the application sidebar"""
    with st.sidebar:
        # --- Inject CSS directly for sidebar buttons --- #
        st.markdown("""
            <style>
                /* Target the button's container within the user content area */
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] {
                    background-color: transparent !important;
                    border: none !important;
                    box-shadow: none !important;
                    padding: 0 !important;
                    margin: 0 !important;
                }

                /* Style the button text itself */
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] > button {
                    width: 100%;
                    padding: 0.5rem 0.75rem; /* Adjust padding */
                    margin: 0.1rem 0; /* Adjust margin */
                    background-color: transparent !important;
                    color: #fafafa;
                    border: none !important;
                    border-radius: 0.3rem;
                    text-align: left;
                    transition: color 0.2s, background-color 0.2s;
                }
                
                /* Hover effect - subtle background */
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] > button:hover:not(:disabled) {
                    background-color: rgba(255, 255, 255, 0.05) !important;
                    color: #6fa8dc !important;
                    border: none !important;
                }

                /* Active/Selected state - left border and highlight */
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] > button:focus,
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] > button:active,
                div[data-testid="stSidebarUserContent"] div[data-testid="stButton"] > button[kind="secondary"] {
                    background-color: rgba(255, 255, 255, 0.08) !important;
                    color: #ffffff !important;
                    border-left: 3px solid #6fa8dc !important;
                    padding-left: calc(0.75rem - 3px) !important; /* Adjust padding for border */
                    }
                    </style>
            """, unsafe_allow_html=True)
        # --- End of CSS Injection --- #

        # Logo container - Now using st.image with updated parameter
        st.markdown("""
            <style>
            [data-testid="stSidebarUserContent"] {
                text-align: center;
            }
            [data-testid="stSidebarUserContent"] [data-testid="stImage"] {
                display: inline-block !important;
                max-width: 200px !important;
                margin: 0 auto !important;
            }
            [data-testid="stSidebarUserContent"] [data-testid="stImage"] img {
                max-width: 200px !important;
                height: auto !important;
                margin: 0 auto !important;
            }
            </style>
        """, unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if os.path.exists(config.LOGO_PATH): 
                st.image(config.LOGO_PATH, use_container_width=False, width=200)
            else:
                st.warning(f"Logo not found at path: {config.LOGO_PATH}")
        
        # Apply custom CSS for navigation menu
        st.markdown(get_section_navigation_css(), unsafe_allow_html=True)
        
        # Make sure we apply common button CSS
        st.markdown(get_common_button_css(), unsafe_allow_html=True)
        
        # Navigation section title
        
        # Check if assessment parameters are filled AND assessment is started
        assessment_ready = (
            st.session_state.organization_name and 
            st.session_state.organization_name.strip() != "" and 
            st.session_state.selected_regulation and
            st.session_state.selected_industry and
            st.session_state.get('assessment_started', False)  # New condition
        )



        # Define navigation items with conditional display
        nav_items = [
            {"label": "Privacy Policy Analyzer", "key": "nav_home", "page": "welcome", "always_show": True},
            {"label": "Assessment", "key": "nav_assessment", "page": "assessment", "show_if_ready": assessment_ready},
            {"label": "AI Report ✨", "key": "nav_report", "page": "report", "show_if": "assessment_complete"},
            {"label": "AI Data Discovery 🪄", "key": "nav_discovery", "page": "discovery", "show_if": "assessment_complete"},
            {"label": "AI Privacy Policy Analyzer 📄", "key": "nav_privacy", "page": "privacy", "always_show": True},
            {"label": "Admin", "key": "nav_admin", "page": "admin", "show_if": "is_admin"},
            {"label": "FAQ", "key": "nav_faq", "page": "faq", "always_show": True}
        ]
        
        # Fix for button rendering
        for item in nav_items:
            should_show = (
                item.get("always_show", False) or 
                (item.get("show_if") and st.session_state.get(item.get("show_if"), False)) or
                (item.get("show_if_ready") and item.get("show_if_ready"))
            )
            if should_show:
                button_type = "secondary" if st.session_state.current_page == item["page"] else "primary"
                if st.button(
                    item["label"], 
                    key=item["key"], 
                    type=button_type, 
                    use_container_width=True
                ):
                    go_to_page(item["page"])

def render_welcome_page():
    """Render the welcome page"""
    # Center all content
    _, center_col, _ = st.columns([1, 2, 1])
    
    with center_col:
        # Create container for form elements
        with st.container():
            st.markdown(get_input_label_css(), unsafe_allow_html=True)
            
            # --- Callback to handle Regulation change --- #
            def handle_regulation_change():
                new_regulation = st.session_state.selected_regulation_key # Use the key from selectbox
                if new_regulation:
                    new_industries = config.get_available_industries(new_regulation)
                    new_industry_options = list(new_industries.keys())
                    if new_industry_options:
                        # Update the session state for industry to the first new option
                        # This ensures the Industry selectbox below will pick up the change
                        if st.session_state.selected_industry not in new_industry_options:
                            st.session_state.selected_industry = new_industry_options[0]
                            logger.info(f"Regulation changed to {new_regulation}, Industry state reset to {st.session_state.selected_industry}")
                    else:
                        if st.session_state.selected_industry is not None:
                            st.session_state.selected_industry = None
                            logger.info(f"Regulation changed to {new_regulation}, Industry state cleared as no options available")
            # --- End Callback --- #
            
            # Organization name with smaller label
            st.markdown('<p class="input-label">Organization Name *</p>', unsafe_allow_html=True)
            org_name = st.text_input(
                "Organization Name",  # Non-empty label
                value=st.session_state.organization_name,
                key="org_name_input",
                placeholder="Enter organization name",
                label_visibility="collapsed"
            )
            
            if org_name != st.session_state.organization_name:
                st.session_state.organization_name = org_name
            
            st.write("")
            
            # Regulation selection with callback
            st.markdown('<p class="input-label">Select Regulation *</p>', unsafe_allow_html=True)
            regulations = config.REGULATIONS
            selected_regulation = st.selectbox(
                "Regulation",  # Non-empty label
                options=list(regulations.keys()),
                label_visibility="collapsed"
            )
            
            # Add some spacing
            st.write("")
            
            # Industry selection with smaller label
            st.markdown('<p class="input-label">Select Industry *</p>', unsafe_allow_html=True)
            industries = config.get_available_industries(selected_regulation)
            industry_options = list(industries.keys())

            # Determine the default index safely
            current_industry_from_state = st.session_state.get('selected_industry')
            default_index = 0
            if current_industry_from_state in industry_options:
                try:
                    default_index = industry_options.index(current_industry_from_state)
                except ValueError:
                    # Should not happen due to the 'in' check, but safeguard anyway
                    logger.warning(f"Industry '{current_industry_from_state}' reported as 'in' options but index lookup failed. Defaulting to 0.")
                    default_index = 0
            elif industry_options:
                 # If the saved industry is not valid for the current regulation, default to the first option
                 logger.info(f"Saved industry '{current_industry_from_state}' not valid for regulation '{selected_regulation}'. Defaulting to '{industry_options[0]}'.")
                 default_index = 0
            else:
                 # Handle case where there are no industries for the selected regulation
                 logger.warning(f"No industries found for regulation '{selected_regulation}'.")
                 default_index = 0 # Or handle appropriately, maybe disable the selectbox

            selected_industry = st.selectbox(
                "Industry",  # Non-empty label
                options=industry_options,
                format_func=lambda x: industries.get(x, x), # Use .get for safety
                key="selected_industry",
                label_visibility="collapsed",
                index=default_index, # Use the safely calculated default index
                
            )
            
            # Add spacing before button
            st.write("")
            st.write("")
            
            # Centered button with fixed width
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button(
                    "Start Assessment",
                    type="primary",
                    use_container_width=True,
                ):
                    if not org_name.strip():
                        st.error("Please enter your organization name before starting the assessment.")
                        return
                    
                    # Reset responses and assessment completion status
                    st.session_state.responses = {}
                    st.session_state.assessment_complete = False
                    st.session_state.results = None
                    st.session_state.current_section = 0
                    st.session_state.assessment_started = True
                    logger.info(f"Starting assessment for {org_name}")
                    go_to_page('assessment')
                    st.rerun()

def render_dashboard():
    """Render the dashboard view"""
    pass

def render_faq():
    """Render the FAQ view"""
    st.markdown(get_faq_css(), unsafe_allow_html=True)
    st.markdown("<h1 class='faq-header'>Frequently Asked Questions</h1>", unsafe_allow_html=True)
    
    for category, faqs in FAQ_DATA.items():
        st.markdown(f"<h2 class='faq-category'>{category}</h2>", unsafe_allow_html=True)
        for question, answer in faqs.items():
            with st.expander(question):
                st.markdown(answer)

def render_data_discovery():
    """Render the data discovery view"""
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to access the data discovery tool")
        if st.button("Go to Assessment", type="primary"):
            st.session_state.current_page = 'assessment'
            st.rerun()
        return
    
    # Add custom CSS for data discovery page
    st.markdown(get_data_discovery_css(), unsafe_allow_html=True)

    st.header("AI Data Discovery")
    
    # Import and use the data discovery functionality
    from data_discovery import analyze_ddl_script, render_findings_section, get_recommendations
    
    # File upload for DDL script
    uploaded_file = st.file_uploader("Upload your database DDL script (SQL or TXT format)", type=['sql', 'txt'])
    
    if uploaded_file is not None:
        try:
            ddl_content = uploaded_file.getvalue().decode("utf-8")
            
            with st.spinner("Analyzing database schema..."):
                findings = analyze_ddl_script(ddl_content)
                
                if "error" in findings:
                    st.error(f"Analysis failed: {findings['error']}")
                else:
                    # Display findings
                    render_findings_section(findings)
                    
                    st.subheader("Recommendations")
                    recommendations = get_recommendations(findings)
                    for rec in recommendations:
                        st.markdown(f"• {rec}")
        except Exception as e:
            st.error(f"Error analyzing file: {str(e)}")
    
    # Show example of what will be analyzed
    with st.expander("What will be analyzed?"):
        st.markdown("""
            Our AI will analyze your database schema to identify:

            **Risk Levels:**
            - 🚨 HIGH RISK (Direct Identifiers)
            - ⚠️ MEDIUM RISK (Indirect Identifiers)
            - ℹ️ LOW RISK (Generic Information)

            **Data Categories:**
            - Personal Identifiers (names, emails, IDs)
            - Financial Information (salary, payment details)
            - Health Information (medical records)
            - Biometric Data (fingerprints, facial data)
            - Digital Identifiers (device IDs, IP addresses)
            - Location Data (addresses, coordinates)
            - Professional Data (employment records)

            The analysis will identify specific table and column names containing sensitive data, their risk levels, and data combinations that could reveal personal information.

            Contact info@datainfa.com for further understanding and DPDP implementation
        """)
        
    st.markdown(get_penalties_note_css(), unsafe_allow_html=True)
    st.markdown("""
        <div class='penalties-note'>
            ℹ️ We never store your data. We only use it to provide you with a report.
        </div>
    """, unsafe_allow_html=True)

def get_compliance_level_color(level):
    """Return color based on compliance level"""
    colors = {
        "Non-Compliant": "#FF4B4B",  # Red
        "Partially Compliant": "#FFA500",  # Orange
        "Mostly Compliant": "#FFD700",  # Gold
        "Fully Compliant": "#4CAF50"  # Green
    }
    return colors.get(level, "#808080")  # Default to gray if level not found

def convert_for_download():
    """Convert report content to a downloadable PDF format.
    Parameters:
        - None
    Returns:
        - bytes: The binary data of the generated PDF if successful, otherwise None.
    Processing Logic:
        - Retrieves the report content and organization name from session state.
        - Adds a header including current date and optional organization logo.
        - Generates a PDF from combined header and report content, displaying success or error messages accordingly."""
    try:
        # Get the original report content from session state
        original_report_content = st.session_state.get('ai_report_content')
        if not original_report_content:
            st.error("No report content available. Please generate a report first.")
            return None

        # Get organization name
        org_name = st.session_state.get('organization_name', 'Organization')
        current_date = datetime.now().strftime("%B %d, %Y")

        # Add header with logo if available
        logo_path = os.path.join(config.BASE_DIR, "Assets", "@logo.png")
        header = f"""#### AI Report generated by DataINFA on: {current_date} for {org_name}

---

"""
        
        # Combine header with the report content
        report_with_header = f"{header}{original_report_content}"
        
        with st.spinner("Generating PDF report..."):
            # Generate PDF
            pdf_data = convert_markdown_to_pdf(report_with_header, org_name)
            if pdf_data:
                st.success("PDF report generated successfully!")
                return pdf_data
            else:
                st.error("Failed to generate PDF report. Please try again.")
                return None
    except Exception as e:
        logger.error(f"Error generating PDF: {e}")
        st.error("An error occurred while generating the PDF. Please try again.")
        return None

# In the main UI section where the download button is rendered:
if st.session_state.get('ai_report_generated', False):
    col1, col2 = st.columns([0.15, 0.85])
    with col1:
        # Generate PDF data first
        pdf_data = convert_for_download() if st.session_state.get('ai_report_content') else None
        
        # Only show download button if we have PDF data
        if pdf_data is not None:
            if st.download_button(
                "📥 Download",
                data=pdf_data,
                file_name=f"AI_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                mime="application/pdf",
                help="Download the report as PDF",
                use_container_width=False
            ):
                pass  # The download will be handled by Streamlit

def render_privacy_policy_analyzer():
    """Render the privacy policy analyzer page"""
    # Add custom CSS for the privacy analyzer page
    st.markdown("""
        <style>
        .privacy-analyzer-container {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .input-option {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 10px 0;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .input-option:hover {
            border-color: #6fa8dc;
            background: rgba(111, 168, 220, 0.1);
        }
        
        /* File uploader styling */
        .stFileUploader {
            background: rgba(255, 255, 255, 0.05) !important;
            padding: 2rem !important;
            border-radius: 10px !important;
            border: 2px dashed rgba(255, 255, 255, 0.2) !important;
            margin: 1rem 0 !important;
            transition: all 0.3s ease !important;
        }
        
        .stFileUploader:hover {
            border-color: #6fa8dc !important;
            background: rgba(111, 168, 220, 0.1) !important;
        }

        /* AI Analysis Results Styling */
        .analysis-results {
            background: rgba(255, 255, 255, 0.05);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
        
        .analysis-results h1 {
            font-size: 1.8em;
            font-weight: bold;
            color: white;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .analysis-results h2 {
            color: #6fa8dc;
            font-size: 1.5em;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        
        .analysis-results h3 {
            color: #6fa8dc;
            font-size: 1.3em;
            margin-top: 20px;
            margin-bottom: 15px;
        }
        
        .analysis-results strong {
            color: #f8aeae;
        }
        
        .analysis-results ul {
            margin-left: 20px;
            margin-bottom: 15px;
        }
        
        .analysis-results li {
            margin-bottom: 10px;
            line-height: 1.6;
        }
        
        .analysis-results p {
            line-height: 1.6;
            margin-bottom: 15px;
        }

        /* Header Styling */
        .page-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .page-header h1 {
            color: white;
            font-size: 2.2em;
            font-weight: bold;
            margin-bottom: 0.5rem;
        }
        
        .page-header p {
            color: rgba(255, 255, 255, 0.7);
            font-size: 1.1em;
        }
        </style>
    """, unsafe_allow_html=True)

    # Page Header
    st.markdown("""
        <div class="page-header">
            <h1>AI Privacy Policy Analyzer</h1>
            <p>Analyze your privacy policy against data protection laws</p>
        </div>
    """, unsafe_allow_html=True)

    # Add compliance law selection
    from privacy_policy_analyzer import PRIVACY_LAWS
    law_options = {config["name"]: key for key, config in PRIVACY_LAWS.items()}
    selected_law = st.selectbox(
        "Select Compliance Law",
        options=list(law_options.keys()),
        help="Choose the data protection law to analyze against"
    )
    selected_law_key = law_options[selected_law]

    # Create tabs for different input methods
    tab1, tab2, tab3 = st.tabs(["Company Name", "Policy URL", "Text File"])
    
    policy_content = None
    policy_url = None

    with tab1:
        st.markdown("""
            <div class="input-option">
                <h3>Enter Company Name</h3>
                <p>We'll automatically find and analyze the company's privacy policy.</p>
            </div>
        """, unsafe_allow_html=True)
        
        company_name = st.text_input("Company Name")
        if company_name and st.button("Find & Analyze Policy", key="find_policy"):
            with st.spinner("Finding privacy policy..."):
                from privacy_policy_analyzer import find_privacy_policy_url, fetch_policy_content, analyze_privacy_policy
                policy_url = find_privacy_policy_url(company_name)
                if policy_url:
                    st.info(f"Found privacy policy at: {policy_url}")
                    policy_content = fetch_policy_content(policy_url)
                    if not policy_content:
                        st.error("Could not extract policy content from the URL.")
                else:
                    st.error("Could not find privacy policy URL.")

    with tab2:
        st.markdown("""
            <div class="input-option">
                <h3>Enter Privacy Policy URL</h3>
                <p>Provide the direct URL to the privacy policy page.</p>
            </div>
        """, unsafe_allow_html=True)
        
        policy_url = st.text_input("Privacy Policy URL", placeholder="https://example.com/privacy-policy")
        if policy_url and st.button("Analyze URL", key="analyze_url"):
            with st.spinner("Fetching and analyzing privacy policy..."):
                from privacy_policy_analyzer import fetch_policy_content, analyze_privacy_policy
                policy_content = fetch_policy_content(policy_url)
                if not policy_content:
                    st.error("Could not fetch or extract content from the provided URL.")

    with tab3:
        st.markdown("""
            <div class="input-option">
                <h3>Upload Text File</h3>
                <p>Upload a text file containing the privacy policy.</p>
            </div>
        """, unsafe_allow_html=True)
        
        uploaded_file = st.file_uploader(
            label="Upload Privacy Policy",
            type=['txt'],
            label_visibility="collapsed"
        )
        
        if uploaded_file is not None:
            try:
                policy_content = uploaded_file.getvalue().decode("utf-8")
                # Log the file content length
                logger.info(f"Uploaded file content length: {len(policy_content)} characters")
                logger.info(f"Uploaded file content preview: {policy_content[:100]}")
                
                # Check if content is empty
                if not policy_content or policy_content.strip() == "":
                    st.error("The uploaded file appears to be empty.")
                    policy_content = None
            except Exception as e:
                logger.error(f"Error reading uploaded file: {str(e)}")
                st.error(f"Error reading the uploaded file: {str(e)}")
                policy_content = None

    # Show file size limit
    st.markdown("""
        <div style='text-align: center; color: rgba(255, 255, 255, 0.5); font-size: 0.8rem; margin-top: -0.5rem;'>
            Maximum file size: 200MB
        </div>
    """, unsafe_allow_html=True)
    
    # Analysis section
    if policy_content:
        try:
            with st.spinner(f"Analyzing privacy policy against {selected_law} requirements..."):
                from privacy_policy_analyzer import analyze_privacy_policy
                
                # Get organization name based on input method
                org_name = None
                if company_name:  # From company name tab
                    org_name = company_name
                elif policy_url:  # From URL tab
                    # Extract domain name from URL
                    from urllib.parse import urlparse
                    domain = urlparse(policy_url).netloc
                    org_name = domain.split('.')[-2] if domain else "Organization"
                else:  # From file upload
                    org_name = "Organization"
                
                analysis_result = analyze_privacy_policy(policy_content, selected_law_key, organization_name=org_name)
                
                if "error" in analysis_result:
                    st.error(f"Error analyzing privacy policy: {analysis_result['error']}")
                    return
                
                # Display the analysis results with AI report styling
                st.markdown("""
                    <div class="analysis-results">
                        {}
                    </div>
                """.format(analysis_result["analysis"]), unsafe_allow_html=True)
                
                # Add PDF download button if PDF content is available
                if "pdf_content" in analysis_result and analysis_result["pdf_content"]:
                    st.download_button(
                        label="📥 Download Analysis Report (PDF)",
                        data=analysis_result["pdf_content"],
                        file_name=f"Privacy_Policy_Assessment_Report_{datetime.now().strftime('%Y%m%d')}.pdf",
                        mime="application/pdf",
                        help="Download the analysis report as a PDF document",
                        use_container_width=False
                    )
                
                # Add a note about data privacy
                st.markdown("""
                    <div style="background: rgba(111, 168, 220, 0.1); padding: 1rem; border-radius: 8px; margin-top: 2rem; border-left: 4px solid #6fa8dc;">
                        <strong style="color: #6fa8dc;">Note:</strong> Your privacy policy document is processed securely and is not stored. 
                        The analysis is performed in real-time and results are displayed immediately.
                    </div>
                """, unsafe_allow_html=True)
                
        except Exception as e:
            st.error(f"Error processing privacy policy: {str(e)}")
            logger.error(f"Privacy policy processing error: {str(e)}")




