"""
This module handles the loading of questionnaires from JSON files
based on the selected regulation and industry.

When adding new regulations or industries, simply add the corresponding
JSON files in the questionnaires directory structure without modifying this code.
"""

import json
import os
import logging

# Setup logging
logger = logging.getLogger(__name__)

def get_questionnaire(regulation, industry):
    """
    Load and return the appropriate questionnaire based on regulation and industry.
    
    Args:
        regulation (str): Regulation code (e.g., 'DPDP', 'GDPR')
        industry (str): Industry code (e.g., 'general', 'finance')
        
    Returns:
        dict: The questionnaire data structure with sections, answer points, and recommendations
    """
    try:
        # Construct file path
        file_path = os.path.join('Questionnaire', f"{industry}.json")
        
        # Try to load industry-specific questionnaire
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as file:
                logger.info(f"Loaded questionnaire from {file_path}")
                return json.load(file)
        
        # Fall back to general questionnaire if industry-specific doesn't exist
        general_path = os.path.join('Questionnaire', "general.json")
        if os.path.exists(general_path):
            with open(general_path, 'r', encoding='utf-8') as file:
                logger.info(f"Loaded general questionnaire for {regulation} (industry-specific not found)")
                return json.load(file)
                
        # If neither exists, return default questionnaire
        logger.warning(f"No questionnaire found for {regulation}/{industry}")
        return get_default_questionnaire()
        
    except Exception as e:
        logger.error(f"Error loading questionnaire for {regulation}/{industry}: {e}")
        return get_default_questionnaire()

def get_default_questionnaire():
    """Return minimal default questionnaire as fallback if no files are found"""
    logger.warning("Using default questionnaire as fallback")
    return {
        "sections": [
            {
                "name": "General Compliance",
                "weight": 1.0,
                "questions": ["Is your organization aware of applicable data protection regulations?"],
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
            "General Compliance": {
                "Partially": "Improve organizational awareness of data protection regulations",
                "No": "Establish data protection awareness training for all staff"
            }
        }
    }

def get_available_regulations():
    """
    Return a list of available regulations based on existing directories
    
    Returns:
        list: Available regulation codes
    """
    try:
        # Since we're using a flat structure based on the screenshot,
        # we'll just return the regulations defined in config
        import config
        return list(config.REGULATIONS.keys())
    except Exception as e:
        logger.error(f"Error getting available regulations: {e}")
        return ["DPDP"]  # Default fallback

def get_available_industries(regulation):
    """
    Return a list of available industries for a specific regulation
    
    Args:
        regulation (str): Regulation code (e.g., 'DPDP', 'GDPR')
        
    Returns:
        list: Available industry codes for the specified regulation
    """
    try:
        industries = []
        questionnaire_dir = 'Questionnaire'
        
        if os.path.exists(questionnaire_dir):
            for item in os.listdir(questionnaire_dir):
                if item.endswith('.json'):
                    industry = item[:-5]  # Remove .json extension
                    if industry != '__init__':  # Skip __init__ files
                        industries.append(industry)
        
        return industries
    except Exception as e:
        logger.error(f"Error getting available industries for {regulation}: {e}")
        return ["general"]  # Default fallback