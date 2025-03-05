"""
Utility functions for the Compliance Assessment Tool.
"""

import streamlit as st
import pandas as pd
import base64
from io import BytesIO
import json
import logging
from datetime import datetime
import os
from questionnaire_structure import get_questionnaire
from scoring import calculate_compliance_score
import config

# Setup logging
logger = logging.getLogger(__name__)

def initialize_session_state():
    """Initialize all session state variables if they don't exist"""
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
        st.session_state.assessment_date = config.DEFAULT_DATE
    if 'selected_regulation' not in st.session_state:
        st.session_state.selected_regulation = "DPDP"
    if 'selected_industry' not in st.session_state:
        st.session_state.selected_industry = "general"

def go_to_page(page):
    """Navigate to a specific page in the application"""
    st.session_state.current_page = page
    logger.info(f"Navigating to page: {page}")

def go_to_section(section_idx):
    """Navigate to a specific section in the assessment"""
    # Get questionnaire for selected regulation and industry
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    sections = questionnaire["sections"]
    
    if section_idx < 0:
        section_idx = 0
    
    if section_idx >= len(sections):
        # Completed all sections
        logger.info("Assessment completed, calculating results")
        st.session_state.assessment_complete = True
        st.session_state.results = calculate_compliance_score(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
        go_to_page('report')
        return
    
    st.session_state.current_section = section_idx
    go_to_page('assessment')
    logger.info(f"Navigating to section {section_idx + 1} of {len(sections)}")

def save_response(section_idx, question_idx, response):
    """Save a response to a question in the session state"""
    key = f"s{section_idx}_q{question_idx}"
    st.session_state.responses[key] = response
    logger.debug(f"Saved response for {key}: {response}")

def reset_assessment():
    """Reset the assessment to start over"""
    st.session_state.responses = {}
    st.session_state.assessment_complete = False
    st.session_state.results = None
    st.session_state.current_section = 0
    logger.info("Assessment reset")

def get_progress_percentage():
    """Calculate progress percentage through the assessment"""
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    sections = questionnaire["sections"]
    
    total_questions = sum(len(section["questions"]) for section in sections)
    answered_questions = len(st.session_state.responses)
    if total_questions == 0:
        return 0
    return min(100, (answered_questions / total_questions) * 100)

def get_section_progress_percentage():
    """Calculate progress percentage through the current section"""
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    sections = questionnaire["sections"]
    
    if st.session_state.current_section >= len(sections):
        return 100
    
    current_section = sections[st.session_state.current_section]
    total_questions = len(current_section["questions"])
    
    answered_questions = 0
    for q_idx in range(total_questions):
        key = f"s{st.session_state.current_section}_q{q_idx}"
        if key in st.session_state.responses:
            answered_questions += 1
    
    if total_questions == 0:
        return 0
    return (answered_questions / total_questions) * 100

def generate_excel_download_link(results, organization, date, regulation, industry):
    """Generate a download link for Excel export of results"""
    # Create sections dataframe
    sections_df = pd.DataFrame([
        {
            "Section": section, 
            "Score": score * 100,
            "Status": "High Risk" if score < 0.6 else ("Moderate Risk" if score < 0.75 else "Compliant")
        } 
        for section, score in results["section_scores"].items()
        if score is not None
    ])
    
    # Add metadata
    metadata_df = pd.DataFrame([
        {"Key": "Organization", "Value": organization},
        {"Key": "Date", "Value": date},
        {"Key": "Regulation", "Value": config.REGULATIONS.get(regulation, regulation)},
        {"Key": "Industry", "Value": config.INDUSTRIES.get(industry, industry)},
        {"Key": "Overall Score", "Value": f"{results['overall_score']:.1f}%"},
        {"Key": "Compliance Level", "Value": results['compliance_level']}
    ])
    
    # Create recommendations dataframe
    recs = []
    for section, recommendations_list in results["recommendations"].items():
        for rec in recommendations_list:
            recs.append({"Section": section, "Recommendation": rec})
    
    recommendations_df = pd.DataFrame(recs) if recs else pd.DataFrame(columns=["Section", "Recommendation"])
    
    # Generate Excel file with multiple sheets
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        metadata_df.to_excel(writer, sheet_name='Overview', index=False)
        sections_df.to_excel(writer, sheet_name='Section Scores', index=False)
        recommendations_df.to_excel(writer, sheet_name='Recommendations', index=False)
    
    buffer.seek(0)
    
    # Create download link
    b64 = base64.b64encode(buffer.read()).decode()
    filename = f"{regulation}_{industry}_{organization.replace(' ', '_')}_{date}.xlsx"
    return f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{filename}">Download Excel Report</a>'

def generate_csv_download_link(results, organization, date, regulation, industry):
    """Generate a download link for CSV export of results"""
    # Create sections dataframe
    sections_df = pd.DataFrame([
        {
            "Section": section, 
            "Score": score * 100,
            "Status": "High Risk" if score < 0.6 else ("Moderate Risk" if score < 0.75 else "Compliant")
        } 
        for section, score in results["section_scores"].items()
        if score is not None
    ])
    
    # Generate CSV
    buffer = BytesIO()
    sections_df.to_csv(buffer, index=False)
    buffer.seek(0)
    
    # Create download link
    b64 = base64.b64encode(buffer.read()).decode()
    filename = f"{regulation}_{industry}_{organization.replace(' ', '_')}_{date}.csv"
    return f'<a href="data:file/csv;base64,{b64}" download="{filename}">Download CSV</a>'

def track_event(event_name, properties=None):
    """Track user events for analytics"""
    # Simple logging implementation - would be replaced with actual analytics in production
    if properties is None:
        properties = {}
    logger.info(f"Event: {event_name}, Properties: {json.dumps(properties)}")
    
def change_questionnaire(regulation, industry):
    """Change the selected questionnaire and reset the assessment"""
    # Only reset if different from current selection
    if (st.session_state.selected_regulation != regulation or 
        st.session_state.selected_industry != industry):
        
        st.session_state.selected_regulation = regulation
        st.session_state.selected_industry = industry
        reset_assessment()
        track_event("questionnaire_changed", {
            "regulation": regulation,
            "industry": industry
        })
        logger.info(f"Changed questionnaire to {regulation}/{industry}")
    
def format_regulation_name(regulation_code):
    """Return the full name of a regulation from its code"""
    return config.REGULATIONS.get(regulation_code, regulation_code)

def ensure_directories_exist():
    """Ensure necessary directories exist for the application"""
    # Ensure questionnaires directory structure exists
    for regulation in config.REGULATIONS.keys():
        os.makedirs(f'questionnaires/{regulation.lower()}', exist_ok=True)
    
    # Ensure logs directory exists
    os.makedirs('logs', exist_ok=True)

def create_sample_questionnaires_if_needed():
    """Create sample questionnaires if they don't exist"""
    # Check if DPDP general questionnaire exists
    dpdp_general_path = os.path.join('questionnaires', 'dpdp', 'general.json')
    
    if not os.path.exists(dpdp_general_path):
        logger.info("Creating sample DPDP general questionnaire")
        # Create a minimal questionnaire
        sample_questionnaire = {
            "sections": [
                {
                    "name": "Basic Compliance",
                    "weight": 1.0,
                    "questions": ["Is your organization aware of DPDP requirements?"],
                    "options": [["Yes", "Partially", "No", "Not applicable"]]
                }
            ],
            "answer_points": {
                "Yes": 1.0,
                "Partially": 0.5,
                "No": 0.0,
                "Not applicable": None
            },
            "recommendations": {
                "Basic Compliance": {
                    "Partially": "Improve organizational awareness of DPDP requirements",
                    "No": "Establish DPDP awareness training for all staff"
                }
            }
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(dpdp_general_path), exist_ok=True)
        
        # Write the sample questionnaire
        with open(dpdp_general_path, 'w', encoding='utf-8') as f:
            json.dump(sample_questionnaire, f, indent=2)

def load_responses_from_file(filepath):
    """Load saved responses from a JSON file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            saved_data = json.load(f)
            
        # Update session state
        st.session_state.responses = saved_data.get('responses', {})
        st.session_state.organization_name = saved_data.get('organization_name', '')
        st.session_state.assessment_date = saved_data.get('assessment_date', config.DEFAULT_DATE)
        st.session_state.selected_regulation = saved_data.get('selected_regulation', 'DPDP')
        st.session_state.selected_industry = saved_data.get('selected_industry', 'general')
        
        # Recalculate results if all sections were completed
        if saved_data.get('assessment_complete', False):
            st.session_state.assessment_complete = True
            st.session_state.results = calculate_compliance_score(
                st.session_state.selected_regulation,
                st.session_state.selected_industry
            )
            
        logger.info(f"Loaded responses from {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error loading responses from {filepath}: {e}")
        return False

def save_responses_to_file(filepath):
    """Save current responses to a JSON file"""
    try:
        save_data = {
            'responses': st.session_state.responses,
            'organization_name': st.session_state.organization_name,
            'assessment_date': st.session_state.assessment_date,
            'selected_regulation': st.session_state.selected_regulation,
            'selected_industry': st.session_state.selected_industry,
            'assessment_complete': st.session_state.assessment_complete
        }
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
            
        logger.info(f"Saved responses to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving responses to {filepath}: {e}")
        return False