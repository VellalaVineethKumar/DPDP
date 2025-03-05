"""
Configuration settings for the Compliance Assessment Application.

This module contains centralized configuration constants used throughout the application.
When adding new regulations or industries, update the relevant dictionaries in this file.
"""

import os
from datetime import datetime

# App settings
APP_TITLE = "Compliance Assessment Tool"
APP_ICON = "🔒"
APP_LAYOUT = "wide"
SIDEBAR_STATE = "expanded"

# Image paths
LOGO_PATH = "https://img.icons8.com/color/96/000000/data-protection.png"

# Default values
DEFAULT_DATE = datetime.now().strftime("%Y-%m-%d")

# Available regulations
REGULATIONS = {
    "DPDP": "Digital Personal Data Protection Act (India)",
    "GDPR": "General Data Protection Regulation (EU)",
    "PDPL": "Personal Data Privacy Protection Law (Qatar)",
    "CCPA": "California Consumer Privacy Act (USA)",
    "LGPD": "Lei Geral de Proteção de Dados (Brazil)",
    "POPIA": "Protection of Personal Information Act (South Africa)"
}

# Available industries
INDUSTRIES = {
    "general": "General Business",
    "healthcare": "Healthcare",
    "finance": "Finance & Banking",
    "ecommerce": "E-commerce & Retail",
    "technology": "Technology & SaaS",
    "education": "Education",
    "telecom": "Telecommunications",
    "hospitality": "Hospitality & Tourism",
    "manufacturing": "Manufacturing",
    "professional": "Professional Services"
}

# Future settings (for when you add these features)
# DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///compliance_data.db")
# SECRET_KEY = os.getenv("SECRET_KEY", "your-default-secret-key")