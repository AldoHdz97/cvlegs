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
# Generate unique identifiers for cache busting and session tracking
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())[:8]

if "css_version" not in st.session_state:
    st.session_state.css_version = hashlib.md5(f"{time.time()}{st.session_state.session_id}".encode()).hexdigest()[:8]

# --- SESSION STATE INITIALIZATION ---
# Theme
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

# Device detection state
if "device_detected" not in st.session_state:
    st.session_state.device_detected = False

if "manual_theme_override" not in st.session_state:
    st.session_state.manual_theme_override = False

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

# Backend connection status - now per session
if "backend_connected" not in st.session_state:
    st.session_state.backend_connected = None

# User session info for debugging
if "user_session_id" not in st.session_state:
    st.session_state.user_session_id = None

# Validation error state
if "validation_error" not in st.session_state:
    st.session_state.validation_error = None

# --- VALIDATION FUNCTIONS ---
def validate_message(message):
    """
    Validate user message before sending to API
    Returns: (is_valid: bool, error_message: str)
    """
    if not message or not message.strip():
        return False, "Please enter a message"
    
    # Check minimum word count
    word_count = len(message.strip().split())
    if word_count < 2:
        return False, "Sorry, your message is too short. Please provide more details."
    
    # Check minimum character count
    if len(message.strip()) < 5:
        return False, "Sorry, your message is too short. Please provide more details."
    
    return True, ""

def show_validation_error(error_message):
    """Display validation error bubble"""
    st.session_state.validation_error = error_message

# --- INITIALIZE MULTI-USER BACKEND CLIENT ---
def get_user_cv_client():
    """Get session-specific CV client - NO GLOBAL CACHING"""
    return get_session_cv_client()

def initialize_user_backend():
    """Initialize backend per user session - NO GLOBAL STATE"""
    try:
        client = initialize_session_backend()
        logger.info(f"Backend initialized for user session: {st.session_state.user_session_id[:8] if st.session_state.user_session_id else 'unknown'}")
        return client
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        st.session_state.backend_connected = False
        return None

# Initialize per-user backend (not cached globally)
cv_client = initialize_user_backend()

# Only show status indicator when there's actually a connection problem
if cv_client is None:
    st.session_state.backend_connected = False
    logger.error("Backend connection failed")
else:
    # Remove the connected status entirely - don't set to True
    st.session_state.backend_connected = None

# --- ROBUST THEME CONTROL WITH ADVANCED VISUAL ENHANCEMENTS ---
def set_theme():
    """Enhanced theme system with v13 visual improvements and robust CSS"""
    if st.session_state.dark_mode:
        bg, text = "#000510", "#ffffff"
        chat_bg, chat_text = "#1a1a2e", "#ffffff"
        sidebar_bg = "#0a0a15"
        placeholder_color = "#888"
        shadow_color = "rgba(255, 255, 255, 0.1)"
        border_color = "#333"
    else:
        bg, text = "#ffffff", "#222326"
        chat_bg, chat_text = "#f8f9fa", "#222326"
        sidebar_bg = "#fafafa"
        placeholder_color = "#666"
        shadow_color = "rgba(0, 0, 0, 0.1)"
        border_color = "#e0e0e0"

    # Enhanced CSS with cache busting, visual improvements, and robust application
    css_content = f"""
    <style id="main-theme-{st.session_state.css_version}">
        /* Cache busting meta refresh */
        meta[http-equiv="Cache-Control"] {{ content: "no-cache, no-store, must-revalidate"; }}
        meta[http-equiv="Pragma"] {{ content: "no-cache"; }}
        meta[http-equiv="Expires"] {{ content: "0"; }}
        
        /* Force CSS application with high specificity */
        html, body, #root, .stApp, 
        div[data-testid="stAppViewContainer"], 
        section[data-testid="stAppViewContainer"] {{
            background-color: {bg} !important;
            color: {text} !important;
            transition: all 0.3s ease !important;
        }}
        
        .main .block-container,
        div[data-testid="block-container"] {{
            background-color: {bg} !important;
            color: {text} !important;
            padding-top: 2rem !important;
        }}
        
        /* Enhanced chat messages with shadows */
        div[data-testid="chat-message"],
        .stChatMessage {{
            background: transparent !important;
            color: {text} !important;
            margin-bottom: 1rem !important;
            border-radius: 0.75rem !important;
            box-shadow: 0 2px 8px {shadow_color} !important;
            padding: 0.5rem !important;
        }}
        
        div[data-testid="chat-message"] p,
        div[data-testid="chat-message"] div,
        .stChatMessage p,
        .stChatMessage div {{
            color: {text} !important;
        }}
        
        /* Hide Streamlit branding */
        #MainMenu, footer, header,
        div[data-testid="stToolbar"],
        .stDeployButton,
        div[data-testid="stDecoration"] {{
            visibility: hidden !important;
            display: none !important;
        }}

        /* Enhanced chat input with premium styling */
        .stChatInput > div > div > div > div,
        div[data-testid="stChatInput"] > div,
        div[data-baseweb="input"] {{
            background: {chat_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 2rem !important;
            box-shadow: 0 4px 12px {shadow_color} !important;
            transition: all 0.2s ease !important;
            overflow: hidden !important;
        }}

        .stChatInput > div > div > div > div:hover,
        div[data-testid="stChatInput"] > div:hover {{
            box-shadow: 0 6px 20px {shadow_color} !important;
            transform: translateY(-1px) !important;
        }}

        .stChatInput textarea,
        div[data-testid="stChatInput"] textarea {{
            background-color: transparent !important;
            color: {chat_text} !important;
            border: none !important;
            outline: none !important;
            padding: 0.875rem 1.25rem !important;
            font-size: 14px !important;
            line-height: 1.5 !important;
            caret-color: {chat_text} !important;
        }}

        .stChatInput textarea::placeholder,
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {placeholder_color} !important;
            opacity: 0.7 !important;
        }}

        .stChatInput textarea:focus,
        div[data-testid="stChatInput"] textarea:focus {{
            outline: none !important;
            box-shadow: none !important;
        }}

        /* Force remove any validation styling */
        .stChatInput *,
        .stChatInput *:focus,
        .stChatInput *:hover,
        .stChatInput *:active,
        .stChatInput *:invalid {{
            border-color: {border_color} !important;
            outline: none !important;
        }}

        /* Enhanced sidebar */
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

        /* Enhanced selectbox styling */
        .stSelectbox > div > div {{
            background-color: {chat_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
            box-shadow: 0 2px 4px {shadow_color} !important;
        }}

        /* Engine icon with enhanced styling */
        .engine-icon {{
            position: fixed;
            top: 20px;
            left: 20px;
            z-index: 999;
            opacity: 0.4;
            transition: all 0.3s ease;
            filter: drop-shadow(0 2px 4px {shadow_color});
        }}
        .engine-icon:hover {{
            opacity: 0.8;
            transform: scale(1.05);
        }}

        /* Backend status with enhanced styling */
        .backend-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: linear-gradient(135deg, #ff4444, #cc0000);
            color: white;
            padding: 10px 18px;
            border-radius: 25px;
            font-size: 12px;
            font-weight: 600;
            box-shadow: 0 4px 12px rgba(255, 68, 68, 0.3);
            animation: pulse 2s infinite;
        }}

        @keyframes pulse {{
            0%, 100% {{ opacity: 0.9; }}
            50% {{ opacity: 0.7; }}
        }}

        /* Enhanced validation bubble */
        .validation-bubble {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: linear-gradient(135deg, rgba(244, 67, 54, 0.95), rgba(200, 20, 20, 0.95));
            color: white;
            padding: 16px 28px;
            border-radius: 30px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 8px 32px rgba(244, 67, 54, 0.4);
            backdrop-filter: blur(10px);
            animation: fadeInOut 3.5s ease-in-out forwards;
        }}

        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); }}
            15% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            85% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); visibility: hidden; }}
        }}

        /* Mobile responsiveness */
        @media (max-width: 768px) {{
            .validation-bubble {{
                font-size: 13px;
                padding: 12px 20px;
                max-width: 85vw;
                text-align: center;
            }}
            
            .engine-icon {{
                top: 15px;
                left: 15px;
            }}
            
            .backend-status {{
                top: 15px;
                right: 15px;
                padding: 8px 14px;
                font-size: 11px;
            }}
        }}
        
        /* CSS version identifier for debugging */
        body::after {{
            content: "CSS-{st.session_state.css_version}";
            position: fixed;
            bottom: 0;
            right: 0;
            font-size: 8px;
            opacity: 0.1;
            pointer-events: none;
        }}
    </style>
    
    <script>
    // Advanced device detection and theme management
    (function() {{
        const sessionId = '{st.session_state.session_id}';
        const cssVersion = '{st.session_state.css_version}';
        
        // Device detection with multiple fallbacks
        function detectDevice() {{
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
            const isMobileScreen = window.innerWidth <= 768 || window.innerHeight <= 768;
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            // Combine multiple detection methods
            return isMobileUA || (isMobileScreen && isTouchDevice);
        }}
        
        // Theme management
        function initializeTheme() {{
            const stored = localStorage.getItem(`theme_${{sessionId}}`);
            const manualOverride = localStorage.getItem('manual_theme_override') === 'true';
            
            if (!manualOverride && !stored) {{
                const isMobile = detectDevice();
                const shouldBeDark = !isMobile; // Mobile = light, Desktop = dark
                const currentIsDark = {str(st.session_state.dark_mode).lower()};
                
                if (currentIsDark !== shouldBeDark) {{
                    localStorage.setItem(`theme_${{sessionId}}`, shouldBeDark.toString());
                    localStorage.setItem('device_detected', 'true');
                    
                    // Trigger theme change via URL parameter
                    const url = new URL(window.location);
                    url.searchParams.set('auto_theme', shouldBeDark ? 'dark' : 'light');
                    url.searchParams.set('session_id', sessionId);
                    window.location.href = url.toString();
                }}
            }}
        }}
        
        // Force CSS refresh and anti-cache measures
        function refreshCSS() {{
            // Remove old stylesheets
            const oldStyles = document.querySelectorAll('[id^="main-theme-"]');
            oldStyles.forEach(style => {{
                if (style.id !== 'main-theme-{st.session_state.css_version}') {{
                    style.remove();
                }}
            }});
            
            // Force browser reflow
            document.body.style.display = 'none';
            document.body.offsetHeight; // Trigger reflow
            document.body.style.display = '';
            
            // Set cache control
            const meta1 = document.createElement('meta');
            meta1.setAttribute('http-equiv', 'Cache-Control');
            meta1.setAttribute('content', 'no-cache, no-store, must-revalidate');
            document.head.appendChild(meta1);
            
            const meta2 = document.createElement('meta');
            meta2.setAttribute('http-equiv', 'Pragma');
            meta2.setAttribute('content', 'no-cache');
            document.head.appendChild(meta2);
        }}
        
        // Initialize on page load
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                refreshCSS();
                initializeTheme();
            }});
        }} else {{
            refreshCSS();
            initializeTheme();
        }}
        
        // Handle orientation changes on mobile
        window.addEventListener('orientationchange', function() {{
            setTimeout(refreshCSS, 100);
        }});
        
    }})();
    </script>
    """
    
    st.markdown(css_content, unsafe_allow_html=True)
    return bg, text

bg, text = set_theme()

# Handle automatic theme detection from URL
if "auto_theme" in st.query_params and not st.session_state.manual_theme_override:
    auto_theme = st.query_params.get("auto_theme")
    if auto_theme == "dark" and not st.session_state.dark_mode:
        st.session_state.dark_mode = True
        st.session_state.device_detected = True
        st.rerun()
    elif auto_theme == "light" and st.session_state.dark_mode:
        st.session_state.dark_mode = False
        st.session_state.device_detected = True
        st.rerun()

# Enhanced validation bubble display
if st.session_state.validation_error:
    st.markdown(f"""
    <div class="validation-bubble">
        {st.session_state.validation_error}
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-clear mechanism
    time.sleep(0.1)
    st.session_state.validation_error = None

# Show backend status only when offline
if st.session_state.backend_connected is False:
    st.markdown("""
    <div class="backend-status">
        OFFLINE
    </div>
    """, unsafe_allow_html=True)

# --- MINIMALISTIC TITLE ---
st.markdown(
    f"<h2 style='font-family:Roboto,sans-serif;font-weight:300;margin-bottom:8px;margin-top:8px;color:{text};text-align:center;'>hola,welcome</h2>",
    unsafe_allow_html=True,
)

# --- ENHANCED ENGINE ICON ---
engine_svg = '''
<svg width="38" height="38" fill="gray" fill-opacity="0.40" style="display:inline-block;vertical-align:middle;border-radius:12px;">
    <ellipse cx="19" cy="19" rx="18" ry="14" fill="gray" fill-opacity="0.25"/>
    <ellipse cx="19" cy="19" rx="13" ry="10" fill="white" fill-opacity="0.15"/>
    <ellipse cx="19" cy="19" rx="6" ry="5" fill="gray" fill-opacity="0.40"/>
    <rect x="10" y="6" width="18" height="26" rx="8" fill="gray" fill-opacity="0.20"/>
</svg>
'''

st.markdown(
    f'<div class="engine-icon" style="width:38px;height:38px;" title="hola, welcome">{engine_svg}</div>',
    unsafe_allow_html=True
)

# --- SIDEBAR WITH PROPERLY INDENTED INTERVIEW SCHEDULING ---
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Backend status - now per session (only show when there's an issue)
    if st.session_state.backend_connected is False:
        st.error("Backend Offline")
        if st.button("Reconnect", key="reconnect_backend"):
            cv_client = initialize_user_backend()
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
    
    # Enhanced theme toggle with manual override tracking
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.session_state.manual_theme_override = True
        # Store manual override in localStorage
        st.markdown('<script>localStorage.setItem("manual_theme_override", "true");</script>', unsafe_allow_html=True)
        st.rerun()

    st.markdown("---")
    
    # Schedule Interview button
    if st.button("📅 Schedule an Interview", key="open_schedule", use_container_width=True):
        st.session_state.show_calendar_picker = True
        st.session_state.scheduling_step = 0
        st.rerun()

    # Interview scheduling flow
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
            st.markdown("##### 📝 Step 3: Add a mail (must)")
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
                if st.button("Request Interview", key="submit_int", type="primary", use_container_width=True):
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

# --- Initial greeting ---
if not st.session_state.greeting_streamed:
    greeting = ("Hi there! I'm Aldo*—or at least, my digital twin. "
                "Go ahead and ask me anything about my professional life, projects, or skills. "
                "I promise not to humblebrag too much (okay, maybe just a little).")
    
    with st.chat_message("assistant"):
        streamed_greeting = stream_message(greeting)
    
    st.session_state.messages.append({"role": "assistant", "content": streamed_greeting})
    st.session_state.greeting_streamed = True
else:
    # Show message history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# --- CHAT INPUT WITH VALIDATION ---
if prompt := st.chat_input("Ask! Don't be shy !", key="main_chat_input"):
    # Validate the message
    is_valid, error_message = validate_message(prompt)
    
    if not is_valid:
        # Show validation bubble instead of processing the message
        show_validation_error(error_message)
        st.rerun()  # Refresh to show the bubble
    else:
        # Process the valid message as normal
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)
        
        # Generate assistant response
        with st.chat_message("assistant"):
            if st.session_state.backend_connected is False or not cv_client:
                # Use original fallback responses when backend is offline
                with st.spinner("..."):
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
                
                with st.spinner("..."):
                    # Make API call to backend with session-specific client
                    api_response = cv_client.query_cv(prompt, response_format)
                    
                    if api_response.success:
                        # Stream the backend response
                        streamed = stream_message(api_response.content)
                        st.session_state.messages.append({"role": "assistant", "content": streamed})
                        
                        # Show response time if available
                        if hasattr(api_response, 'processing_time') and api_response.processing_time:
                            st.caption(f"Response time: {api_response.processing_time:.2f}s")
                            
                    else:
                        # Handle API errors gracefully per session
                        error_message = f"Having trouble accessing my knowledge base right now. {api_response.error or 'Please try again in a moment.'}"
                        streamed = stream_message(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": streamed})
                        
                        # If it's a connection issue, suggest reconnecting
                        if "connect" in str(api_response.error).lower():
                            st.caption("Try clicking 'Reconnect' in the sidebar")
