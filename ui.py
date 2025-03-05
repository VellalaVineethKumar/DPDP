"""
User interface rendering functions for the Compliance Assessment Tool.
This module contains all the Streamlit UI components and page rendering.
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import logging
import os

import config
from questionnaire_structure import get_questionnaire, get_available_regulations, get_available_industries
from scoring import calculate_compliance_score, get_recommendation_priority
from utils import (
    go_to_page, 
    go_to_section, 
    save_response, 
    reset_assessment, 
    generate_excel_download_link,
    track_event,
    get_section_progress_percentage,
    change_questionnaire,
    format_regulation_name
)

# Setup logging
logger = logging.getLogger(__name__)

def render_header():
    """Render the application header"""
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title(f"{config.APP_ICON} {config.APP_TITLE}")
    with col2:
        st.write("")
        st.write("")
        if st.session_state.current_page != 'welcome':
            if st.button("Start New Assessment", type="primary"):
                # Reset assessment
                reset_assessment()
                go_to_page('welcome')
                track_event("new_assessment_started")

def render_sidebar():
    """Render the sidebar navigation"""
    with st.sidebar:
        st.image(config.LOGO_PATH, width=100)
        st.title("Navigation")
        
        # Selection information if available
        if st.session_state.selected_regulation and st.session_state.selected_regulation in config.REGULATIONS:
            st.write(f"**Regulation:** {config.REGULATIONS[st.session_state.selected_regulation]}")
        
        if st.session_state.selected_industry and st.session_state.selected_industry in config.INDUSTRIES:
            st.write(f"**Industry:** {config.INDUSTRIES[st.session_state.selected_industry]}")
        
        # Navigation buttons
        if st.button("Dashboard", use_container_width=True):
            go_to_page('dashboard')
            track_event("navigation", {"destination": "dashboard"})
        
        if st.button("Start Assessment", use_container_width=True):
            if not st.session_state.organization_name:
                go_to_page('welcome')
            else:
                go_to_page('assessment')
            track_event("navigation", {"destination": "assessment"})
                
        if st.button("View Report", use_container_width=True):
            if st.session_state.assessment_complete:
                go_to_page('report')
                track_event("navigation", {"destination": "report"})
            else:
                st.sidebar.warning("Complete the assessment first to view the report")
                
        if st.button("Recommendations", use_container_width=True):
            if st.session_state.assessment_complete:
                go_to_page('recommendations')
                track_event("navigation", {"destination": "recommendations"})
            else:
                st.sidebar.warning("Complete the assessment first to view recommendations")
        
        st.divider()
        if st.session_state.organization_name:
            st.write(f"**Organization:** {st.session_state.organization_name}")
            st.write(f"**Assessment Date:** {st.session_state.assessment_date}")
            
            # Display progress
            if st.session_state.current_page == 'assessment':
                questionnaire = get_questionnaire(
                    st.session_state.selected_regulation,
                    st.session_state.selected_industry
                )
                progress = st.session_state.current_section / len(questionnaire["sections"])
                st.progress(progress)
                st.write(f"Section {st.session_state.current_section + 1} of {len(questionnaire['sections'])}")

def render_welcome_page():
    """Render the welcome page with regulation and industry selection"""
    st.header("Welcome to the Compliance Assessment Tool")
    st.write("""
    This tool helps you assess your organization's compliance with various data protection regulations.
    Select your industry and the relevant regulation to get a tailored assessment.
    """)
    
    # Check if we have questionnaires available
    available_regulations = get_available_regulations()
    if not available_regulations:
        st.warning("""
        No questionnaires found. Please ensure you have created questionnaire files in the 'questionnaires' directory.
        For example, questionnaires/dpdp/general.json
        """)
        return
    
    # Regulation and industry selection
    col1, col2 = st.columns(2)
    
    with col1:
        regulation_options = [reg for reg in config.REGULATIONS.keys() if reg in available_regulations]
        regulation = st.selectbox(
            "Select Regulation",
            options=regulation_options,
            format_func=lambda x: config.REGULATIONS[x],
            index=regulation_options.index(st.session_state.selected_regulation) 
            if st.session_state.selected_regulation in regulation_options else 0
        )
    
    # Get available industries for selected regulation
    available_industries = get_available_industries(regulation)
    industry_options = [ind for ind in config.INDUSTRIES.keys() if ind in available_industries or ind == "general"]
    
    with col2:
        industry = st.selectbox(
            "Select Industry",
            options=industry_options,
            format_func=lambda x: config.INDUSTRIES[x],
            index=industry_options.index(st.session_state.selected_industry)
            if st.session_state.selected_industry in industry_options else 0
        )
    
    # Update selected regulation and industry
    if regulation != st.session_state.selected_regulation or industry != st.session_state.selected_industry:
        change_questionnaire(regulation, industry)
    
    st.subheader("Before you begin")
    st.write(f"""
    You'll be asked a series of questions about your organization's compliance with 
    {config.REGULATIONS[regulation]} for the {config.INDUSTRIES[industry]} industry.
    
    The assessment takes approximately 15-20 minutes to complete.
    Your responses will be used to calculate compliance scores and generate tailored recommendations.
    """)
    
    with st.form("organization_form"):
        st.subheader("Organization Information")
        org_name = st.text_input("Organization Name", key="org_name_input")
        assessment_date = st.date_input("Assessment Date", value=datetime.now())
        
        submitted = st.form_submit_button("Begin Assessment", type="primary")
        if submitted and org_name:
            st.session_state.organization_name = org_name
            st.session_state.assessment_date = assessment_date.strftime("%Y-%m-%d")
            track_event("assessment_started", {
                "organization": org_name,
                "regulation": regulation,
                "industry": industry,
                "date": assessment_date.strftime("%Y-%m-%d")
            })
            go_to_section(0)
            st.rerun()

def render_dashboard():
    """Render the compliance dashboard"""
    st.header(f"{format_regulation_name(st.session_state.selected_regulation)} Compliance Dashboard")
    
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to view your compliance dashboard")
        if st.button("Start Assessment", type="primary"):
            if not st.session_state.organization_name:
                go_to_page('welcome')
            else:
                go_to_section(0)
        return
    
    results = st.session_state.results
    
    # Create dashboard layout
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
                    {'range': [90, 100], 'color': "green"},
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
                st.error(f"{area} ({score:.1f}%)", icon="🚨")
    
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
        df = df.sort_values("Score")
        
        # Create horizontal bar chart
        fig = px.bar(
            df, 
            x="Score", 
            y="Section", 
            orientation='h',
            color="Score",
            color_continuous_scale=["red", "orange", "lightgreen", "green"],
            range_color=[0, 100]
        )
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)
    
    # Action Items
    st.subheader("Recommended Actions")
    if results["improvement_priorities"]:
        for i, area in enumerate(results["improvement_priorities"]):
            with st.expander(f"Priority {i+1}: {area}"):
                if area in results["recommendations"] and results["recommendations"][area]:
                    for rec in results["recommendations"][area]:
                        st.write(f"• {rec}")
                else:
                    st.write("No specific recommendations available for this area.")

def render_assessment():
    """Render the assessment questionnaire"""
    # Get current questionnaire
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    
    sections = questionnaire["sections"]
    
    if st.session_state.current_section >= len(sections):
        st.session_state.assessment_complete = True
        st.session_state.results = calculate_compliance_score(
            st.session_state.selected_regulation,
            st.session_state.selected_industry
        )
        go_to_page('report')
        return
    
    section = sections[st.session_state.current_section]
    st.header(f"Section: {section['name']}")
    
    # Progress bar
    progress = st.session_state.current_section / len(sections)
    st.progress(progress)
    
    # Display questions
    for q_idx, question in enumerate(section["questions"]):
        st.subheader(f"Question {q_idx + 1}")
        st.write(question)
        
        # Get current response if any
        current_response = st.session_state.responses.get(f"s{st.session_state.current_section}_q{q_idx}", None)
        
        # Display options as radio buttons
        options = section["options"][q_idx]
        response = st.radio(
            "Select your answer:",
            options,
            key=f"radio_{st.session_state.current_section}_{q_idx}",
            index=options.index(current_response) if current_response in options else None
        )
        
        # Save response when selected
        if response:
            save_response(st.session_state.current_section, q_idx, response)
        
        st.divider()
    
    # Navigation buttons
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        if st.session_state.current_section > 0:
            if st.button("Previous Section"):
                go_to_section(st.session_state.current_section - 1)
                track_event("navigation", {"action": "previous_section"})
    
    with col3:
        if st.button("Next Section", type="primary"):
            # Check if all questions in current section are answered
            all_answered = True
            for q_idx in range(len(section["questions"])):
                key = f"s{st.session_state.current_section}_q{q_idx}"
                if key not in st.session_state.responses:
                    all_answered = False
            
            if all_answered:
                go_to_section(st.session_state.current_section + 1)
                track_event("navigation", {"action": "next_section"})
            else:
                st.error("Please answer all questions before proceeding.")

def render_report():
    """Render the compliance report"""
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to view your compliance report")
        if st.button("Start Assessment", type="primary"):
            if not st.session_state.organization_name:
                go_to_page('welcome')
            else:
                go_to_section(0)
        return
    
    results = st.session_state.results
    
    st.header(f"{format_regulation_name(st.session_state.selected_regulation)} Compliance Report")
    st.subheader(f"For: {st.session_state.organization_name}")
    st.write(f"Industry: {config.INDUSTRIES[st.session_state.selected_industry]}")
    st.write(f"Assessment Date: {st.session_state.assessment_date}")
    
    # Summary section
    st.markdown(f"""
    ### Overall Compliance: {results['overall_score']:.1f}% - {results['compliance_level']}
    
    This report provides a detailed assessment of your organization's compliance with 
    the {format_regulation_name(st.session_state.selected_regulation)} across multiple key areas. 
    Review the section scores and recommendations below to identify areas for improvement.
    """)
    
    # Section scores table
    st.subheader("Section Compliance Scores")
    
    # Create dataframe for section scores
    section_data = []
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    
    for section in questionnaire["sections"]:
        section_name = section["name"]
        if section_name in results["section_scores"] and results["section_scores"][section_name] is not None:
            score = results["section_scores"][section_name] * 100
            section_data.append({
                "Section": section_name,
                "Score (%)": f"{score:.1f}%",
                "Weight": f"{section['weight'] * 100:.1f}%",
                "Status": "High Risk" if score < 60 else ("Moderate Risk" if score < 75 else "Compliant")
            })
    
    df = pd.DataFrame(section_data)
    st.dataframe(df, use_container_width=True)
    
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
    
    # Export options
    st.subheader("Export Report")
    export_link = generate_excel_download_link(
        results, 
        st.session_state.organization_name,
        st.session_state.assessment_date,
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    st.markdown(export_link, unsafe_allow_html=True)
    
    # Navigation buttons
    if st.button("View Detailed Recommendations", type="primary"):
        go_to_page('recommendations')
        track_event("navigation", {"destination": "recommendations"})

def render_recommendations():
    """Render detailed recommendations page"""
    if not st.session_state.assessment_complete:
        st.info("Complete the assessment to view recommendations")
        if st.button("Start Assessment", type="primary"):
            if not st.session_state.organization_name:
                go_to_page('welcome')
            else:
                go_to_section(0)
        return
    
    results = st.session_state.results
    
    st.header("Detailed Recommendations")
    st.write(f"""
    Based on your assessment, we recommend the following actions to improve 
    {format_regulation_name(st.session_state.selected_regulation)} compliance:
    """)
    
    # Get current questionnaire
    questionnaire = get_questionnaire(
        st.session_state.selected_regulation,
        st.session_state.selected_industry
    )
    
    # Display recommendations by section
    for section in questionnaire["sections"]:
        section_name = section["name"]
        if section_name in results["recommendations"] and results["recommendations"][section_name]:
            with st.expander(f"{section_name}"):
                score = results["section_scores"].get(section_name, 0)
                if score is not None:
                    score_percentage = score * 100
                    st.write(f"Current compliance score: {score_percentage:.1f}%")
                
                st.write("**Recommended Actions:**")
                for rec in results["recommendations"][section_name]:
                    st.write(f"• {rec}")
    
    # Priority action plan
    st.subheader("Priority Action Plan")
    st.write("Focus on these areas first to significantly improve your compliance:")
    
    for i, area in enumerate(results["improvement_priorities"][:3]):
        st.write(f"**Priority {i+1}: {area}**")
        if area in results["recommendations"] and results["recommendations"][area]:
            for rec in results["recommendations"][area][:3]:  # Top 3 recommendations
                st.write(f"• {rec}")
    
    # Resources
    st.subheader("Helpful Resources")
    
    if st.session_state.selected_regulation == "DPDP":
        st.write("""
        - [DPDP Act Official Website](https://digitalindia.gov.in/)
        - [Official DPDP Act Guidelines](https://digitalindia.gov.in/)
        - [DPDP Compliance Checklist](https://digitalindia.gov.in/)
        - [Contact a DPDP Compliance Expert](mailto:info@compliance.com)
        """)
    elif st.session_state.selected_regulation == "GDPR":
        st.write("""
        - [Official EU GDPR Portal](https://gdpr.eu/)
        - [European Data Protection Board Guidelines](https://edpb.europa.eu/our-work-tools/general-guidance/guidelines-recommendations-best-practices_en)
        - [ICO's Guide to GDPR](https://ico.org.uk/for-organisations/guide-to-data-protection/guide-to-the-general-data-protection-regulation-gdpr/)
        - [GDPR Compliance Checklist](https://gdpr.eu/checklist/)
        """)
    else:
        st.write("""
        - [Data Protection Authority Website](https://example.org/)
        - [Official Compliance Guidelines](https://example.org/)
        - [Contact a Data Protection Expert](mailto:info@compliance.com)
        """)