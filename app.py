import streamlit as st
import time
import logging
from datetime import datetime, timedelta
import hashlib
import uuid

# Import from our separate API client module - now with multi-user support
from api_client import get_session_cv_client, initialize_session_backend, APIResponse

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="hola",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CACHE BUSTING AND UNIQUE SESSION ---
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "css_version" not in st.session_state:
    st.session_state.css_version = hashlib.md5(f"{time.time()}{st.session_state.session_id}".encode()).hexdigest()[:8]

# --- SESSION STATE INITIALIZATION ---
# Theme with better initialization
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

if "manual_theme_override" not in st.session_state:
    st.session_state.manual_theme_override = False

# Interview scheduling
if "show_calendar_picker" not in st.session_state:
    st.session_state.show_calendar_picker = False
if "selected_day" not in st.session_state:
    st.session_state.selected_day = None
if "selected_time" not in st.session_state:
    st.session_state.selected_time = None
if "contact_info" not in st.session_state:
    st.session_state.contact_info = ""
if "scheduling_step" not in st.session_state:
    st.session_state.scheduling_step = 0

# Chat
if "messages" not in st.session_state:
    st.session_state.messages = []
if "greeting_streamed" not in st.session_state:
    st.session_state.greeting_streamed = False

# Config
if "show_config" not in st.session_state:
    st.session_state.show_config = False

# Backend connection status
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = None

if "user_session_id" not in st.session_state:
    st.session_state.user_session_id = None

# Validation error state
if "validation_error" not in st.session_state:
    st.session_state.validation_error = None

# --- VALIDATION FUNCTIONS ---
def validate_message(message):
    """Validate user message before sending to API"""
    if not message or not message.strip():
        return False, "Please enter a message"
    
    word_count = len(message.strip().split())
    if word_count < 2:
        return False, "Sorry, your message is too short. Please provide more details."
    
    if len(message.strip()) < 5:
        return False, "Sorry, your message is too short. Please provide more details."
    
    return True, ""

def show_validation_error(error_message):
    """Display validation error bubble"""
    st.session_state.validation_error = error_message

# --- BACKEND INITIALIZATION ---
def get_user_cv_client():
    """Get session-specific CV client"""
    return get_session_cv_client()

def initialize_user_backend():
    """Initialize backend per user session"""
    try:
        client = initialize_session_backend()
        logger.info(f"Backend initialized for user session: {st.session_state.user_session_id[:8] if st.session_state.user_session_id else 'unknown'}")
        return client
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        st.session_state.backend_connected = False
        return None

# Initialize backend
cv_client = initialize_user_backend()
if cv_client is None:
    st.session_state.backend_connected = False
else:
    st.session_state.backend_connected = None

# --- MINIMAL THEME CONTROL ---
def set_theme():
    """Minimal theme system - only essential styling"""
    if st.session_state.dark_mode:
        bg, text = "#000510", "#ffffff"
        sidebar_bg = "#0f0f0f"
        input_bg = "#1a1a1a"
        border_color = "#333"
    else:
        bg, text = "#ffffff", "#222326"
        sidebar_bg = "#fafafa"
        input_bg = "#ffffff"
        border_color = "#e0e0e0"

    # MINIMAL CSS - only core theming, no interference with controls
    css_content = f"""
    <style>
        /* Core app background */
        .stApp {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        /* Sidebar background */
        .stSidebar {{
            background-color: {sidebar_bg} !important;
        }}
        
        /* Chat input */
        .stChatInput > div {{
            background: {input_bg} !important;
            border: 2px solid {border_color} !important;
            border-radius: 24px !important;
        }}
        
        .stChatInput textarea {{
            color: {text} !important;
        }}
        
        /* Hide Streamlit branding only */
        #MainMenu, footer, header {{
            visibility: hidden !important;
        }}
        
        /* Error message */
        .validation-bubble {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: red !important;
            color: white !important;
            padding: 16px 24px;
            border-radius: 8px;
            z-index: 1000;
            animation: fadeOut 3s forwards;
        }}
        
        @keyframes fadeOut {{
            0% {{ opacity: 1; }}
            70% {{ opacity: 1; }}
            100% {{ opacity: 0; visibility: hidden; }}
        }}
    </style>
    """
    
    st.markdown(css_content, unsafe_allow_html=True)
    return bg, text

bg, text = set_theme()

# Handle theme detection from URL
if "theme_auto" in st.query_params and not st.session_state.manual_theme_override:
    theme_auto = st.query_params.get("theme_auto")
    session_param = st.query_params.get("s")
    
    if session_param == st.session_state.session_id:
        if theme_auto == "dark" and not st.session_state.dark_mode:
            st.session_state.dark_mode = True
            st.query_params.clear()
            st.rerun()
        elif theme_auto == "light" and st.session_state.dark_mode:
            st.session_state.dark_mode = False
            st.query_params.clear()
            st.rerun()

# Validation error display
if st.session_state.validation_error:
    st.markdown(f"""
    <div class="validation-bubble">
        {st.session_state.validation_error}
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(0.1)
    st.session_state.validation_error = None

# Backend status
if st.session_state.backend_connected is False:
    st.error("Backend Offline")

# Title
st.markdown(
    f"<h2 style='font-family:Roboto,sans-serif;font-weight:300;margin-bottom:8px;margin-top:8px;color:{text};text-align:center;'>hola,welcome</h2>",
    unsafe_allow_html=True,
)

# Sidebar
with st.sidebar:
    st.header("Configuration")
    
    if st.session_state.backend_connected is False:
        st.error("Backend Offline")
        if st.button("Reconnect", key="reconnect_backend"):
            cv_client = initialize_user_backend()
            st.rerun()
    
    st.markdown("---")
    
    st.selectbox(
        "Response Style",
        ["Detailed", "Summary", "Bullet points", "Technical", "Conversational"],
        index=0,
        key="response_format",
        help="Choose how you'd like responses formatted"
    )
    
    # Theme toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.session_state.manual_theme_override = True
        st.rerun()

    st.markdown("---")
    
    # Schedule Interview
    if st.button("📅 Schedule an Interview", key="open_schedule", use_container_width=True):
        st.session_state.show_calendar_picker = True
        st.session_state.scheduling_step = 0
        st.rerun()

    if st.session_state.show_calendar_picker:
        
        if st.session_state.scheduling_step == 0:
            st.markdown("##### Step 1: Pick a day")
            today = datetime.now()
            days = [(today + timedelta(days=i)).strftime("%A, %B %d, %Y") for i in range(14)]
            selected = st.selectbox("Available Days", days, key="day_select")
            st.session_state.selected_day = selected
            
            col1, col2 = st.columns([1, 2])
            with col2:
                if st.button("Next", key="next_to_time", use_container_width=True):
                    st.session_state.scheduling_step = 1
                    st.rerun()
        
        elif st.session_state.scheduling_step == 1:
            st.markdown("##### Step 2: Pick a time slot")
            slots = [
                "8:00-9:30 AM", "9:30-11:00 AM", "11:00-12:30 PM",
                "12:30-2:00 PM", "2:00-3:30 PM", "3:30-5:00 PM"
            ]
            selected_time = st.selectbox("Available Times", slots, key="slot_select")
            st.session_state.selected_time = selected_time
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back", key="back_to_day", use_container_width=True):
                    st.session_state.scheduling_step = 0
                    st.rerun()
            with col2:
                if st.button("Next", key="next_to_contact", use_container_width=True):
                    st.session_state.scheduling_step = 2
                    st.rerun()
        
        elif st.session_state.scheduling_step == 2:
            st.markdown("##### Step 3: Contact information")
            contact_info = st.text_area(
                "Please provide your contact information (email, phone, or preferred method):",
                value=st.session_state.contact_info,
                key="contact_area", 
                height=80,
                placeholder="e.g., john@email.com or +1234567890"
            )
            st.session_state.contact_info = contact_info
            
            st.info("You'll receive a confirmation once your request is reviewed.")
            
            with st.expander("Review Summary", expanded=True):
                st.write(f"**Day:** {st.session_state.selected_day}")
                st.write(f"**Time:** {st.session_state.selected_time}")
                if contact_info.strip():
                    st.write(f"**Contact:** {contact_info}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Back", key="back_to_time", use_container_width=True):
                    st.session_state.scheduling_step = 1
                    st.rerun()
            with col2:
                if st.button("Request Interview", key="submit_int", type="primary", use_container_width=True):
                    if contact_info.strip():
                        st.success("Interview request sent! You'll receive a confirmation soon.")
                        st.session_state.show_calendar_picker = False
                        st.session_state.scheduling_step = 0
                        st.session_state.selected_day = None
                        st.session_state.selected_time = None
                        st.session_state.contact_info = ""
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("Please provide contact information.")

        st.markdown("---")
        if st.button("Cancel", key="cancel_int", use_container_width=True):
            st.session_state.show_calendar_picker = False
            st.session_state.scheduling_step = 0
            st.rerun()

def stream_message(msg, delay=0.016):
    output = st.empty()
    txt = ""
    for char in msg:
        txt += char
        output.markdown(txt)
        time.sleep(delay)
    return txt

# Initial greeting
if not st.session_state.greeting_streamed:
    greeting = ("Hi there! I'm Aldo—or at least, my digital twin. "
                "Go ahead and ask me anything about my professional life, projects, or skills. "
                "I promise not to humblebrag too much (okay, maybe just a little).")
    
    with st.chat_message("assistant"):
        streamed_greeting = stream_message(greeting)
    
    st.session_state.messages.append({"role": "assistant", "content": streamed_greeting})
    st.session_state.greeting_streamed = True
else:
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Chat input with validation
if prompt := st.chat_input("Ask! Don't be shy !", key="main_chat_input"):
    is_valid, error_message = validate_message(prompt)
    
    if not is_valid:
        show_validation_error(error_message)
        st.rerun()
    else:
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        with st.chat_message("assistant"):
            if st.session_state.backend_connected is False or not cv_client:
                # Simple loading indicator
                with st.spinner("Thinking..."):
                    time.sleep(0.5)
                
                if any(word in prompt.lower() for word in ['skill', 'technology', 'programming', 'language']):
                    answer = "Great question about skills! Based on Aldo's background, he has extensive experience with Python, SQL, Tableau, and data analysis. He's particularly strong in economics, data visualization, and building automated reporting systems. His technical skills span from web scraping to machine learning applications."
                elif any(word in prompt.lower() for word in ['experience', 'work', 'job', 'company']):
                    answer = "Aldo has diverse professional experience! He's currently a Social Listening & Insights Analyst at Swarm Data and People, where he analyzes performance for multiple Tec de Monterrey campuses. Previously, he worked as a Data Analyst at Wii México and had his own content creation business. His experience spans data analysis, automation, and stakeholder engagement."
                elif any(word in prompt.lower() for word in ['education', 'degree', 'university', 'study']):
                    answer = "Aldo graduated with a B.A. in Economics from Tecnológico de Monterrey (2015-2021). His academic background includes statistical analysis projects using Python and R. He's also earned certifications in Tableau Desktop, Power BI, and OpenAI development."
                elif any(word in prompt.lower() for word in ['project', 'built', 'created', 'developed']):
                    answer = "Aldo has worked on fascinating projects! Some highlights include: a Business Growth Analysis dashboard tracking business density across Nuevo León municipalities, an NFL Betting Index aggregation system, and an AI-driven CV Manager using Next.js and OpenAI. His projects showcase skills in data visualization, web development, and AI integration."
                else:
                    answer = f"Thank you for asking about '{prompt}'. I'd be happy to help you learn more about Aldo's professional background! He's an accomplished economist and data analyst with strong technical skills in Python, data visualization, and AI applications. What specific aspect would you like to know more about?"
                
                streamed = stream_message(answer)
                st.session_state.messages.append({"role": "assistant", "content": streamed})
            
            else:
                response_format = st.session_state.get("response_format", "Detailed")
                
                with st.spinner("Thinking..."):
                    api_response = cv_client.query_cv(prompt, response_format)
                
                if api_response.success:
                    streamed = stream_message(api_response.content)
                    st.session_state.messages.append({"role": "assistant", "content": streamed})
                    
                    if hasattr(api_response, 'processing_time') and api_response.processing_time:
                        st.caption(f"Response time: {api_response.processing_time:.2f}s")
                        
                else:
                    error_message = f"Having trouble accessing my knowledge base right now. {api_response.error or 'Please try again in a moment.'}"
                    streamed = stream_message(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": streamed})
                    
                    if "connect" in str(api_response.error).lower():
                        st.caption("Try clicking 'Reconnect' in the sidebar")
