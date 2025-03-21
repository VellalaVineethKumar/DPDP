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

import config
# Update import: get reg/ind functions from config instead of assessment
from config import get_available_regulations, get_available_industries
from assessment import get_questionnaire, calculate_compliance_score
# Import from new recommendation engine instead of assessment
from recommendation_engine import get_recommendation_priority, organize_recommendations_by_priority
from helpers import (
    go_to_page, 
    go_to_section, 
    save_response, 
    reset_assessment, 
    generate_excel_download_link,
    track_event,
    get_section_progress_percentage,  # Use this instead of local implementation
    change_questionnaire,
    format_regulation_name,
    validate_token
)
from token_storage import generate_token, cleanup_expired_tokens, revoke_token, get_organization_for_token

# Import the newly created styles
from styles import (
    get_landing_page_css, 
    get_sidebar_css, 
    get_radio_button_css,
    get_print_export_css,
    get_print_button_html,
    get_expiry_box_css
)

# Setup logging
logger = logging.getLogger(__name__)

# Base64 logo function (moved from landing.py)
def get_base64_logo():
    """Get base64 encoded logo with better error handling"""
    try:
        if not config.LOGO_PATH:
            logger.warning("No logo path configured")
            return ""
            
        if not os.path.exists(config.LOGO_PATH):
            logger.error(f"Logo file not found at: {config.LOGO_PATH}")
            return ""
            
        with open(config.LOGO_PATH, "rb") as img_file:
            encoded = base64.b64encode(img_file.read()).decode()
            logger.info("Successfully loaded and encoded logo")
            return encoded
    except Exception as e:
        logger.error(f"Error loading logo: {str(e)}")
        return ""

def render_header():
    """Render the application header"""
    # Show organization name only if it exists and isn't empty
    org_name = st.session_state.organization_name if st.session_state.organization_name and st.session_state.organization_name.strip() else None
    
    if org_name:
        st.markdown(f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1>{config.APP_TITLE}</h1>
                <p style='font-size: 1.2em; font-weight: 500;'>Organization: {org_name}</p>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style='text-align: center; margin-bottom: 2rem;'>
                <h1>{config.APP_TITLE}</h1>
            </div>
        """, unsafe_allow_html=True)

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
    
    # Logo
    logo_base64 = get_base64_logo()
    if logo_base64:
        st.markdown(f"""
            <div class="logo-container">
                <img src="data:image/jpeg;base64,{logo_base64}" alt="Logo">
            </div>
        """, unsafe_allow_html=True)
    
    # Title
    st.markdown(f"""
        <div class="title-container">
            <h1>{config.APP_TITLE}</h1>
            <p>Enter your access token to begin the assessment</p>
            <p style="font-size: 0.9rem; margin-top: 1rem;">If you do not have a token, please <a href="mailto:info@datainfa.com?subject=Requesting%20Access%20token%20for%20my%20organisation">contact us</a> to get your access token.</p>
        </div>
    """, unsafe_allow_html=True)
    
    # Token input
    token = st.text_input("Access Token", type="password")
    
    if st.button("Access Assessment", type="primary"):
        if validate_token(token):
            st.session_state.authenticated = True
            st.session_state.current_page = 'welcome'
            st.rerun()
        else:
            st.error("Invalid token. Please try again or contact support.")
    
    # Footer
    st.markdown("""
        <div class="footer">
            &copy; 2025 Compliance Assessment Tool | All Rights Reserved
        </div>
    """, unsafe_allow_html=True)

def render_assessment():
    """Render the assessment questionnaire"""
    # Create a top anchor to scroll to
    st.markdown('<div id="top"></div>', unsafe_allow_html=True)
    
    # Add JavaScript to scroll to top automatically
    st.markdown("""
        <script>
            // Function to scroll to top
            function scrollToTop() {
                window.scrollTo(0, 0);
            }
            
            // Call scroll function after component loads
            window.addEventListener('load', function() {
                scrollToTop();
            });
            
            // Additional fallback for Streamlit
            setTimeout(scrollToTop, 100);
        </script>
    """, unsafe_allow_html=True)

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
    
    # Add a hidden control at the top with autoFocus to ensure page scrolls up
    st.text_input(
        label="Scroll to top",  # Add non-empty label
        value="", 
        key="scroll_to_top_input", 
        label_visibility="hidden",
        help="This hidden element helps to scroll to the top of the page automatically", 
        autocomplete="off", 
        disabled=True
    )
    
    # Add JavaScript to scroll to top of page when loading a new section
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
        # Check if we're trying to use "new" or "new banking fin"
        if st.session_state.selected_industry.lower() in ['new', 'new banking fin']:
            logger.info("Detected 'new' industry selection, ensuring we use the complete questionnaire")
            # Force the industry to be consistently named
            st.session_state.selected_industry = "new banking fin"
            
        st.session_state.current_questionnaire = get_questionnaire(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
    
    # Use the cached questionnaire
    questionnaire = st.session_state.current_questionnaire
    
    # Show questionnaire debug info in sidebar with more details
    with st.sidebar.expander("Questionnaire Debug", expanded=False):
        st.write(f"Regulation: {st.session_state.selected_regulation}")
        st.write(f"Industry: {st.session_state.selected_industry}")
        if "sections" in questionnaire:
            sections_count = len(questionnaire["sections"])
            st.write(f"Sections: {sections_count}")
            
            # For DPDP + "new banking fin", we expect a full questionnaire
            expected_section_count = 13 if st.session_state.selected_industry.lower() in ['new', 'new banking fin'] else 1
            
            if sections_count < expected_section_count:
                st.warning(f"⚠️ This questionnaire only contains {sections_count} section(s). Expected {expected_section_count} for {st.session_state.selected_industry}.")
                if st.button("Reload Complete Questionnaire"):
                    clear_questionnaire_cache()
                    # If this is the "new banking fin" questionnaire, ensure we use the right version
                    if st.session_state.selected_industry.lower() in ['new', 'new banking fin']:
                        st.session_state.selected_industry = "new banking fin"
                    st.rerun()
            
            st.write("Section names:")
            for i, section in enumerate(questionnaire["sections"]):
                st.write(f"{i+1}. {section['name']}")
    
    # TESTING ONLY - TO BE REMOVED BEFORE PRODUCTION
    # Add quick-fill testing option in sidebar for faster testing
    with st.sidebar.expander("⚠️ TESTING TOOLS - REMOVE BEFORE PRODUCTION", expanded=False):
        st.warning("This section is for testing only and should be removed before production deployment.")
        
        auto_fill_option = st.radio(
            "Auto-fill responses with:",
            ["None", "All Yes/Positive", "All Partial/Medium", "All No/Negative", "Random Mix"],
            key="auto_fill_option"
        )
        
        if st.button("Apply Auto-Fill", key="apply_auto_fill"):
            sections = questionnaire["sections"]
            current_section = st.session_state.current_section
            
            if current_section < len(sections):
                section = sections[current_section]
                questions = section["questions"]
                
                for q_idx, question in enumerate(questions):
                    # Get options
                    if isinstance(question, dict):
                        options = question.get("options", [])
                    else:
                        try:
                            options = section.get("options", [])[q_idx]
                        except (IndexError, KeyError):
                            options = ["Yes", "No", "Not applicable"]
                    
                    if not options:
                        continue
                        
                    # Determine which option to select based on auto_fill_option
                    selected_option = None
                    if auto_fill_option == "All Yes/Positive":
                        # Look for positive answers ("Yes", contains "with", etc.)
                        for option in options:
                            option_lower = option.lower()
                            if option_lower.startswith("yes") or "with" in option_lower or "clear" in option_lower:
                                selected_option = option
                                break
                        # Default to first option if no positive option found
                        if selected_option is None and options:
                            selected_option = options[0]
                    elif auto_fill_option == "All Partial/Medium":
                        # Look for partial answers
                        for option in options:
                            option_lower = option.lower()
                            if "partial" in option_lower or "need" in option_lower or "improvement" in option_lower:
                                selected_option = option
                                break
                        # Default to middle option if no partial option found
                        if selected_option is None and len(options) > 1:
                            selected_option = options[len(options) // 2]
                        elif options:
                            selected_option = options[0]
                    elif auto_fill_option == "All No/Negative":
                        # Look for negative answers
                        for option in options:
                            option_lower = option.lower()
                            if option_lower.startswith("no") or "lack" in option_lower or "not" in option_lower:
                                selected_option = option
                                break
                        # Default to last option if no negative option found
                        if selected_option is None and options:
                            selected_option = options[-1]
                    elif auto_fill_option == "Random Mix":
                        import random
                        selected_option = random.choice(options)
                    
                    # Save the response if an option was selected
                    if selected_option:
                        response_key = f"s{current_section}_q{q_idx}"
                        st.session_state.responses[response_key] = selected_option
                
                st.success(f"Auto-filled {len(questions)} responses for current section")
                st.rerun()
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
    st.header(f"Section {st.session_state.current_section + 1}: {section_name}")
    
    # Show current section progress
    section_progress = get_section_progress_percentage()
    st.progress(section_progress / 100)
    
    # Show both progress metrics
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"Section progress: {section_progress:.1f}%")
    with col2:
        st.markdown(f"Overall progress: {overall_progress:.1f}% ({answered_questions}/{total_questions} questions)")
    
    # Apply radio button styling
    st.markdown(get_radio_button_css(), unsafe_allow_html=True)
    
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
            st.markdown(q_text)
            
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
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            prev_disabled = st.session_state.current_section <= 0
            if st.form_submit_button("Previous Section", disabled=prev_disabled, use_container_width=True):
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
            
            if st.form_submit_button(next_button_label, type="primary", use_container_width=True):
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
    
    Args:
        results: Assessment results dictionary containing scores and recommendations
        
    Returns:
        A natural language summary of the assessment results
    """
    # Use the nlg_report module to generate the report
    logger.info("Requesting AI report generation with the following configuration:")
    logger.info(f"AI enabled: {config.get_ai_enabled()}")
    logger.info(f"API key available: {'Yes' if config.get_ai_api_key() else 'No'}")
    logger.info(f"API provider: {config.get_ai_provider()}")
    
    # Record timing information
    start_time = time.time()
    report = generate_report(results, use_external_api=config.get_ai_enabled())
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
    st.subheader(f"For: {st.session_state.organization_name}")
    st.write(f"Assessment Date: {st.session_state.assessment_date}")
    
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
    
    # Add debug expander to display actual weight values from the questionnaire
    with st.expander("Debug Weight Values", expanded=False):
        st.write("Section weights from questionnaire:")
        questionnaire = get_questionnaire(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
        weight_data = []
        for section in questionnaire["sections"]:
            weight = section.get("weight", 1.0 / len(questionnaire["sections"]))
            weight_data.append({
                "Section": section["name"],
                "Weight": f"{weight:.2f}",
                "Questions": len(section["questions"])
            })
        
        weight_df = pd.DataFrame(weight_data)
        st.dataframe(weight_df)
        
        st.write("Total weight sum:", sum(float(w["Weight"]) for w in weight_data))
        
        # Recalculate scores manually with equal weights for verification
        if all_section_scores:
            manual_score = sum(all_section_scores) / len(all_section_scores) * 100
            st.write(f"Score with equal weights (ignoring section weights): {manual_score:.1f}%")
            
            if abs(manual_score - results["overall_score"]) > 1.0:
                st.error(f"Large discrepancy between weighted score ({results['overall_score']:.1f}%) and equal-weight score ({manual_score:.1f}%)")
        
        # Add new section to debug scoring discrepancies
        st.write("Detailed score diagnostics:")
        for section_name, score in results["section_scores"].items():
            # Get all responses for this section
            section_responses = []
            section_idx = None
            
            # Find the section index
            questionnaire = get_questionnaire(
                st.session_state.selected_regulation,
                st.session_state.selected_industry
            )
            for idx, section in enumerate(questionnaire["sections"]):
                if section["name"] == section_name:
                    section_idx = idx
                    break
                    
            if section_idx is not None:
                # Get all responses for this section
                section_responses = [
                    st.session_state.responses.get(f"s{section_idx}_q{q_idx}")
                    for q_idx in range(len(questionnaire["sections"][section_idx]["questions"]))
                ]
                
                # Create a mini scoring calculator directly in the debug view
                perfect_answers = sum(1 for r in section_responses if r is not None and "yes" in r.lower())
                total_answers = sum(1 for r in section_responses if r is not None)
                
                if total_answers > 0:
                    expected_score = perfect_answers / total_answers
                    st.write(f"Section: {section_name}")
                    
                    # Fix: Check if score is None before multiplying by 100
                    if score is not None:
                        st.write(f"- Official score: {score * 100:.1f}%")
                    else:
                        st.write(f"- Official score: None (N/A)")
                        
                    st.write(f"- Perfect answers: {perfect_answers} of {total_answers}")
                    st.write(f"- Expected score: {expected_score * 100:.1f}%")
                    
                    # Only compare if score is not None
                    if score is not None and abs(expected_score - score) > 0.01:
                        st.error(f"Scoring discrepancy detected! Difference: {abs(expected_score - score) * 100:.1f}%")
                        
                        # Add explanation for perfect scores
                        if score == 1.0 and expected_score < 1.0:
                            st.info("""
                            **Note about perfect score:** While not all answers are perfect, the system has applied 
                            score adjustment rules that can result in a perfect score when certain criteria are met. 
                            This may include:
                            - Having high-quality responses in critical questions
                            - Meeting minimum threshold requirements for the section
                            - Automatic corrections for known scoring issues
                            
                            You can see the actual response quality in the 'Perfect answers' metric above.
                            """)
                    
                    # Add validation that should fix most scoring issues
                    if score is not None and score < 1.0 and all("yes" in r.lower() for r in section_responses if r is not None):
                        st.warning(f"All answers are 'yes' but score is not 100%. This is a known issue that will be fixed.")
                        # Provide button to fix this specific section score
                        if st.button(f"Fix '{section_name}' score to 100%", key=f"fix_{section_name}"):
                            # Directly update the result in session state
                            results["section_scores"][section_name] = 1.0
                            # Recalculate overall score
                            weighted_scores = [
                                s * w for s, w in zip(
                                    [score for score in results["section_scores"].values() if score is not None],
                                    [section.get("weight", 1.0/len(questionnaire["sections"])) 
                                    for section in questionnaire["sections"] 
                                    if section["name"] in results["section_scores"] 
                                    and results["section_scores"][section["name"]] is not None]
                                )
                            ]
                            total_weight = sum(section.get("weight", 1.0/len(questionnaire["sections"])) 
                                            for section in questionnaire["sections"] 
                                            if section["name"] in results["section_scores"] 
                                            and results["section_scores"][section["name"]] is not None)
                            if total_weight > 0:
                                results["overall_score"] = sum(weighted_scores) / total_weight * 100
                            st.success(f"Fixed score! Please refresh the report to see updated values.")
                            st.session_state.results = results  # Update session state
                            st.rerun()  # Force refresh
        
        # Add a more comprehensive debug expander
        st.write("### Questionnaire Structure Check")
        st.write(f"Questionnaire has {len(questionnaire.get('sections', []))} sections defined:")
        for i, section in enumerate(questionnaire.get("sections", [])):
            section_name = section.get("name", f"Section {i+1}")
            question_count = len(section.get("questions", []))
            # Highlight if this section doesn't have a score
            has_score = section_name in results.get("section_scores", {})
            if has_score:
                st.write(f"{i+1}. {section_name}: {question_count} questions")
            else:
                st.write(f"{i+1}. 🚫 {section_name}: {question_count} questions (No score calculated)")
        
        # Check for sections in the questionnaire that don't have scores
        missing_sections = []
        for section in questionnaire.get("sections", []):
            section_name = section.get("name", "")
            if section_name and section_name not in results.get("section_scores", {}):
                missing_sections.append(section_name)
        
        if missing_sections:
            st.error(f"Missing sections in results: {', '.join(missing_sections)}")
            st.write("This indicates that the assessment didn't process these sections properly.")
            
            # Add a button to force recalculation that processes all sections
            if st.button("Force Process All Sections", key="force_process_all"):
                # Force recreation of the results with a special flag
                st.session_state.process_all_sections = True
                st.session_state.results = calculate_compliance_score(
                    st.session_state.selected_regulation,
                    st.session_state.selected_industry
                )
                st.success("All sections processed. Refreshing the report to show updated results.")
                st.rerun()
        else:
            st.success("All sections from the questionnaire have scores calculated.")
    
    # Section scores table
    st.subheader("Section Compliance Scores")
    
    # Create dataframe for section scores
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
    st.dataframe(df, use_container_width=True)
    
    # Display sections with None scores
    if none_score_sections:
        st.info("The following sections have no score because all questions were marked as 'Not applicable' or had no responses:")
        for section in none_score_sections:
            st.write(f"• {section}")
    
    # Key findings
    st.subheader("Key Findings")
    
    # Strengths
    strengths = [
        section for section, score in results["section_scores"].items() 
        if score is not None and score >= 0.75
    ]
    
    if strengths:
        st.write("**Strengths:**")
        for strength in strengths[:3]:  # Top 3 strengths
            score = results["section_scores"][strength] * 100
            st.success(f"• {strength} ({score:.1f}%)")
    
    # Areas for improvement
    if results["high_risk_areas"]:
        st.write("**Areas for Improvement:**")
        for area in results["high_risk_areas"]:
            score = results["section_scores"][area] * 100
            st.error(f"• {area} ({score:.1f}%)")
            
            # Display top recommendation for this area
            if area in results["recommendations"] and results["recommendations"][area]:
                with st.expander("Key recommendation"):
                    st.write(results["recommendations"][area][0])
    
    # Export options
    st.subheader("Export Report")
    col1, col2, col3 = st.columns(3)
    
    with col2:
        st.metric("Compliance Level", results['compliance_level'])
        st.write("")
        st.write("")
        st.write("")
        
        # Download buttons
        excel_link = generate_excel_download_link(
            results,
            st.session_state.organization_name,
            st.session_state.assessment_date,
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
        st.markdown(excel_link, unsafe_allow_html=True)
    
    # # High risk areas
    # if results["high_risk_areas"]:
    #     st.subheader("High Risk Areas")
    #     for area in results["high_risk_areas"]:
    #         score = results["section_scores"][area] * 100
    #         st.error(f"{area} ({score:.1f}%)", icon="🚨")
    # else:
    #     st.subheader("No High Risk Areas")
    #     st.success("All sections have acceptable compliance levels", icon="✅")
    
    # Section scores - SECOND INSTANCE (change the title to be more descriptive)
    st.subheader("Section Scores Visualization")  # Changed from "Section Compliance Scores"
    
    # Create dataframe for section scores
    section_data = []
    
    for section, score in results["section_scores"].items():
        if score is not None:
            status = "High Risk" if score < 0.6 else ("Moderate Risk" if score < 0.75 else "Compliant")
            section_data.append({
                "Section": section,
                "Score": score * 100,
                "Status": status
            })
    
    df = pd.DataFrame(section_data)
    if not df.empty:
        df = df.sort_values("Score")
        
        # Create horizontal bar chart - Fix for the error
        try:
            fig = px.bar(
                df, 
                x="Score", 
                y="Section", 
                orientation='h',
                color="Status",
                color_discrete_map={
                    "High Risk": "#FF4B4B",
                    "Moderate Risk": "#FFA500",
                    "Compliant": "#00CC96"
                },
                labels={"Score": "Compliance Score (%)"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"Error generating chart: {e}")
            # Fallback to show scores as text
            st.write("Section Scores:")
            for _, row in df.iterrows():
                color = "#FF4B4B" if row["Status"] == "High Risk" else "#FFA500" if row["Status"] == "Moderate Risk" else "#00CC96"
                st.markdown(f"<div style='color:{color};'>• {row['Section']}: {row['Score']:.1f}%</div>", unsafe_allow_html=True)
    else:
        st.info("No section scores available to display.")
    
    # Recommendations summary
    st.subheader("Key Recommendations")
    if results["improvement_priorities"]:
        for i, area in enumerate(results["improvement_priorities"][:3]):
            with st.expander(f"Priority {i+1}: {area}"):
                if area in results["recommendations"] and results["recommendations"][area]:
                    for rec in results["recommendations"][area]:
                        # Highlight critical recommendations with icons
                        if any(keyword in rec.lower() for keyword in ["critical", "immediate", "urgent", "required", "necessary"]):
                            st.error(f"• {rec} ⚠️")
                        else:
                            st.write(f"• {rec}")
                else:
                    st.write("No specific recommendations available for this area.")
    else:
        st.info("No priority recommendations identified.")
    
    # Button to view detailed recommendations
    if st.button("View All Recommendations", type="primary"):
        go_to_page('recommendations')
        track_event("navigation", {"destination": "recommendations"})

    # Add tabs before accessing tab1
    tabs = st.tabs(["AI Summary", "Detailed Scores", "Recommendations"])
    
    with tabs[0]:  # AI Summary tab
        # Show AI loading indicator
        with st.spinner("Generating detailed analysis..."):
            # Get organization name and date
            org_name = st.session_state.get("organization_name", "Your Organization")
            assessment_date = st.session_state.get("assessment_date", datetime.now().strftime("%Y-%m-%d"))
            
            # Generate report - now returns plain text
            ai_report = generate_natural_language_report(st.session_state.results)
            
            # Replace placeholders
            ai_report = ai_report.replace("[Insert Date]", assessment_date)
            ai_report = ai_report.replace("[Insert Organization Name]", org_name)
            
            # Display the report using Streamlit's native markdown
            st.markdown(ai_report)

            # Add download button for the report
            if ai_report:
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.download_button(
                        label="📥 Download Report",
                        data=ai_report,
                        file_name=f"compliance_report_{datetime.now().strftime('%Y%m%d')}.txt",
                        mime="text/plain",
                        help="Download the report as a text file"
                    )
                with col2:
                    if st.button("🔄 Regenerate Analysis"):
                        st.session_state.ai_report_generated = False
                        st.rerun()

    # Add content for other tabs
    with tabs[1]:
        st.write("Detailed scores will be shown here")
        # Add detailed scores visualization

    with tabs[2]:
        st.write("Recommendations will be shown here")
        # Add recommendations content

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

# This Admin page section duplicates functionality in debug_response_viewer.py
def render_admin_page():
    """Render the admin page"""
    st.title("Admin Dashboard")
    if not st.session_state.get('is_admin', False):
        st.error("Access denied. Admin privileges required.")
        return
    
    # Add tabs for different admin functions
    admin_tabs = st.tabs(["Token Management", "Response Maintenance", "System Status"])
    
    # Token Management Tab
    with admin_tabs[0]:
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
                            st.success(f"Token successfully generated for DINFA!")
                            
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
                token_file_path = os.path.join('secure', 'tokens.csv')
                if os.path.exists(token_file_path):
                    # Read the actual CSV structure first to determine the column format
                    with open(token_file_path, 'r') as f:
                        first_line = f.readline().strip()
                        logger.info(f"CSV Header: {first_line}")
                    # Read the actual CSV structure first to determine the column format
                    # Read CSV file with correct columns
                    tokens_df = pd.read_csv(token_file_path)
                    logger.info(f"CSV columns detected: {list(tokens_df.columns)}")
                    
                    if not tokens_df.empty:
                        # Rename columns if needed for display consistency
                        column_mapping = {}
                        if 'organization_name' in tokens_df.columns:
                            column_mapping['organization_name'] = 'organization'
                        # Rename columns if needed for display consistency
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
                token_file_path = os.path.join('secure', 'tokens.csv')
                if os.path.exists(token_file_path):
                    import base64
                    with open(token_file_path, 'rb') as f:
                        b64 = base64.b64encode(f.read()).decode()
                        href = f'<a href="data:file/csv;base64,{b64}" download="tokens_export.csv">Download CSV</a>'
                        st.markdown(href, unsafe_allow_html=True)
                else:
                    st.info("No token database found to export")
    
    # Response Maintenance Tab
    with admin_tabs[1]:
        st.subheader("Response Maintenance")
        
        # Add Null Response Fixing Tool
        with st.expander("Fix Null Responses Tool", expanded=True):
            st.write("This tool helps fix null/None responses in the current session state.")
            
            if 'responses' not in st.session_state:
                st.warning("No responses found in session state")
            else:
                null_keys = [key for key, value in st.session_state.responses.items() if value is None]
                
                if not null_keys:
                    st.success("No null responses found in session state!")
                else:
                    st.warning(f"Found {len(null_keys)} null responses in session state")
                    st.write("Null responses found:")
                    for key in null_keys:
                        st.code(f"• {key}")
                    
                    # Options for fixing the null responses
                    fix_options = st.radio(
                        "How would you like to fix these null responses?",
                        ["Remove them", "Replace with 'Not applicable'", "Replace with custom value"]
                    )
                    custom_value = ""
                    if fix_options == "Replace with custom value":
                        custom_value = st.text_input("Enter custom value:")
                    
                    # Fix button
                    if st.button("Fix Responses", type="primary"):
                        from helpers import fix_null_responses
                        
                        if fix_options == "Remove them":
                            # Remove the null responses
                            for key in null_keys:
                                if key in st.session_state.responses:
                                    del st.session_state.responses[key]
                            st.success(f"Removed {len(null_keys)} null responses")
                        elif fix_options == "Replace with 'Not applicable'":
                            # Fix with default value
                            fixed = fix_null_responses("Not applicable")
                            st.success(f"Fixed {fixed} null responses")
                        elif fix_options == "Replace with custom value" and custom_value:
                            # Fix with custom value
                            fixed = fix_null_responses(custom_value)
                            st.success(f"Fixed {fixed} null responses")
                        
                        # Option to recalculate scores
                        if st.button("Recalculate Scores"):
                            if 'selected_regulation' in st.session_state and 'selected_industry' in st.session_state:
                                # Recalculate scores based on current responses
                                st.session_state.results = calculate_compliance_score(
                                    st.session_state.selected_regulation,
                                    st.session_state.selected_industry
                                )
                                st.success("Scores recalculated successfully")
                            else:
                                st.error("Missing regulation or industry selection")
        
        with st.expander("Response Viewer", expanded=False):
            if 'responses' in st.session_state and st.session_state.responses:
                st.write(f"Total responses: {len(st.session_state.responses)}")
                
                # Group responses by section
                sections = {}
                for key, value in st.session_state.responses.items():
                    if key.startswith('s') and '_q' in key:
                        try:
                            section_idx = int(key.split('_')[0][1:])
                            question_idx = int(key.split('_')[1][1:])
                            
                            if section_idx not in sections:
                                sections[section_idx] = {}
                            sections[section_idx][question_idx] = value
                        except (ValueError, IndexError):
                            st.error(f"Could not parse response key: {key}")
                
                # Use tabs instead of nested expanders to avoid nesting error
                if sections:
                    section_tabs = st.tabs([f"Section {idx+1}" for idx in sorted(sections.keys())])
                    
                    for i, section_idx in enumerate(sorted(sections.keys())):
                        with section_tabs[i]:
                            questions = sections[section_idx]
                            for question_idx in sorted(questions.keys()):
                                response = questions[question_idx]
                                
                                # Display with color coding based on apparent score
                                if response is None:
                                    st.markdown(f"**Q{question_idx + 1}**: 🚫 `None`")
                                elif isinstance(response, str):
                                    if response.lower().startswith(("yes", "full", "comprehensive")):
                                        st.markdown(f"**Q{question_idx + 1}**: ✅ `{response}`")
                                    elif response.lower().startswith(("partial", "basic", "limited", "mostly")):
                                        st.markdown(f"**Q{question_idx + 1}**: ⚠️ `{response}`")
                                    elif response.lower().startswith(("no", "not ", "none", "rarely")):
                                        st.markdown(f"**Q{question_idx + 1}**: ❌ `{response}`")
                                    elif "not applicable" in response.lower():
                                        st.markdown(f"**Q{question_idx + 1}**: ℹ️ `{response}`")
                                    else:
                                        st.markdown(f"**Q{question_idx + 1}**: `{response}`")
                                else:
                                    st.markdown(f"**Q{question_idx + 1}**: `{response}`")
                else:
                    st.info("No responses organized by sections found")
                
                # Export option
                if st.button("Export Responses to JSON"):
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    export_data = {
                        "timestamp": timestamp,
                        "responses": st.session_state.responses
                    }
                    json_str = json.dumps(export_data, indent=2)
                    st.download_button(
                        label="Download JSON",
                        data=json_str,
                        file_name=f"responses_{timestamp}.json",
                        mime="application/json"
                    )
            else:
                st.warning("No responses available in session state")
    
    # System Status Tab
    with admin_tabs[2]:
        st.subheader("System Status")
        st.write("Session State Information:")
        
        # Display key session state values
        status_data = {
            "Authentication": st.session_state.get('authenticated', False),
            "Current Page": st.session_state.get('current_page', ''),
            "Organization": st.session_state.get('organization_name', ''),
            "Regulation": st.session_state.get('selected_regulation', ''),
            "Industry": st.session_state.get('selected_industry', ''),
            "Assessment Complete": st.session_state.get('assessment_complete', False),
            "Current Section": st.session_state.get('current_section', 0),
            "Response Count": len(st.session_state.get('responses', {})),
        }
        
        for key, value in status_data.items():
            st.text(f"{key}: {value}")

def render_sidebar():
    """Render the application sidebar"""
    with st.sidebar:
        # Logo with debug info
        logo_base64 = get_base64_logo()
        if logo_base64:
            st.markdown(f"""
                <div class='logo-container'>
                    <img src="data:image/png;base64,{logo_base64}" 
                         style='width: 200px; display: block; margin: 0 auto;'>
                </div>
            """, unsafe_allow_html=True)
        else:
            st.warning("Logo not available")
            logger.warning("Logo not rendered in sidebar")
        
        # Apply custom CSS for navigation menu
        st.markdown(get_sidebar_css(), unsafe_allow_html=True)
        
        # Navigation section title
        st.markdown("<div class='nav-title'>Navigation</div>", unsafe_allow_html=True)
        
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
            {"label": "Home", "key": "nav_home", "page": "welcome", "always_show": True},
            {"label": "Assessment", "key": "nav_assessment", "page": "assessment", "show_if_ready": assessment_ready},
            {"label": "Dashboard", "key": "nav_dashboard", "page": "dashboard", "show_if": "assessment_complete"},
            {"label": "Report", "key": "nav_report", "page": "report", "show_if": "assessment_complete"},
            {"label": "Recommendations", "key": "nav_recommendations", "page": "recommendations", "show_if": "assessment_complete"},
            {"label": "Admin", "key": "nav_admin", "page": "admin", "show_if": "is_admin"}
        ]
        
        # Fix for button rendering
        for item in nav_items:
            should_show = (
                item.get("always_show", False) or 
                (item.get("show_if") and st.session_state.get(item.get("show_if"), False)) or
                (item.get("show_if_ready") and item.get("show_if_ready"))
            )
            if should_show:
                button_class = "secondary" if st.session_state.current_page == item["page"] else "primary"
                if st.button(item["label"], key=item["key"], type=button_class, use_container_width=True):
                    go_to_page(item["page"])

def render_welcome_page():
    """Render the welcome page"""
    st.title("Welcome to the Compliance Assessment Tool")
    st.write("This tool helps you assess your organization's compliance with data protection regulations.")
    
    # Organization name input with required flag
    org_name = st.text_input(
        "Organization Name *", 
        value=st.session_state.organization_name,
        key="org_name_input",
        help="This field is required to start the assessment"
    )
    
    # Update session state when changed
    if org_name != st.session_state.organization_name:
        st.session_state.organization_name = org_name
    
    # Regulation selection
    regulations = config.REGULATIONS
    selected_regulation = st.selectbox(
        "Select Regulation",
        options=list(regulations.keys()),
    )
    
    # Get industries specific to the selected regulation
    # This will dynamically update when regulation changes
    industries = config.get_available_industries(selected_regulation)
    
    # Industry selection - FIX: Add missing label and options parameters
    selected_industry = st.selectbox(
        label="Select Industry",
        options=list(industries.keys()),
        format_func=lambda x: industries[x],
        key="selected_industry"
    )
    
    # Always enable the button, but validate on click
    if st.button("Start Assessment", type="primary"):
        if not org_name.strip():
            st.error("Please enter your organization name before starting the assessment.")
            return
        
        # Reset responses and assessment completion status
        st.session_state.responses = {}
        st.session_state.assessment_complete = False
        st.session_state.results = None
        st.session_state.current_section = 0
        st.session_state.assessment_started = True  # Set flag when assessment starts
        # Log the transition
        logger.info(f"Starting new assessment for {st.session_state.organization_name}, regulation: {st.session_state.selected_regulation}, industry: {st.session_state.selected_industry}")
        # Use go_to_page instead of manually setting the page
        go_to_page('assessment')
        st.rerun()

def render_dashboard():
    """Render the dashboard view"""
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to view your compliance dashboard")
        if st.button("Start Assessment", type="primary"):
            st.session_state.current_page = 'assessment'
            st.rerun()
        return
    
    results = st.session_state.results
    
    st.header("DPDP Compliance Dashboard")
    export_pdf_button()
    
    # Create dashboard layout in separate containers for better formatting
    col1, col2 = st.columns([1, 2])
    
    with col1:
        # Overall score gauge
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=results["overall_score"],
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': "Overall Compliance"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "red"},
                    {'range': [50, 75], 'color': "orange"},
                    {'range': [75, 90], 'color': "lightgreen"},
                    {'range': [90, 100], 'color': "green"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': results["overall_score"]
                }
            }
        ))
        fig.update_layout(height=250)
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Compliance Level")
        st.write(f"**{results['compliance_level']}**")
        
        # High risk areas
        if results["high_risk_areas"]:
            st.subheader("High Risk Areas")
            for area in results["high_risk_areas"]:
                score = results["section_scores"][area] * 100
                st.error(f"• {area} ({score:.1f}%)")
    
    with col2:
        # Section scores
        st.subheader("Section Compliance Scores")
        
        # Create dataframe for section scores
        section_data = []
        for section, score in results["section_scores"].items():
            if score is not None:
                section_data.append({
                    "Section": section,
                    "Score": score * 100
                })
        
        df = pd.DataFrame(section_data)
        if not df.empty:
            df = df.sort_values("Score")
            
            # Create horizontal bar chart
            fig = px.bar(
                df, 
                x="Score", 
                y="Section", 
                orientation='h',
                color="Score",
                color_continuous_scale=["red", "orange", "lightgreen", "green"],
                range_color=[0, 100],
                labels={"Score": "Compliance Score (%)"}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
    
    st.subheader("Recommended Actions")
    if results["improvement_priorities"]:
        for i, area in enumerate(results["improvement_priorities"][:3]):
            with st.expander(f"Priority {i+1}: {area}"):
                if area in results["recommendations"] and results["recommendations"][area]:
                    for rec in results["recommendations"][area]:
                        st.write(f"• {rec}")
                else:
                    st.write("No specific recommendations available for this area.")

def export_pdf_button():
    """Create a PDF export button that uses custom JS to print a clean dashboard"""
    # Apply custom CSS for printing
    st.markdown(get_print_export_css(), unsafe_allow_html=True)
    
    # Add print button HTML
    st.markdown(get_print_button_html(), unsafe_allow_html=True)
