"""
Configuration settings for the Compliance Assessment Tool.

This module contains constants and settings used throughout the application.
"""

import os
import sys
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Get absolute path of the application root
if getattr(sys, 'frozen', False):
    # Running as bundled executable
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # Running from source
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Use absolute paths for questionnaires directory
QUESTIONNAIRE_DIR = os.path.join(BASE_DIR, "Questionnaire")
DATA_DIR = os.path.join(BASE_DIR, "data")
LOGO_PATH = os.path.join(BASE_DIR, "assets", "logo.png")

# Ensure critical directories exist
for directory in [QUESTIONNAIRE_DIR, os.path.join(BASE_DIR, "data"), os.path.join(BASE_DIR, "secure")]:
    os.makedirs(directory, exist_ok=True)
os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)

# App settings
APP_TITLE = "Compliance Assessment Tool"
APP_ICON = "🔐"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Available regulations and industries
REGULATIONS = {
    "DPDP": "Digital Personal Data Protection Act (India)",
}

# Industry-to-filename mapping
# This maps industry codes to their corresponding JSON filenames (without the .json extension)
# Case-insensitive industry mapping
INDUSTRY_FILENAME_MAP = {
    "DPDP": {
        "general": "Banking and finance",
        "banking": "Banking and finance",
        "banking and finance": "Banking and finance",
        "e-commerce": "E-commerce",
        "ecommerce": "E-commerce",
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



# AI Report Generation settings
AI_ENABLED = True
AI_PROVIDER = "openrouter"

# OpenRouter API key with bearer prefix
AI_API_KEY_1 = "Bearer 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"
AI_API_KEY_2 = "Bearer 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"
AI_API_KEY_3 = "Bearer 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"

# API key rotation settings
_current_api_key_index = 0
API_KEYS = [AI_API_KEY_1, AI_API_KEY_2, AI_API_KEY_3]

def get_ai_api_key():
    """Get the API key for AI services with rotation support"""
    global _current_api_key_index
    key = API_KEYS[_current_api_key_index]
    return key.replace("Bearer ", "") if key and key.startswith("Bearer ") else key

def rotate_api_key():
    """Rotate to the next available API key"""
    global _current_api_key_index
    _current_api_key_index = (_current_api_key_index + 1) % len(API_KEYS)
    logger.info(f"Rotating to API key {_current_api_key_index + 1}")
    return get_ai_api_key()

# Update the getter function to handle missing keys better
def get_ai_enabled():
    """Get whether AI report generation is enabled"""
    return AI_ENABLED

def get_ai_provider():
    """Get the AI provider to use"""
    return AI_PROVIDER
