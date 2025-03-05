"""
This module handles the calculation of compliance scores based on the questionnaire
responses and provides recommendations for improvement.
"""

import streamlit as st
import logging
from questionnaire_structure import get_questionnaire

# Setup basic logging
logger = logging.getLogger(__name__)

def calculate_compliance_score(regulation, industry):
    """
    Calculate compliance scores based on questionnaire responses.
    Returns a dictionary with overall score, compliance level, section scores, and recommendations.
    
    Args:
        regulation (str): The regulation code (e.g., 'DPDP', 'GDPR')
        industry (str): The industry code (e.g., 'general', 'finance')
    
    Returns:
        dict: Results with scores and recommendations
    """
    try:
        # Load the appropriate questionnaire
        questionnaire = get_questionnaire(regulation, industry)
        sections = questionnaire["sections"]
        answer_points = questionnaire["answer_points"]
        recommendations = questionnaire["recommendations"]
        
        section_scores = {}
        section_recommendations = {}
        
        # Calculate scores for each section
        for i, section in enumerate(sections):
            section_name = section["name"]
            section_weight = section["weight"]
            section_score = 0
            applicable_questions = 0
            section_recommendations[section_name] = []
            
            # Process each question in the section
            for j, question in enumerate(section["questions"]):
                question_key = f"s{i}_q{j}"
                
                if question_key in st.session_state.responses:
                    response = st.session_state.responses[question_key]
                    score = answer_points.get(response)
                    
                    # Skip N/A responses
                    if score is None:
                        continue
                    
                    section_score += score
                    applicable_questions += 1
                    
                    # Generate recommendation if score < 1
                    if score < 1.0:
                        if section_name in recommendations and response in recommendations.get(section_name, {}):
                            section_recommendations[section_name].append(
                                recommendations[section_name][response]
                            )
            
            # Calculate average score for the section
            if applicable_questions > 0:
                section_scores[section_name] = section_score / applicable_questions
            else:
                section_scores[section_name] = None
        
        # Calculate weighted overall score
        total_weighted_score = 0
        applicable_weight_sum = 0
        
        for section_name, score in section_scores.items():
            if score is not None:
                section_weight = next((s["weight"] for s in sections if s["name"] == section_name), 0)
                total_weighted_score += score * section_weight
                applicable_weight_sum += section_weight
        
        overall_score = 0
        if applicable_weight_sum > 0:
            overall_score = (total_weighted_score / applicable_weight_sum) * 100
        
        # Determine compliance level
        compliance_level = ""
        if overall_score >= 90:
            compliance_level = "High Compliance"
        elif overall_score >= 75:
            compliance_level = "Substantial Compliance"
        elif overall_score >= 50:
            compliance_level = "Partial Compliance"
        else:
            compliance_level = "Low Compliance"
        
        # Identify high risk areas (sections with scores below 0.6)
        high_risk_areas = [
            section for section, score in section_scores.items() 
            if score is not None and score < 0.6
        ]
        high_risk_areas.sort(key=lambda x: section_scores.get(x, 1))
        
        # Return results
        return {
            "overall_score": overall_score,
            "compliance_level": compliance_level,
            "section_scores": section_scores,
            "high_risk_areas": high_risk_areas,
            "recommendations": section_recommendations,
            "improvement_priorities": high_risk_areas[:3]  # Top 3 areas to focus on
        }
    except Exception as e:
        logger.error(f"Error calculating compliance score: {str(e)}", exc_info=True)
        # Return default values in case of error
        return {
            "overall_score": 0,
            "compliance_level": "Error",
            "section_scores": {},
            "high_risk_areas": [],
            "recommendations": {},
            "improvement_priorities": []
        }

def get_recommendation_priority(results):
    """
    Get prioritized recommendations based on high risk areas.
    
    Args:
        results (dict): Results from calculate_compliance_score
        
    Returns:
        dict: Priority recommendations by area
    """
    try:
        priority_recommendations = {}
        
        for area in results.get("improvement_priorities", []):
            if area in results.get("recommendations", {}) and results["recommendations"][area]:
                priority_recommendations[area] = results["recommendations"][area][:3]  # Top 3 recommendations
        
        return priority_recommendations
    except Exception as e:
        logger.error(f"Error getting prioritized recommendations: {str(e)}", exc_info=True)
        return {}