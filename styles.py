"""
Centralized CSS styles for the Compliance Assessment Tool.

This module contains all CSS styling used throughout the application,
organized by component or page.
"""

def get_landing_page_css():
    """Return the CSS for the landing page"""
    return """
        <style>
        .main > div {
            padding: 2rem;
            max-width: 800px;
            margin: 0 auto;
        }
        .stButton>button {
            width: 100%;
            margin-top: 1rem;
            padding: 0.5rem;
            font-size: 1.1rem;
        }
        .logo-container {
            text-align: center;
            padding: 2rem 0;
        }
        .logo-container img {
            max-width: 300px;  /* Increased from 75px to 300px */
            margin: 0 auto;
            display: block;
        }
        .title-container {
            text-align: center;
            margin-bottom: 2rem;
        }
        .footer {
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 1rem;
            text-align: center;
            font-size: 0.8rem;
            color: #888;
        }
        </style>
    """

def get_sidebar_css():
    """Return the CSS for the sidebar navigation"""
    return """
        <style>
            section[data-testid="stSidebar"] > div {
                padding-top: 0;
                background-color: #0e1117;
            }
            section[data-testid="stSidebar"] .stButton > button {
                background: none !important;
                border: none !important;
                width: 100%;
                text-align: left;
                color: #fafafa;
                padding: 0.75rem 1.5rem;
                margin: 0.25rem 0;
                transition: all 0.2s ease;
                font-size: 0.95rem;
                font-weight: 400;
                box-shadow: none !important;
            }
            section[data-testid="stSidebar"] .stButton > button:hover {
                color: #1a73e8;
            }
            section[data-testid="stSidebar"] .stButton > button[data-testid="baseButton-secondary"] {
                color: #1a73e8;
                background-color: #e8f0fe !important;
                border-left: 3px solid #1a73e8 !important;
            }
            section[data-testid="stSidebar"] .nav-title {
                padding: 1rem 1.5rem;
                font-size: 0.8rem;
                text-transform: uppercase;
                letter-spacing: 0.1em;
                color: #fafafa;
                font-weight: 600;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 0.5rem;
            }
            section[data-testid="stSidebar"] .logo-container {
                padding: 1.5rem;
                border-bottom: 1px solid #dee2e6;
                margin-bottom: 0.5rem;
            }
        </style>
    """

def get_radio_button_css():
    """Return the CSS for enhanced radio buttons"""
    return """
        <style>
        div.row-widget.stRadio > div {
            flex-direction: column;
            gap: 10px;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label {
            padding: 10px;
            background: #262730;  /* Changed to darker background to match Streamlit's theme */
            border: 1px solid #4e4e61;  /* Added border for better visibility */
            border-radius: 5px;
            width: 100%;
            transition: background-color 0.3s;
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label:hover {
            background: #3b3b49;  /* Slightly lighter on hover */
            border-color: #6e6e80;  /* Brighter border on hover */
        }
        div.row-widget.stRadio > div[role="radiogroup"] > label > div:first-child {
            margin-right: 10px;
        }
        </style>
    """

def get_print_export_css():
    """Return the CSS for print/PDF export"""
    return """
    <style>
    @media print {
        header, footer, .stSidebar, .main .block-container > div:first-child, 
        button[kind="primary"], button[kind="secondary"], .reportview-container .main footer,
        .viewerBadge_container__1QSob, [data-testid="stToolbar"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 100% !important;
            padding: 0 !important;
        }
        [data-testid="stHeader"] {
            display: none !important;
        }
        h1 {
            text-align: center;
            font-size: 1.5em !important;
        }
        @page {
            margin: 0.5cm;
        }
        body {
            print-color-adjust: exact !important;
            -webkit-print-color-adjust: exact !important;
        }
    }
    </style>
    """

def get_expiry_box_css():
    """Return the CSS for admin token expiry box styling"""
    return """
    <style>
    /* Fix alignment between input and display box */
    div[data-testid="column"] > div {
        display: flex;
        align-items: center;
        height: 100%;
    }
    /* Ensure the number input element is properly aligned */
    div[data-testid="stNumberInput"] {
        margin-bottom: 0 !important;
    }
    /* Style for the expiry box */
    .expiry-box {
        background-color: #262730;
        color: #ffffff;
        border-radius: 5px;
        padding: 10px 15px;
        display: flex;
        align-items: center;
        height: 42px;
        box-sizing: border-box;
        margin-top: 23px; /* Match label height offset */
    }
    </style>
    """

def get_print_button_html():
    """Return the HTML for the print button"""
    return """
    <div style="text-align: right; margin: 0.5rem 0;">
        <button 
            onclick="window.print()"
            style="
                background-color: #4CAF50;
                border: none;
                color: white;
                padding: 8px 16px;
                text-align: center;
                text-decoration: none;
                display: inline-block;
                font-size: 14px;
                margin: 4px 2px;
                cursor: pointer;
                border-radius: 4px;
            "
        >
            📄 Export as PDF
        </button>
    </div>
    """
