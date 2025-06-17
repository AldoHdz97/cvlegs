import streamlit as st
import time
import logging
from datetime import datetime, timedelta

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

# --- SESSION STATE INITIALIZATION ---
# Device detection and theme initialization
if "device_detected" not in st.session_state:
    # Use a more reliable approach with query params and user agent
    st.session_state.device_detected = False
    
    # JavaScript detection that immediately sets the theme
    device_detection_js = """
    <script>
    function detectAndSetTheme() {
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                         window.innerWidth <= 768 || 
                         ('ontouchstart' in window);
        
        // Set theme immediately based on device
        const shouldBeLightMode = isMobile;
        
        // Create a form to submit the detected theme
        const form = document.createElement('form');
        form.method = 'GET';
        form.style.display = 'none';
        
        const input = document.createElement('input');
        input.type = 'hidden';
        input.name = 'mobile_detected';
        input.value = isMobile ? 'true' : 'false';
        
        form.appendChild(input);
        document.body.appendChild(form);
        
        // If this is the first load and we detect mobile, reload with parameter
        const urlParams = new URLSearchParams(window.location.search);
        if (!urlParams.has('mobile_detected') && isMobile) {
            window.location.href = window.location.href + '?mobile_detected=true';
        } else if (!urlParams.has('mobile_detected') && !isMobile) {
            window.location.href = window.location.href + '?mobile_detected=false';
        }
    }
    
    // Run detection immediately
    detectAndSetTheme();
    </script>
    """
    
    st.markdown(device_detection_js, unsafe_allow_html=True)

# Check for mobile detection from URL parameters
mobile_detected = st.query_params.get('mobile_detected', None)

# Theme initialization based on device detection
if "dark_mode" not in st.session_state:
    if mobile_detected == 'true':
        st.session_state.dark_mode = False  # Light mode for mobile
        st.session_state.device_detected = True
    elif mobile_detected == 'false':
        st.session_state.dark_mode = True   # Dark mode for desktop
        st.session_state.device_detected = True
    else:
        st.session_state.dark_mode = True   # Default to dark mode
        
# Mark as manually set when user toggles
if "manual_theme_set" not in st.session_state:
    st.session_state.manual_theme_set = False

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
    
    # Check minimum word count (adjust threshold as needed)
    word_count = len(message.strip().split())
    if word_count < 2:
        return False, "Sorry, your message is too short. Please provide more details."
    
    # Check minimum character count (optional additional validation)
    if len(message.strip()) < 5:
        return False, "Sorry, your message is too short. Please provide more details."
    
    return True, ""

def show_validation_error(error_message):
    """Display validation error bubble"""
    st.session_state.validation_error = error_message
    st.session_state.validation_error_time = time.time()

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

# --- THEME CONTROL WITH DEVICE-RESPONSIVE STYLING ---
def set_theme():
    if st.session_state.dark_mode:
        bg, text = "#000510", "#ffffff"
        chat_bg, chat_border = "#222", "transparent"
        chat_text = "#ffffff"
    else:
        bg, text = "#ffffff", "#222326"
        chat_bg, chat_border = "#f8f9fa", "transparent" 
        chat_text = "#222326"

    st.markdown(f"""
    <style>
        .stApp {{background-color: {bg} !important; color: {text} !important;}}
        .main .block-container {{background-color: {bg} !important;}}
        div[data-testid="chat-message"] {{background: transparent !important; color: {text} !important;}}
        .stChatMessage {{background: transparent !important; color: {text} !important;}}
        #MainMenu, footer, header {{visibility: hidden;}}

        /* RESPONSIVE CHAT INPUT - ADAPTS TO THEME */
        .stChatInput, 
        .stChatInput *, 
        .stChatInput *:focus, 
        .stChatInput *:hover, 
        .stChatInput *:active,
        .stChatInput *:invalid,
        .stChatInput *:focus-visible {{
            border: none !important;
            outline: none !important;
            box-shadow: none !important;
        }}

        /* Target the actual input container - THEME RESPONSIVE */
        .stChatInput > div {{
            border: none !important;
            border-radius: 1.5rem !important;
            background-color: {chat_bg} !important;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1) !important;
        }}

        .stChatInput > div > div {{
            border: none !important;
            background-color: transparent !important;
        }}

        .stChatInput > div > div > div {{
            border: none !important;
            background-color: transparent !important;
        }}

        .stChatInput > div > div > div > div {{
            border: none !important;
            background-color: transparent !important;
        }}

        /* The textarea itself - THEME RESPONSIVE */
        .stChatInput textarea {{
            border: none !important;
            background-color: transparent !important;
            color: {chat_text} !important;
            padding-left: 0.75rem !important;
            padding-top: 0.5rem !important;
            outline: none !important;
            box-shadow: none !important;
            caret-color: {chat_text} !important;
        }}

        .stChatInput textarea::placeholder {{
            color: {"#888" if st.session_state.dark_mode else "#666"} !important;
        }}

        /* Force override any dynamic styles that Streamlit adds */
        .stChatInput [class*="css"] {{
            border: none !important;
            box-shadow: none !important;
        }}

        /* Override BaseWeb input component styles */
        div[data-baseweb="input"] {{
            border: none !important;
            box-shadow: none !important;
            background-color: {chat_bg} !important;
        }}

        div[data-baseweb="input"]:focus-within {{
            border: none !important;
            box-shadow: 0 2px 15px rgba(0,0,0,0.15) !important;
            background-color: {chat_bg} !important;
        }}

        /* Override any error states */
        .stChatInput *[aria-invalid="true"] {{
            border: none !important;
            box-shadow: none !important;
        }}

        /* CSS Custom Properties override */
        .stChatInput {{
            --border-color: transparent !important;
            --focus-border-color: transparent !important;
            --error-border-color: transparent !important;
        }}

        /* Force remove any borders with attribute selectors */
        .stChatInput *[style*="border"] {{
            border: none !important;
        }}

        .stChatInput *[style*="outline"] {{
            outline: none !important;
        }}

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

        .backend-status {{
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 999;
            background: #F44336;
            color: white;
            padding: 8px 15px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: bold;
            opacity: 0.9;
            box-shadow: 0 2px 8px rgba(244, 67, 54, 0.3);
        }}

        .validation-bubble {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: rgba(244, 67, 54, 0.95);
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            box-shadow: 0 4px 20px rgba(244, 67, 54, 0.3);
            animation: fadeInOut 3s ease-in-out forwards;
        }}

        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); }}
            15% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            85% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.8); display: none; }}
        }}

        /* Mobile responsive adjustments */
        @media (max-width: 768px) {{
            .stChatInput {{
                margin-bottom: 10px;
            }}
            
            .stChatInput > div {{
                padding: 2px;
            }}
            
            .validation-bubble {{
                font-size: 13px;
                padding: 10px 20px;
                max-width: 90vw;
                text-align: center;
            }}
        }}

        /* Device-specific theme detection script */
        .theme-detector {{
            display: none;
        }}
    </style>
    
    <script>
    // Only auto-detect if theme hasn't been manually set
    if (!{str(st.session_state.manual_theme_set).lower()}) {{
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                         window.innerWidth <= 768 || 
                         ('ontouchstart' in window);
        const shouldBeDark = !isMobile; // Mobile = light, Desktop = dark
        
        // Only change if current theme doesn't match expected and device was detected
        const currentTheme = {str(st.session_state.dark_mode).lower()};
        const deviceDetected = {str(st.session_state.device_detected).lower()};
        
        if (shouldBeDark !== currentTheme && !deviceDetected) {{
            // Reload with correct theme parameter
            const newUrl = new URL(window.location);
            newUrl.searchParams.set('mobile_detected', isMobile ? 'true' : 'false');
            window.location.href = newUrl.toString();
        }}
    }}
    </script>
    """, unsafe_allow_html=True)
    return bg, text

bg, text = set_theme()

# Display validation error bubble if present
if st.session_state.validation_error:
    st.markdown(f"""
    <div class="validation-bubble" id="validation-bubble-{int(time.time())}">
        {st.session_state.validation_error}
    </div>
    <script>
        setTimeout(function() {{
            // Remove the bubble from DOM
            const bubble = document.querySelector('.validation-bubble');
            if (bubble) {{
                bubble.style.display = 'none';
            }}
        }}, 3000);
    </script>
    """, unsafe_allow_html=True)
    
    # Clear the validation error immediately after displaying to prevent persistence
    if 'clear_validation_flag' not in st.session_state:
        st.session_state.clear_validation_flag = True

# Clear validation error if flag is set
if st.session_state.get('clear_validation_flag') and st.session_state.validation_error:
    st.session_state.validation_error = None
    st.session_state.clear_validation_flag = None

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
    
    # Dark/Light mode toggle - with manual override detection
    dark_mode = st.toggle("🌙 Dark Mode", value=st.session_state.dark_mode, key="theme_toggle")
    if dark_mode != st.session_state.dark_mode:
        st.session_state.dark_mode = dark_mode
        st.session_state.manual_theme_set = True  # Mark as manually set
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
                with st.spinner("Thinking..."):
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
                
                with st.spinner("Thinking..."):
                    # Make API call to backend with session-specific client
                    api_response = cv_client.query_cv(prompt, response_format)
                    
                    if api_response.success:
                        # Stream the backend response
                        streamed = stream_message(api_response.content)
                        st.session_state.messages.append({"role": "assistant", "content": streamed})
                        
                        # Show response time if available
                        if hasattr(api_response, 'processing_time') and api_response.processing_time:
                            st.caption(f"⚡ Response time: {api_response.processing_time:.2f}s")
                            
                    else:
                        # Handle API errors gracefully per session
                        error_message = f"Having trouble accessing my knowledge base right now. {api_response.error or 'Please try again in a moment.'}"
                        streamed = stream_message(error_message)
                        st.session_state.messages.append({"role": "assistant", "content": streamed})
                        
                        # If it's a connection issue, suggest reconnecting
                        if "connect" in str(api_response.error).lower():
                            st.caption("Try clicking 'Reconnect' in the sidebar")
