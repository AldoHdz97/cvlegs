import streamlit as st
import time
import logging
from datetime import datetime, timedelta

from api_client import get_cv_client, initialize_backend

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page config
st.set_page_config(
    page_title="CV Assistant",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "greeting_sent" not in st.session_state:
    st.session_state.greeting_sent = False
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = None
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Interview scheduling state
if "show_calendar" not in st.session_state:
    st.session_state.show_calendar = False
if "selected_date" not in st.session_state:
    st.session_state.selected_date = None
if "selected_time" not in st.session_state:
    st.session_state.selected_time = None
if "interview_note" not in st.session_state:
    st.session_state.interview_note = ""

# Initialize backend
cv_client = initialize_backend()

# Theme styling
def apply_theme():
    bg_color = "#000510" if st.session_state.dark_mode else "#ffffff"
    text_color = "#ffffff" if st.session_state.dark_mode else "#222326"
    status_color = "#4CAF50" if st.session_state.backend_connected else "#F44336"
    
    st.markdown(f"""
    <style>
        .stApp {{
            background-color: {bg_color} !important;
            color: {text_color} !important;
        }}
        .main .block-container {{
            background-color: {bg_color} !important;
        }}
        .backend-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: {status_color};
            color: white;
            padding: 5px 10px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: bold;
            opacity: 0.8;
        }}
        #MainMenu, footer, header {{visibility: hidden;}}
    </style>
    """, unsafe_allow_html=True)

apply_theme()

# Backend status indicator
status_text = "🟢 Connected" if st.session_state.backend_connected else "🔴 Offline"
st.markdown(f'<div class="backend-status">{status_text}</div>', unsafe_allow_html=True)

# Title
st.markdown(
    "<h2 style='text-align:center;font-weight:300;margin:20px 0;'>CV Assistant</h2>",
    unsafe_allow_html=True
)

# Sidebar
with st.sidebar:
    st.header("⚙️ Settings")
    
    # Backend status
    if st.session_state.backend_connected:
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Offline")
        if st.button("🔄 Reconnect", key="reconnect"):
            cv_client = initialize_backend()
            st.rerun()
    
    st.markdown("---")
    
    # Theme toggle
    if st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode):
        st.session_state.dark_mode = True
    else:
        st.session_state.dark_mode = False
    
    st.markdown("---")
    
    # Interview scheduling
    if st.button("📅 Schedule Interview", use_container_width=True):
        st.session_state.show_calendar = True
    
    if st.session_state.show_calendar:
        st.markdown("##### Pick a date")
        today = datetime.now()
        dates = [(today + timedelta(days=i)).strftime("%A, %B %d") for i in range(14)]
        st.session_state.selected_date = st.selectbox("Available dates", dates)
        
        st.markdown("##### Pick a time")
        times = ["9:00 AM", "10:30 AM", "12:00 PM", "2:00 PM", "3:30 PM", "5:00 PM"]
        st.session_state.selected_time = st.selectbox("Available times", times)
        
        st.markdown("##### Note (optional)")
        st.session_state.interview_note = st.text_area("Add a note", height=80)
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_calendar = False
                st.rerun()
        with col2:
            if st.button("✅ Schedule", use_container_width=True, type="primary"):
                st.success("Interview request sent! You'll receive confirmation via email.")
                st.session_state.show_calendar = False
                time.sleep(2)
                st.rerun()

# Streaming function
def stream_message(message, delay=0.02):
    """Stream message word by word"""
    container = st.empty()
    text = ""
    words = message.split()
    
    for word in words:
        text += word + " "
        container.markdown(text)
        time.sleep(delay)
    
    return text.strip()

# Initial greeting
if not st.session_state.greeting_sent:
    greeting = (
        "Hi there! I'm Aldo's digital assistant. "
        "Ask me anything about his professional experience, skills, or background. "
        "I'm here to help you learn more about his qualifications and expertise."
    )
    
    with st.chat_message("assistant"):
        streamed_greeting = stream_message(greeting)
    
    st.session_state.messages.append({"role": "assistant", "content": streamed_greeting})
    st.session_state.greeting_sent = True

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about Aldo's professional background..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate response
    with st.chat_message("assistant"):
        if st.session_state.backend_connected:
            # Use backend
            with st.spinner("Thinking..."):
                response = cv_client.query_cv(prompt)
                
                if response.success:
                    answer = stream_message(response.content)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
                    
                    # Show response time
                    if response.processing_time:
                        st.caption(f"⚡ Response time: {response.processing_time:.2f}s")
                else:
                    error_msg = f"⚠️ Sorry, I'm having trouble accessing my knowledge base. {response.error or 'Please try again.'}"
                    answer = stream_message(error_msg)
                    st.session_state.messages.append({"role": "assistant", "content": answer})
        else:
            # Fallback responses when backend is offline
            fallback_responses = {
                "skills": "Aldo has strong technical skills including Python, SQL, data analysis, and AI/ML. He's experienced with FastAPI, Tableau, and modern web technologies.",
                "experience": "Aldo works as a Social Listening & Insights Analyst at Swarm Data and People, analyzing performance for Tec de Monterrey campuses. He previously worked as a Data Analyst at Wii México.",
                "education": "Aldo graduated with a B.A. in Economics from Tecnológico de Monterrey (2015-2021) and has certifications in Power BI and LLM Engineering.",
                "projects": "Aldo has built several impressive projects including a CV-AI system with FastAPI and OpenAI, business growth analysis dashboards, and NFL betting analytics."
            }
            
            # Simple keyword matching for fallback
            response_key = "skills"
            for key in fallback_responses.keys():
                if key in prompt.lower():
                    response_key = key
                    break
            
            fallback_answer = fallback_responses.get(response_key, 
                "I'd be happy to tell you about Aldo's professional background! He's an economist and data analyst with strong technical skills. What specific area would you like to know more about?")
            
            answer = stream_message(fallback_answer)
            st.session_state.messages.append({"role": "assistant", "content": answer})
