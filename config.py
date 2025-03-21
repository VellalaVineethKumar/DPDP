"""
Configuration settings for the Compliance Assessment Tool.

This module contains constants and settings used throughout the application.
"""

import os
import sys
import streamlit as st
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
    "GDPR": "General Data Protection Regulation (EU)"
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

def get_questionnaire_path(regulation: str, industry: str) -> str:
    """Get full path to questionnaire file with fallback options"""
    try:
        regulation = regulation.strip().upper()
        industry = industry.strip().lower()
        
        # Get mapped filename
        filename = INDUSTRY_FILENAME_MAP.get(regulation, {}).get(industry)
        if not filename:
            filename = f"{industry}.json"
            
        file_path = os.path.join(QUESTIONNAIRE_DIR, regulation, filename)
        
        # Check for case-insensitive match if file doesn't exist
        if not os.path.exists(file_path):
            dir_path = os.path.join(QUESTIONNAIRE_DIR, regulation)
            if os.path.exists(dir_path):
                files = os.listdir(dir_path)
                for f in files:
                    if f.lower() == filename.lower():
                        return os.path.join(dir_path, f)
                        
            # Fall back to default questionnaire
            return os.path.join(QUESTIONNAIRE_DIR, regulation, "Banking and finance.json")
            
        return file_path
        
    except Exception as e:
        logger.error(f"Error getting questionnaire path: {str(e)}")
        return os.path.join(QUESTIONNAIRE_DIR, regulation, "Banking and finance.json")

# AI Report Generation settings
AI_ENABLED = True
AI_PROVIDER = "openrouter"

# OpenRouter API key with bearer prefix
AI_API_KEY = "Bearer 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"

# Update logo path handling with debug logs
def get_logo_path():
    """Get absolute path to logo file with debug logging"""
    logo_paths = [
        os.path.join(BASE_DIR, "assets", "logo.png"),
        os.path.join(BASE_DIR, "logo.png"),
        os.path.join(os.path.dirname(BASE_DIR), "assets", "logo.png")
    ]
    
    for path in logo_paths:
        logger.info(f"Checking logo path: {path}")
        if os.path.exists(path):
            logger.info(f"Found logo at: {path}")
            return path
            
    logger.warning("Logo file not found in any location")
    return None

LOGO_PATH = get_logo_path()

# Update API configuration to use Streamlit secrets
def get_ai_api_key():
    """Get API key from Streamlit secrets or environment"""
    try:
        # Try Streamlit secrets first
        api_key = st.secrets["openrouter_api_key"]
        logger.info("Using API key from Streamlit secrets")
    except Exception:
        # Fall back to environment variable
        api_key = os.environ.get("OPENROUTER_API_KEY", AI_API_KEY)
        logger.info("Using API key from environment/config")
    
    return api_key.replace("Bearer ", "") if api_key and api_key.startswith("Bearer ") else api_key

def get_ai_enabled():
    """Get whether AI report generation is enabled"""
    return AI_ENABLED

def get_ai_provider():
    """Get the AI provider to use"""
    return AI_PROVIDER
