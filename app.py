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

# --- MINIMALISTIC THEME CONTROL ---
def set_theme():
    """Minimalistic theme system with performance optimizations"""
    if st.session_state.dark_mode:
        bg, text = "#000510", "#ffffff"
        chat_bg, chat_text = "#1a1a1a", "#ffffff"
        sidebar_bg = "#0f0f0f"
        placeholder_color = "#888"
        border_color = "#333"
    else:
        bg, text = "#ffffff", "#222326"
        chat_bg, chat_text = "#f8f8f8", "#222326"
        sidebar_bg = "#fafafa"
        placeholder_color = "#666"
        border_color = "#e0e0e0"

    # Minimalistic CSS with performance optimizations
    css_content = f"""
    <style id="main-theme-{st.session_state.css_version}">
        /* Anti-cache headers */
        meta[http-equiv="Cache-Control"] {{ content: "no-cache, no-store, must-revalidate"; }}
        
        /* Core app styling */
        html, body, #root, .stApp, 
        div[data-testid="stAppViewContainer"], 
        section[data-testid="stAppViewContainer"] {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        .main .block-container,
        div[data-testid="block-container"] {{
            background-color: {bg} !important;
            color: {text} !important;
            padding-top: 2rem !important;
        }}
        
        /* Clean chat messages - no colored backgrounds, proper alignment */
        div[data-testid="chat-message"],
        .stChatMessage {{
            background: transparent !important;
            color: {text} !important;
            margin-bottom: 1rem !important;
            display: flex !important;
            align-items: flex-start !important;
            gap: 0.75rem !important;
        }}
        
        /* Remove avatar backgrounds */
        div[data-testid="chat-message"] > div:first-child,
        .stChatMessage > div:first-child {{
            background: transparent !important;
            border-radius: 50% !important;
            padding: 0 !important;
            width: 40px !important;
            height: 40px !important;
            min-width: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
        }}
        
        /* Chat message content alignment */
        div[data-testid="chat-message"] > div:last-child,
        .stChatMessage > div:last-child {{
            flex: 1 !important;
            padding-top: 8px !important;
        }}
        
        div[data-testid="chat-message"] p,
        div[data-testid="chat-message"] div,
        .stChatMessage p,
        .stChatMessage div {{
            color: {text} !important;
            margin: 0 !important;
            line-height: 1.5 !important;
        }}
        
        /* Hide Streamlit loading spinner */
        .stSpinner,
        div[data-testid="stSpinner"] {{
            display: none !important;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu, footer, header,
        div[data-testid="stToolbar"],
        .stDeployButton,
        div[data-testid="stDecoration"] {{
            visibility: hidden !important;
            display: none !important;
        }}

        /* Minimalistic chat input */
        .stChatInput > div > div > div > div,
        div[data-testid="stChatInput"] > div,
        div[data-baseweb="input"] {{
            background: {chat_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 1.5rem !important;
            transition: border-color 0.2s ease !important;
        }}

        .stChatInput > div > div > div > div:focus-within,
        div[data-testid="stChatInput"] > div:focus-within {{
            border-color: {text} !important;
        }}

        .stChatInput textarea,
        div[data-testid="stChatInput"] textarea {{
            background-color: transparent !important;
            color: {chat_text} !important;
            border: none !important;
            outline: none !important;
            padding: 0.75rem 1rem !important;
            font-size: 14px !important;
            caret-color: {chat_text} !important;
        }}

        .stChatInput textarea::placeholder,
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {placeholder_color} !important;
            opacity: 0.7 !important;
        }}

        /* Force remove validation styling */
        .stChatInput *,
        .stChatInput *:focus,
        .stChatInput *:hover,
        .stChatInput *:active,
        .stChatInput *:invalid {{
            border-color: {border_color} !important;
            outline: none !important;
            box-shadow: none !important;
        }}

        .stChatInput *:focus {{
            border-color: {text} !important;
        }}

        /* Clean sidebar */
        .stSidebar,
        section[data-testid="stSidebar"] {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
        }}
        
        .stSidebar .stSelectbox > div > div,
        .stSidebar .stToggle,
        .stSidebar div,
        .stSidebar p,
        .stSidebar span,
        .stSidebar label {{
            color: {text} !important;
        }}

        /* Clean selectbox */
        .stSelectbox > div > div {{
            background-color: {chat_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
        }}

        /* Minimalistic engine icon */
        .engine-icon {{
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 999;
            opacity: 0.3;
            transition: opacity 0.2s ease;
        }}
        .engine-icon:hover {{
            opacity: 0.6;
        }}

        /* Simple backend status */
        .backend-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: {text};
            color: {bg};
            padding: 8px 15px;
            border-radius: 15px;
            font-size: 12px;
            font-weight: 500;
        }}

        /* Clean validation bubble */
        .validation-bubble {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: {text};
            color: {bg};
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            animation: fadeInOut 3s ease-in-out forwards;
        }}

        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); }}
            15% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            85% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); visibility: hidden; }}
        }}

        /* Simple animated dots for loading - aligned with avatar */
        .loading-dots {{
            display: flex;
            align-items: center;
            height: 40px;
            padding-top: 8px;
            gap: 4px;
        }}

        .loading-dots span {{
            width: 4px;
            height: 4px;
            border-radius: 50%;
            background-color: {text};
            animation: dotPulse 1.4s infinite ease-in-out;
        }}

        .loading-dots span:nth-child(1) {{ animation-delay: 0s; }}
        .loading-dots span:nth-child(2) {{ animation-delay: 0.2s; }}
        .loading-dots span:nth-child(3) {{ animation-delay: 0.4s; }}

        @keyframes dotPulse {{
            0%, 60%, 100% {{ 
                opacity: 0.3; 
                transform: scale(0.8); 
            }}
            30% {{ 
                opacity: 1; 
                transform: scale(1); 
            }}
        }}

        /* Mobile responsive */
        @media (max-width: 768px) {{
            .validation-bubble {{
                font-size: 13px;
                padding: 10px 20px;
                max-width: 85vw;
            }}
            
            .engine-icon {{
                top: 15px;
                left: 15px;
            }}
            
            .backend-status {{
                top: 15px;
                right: 15px;
                padding: 6px 12px;
                font-size: 11px;
            }}
        }}
    </style>
    
    <script>
    // Simple, reliable device detection and theme management
    (function() {{
        const sessionId = '{st.session_state.session_id}';
        
        // Improved device detection
        function detectDevice() {{
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
            const isMobileScreen = window.innerWidth <= 768;
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            return isMobileUA || (isMobileScreen && isTouchDevice);
        }}
        
        // Simple theme initialization
        function initializeTheme() {{
            const manualOverride = localStorage.getItem('manual_theme_override') === 'true';
            const hasDetected = localStorage.getItem(`device_detected_${{sessionId}}`) === 'true';
            
            if (!manualOverride && !hasDetected) {{
                const isMobile = detectDevice();
                const shouldBeDark = !isMobile;
                const currentIsDark = {str(st.session_state.dark_mode).lower()};
                
                if (currentIsDark !== shouldBeDark) {{
                    localStorage.setItem(`device_detected_${{sessionId}}`, 'true');
                    
                    // Simple URL redirect approach
                    const url = new URL(window.location);
                    url.searchParams.set('theme_auto', shouldBeDark ? 'dark' : 'light');
                    url.searchParams.set('s', sessionId);
                    
                    // Clear any existing params and redirect
                    const cleanUrl = `${{url.origin}}${{url.pathname}}?theme_auto=${{shouldBeDark ? 'dark' : 'light'}}&s=${{sessionId}}`;
                    window.location.replace(cleanUrl);
                    return;
                }}
            }}
        }}
        
        // Force CSS application
        function applyCSSFixes() {{
            // Remove old styles
            const oldStyles = document.querySelectorAll('[id^="main-theme-"]');
            oldStyles.forEach(style => {{
                if (style.id !== 'main-theme-{st.session_state.css_version}') {{
                    style.remove();
                }}
            }});
            
            // Force reflow
            document.body.offsetHeight;
        }}
        
        // Initialize everything
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                applyCSSFixes();
                setTimeout(initializeTheme, 100);
            }});
        }} else {{
            applyCSSFixes();
            setTimeout(initializeTheme, 100);
        }}
    }})();
    </script>
    """
    
    st.markdown(css_content, unsafe_allow_html=True)
    return bg, text

bg, text = set_theme()

# Handle theme detection from URL with improved logic
if "theme_auto" in st.query_params and not st.session_state.manual_theme_override:
    theme_auto = st.query_params.get("theme_auto")
    session_param = st.query_params.get("s")
    
    if session_param == st.session_state.session_id:
        if theme_auto == "dark" and not st.session_state.dark_mode:
            st.session_state.dark_mode = True
            # Clear URL params after applying
            st.query_params.clear()
            st.rerun()
        elif theme_auto == "light" and st.session_state.dark_mode:
            st.session_state.dark_mode = False
            # Clear URL params after applying
            st.query_params.clear()
            st.rerun()

# Clean validation bubble display
if st.session_state.validation_error:
    st.markdown(f"""
    <div class="validation-bubble">
        {st.session_state.validation_error}
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(0.1)
    st.session_state.validation_error = None

# Simple backend status
if st.session_state.backend_connected is False:
    st.markdown('<div class="backend-status">OFFLINE</div>', unsafe_allow_html=True)

# Clean title
st.markdown(
    f"<h2 style='font-family:Roboto,sans-serif;font-weight:300;margin-bottom:8px;margin-top:8px;color:{text};text-align:center;'>hola,welcome</h2>",
    unsafe_allow_html=True,
)

# Simple engine icon
engine_svg = '''
<svg width="38" height="38" fill="gray" fill-opacity="0.40" style="display:inline-block;vertical-align:middle;border-radius:12px;">
    <ellipse cx="19" cy="19" rx="18" ry="14" fill="gray" fill-opacity="0.25"/>
    <ellipse cx="19" cy="19" rx="13" ry="10" fill="white" fill-opacity="0.15"/>
    <ellipse cx="19" cy="19" rx="6" ry="5" fill="gray" fill-opacity="0.40"/>
    <rect x="10" y="6" width="18" height="26" rx="8" fill="gray" fill-opacity="0.20"/>
</svg>
'''

st.markdown(f'<div class="engine-icon">{engine_svg}</div>', unsafe_allow_html=True)

# Clean sidebar
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
    
    # Clean theme toggle
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.session_state.manual_theme_override = True
        st.markdown('<script>localStorage.setItem("manual_theme_override", "true");</script>', unsafe_allow_html=True)
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
                # Clean loading indicator aligned with avatar
                loading_placeholder = st.empty()
                loading_placeholder.markdown('<div class="loading-dots"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
                
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
                
                time.sleep(0.5)
                loading_placeholder.empty()
                
                streamed = stream_message(answer)
                st.session_state.messages.append({"role": "assistant", "content": streamed})
            
            else:
                response_format = st.session_state.get("response_format", "Detailed")
                
                loading_placeholder = st.empty()
                loading_placeholder.markdown('<div class="loading-dots"><span></span><span></span><span></span></div>', unsafe_allow_html=True)
                
                api_response = cv_client.query_cv(prompt, response_format)
                
                loading_placeholder.empty()
                
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
