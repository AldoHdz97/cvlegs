import streamlit as st
import time
import logging
from datetime import datetime, timedelta

# Import from our separate API client module
from api_client import CVBackendClient, APIResponse

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

# --- SESSION STATE INITIALIZATION ---
# Theme
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Interview scheduling
if "show_calendar_picker" not in st.session_state:
    st.session_state.show_calendar_picker = False
if "selected_day" not in st.session_state:
    st.session_state.selected_day = None
if "selected_time" not in st.session_state:
    st.session_state.selected_time = None
if "user_note" not in st.session_state:
    st.session_state.user_note = ""
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

# --- INITIALIZE BACKEND CLIENT ---
@st.cache_resource
def get_cv_client() -> CVBackendClient:
    """Get cached CV backend client instance"""
    return CVBackendClient()

@st.cache_resource  
def initialize_backend():
    """Initialize backend client"""
    try:
        client = get_cv_client()
        health = client.get_health_status()
        st.session_state.backend_connected = health["status"] == "healthy"
        return client
    except Exception as e:
        st.session_state.backend_connected = False
        return None

cv_client = initialize_backend()
# --- THEME CONTROL ---
def set_theme():
    if st.session_state.dark_mode:
        bg, text = "#000510", "#ffffff"
    else:
        bg, text = "#ffffff", "#222326"
    
    # Add backend status indicator
    status_color = "#4CAF50" if st.session_state.backend_connected else "#F44336"
    
    st.markdown(f"""
    <style>
        .stApp {{background-color: {bg} !important; color: {text} !important;}}
        .main .block-container {{background-color: {bg} !important;}}
        div[data-testid="chat-message"] {{background: transparent !important; color: {text} !important;}}
        .stChatMessage {{background: transparent !important; color: {text} !important;}}
        #MainMenu, footer, header {{visibility: hidden;}}
        
        /* Engine Icon - Fixed positioning */
        .engine-icon {{
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 999;
            opacity: 0.30;
            transition: opacity 0.2s ease;
        }}
        .engine-icon:hover {{
            opacity: 0.60;
        }}
        
        /* Backend status indicator */
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
        
        /* Background calendar - Centered-right, large, skeleton style */
        .calendar-bg {{
            filter: blur(0.3px);
        }}
        .calendar-bg:hover {{
            filter: blur(0px);
            opacity: 0.95 !important;
        }}
        
        /* Better chat styling */
        .stChatInput {{
            background-color: {bg} !important;
        }}
    </style>
    """, unsafe_allow_html=True)
    return bg, text

bg, text = set_theme()

# --- BACKEND STATUS INDICATOR ---
backend_status_text = "🟢 Connected" if st.session_state.backend_connected else "🔴 Offline"
st.markdown(
    f'<div class="backend-status">{backend_status_text}</div>',
    unsafe_allow_html=True
)

# --- MINIMALISTIC TITLE ---
st.markdown(
    f"<h2 style='font-family:Roboto,sans-serif;font-weight:300;margin-bottom:8px;margin-top:8px;color:{text};text-align:center;'>hola,welcome</h2>",
    unsafe_allow_html=True,
)

# --- ENGINE ICON (GREY, TRANSPARENT) ---
engine_svg = '''
<svg width="38" height="38" fill="gray" fill-opacity="0.40" style="display:inline-block;vertical-align:middle;border-radius:12px;">
    <ellipse cx="19" cy="19" rx="18" ry="14" fill="gray" fill-opacity="0.25"/>
    <ellipse cx="19" cy="19" rx="13" ry="10" fill="white" fill-opacity="0.15"/>
    <ellipse cx="19" cy="19" rx="6" ry="5" fill="gray" fill-opacity="0.40"/>
    <rect x="10" y="6" width="18" height="26" rx="8" fill="gray" fill-opacity="0.20"/>
</svg>
'''

# Place engine icon at top-left
st.markdown(
    f'<div class="engine-icon" style="width:38px;height:38px;" title="hola, welcome">{engine_svg}</div>',
    unsafe_allow_html=True
)

# --- SIDEBAR WITH PROPERLY INDENTED INTERVIEW SCHEDULING ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Backend status
    if st.session_state.backend_connected:
        st.success("🟢 Backend Connected")
    else:
        st.error("🔴 Backend Offline")
        if st.button("🔄 Reconnect", key="reconnect_backend"):
            st.rerun()
    
    st.markdown("---")
    
    # Response Style
    st.selectbox(
        "Response Style",
        ["Detailed", "Summary", "Bullet points", "Technical", "Conversational"],
        index=0,
        key="response_format",
        help="Choose how you'd like responses formatted"
    )
    
    # Dark/Light mode toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.rerun()

    st.markdown("---")
    
    # Schedule Interview button (PROPERLY INDENTED IN SIDEBAR)
    if st.button("📅 Schedule an Interview", key="open_schedule", use_container_width=True):
        st.session_state.show_calendar_picker = True
        st.session_state.scheduling_step = 0
        st.rerun()

    # Interview scheduling flow (PROPERLY INDENTED IN SIDEBAR)
    if st.session_state.show_calendar_picker:
        
        if st.session_state.scheduling_step == 0:
            st.markdown("##### 📅 Step 1: Pick a day")
            today = datetime.now()
            days = [(today + timedelta(days=i)).strftime("%A, %B %d, %Y") for i in range(14)]
            selected = st.selectbox("Available Days", days, key="day_select")
            st.session_state.selected_day = selected
            
            col1, col2 = st.columns([1, 2])
            with col2:
                if st.button("Next →", key="next_to_time", use_container_width=True):
                    st.session_state.scheduling_step = 1
                    st.rerun()
        
        elif st.session_state.scheduling_step == 1:
            st.markdown("##### ⏰ Step 2: Pick a time slot")
            slots = [
                "8:00-9:30 AM", "9:30-11:00 AM", "11:00-12:30 PM",
                "12:30-2:00 PM", "2:00-3:30 PM", "3:30-5:00 PM"
            ]
            selected_time = st.selectbox("Available Times", slots, key="slot_select")
            st.session_state.selected_time = selected_time
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", key="back_to_day", use_container_width=True):
                    st.session_state.scheduling_step = 0
                    st.rerun()
            with col2:
                if st.button("Next →", key="next_to_note", use_container_width=True):
                    st.session_state.scheduling_step = 2
                    st.rerun()
        
        elif st.session_state.scheduling_step == 2:
            st.markdown("##### 📝 Step 3: Add a note (optional)")
            note = st.text_area("Leave a note:", key="note_area", height=80)
            st.session_state.user_note = note
            
            st.info("📧 You'll receive a confirmation email after your request is reviewed.")
            
            # Show summary
            with st.expander("📋 Review Summary", expanded=True):
                st.write(f"**📅 Day:** {st.session_state.selected_day}")
                st.write(f"**⏰ Time:** {st.session_state.selected_time}")
                if note.strip():
                    st.write(f"**📝 Note:** {note}")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("← Back", key="back_to_time", use_container_width=True):
                    st.session_state.scheduling_step = 1
                    st.rerun()
            with col2:
                if st.button("✅ Request Interview", key="submit_int", type="primary", use_container_width=True):
                    st.success("🎉 Interview request sent! You'll receive a confirmation email soon.")
                    # Reset scheduling state
                    st.session_state.show_calendar_picker = False
                    st.session_state.scheduling_step = 0
                    st.session_state.selected_day = None
                    st.session_state.selected_time = None
                    st.session_state.user_note = ""
                    time.sleep(2)  # Brief pause to show success message
                    st.rerun()

        # Cancel button (always visible during scheduling)
        st.markdown("---")
        if st.button("❌ Cancel", key="cancel_int", use_container_width=True):
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

# --- Uso correcto fuera de la función ---
if not st.session_state.greeting_streamed:
    greeting = ("Hi there! I'm Aldo*—or at least, my digital twin. "
                "Go ahead and ask me anything about my professional life, projects, or skills. "
                "I promise not to humblebrag too much (okay, maybe just a little).")
    
    with st.chat_message("assistant"):  # Aquí se usa claramente afuera
        streamed_greeting = stream_message(greeting)
    
    st.session_state.messages.append({"role": "assistant", "content": streamed_greeting})
    st.session_state.greeting_streamed = True
else:
    # Mostrar historial
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])


# --- BACKEND-INTEGRATED CHAT INPUT ---
if prompt := st.chat_input("Ask! Don't be shy !", key="main_chat_input"):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate assistant response
    with st.chat_message("assistant"):
        if not st.session_state.backend_connected or not cv_client:
            # Use original fallback responses when backend is offline
            with st.spinner(" Thinking..."):
                if any(word in prompt.lower() for word in ['skill', 'technology', 'programming', 'language']):
                    answer = f"Great question about skills! Based on Aldo's background, he has extensive experience with Python, SQL, Tableau, and data analysis. He's particularly strong in economics, data visualization, and building automated reporting systems. His technical skills span from web scraping to machine learning applications."
                elif any(word in prompt.lower() for word in ['experience', 'work', 'job', 'company']):
                    answer = f"Aldo has diverse professional experience! He's currently a Social Listening & Insights Analyst at Swarm Data and People, where he analyzes performance for multiple Tec de Monterrey campuses. Previously, he worked as a Data Analyst at Wii México and had his own content creation business. His experience spans data analysis, automation, and stakeholder engagement."
                elif any(word in prompt.lower() for word in ['education', 'degree', 'university', 'study']):
                    answer = f"Aldo graduated with a B.A. in Economics from Tecnológico de Monterrey (2015-2021). His academic background includes statistical analysis projects using Python and R. He's also earned certifications in Tableau Desktop, Power BI, and OpenAI development."
                elif any(word in prompt.lower() for word in ['project', 'built', 'created', 'developed']):
                    answer = f"Aldo has worked on fascinating projects! Some highlights include: a Business Growth Analysis dashboard tracking business density across Nuevo León municipalities, an NFL Betting Index aggregation system, and an AI-driven CV Manager using Next.js and OpenAI. His projects showcase skills in data visualization, web development, and AI integration."
                else:
                    answer = f"Thank you for asking about '{prompt}'. I'd be happy to help you learn more about Aldo's professional background! He's an accomplished economist and data analyst with strong technical skills in Python, data visualization, and AI applications. What specific aspect would you like to know more about?"
                
                # Small delay for realism
                time.sleep(0.5)
            
            # Stream the response
            streamed = stream_message(answer)
            st.session_state.messages.append({"role": "assistant", "content": streamed})
        
        else:
            # Use backend for real responses
            response_format = st.session_state.get("response_format", "Detailed")
            
            with st.spinner(" Thinking..."):
                # Make API call to backend
                api_response = cv_client.query_cv(prompt, response_format)
                
                if api_response.success:
                    # Stream the backend response
                    streamed = stream_message(api_response.content)
                    st.session_state.messages.append({"role": "assistant", "content": streamed})
                    
                    if hasattr(api_response, 'processing_time') and api_response.processing_time:
                        st.caption(f"⚡ Response time: {api_response.processing_time:.2f}s")
                        
                       
                else:
                    # Handle API errors gracefully
                    error_message = f"⚠️ Having trouble accessing my knowledge base right now. {api_response.error or 'Please try again in a moment.'}"
                    streamed = stream_message(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": streamed})
