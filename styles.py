"""
Centralized CSS styles for the Compliance Assessment Tool.

This module contains all CSS styling used throughout the application,
organized by component or page.
"""

def get_common_button_css():
    """Return the CSS for common button styling"""
    return """
        <style>
        /* Common button styles - Material UI inspired */
        button, .stButton>button {
            background-color: #262730 !important;
            color: #fafafa !important;
            border: none !important;
            border-radius: 4px !important;
            text-align: left !important;
            padding: 0.5rem 0.75rem !important;  /* Reduced padding */
            font-size: 0.85rem !important;      /* Smaller font */
            transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24) !important;
            margin: 0.25rem 0 !important;      /* Reduced margin */
            width: 100% !important;
            min-height: 36px !important;       /* Material UI standard height */
            line-height: 1.2 !important;
            letter-spacing: 0.01em !important;
        }
        
        /* Hover state */
        button:hover:not(:disabled), .stButton>button:hover:not(:disabled) {
            background-color: #3b3b49 !important;
            box-shadow: 0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23) !important;
            transform: translateY(-1px) !important;
        }
        
        /* Active/Selected state */
        button:active, .stButton>button:active,
        button[data-testid="baseButton-secondary"] {
            background-color: #2b2d3a !important;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24) !important;
            transform: translateY(0) !important;
        }

        /* Primary button style */
        button[kind="primary"], .stButton>button[kind="primary"] {
            background-color: #2b2d3a !important;
            text-align: center !important;
            font-weight: 500 !important;
        }

        /* Secondary button style */
        button[kind="secondary"], .stButton>button[kind="secondary"] {
            background-color: #1e1e2d !important;
            text-align: center !important;
            opacity: 0.9 !important;
        }
        
        /* Special button styles (like print button) */
        button.special-button {
            background-color: #2b2d3a !important;
            text-align: center !important;
            font-size: 0.85rem !important;
            padding: 0.5rem 1rem !important;
            letter-spacing: 0.02em !important;
        }
        
        /* Disabled state */
        button:disabled, .stButton>button:disabled {
            background-color: #1e1e1e !important;
            color: #666666 !important;
            box-shadow: none !important;
            cursor: not-allowed !important;
            opacity: 0.7 !important;
        }

        /* Container spacing for button groups */
        div.element-container {
            margin-bottom: 0.25rem !important;  /* Reduced margin between containers */
        }

        /* Fix Streamlit's default padding */
        .stButton {
            margin: 0 !important;
            padding: 0 !important;
        }

        /* Navigation panel specific styling */
        section[data-testid="stSidebarContent"] div.stButton button {
            margin: 0.15rem 0 !important;  /* Reduced from 0.4rem to 0.15rem */
            padding: 0.5rem 0.75rem !important;  /* Reduced padding */
            min-height: 32px !important;  /* Reduced from 36px */
        }
        
        /* Compact input styling */
        div[data-testid="stTextInput"] input, 
        div.stSelectbox div[role="listbox"],
        div.stSelectbox div[role="option"] {
            padding: 0.25rem 0.5rem !important;
            min-height: 32px !important;
            font-size: 0.85rem !important;
        }
        
        /* Make select boxes more compact */
        .stSelectbox > div:first-child {
            min-height: 32px !important;
        }
        </style>
    """

def get_landing_page_css():
    """Return the CSS for the landing page"""
    return """
        <style>
        .main > div {
            padding: 1rem;
            max-width: 800px;
            margin: 0 auto;
        }
        /* Remove specific button styling and use common styles */
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
            /* Remove specific button styling and use common styles */
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

def get_header_css():
    """Return the CSS for the application header"""
    return """
        <style>
        .app-header {
            margin-bottom: 0;
            padding: 0.15rem 0;
            border-bottom: 1px solid rgba(49, 51, 63, 0.2);
        }
        .app-header h1 {
            margin: 0;
            font-size: 1.8em;
        }
        .app-header p {
            font-size: 1.2em;
            font-weight: 500;
            margin: 0;
            line-height: 1.2;
        }
        /* Fix for large gap between header and content */
        .block-container {
            padding-top: 1rem !important;
            margin-top: 0 !important;
        }
        /* Remove excessive padding in the main area */
        .main .block-container {
            padding-top: 1rem !important; 
            padding-bottom: 1rem !important;
        }
        /* Fix for empty text input elements */
        [data-testid="stTextInput"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        /* Hide elements that may cause unwanted spacing */
        .element-container:empty {
            display: none !important;
            height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
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

# Update the print button HTML to use the special-button class
def get_print_button_html():
    """Return the HTML for the print button"""
    return """
    <div style="text-align: right; margin: 0.5rem 0;">
        <button 
            onclick="window.print()"
            class="special-button"
            style="padding: 8px 16px; font-size: 14px; margin: 4px 2px;"
        >
            📄 Export as PDF
        </button>
    </div>
    """

# Update section navigation to use common button styles
def get_section_navigation_css():
    """Return the CSS for the section navigation in dark theme"""
    return """
        <style>
        section[data-testid="stSidebarContent"] div.stExpander {
            background-color: transparent !important;
            border: none !important;
        }
        
        /* Dark background for the content area */
        section[data-testid="stSidebarContent"] div.stExpander > div[data-testid="stExpanderContent"] {
            background-color: #0e1117 !important;
            color: #fafafa !important;
            padding: 0 !important;
        }
        
        /* Remove default streamlit styling that causes white backgrounds */
        section[data-testid="stSidebarContent"] div.stExpander > div[data-testid="stExpanderContent"] p {
            color: #d1d1d1 !important;
            font-size: 0.9rem !important;
            margin: 0.5rem 0 !important;
        }
        
        /* Dark themed section buttons */
        section[data-testid="stSidebarContent"] div.stButton button {
            background-color: #444; /* Darker background */
            color: #fafafa; /* Light text for visibility */
            border: 1px solid #555; /* Slightly lighter border */
            border-radius: 4px !important;
            text-align: left !important;
            margin: 0.4rem 0 !important;
            padding: 0.75rem 0.75rem !important;
            font-size: 0.9rem !important;
            transition: all 0.2s ease !important;
            box-shadow: none !important;
        }
        
        /* Hover effect */
        section[data-testid="stSidebarContent"] div.stButton button:hover:not(:disabled) {
            background-color: #555 !important; /* Darker on hover */
            border-color: #777 !important; /* Lighter border on hover */
        }
        
        /* Fix any white backgrounds in the navigation panel */
        section[data-testid="stSidebarContent"] div,
        section[data-testid="stSidebarContent"] div.stExpander,
        section[data-testid="stSidebarContent"] div.stExpanderContent {
            background-color: transparent !important;
        }
        
        /* Caption text styling */
        section[data-testid="stSidebarContent"] div.stExpander .caption {
            color: #d1d1d1 !important;
            font-size: 0.85rem !important;
            margin-top: 0.75rem !important;
        }
        
        /* Style the expander itself to match dark theme */
        section[data-testid="stSidebarContent"] div.streamlit-expanderHeader {
            background-color: #262730 !important;
            color: white !important;
            border-radius: 4px !important;
        }
        
        /* Make sure all text in sidebar is light colored */
        section[data-testid="stSidebarContent"] div {
            color: #d1d1d1;
        }
        </style>
    """

