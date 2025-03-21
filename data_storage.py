"""Data storage module for the Compliance Assessment Tool.

This module handles persistent storage of assessment data including:
- Organization details
- Assessment responses
- Compliance reports
- Historical tracking
"""

import os
import json
from datetime import datetime
import logging
import pandas as pd
from typing import Dict, Any, Optional
from config import BASE_DIR

# Setup logging
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join(BASE_DIR, "data")
ORG_DATA_DIR = os.path.join(DATA_DIR, 'organizations')
REPORTS_DIR = os.path.join(DATA_DIR, 'reports')

def ensure_data_directories():
    """Ensure all necessary data directories exist"""
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(ORG_DATA_DIR, exist_ok=True)
    os.makedirs(REPORTS_DIR, exist_ok=True)

def get_org_directory(org_name: str) -> str:
    """Get the directory path for an organization's data"""
    # Sanitize organization name for filesystem
    safe_name = ''.join(c for c in org_name if c.isalnum() or c in (' ', '-', '_')).strip()
    org_dir = os.path.join(ORG_DATA_DIR, safe_name)
    os.makedirs(org_dir, exist_ok=True)
    return org_dir

def save_assessment_data(data: Dict[str, Any]) -> bool:
    """Save assessment data for an organization
    
    Args:
        data: Dictionary containing assessment data including:
            - organization_name: Name of the organization
            - assessment_date: Date of assessment
            - selected_regulation: Selected regulation code
            - selected_industry: Selected industry code
            - responses: Assessment responses
            - results: Calculated results and recommendations
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        org_name = data.get('organization_name')
        if not org_name:
            logger.error("Organization name is required")
            return False
            
        # Get organization directory
        org_dir = get_org_directory(org_name)
        os.makedirs(org_dir, exist_ok=True)
        
        # Create filename with timestamp
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"assessment_{timestamp}.json"
        filepath = os.path.join(org_dir, filename)
        
        # Add metadata
        save_data = data.copy()
        save_data['saved_at'] = datetime.now().isoformat()
        
        # Save assessment data
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2)
        
        # If assessment is complete, save report
        if data.get('assessment_complete', False) and data.get('results'):
            save_report(data)
            
        logger.info(f"Saved assessment data for {org_name} to {filepath}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving assessment data: {e}")
        return False

def save_report(data: Dict[str, Any]) -> bool:
    """Save assessment report in multiple formats
    
    Args:
        data: Assessment data dictionary
    
    Returns:
        bool: True if save was successful, False otherwise
    """
    try:
        org_name = data['organization_name']
        assessment_date = data['assessment_date']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Create report directory
        report_dir = os.path.join(REPORTS_DIR, org_name)
        os.makedirs(report_dir, exist_ok=True)
        
        # Save JSON report
        json_path = os.path.join(report_dir, f"report_{timestamp}.json")
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data['results'], f, indent=2)
        
        # Save Excel report if pandas is available
        try:
            excel_path = os.path.join(report_dir, f"report_{timestamp}.xlsx")
            
            # Create Excel writer
            with pd.ExcelWriter(excel_path) as writer:
                # Overview sheet
                overview_data = {
                    'Organization': org_name,
                    'Assessment Date': assessment_date,
                    'Regulation': data['selected_regulation'],
                    'Industry': data['selected_industry'],
                    'Overall Score': data['results']['overall_score'],
                    'Compliance Level': data['results']['compliance_level']
                }
                pd.DataFrame([overview_data]).to_excel(writer, sheet_name='Overview', index=False)
                
                # Section scores
                scores_data = [
                    {'Section': section, 'Score': score * 100}
                    for section, score in data['results']['section_scores'].items()
                    if score is not None
                ]
                pd.DataFrame(scores_data).to_excel(writer, sheet_name='Section Scores', index=False)
                
                # Recommendations
                recs_data = []
                for section, recs in data['results']['recommendations'].items():
                    for rec in recs:
                        recs_data.append({'Section': section, 'Recommendation': rec})
                pd.DataFrame(recs_data).to_excel(writer, sheet_name='Recommendations', index=False)
        
        except Exception as e:
            logger.warning(f"Could not save Excel report: {e}")
        
        logger.info(f"Saved assessment report for {org_name}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving report: {e}")
        return False

def get_organization_assessments(org_name: str) -> list:
    """Get list of all assessments for an organization
    
    Args:
        org_name: Name of the organization
    
    Returns:
        list: List of assessment data dictionaries, sorted by date
    """
    try:
        org_dir = get_org_directory(org_name)
        if not os.path.exists(org_dir):
            return []
            
        assessments = []
        for filename in os.listdir(org_dir):
            if filename.endswith('.json'):
                filepath = os.path.join(org_dir, filename)
                with open(filepath, 'r', encoding='utf-8') as f:
                    assessment = json.load(f)
                    assessments.append(assessment)
        
        # Sort by assessment date
        assessments.sort(key=lambda x: x.get('assessment_date', ''), reverse=True)
        return assessments
        
    except Exception as e:
        logger.error(f"Error getting organization assessments: {e}")
        return []

def get_latest_assessment(org_name: str) -> Optional[Dict[str, Any]]:
    """Get the most recent assessment for an organization
    
    Args:
        org_name: Name of the organization
    
    Returns:
        Optional[Dict[str, Any]]: Latest assessment data or None if not found
    """
    assessments = get_organization_assessments(org_name)
    return assessments[0] if assessments else None

# Ensure data directories exist on module import
ensure_data_directories()