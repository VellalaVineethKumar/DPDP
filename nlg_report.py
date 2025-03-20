"""
Natural Language Generation module for creating human-readable reports.
Supports template-based reports and optional integration with external AI APIs.
Returns plain text output for easy reading without formatting requirements.
"""

import logging
import os
import json
import requests
from typing import Dict, Any, List, Optional
import time

import config

logger = logging.getLogger(__name__)

# Constants for different report tones
TONE_POSITIVE = "positive"
TONE_NEUTRAL = "neutral"
TONE_CONCERNED = "concerned"

def generate_report(results: Dict[str, Any], use_external_api: bool = True) -> str:
    """
    Generate a natural language report based on assessment results
    
    Args:
        results: Assessment results dictionary
        use_external_api: Whether to use an external AI API for enhanced report generation
        
    Returns:
        String containing the plain text report
    """
    # Log the start of report generation
    logger.info("Starting report generation process")
    
    # Get AI configuration status and log it
    ai_enabled = _is_api_configured()
    logger.info(f"AI API configuration status: enabled={ai_enabled}, use_external_api={use_external_api}")
    
    if use_external_api and ai_enabled:
        try:
            logger.info(f"Attempting AI-powered report generation using {config.get_ai_provider()} API")
            start_time = time.time()
            report = _generate_report_with_api(results)
            duration = time.time() - start_time
            logger.info(f"Successfully generated AI report in {duration:.2f} seconds")
            return report
        except Exception as e:
            logger.error(f"Error using external API for report generation: {str(e)}", exc_info=True)
            logger.info("Falling back to template-based report")
    else:
        if use_external_api:
            if not ai_enabled:
                logger.warning("External API requested but not configured, using template-based report generation")
            else:
                logger.info("External API configured but not requested, using template-based report generation")
        else:
            logger.info("Using template-based report generation as requested")
    
    # Default to template-based report
    logger.info("Generating template-based report")
    start_time = time.time()
    report = _generate_template_report(results)
    duration = time.time() - start_time
    logger.info(f"Generated template-based report in {duration:.2f} seconds")
    return report

def _generate_template_report(results: Dict[str, Any]) -> str:
    """Generate report using templates and rules, returning plain text format"""
    # Extract key information from the results
    overall_score = results.get("overall_score", 0)
    section_scores = results.get("section_scores", {})
    compliance_level = results.get("compliance_level", "Unknown")
    recommendations = results.get("recommendations", {})
    
    # Determine overall tone based on score
    if overall_score >= 80:
        tone = TONE_POSITIVE
        overall_assessment = "Your organization demonstrates strong compliance with the data protection requirements."
    elif overall_score >= 60:
        tone = TONE_NEUTRAL
        overall_assessment = "Your organization shows moderate compliance with data protection requirements, but there are areas that need improvement."
    else:
        tone = TONE_CONCERNED
        overall_assessment = "Your organization has significant compliance gaps that should be addressed urgently."

    # Generate the report header with plain text formatting
    report = [
        "DATA PROTECTION COMPLIANCE REPORT",
        "=" * 35,
        "",
        "EXECUTIVE SUMMARY",
        "-" * 17,
        f"Based on the assessment, your organization's overall compliance score is {overall_score:.1f}%, "
        f"which indicates a {compliance_level} level of compliance.",
        "",
        f"{overall_assessment}",
        "",
    ]
    
    # Add section insights
    report.append("SECTION ANALYSIS")
    report.append("-" * 15)
    report.append("")
    
    # Sort sections by their scores (ascending) to highlight most critical areas first
    sorted_sections = sorted(section_scores.items(), key=lambda x: x[1] if x[1] is not None else 1.0)
    
    for section, score in sorted_sections:
        if score is None:
            continue
        
        score_percentage = score * 100
        section_recommendations = recommendations.get(section, [])
        
        if score_percentage < 60:
            risk_level = "HIGH RISK"
            action_urgency = "urgent attention"
        elif score_percentage < 75:
            risk_level = "MODERATE RISK"
            action_urgency = "attention"
        else:
            risk_level = "LOW RISK"
            action_urgency = "continued monitoring"
        
        report.append(f"{section} - {score_percentage:.1f}%")
        report.append(f"Risk Level: {risk_level}")
        report.append(f"This area requires {action_urgency}.")
        
        if section_recommendations:
            report.append("Key recommendations:")
            for i, rec in enumerate(section_recommendations[:3], 1):  # Show at most 3 recommendations
                report.append(f"  {i}. {rec}")
            
            if len(section_recommendations) > 3:
                report.append(f"  ...and {len(section_recommendations) - 3} more recommendation(s).")
        
        report.append("")
    
    # Add next steps section
    report.append("SUGGESTED NEXT STEPS")
    report.append("-" * 20)
    report.append("")
    
    if overall_score < 60:
        report.append("Given the high-risk areas identified, we recommend the following priority actions:")
    elif overall_score < 75:
        report.append("To improve your compliance posture, consider the following actions:")
    else:
        report.append("To maintain your strong compliance posture, consider the following actions:")
    
    # Identify top priority areas (lowest scores)
    priority_sections = sorted(
        [(section, score) for section, score in section_scores.items() if score is not None], 
        key=lambda x: x[1]
    )[:3]
    
    for i, (section, _) in enumerate(priority_sections, 1):
        section_recommendations = recommendations.get(section, [])
        if section_recommendations and len(section_recommendations) > 0:
            report.append(f"{i}. Focus on improving {section} by implementing the recommended actions.")
    
    # Return joined report
    return "\n".join(report)

def _generate_report_with_api(results: Dict[str, Any]) -> str:
    """Generate report using external AI API (OpenAI GPT) - returns plain text"""
    api_key = config.get_ai_api_key()
    api_type = config.get_ai_provider()
    
    if not api_key:
        logger.warning("API key not found, falling back to template report")
        return _generate_template_report(results)
    
    # Prepare context for the AI
    logger.info(f"Preparing context data for {api_type} API")
    context = _prepare_ai_context(results)
    
    # Handle different API providers
    logger.info(f"Using API provider: {api_type}")
    if api_type == "openai":
        return _generate_with_openai(context, api_key, use_openrouter=False)
    elif api_type == "azure":
        return _generate_with_azure(context, api_key)
    elif api_type == "openrouter":  # Add explicit handling for openrouter
        logger.info("Using OpenRouter API for report generation")
        return _generate_with_openai(context, api_key, use_openrouter=True)
    else:
        logger.warning(f"Unsupported API type: {api_type}, falling back to template report")
        return _generate_template_report(context)

def _prepare_ai_context(results: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare the context data for the AI model"""
    # Format the input data for the API
    overall_score = results.get("overall_score", 0)
    section_scores = results.get("section_scores", {})
    compliance_level = results.get("compliance_level", "Unknown")
    
    # Convert section scores to list format for better serialization
    section_data = []
    for section, score in section_scores.items():
        if score is not None:
            recommendations = results.get("recommendations", {}).get(section, [])
            section_data.append({
                "name": section,
                "score": score * 100,  # Convert to percentage
                "recommendations": recommendations[:3]  # Limit to top 3 recommendations
            })
    
    # Create the context object
    context = {
        "overall_score": overall_score,
        "compliance_level": compliance_level,
        "sections": section_data,
        "regulation": "Data Protection and Privacy Compliance"
    }
    
    return context

def _generate_with_openai(context: Dict[str, Any], api_key: str, use_openrouter: bool = False) -> str:
    """Generate a report using OpenAI API through OpenRouter or directly"""
    # Update to use OpenAI client format (v1.0.0+)
    from openai import OpenAI
    
    # Initialize client with appropriate configuration
    if use_openrouter:
        logger.info("Configuring client for OpenRouter API")
        logger.info(f"API Key (first 4 chars): {api_key[:4] if api_key and len(api_key) > 4 else 'N/A'}...")
        client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
        model = "deepseek/deepseek-r1:free"
        logger.info(f"Using OpenRouter with model: {model}")
    else:
        logger.info("Configuring client for direct OpenAI API")
        logger.info(f"API Key (first 4 chars): {api_key[:4] if api_key and len(api_key) > 4 else 'N/A'}...")
        client = OpenAI(api_key=api_key)
        model = "gpt-4o-2024-05-13"
        logger.info(f"Using OpenAI with model: {model}")
        
    # Create the prompt
    logger.info("Creating AI prompt from context data")
    prompt = _create_openai_prompt(context)
    logger.info(f"Created prompt with length: {len(prompt)} characters")
    
    # Make the API request with retry logic
    max_retries = 3
    backoff_factor = 2
    retry_count = 0
    
    while retry_count < max_retries:
        try:
            logger.info(f"Making API request attempt {retry_count + 1}/{max_retries}")
            start_time = time.time()
            
            # Build request parameters based on API provider
            request_params = {
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are an expert compliance analyst specializing in data protection regulations. Create a professional compliance report based on the assessment results provided. Return a plain text report without any formatting or markup. The text should be clear and easy to read without requiring any special rendering."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 2000
            }
            
            # Add OpenRouter specific parameters if using OpenRouter
            if use_openrouter:
                request_params["extra_headers"] = {
                    "HTTP-Referer": "https://datainfa.com",
                    "X-Title": "Compliance Assessment Tool",
                }
            
            # Make the API call
            logger.info(f"Sending request to {'OpenRouter' if use_openrouter else 'OpenAI'} API")
            response = client.chat.completions.create(**request_params)
            
            # Calculate and log API call duration
            duration = time.time() - start_time
            logger.info(f"API call completed successfully in {duration:.2f} seconds")
            
            # Access response properties as object attributes
            report_content = response.choices[0].message.content
            logger.info(f"Received response with content length: {len(report_content)} characters")
            
            # Log usage statistics if available
            try:
                usage = dict(response).get('usage', {})
                logger.info(f"API usage statistics: {usage}")
            except Exception as e:
                logger.warning(f"Could not extract usage statistics: {str(e)}")
                
            # Return the content exactly as received - we specifically requested plain text
            return report_content
            
        except Exception as e:
            retry_count += 1
            logger.error(f"API request failed (attempt {retry_count}/{max_retries}): {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            
            # Add more detailed error logging for specific error types
            if "rate_limit" in str(e).lower():
                logger.error("Rate limit exceeded. Consider increasing backoff or reducing request frequency.")
            elif "auth" in str(e).lower() or "api key" in str(e).lower():
                logger.error("Authentication error. Please check your API key.")
            
            if retry_count == max_retries:
                logger.error(f"Failed to generate report with API after {max_retries} attempts. Falling back to template.")
                return _generate_template_report(context)
            
            wait_time = backoff_factor ** retry_count
            logger.warning(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)
    
    # Fallback to template report if all retries fail
    logger.error("All API attempts failed. Using template-based report as fallback.")
    return _generate_template_report(context)

def _generate_with_azure(context: Dict[str, Any], api_key: str) -> str:
    """Generate a report using Azure OpenAI API"""
    # Azure OpenAI implementation
    # This would be similar to the OpenAI implementation but with Azure endpoints
    # For now, we'll fall back to the template report
    logger.warning("Azure OpenAI integration not fully implemented yet")
    return _generate_template_report(context)

def _create_openai_prompt(context: Dict[str, Any]) -> str:
    """Create a detailed prompt for the OpenAI API requesting plain text output"""
    overall_score = context["overall_score"]
    compliance_level = context["compliance_level"]
    sections = context["sections"]
    
    # Serialize the section data in a readable format
    sections_text = ""
    for section in sections:
        sections_text += f"\n- {section['name']}: {section['score']:.1f}% compliance"
        if section.get('recommendations'):
            sections_text += "\n  Key recommendations:"
            for i, rec in enumerate(section['recommendations'], 1):
                sections_text += f"\n  {i}. {rec}"
    
    prompt = f"""
Generate a detailed compliance report based on the following assessment results:

Overall Compliance Score: {overall_score:.1f}%
Compliance Level: {compliance_level}

Section Scores and Recommendations:{sections_text}

Your report should include:
1. An executive summary assessing the overall compliance status
2. Analysis of each section with risk levels and implications
3. Prioritized action items with clear descriptions
4. Strategic recommendations for improving compliance posture

Please format the report in plain text:
- Use clear section headings (can use UPPERCASE for section titles)
- Use simple line breaks to separate sections
- Indicate risk levels clearly (e.g., "HIGH RISK", "MODERATE RISK", "LOW RISK")
- Use simple numbered lists for action items
- Keep paragraphs concise and readable

Ensure the tone is professional but accessible, avoiding overly technical language.
Use data-driven insights to provide specific, actionable recommendations.

IMPORTANT: Return ONLY the plain text report without ANY explanatory text or special formatting.
"""
    
    return prompt

def _is_api_configured() -> bool:
    """Check if external AI API is configured"""
    logger.info("Checking AI API configuration")
    
    # Update to use direct properties instead of function calls if they exist
    # Otherwise, fall back to the function calls for compatibility
    ai_enabled = getattr(config, "AI_ENABLED", None)
    if ai_enabled is None:
        try:
            ai_enabled = config.get_ai_enabled()
            logger.info(f"Got AI_ENABLED via function: {ai_enabled}")
        except AttributeError:
            logger.warning("Could not find AI_ENABLED property or function, defaulting to False")
            ai_enabled = False
            
    ai_api_key = getattr(config, "AI_API_KEY", None)
    if ai_api_key is None:
        try:
            ai_api_key = config.get_ai_api_key()
            logger.info(f"Got AI_API_KEY via function, length: {len(ai_api_key) if ai_api_key else 0}")
        except AttributeError:
            logger.warning("Could not find AI_API_KEY property or function")
            ai_api_key = None
    else:
        logger.info(f"Got AI_API_KEY directly, length: {len(ai_api_key) if ai_api_key else 0}")
    
    # Log detailed configuration status
    if ai_enabled and ai_api_key:
        logger.info("AI API is fully configured and enabled")
        logger.info(f"API key first 4 chars: {ai_api_key[:4] if ai_api_key and len(ai_api_key) > 4 else 'N/A'}")
        return True
    elif not ai_enabled:
        logger.info("AI API is disabled in configuration")
        return False
    elif not ai_api_key:
        logger.warning("AI API is enabled but no API key is available")
        return False
    
    return False