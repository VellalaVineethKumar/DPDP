"""
Response viewer utility for debugging assessment responses.

This script helps administrators inspect and debug user responses
stored in session state.
"""

import streamlit as st
import json
import sys
from datetime import datetime

def display_responses(responses_dict):
    """Display structured view of assessment responses"""
    st.title("Assessment Response Viewer")
    
    if not responses_dict:
        st.warning("No responses found")
        return
        
    # Group responses by section
    sections = {}
    for key, value in responses_dict.items():
        if key.startswith('s') and '_q' in key:
            try:
                section_idx = int(key.split('_')[0][1:])
                question_idx = int(key.split('_')[1][1:])
                
                if section_idx not in sections:
                    sections[section_idx] = {}
                    
                sections[section_idx][question_idx] = value
            except (ValueError, IndexError):
                st.error(f"Could not parse response key: {key}")
    
    # Display responses by section
    for section_idx in sorted(sections.keys()):
        with st.expander(f"Section {section_idx + 1}", expanded=True):
            questions = sections[section_idx]
            for question_idx in sorted(questions.keys()):
                response = questions[question_idx]
                
                # Display with color coding based on apparent score
                if response.lower().startswith(("yes", "full", "comprehensive")):
                    st.markdown(f"**Q{question_idx + 1}**: ✅ `{response}`")
                elif response.lower().startswith(("partial", "basic", "limited", "mostly")):
                    st.markdown(f"**Q{question_idx + 1}**: ⚠️ `{response}`")
                elif response.lower().startswith(("no", "not ", "none", "rarely")):
                    st.markdown(f"**Q{question_idx + 1}**: ❌ `{response}`")
                elif "not applicable" in response.lower():
                    st.markdown(f"**Q{question_idx + 1}**: ℹ️ `{response}`")
                else:
                    st.markdown(f"**Q{question_idx + 1}**: `{response}`")
                    
    # Export option
    if st.button("Export Responses to JSON"):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_data = {
            "timestamp": timestamp,
            "responses": responses_dict
        }
        
        json_str = json.dumps(export_data, indent=2)
        st.download_button(
            label="Download JSON",
            data=json_str,
            file_name=f"responses_{timestamp}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    responses = {}
    # Check if a file was provided
    if len(sys.argv) > 1:
        file_path = sys.argv[1]
        try:
            with open(file_path, 'r') as f:
                responses = json.load(f)
        except Exception as e:
            st.error(f"Error loading responses file: {e}")
            
    # Run in Streamlit context
    if 'st' in globals():
        if 'responses' in st.session_state:
            display_responses(st.session_state.responses)
        else:
            st.warning("No response data available in session state")
