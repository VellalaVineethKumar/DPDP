"""
Configuration settings for the Compliance Assessment Tool.

This module contains constants and settings used throughout the application.
"""

import os
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Get absolute path of this file's directory, regardless of where it's run from
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use relative paths from BASE_DIR
QUESTIONNAIRE_DIR = os.path.join(BASE_DIR, "Questionnaire")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "secure"), exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# App settings
APP_TITLE = "Compliance Assessment Tool"
APP_ICON = "🔐"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Available regulations and industries
REGULATIONS = {
    "DPDP": "Digital Personal Data Protection Act (India)",
    "GDPR": "General Data Protection Regulation (EU)"
}

# Industry-to-filename mapping
# This maps industry codes to their corresponding JSON filenames (without the .json extension)
INDUSTRY_FILENAME_MAP = {
    "DPDP": {
        "general": "Banking and finance",
        "banking": "Banking and finance",
        "ecommerce": "E-commerce",
        "e-commerce": "E-commerce",
        "new": "Banking and finance",
        "new banking fin": "Banking and finance"
    }
}

# Display names for industries
INDUSTRY_DISPLAY_NAMES = {
    "Banking and finance": "Financial Services",
    "E-commerce": "E-commerce & Retail",
    "general": "General Industry"
}

def get_available_regulations() -> Dict[str, str]:
    """Get available regulations"""
    return REGULATIONS

def get_available_industries(regulation_code: str) -> Dict[str, str]:
    """Get available industries for a regulation"""
    try:
        regulation_dir = os.path.join(QUESTIONNAIRE_DIR, regulation_code)
        if os.path.isdir(regulation_dir):
            files = [f for f in os.listdir(regulation_dir) if f.endswith('.json')]
            industries = {}
            
            # Add 'general' option that maps to a default questionnaire
            industries["general"] = INDUSTRY_DISPLAY_NAMES.get("general", "General Industry")
            
            # Add all available industries from files
            for file in files:
                industry_code = os.path.splitext(file)[0].lower()
                base_name = os.path.splitext(file)[0]
                industry_name = INDUSTRY_DISPLAY_NAMES.get(base_name, base_name.replace('_', ' ').title())
                industries[industry_code] = industry_name
                
            return industries
        else:
            logging.warning(f"Regulation directory not found: {regulation_dir}")
            return {"general": "General Industry"}
    except Exception as e:
        logging.error(f"Error getting available industries: {str(e)}")
        return {"general": "General Industry"}

def map_industry_to_filename(regulation_code: str, industry_code: str) -> str:
    """
    Map an industry code to its corresponding filename
    
    Args:
        regulation_code: The regulation code
        industry_code: The industry code to map
        
    Returns:
        The filename to use for this industry code (without .json extension)
    """
    industry_code = industry_code.lower()
    
    # Use mapping if available
    if regulation_code in INDUSTRY_FILENAME_MAP and industry_code in INDUSTRY_FILENAME_MAP[regulation_code]:
        return INDUSTRY_FILENAME_MAP[regulation_code][industry_code]
    
    # Otherwise, use industry code as filename
    return industry_code

# AI Report Generation settings
AI_ENABLED = True
AI_PROVIDER = "openrouter"

# OpenRouter API key with bearer prefix
AI_API_KEY = "Bearer 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"

def get_ai_api_key():
    """Get the API key for AI services"""
    return AI_API_KEY.replace("Bearer ", "") if AI_API_KEY and AI_API_KEY.startswith("Bearer ") else AI_API_KEY

# Update the getter function to handle missing keys better
def get_ai_enabled():
    """Get whether AI report generation is enabled"""
    return AI_ENABLED

def get_ai_provider():
    """Get the AI provider to use"""
    return AI_PROVIDER
