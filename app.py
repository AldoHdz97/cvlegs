import streamlit as st
import time
import logging
from datetime import datetime, timedelta
import hashlib
import uuid

# Import from our separate API client module - now with multi-user support + INTERVIEW SCHEDULING
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

# --- COMPREHENSIVE THEME CONTROL ---
def set_theme():
    """Comprehensive theme system with full coverage"""
    if st.session_state.dark_mode:
        # Dark theme colors
        bg, text = "#000510", "#ffffff"
        chat_bg, chat_text = "#1a1a1a", "#ffffff"
        sidebar_bg = "#0f0f0f"
        placeholder_color = "#888"
        border_color = "#333"
        input_bg = "#1a1a1a"
        button_bg = "#2a2a2a"
        button_text = "#ffffff"
        hover_bg = "#333"
    else:
        # Light theme colors
        bg, text = "#ffffff", "#222326"
        chat_bg, chat_text = "#f8f8f8", "#222326"
        sidebar_bg = "#fafafa"
        placeholder_color = "#666"
        border_color = "#e0e0e0"
        input_bg = "#ffffff"
        button_bg = "#f0f0f0"
        button_text = "#222326"
        hover_bg = "#f5f5f5"

    # Comprehensive CSS with complete coverage
    css_content = f"""
    <style id="main-theme-{st.session_state.css_version}">
        /* Force cache busting */
        meta[http-equiv="Cache-Control"] {{ content: "no-cache, no-store, must-revalidate"; }}
        
        /* === CORE APP STRUCTURE === */
        html, body, #root, 
        .stApp, 
        div[data-testid="stAppViewContainer"], 
        section[data-testid="stAppViewContainer"],
        .main,
        div[data-testid="stMain"],
        .main .block-container,
        div[data-testid="block-container"] {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        .main .block-container,
        div[data-testid="block-container"] {{
            padding-top: 2rem !important;
            padding-bottom: 2rem !important;
        }}
        
        /* === COMPREHENSIVE ELEMENT COVERAGE === */
        /* All text elements */
        p, span, div, h1, h2, h3, h4, h5, h6, 
        .stMarkdown, .stMarkdown *, 
        .stText, .stText *,
        .stCaption, .stCaption *,
        .stSuccess, .stSuccess *,
        .stError, .stError *,
        .stWarning, .stWarning *,
        .stInfo, .stInfo * {{
            color: {text} !important;
        }}
        
        /* All container elements */
        .stContainer, .stColumn, .stColumns,
        div[data-testid="column"],
        div[data-testid="stHorizontalBlock"],
        div[data-testid="stVerticalBlock"] {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        /* === CHAT SYSTEM - CLEAN AND CONSISTENT === */
        /* Chat messages container */
        div[data-testid="chat-message"],
        .stChatMessage {{
            background: transparent !important;
            color: {text} !important;
            margin-bottom: 1rem !important;
            display: flex !important;
            align-items: flex-start !important;
            gap: 0.75rem !important;
            border: none !important;
            box-shadow: none !important;
        }}
        
        /* Avatar styling - remove all backgrounds */
        div[data-testid="chat-message"] > div:first-child,
        .stChatMessage > div:first-child,
        div[data-testid="chat-message"] img,
        .stChatMessage img {{
            background: transparent !important;
            border-radius: 50% !important;
            padding: 0 !important;
            width: 40px !important;
            height: 40px !important;
            min-width: 40px !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            border: none !important;
            box-shadow: none !important;
        }}
        
        /* Chat message content */
        div[data-testid="chat-message"] > div:last-child,
        .stChatMessage > div:last-child {{
            flex: 1 !important;
            padding-top: 8px !important;
            background: transparent !important;
        }}
        
        div[data-testid="chat-message"] p,
        div[data-testid="chat-message"] div,
        .stChatMessage p,
        .stChatMessage div {{
            color: {text} !important;
            margin: 0 !important;
            line-height: 1.5 !important;
            background: transparent !important;
        }}
        
        /* === CHAT INPUT - FIXED SEMICIRCLE ISSUE === */
        /* Main chat input container */
        .stChatInput,
        div[data-testid="stChatInput"] {{
            background: transparent !important;
        }}
        
        /* All nested input containers - this fixes the semicircle */
        .stChatInput > div,
        .stChatInput > div > div,
        .stChatInput > div > div > div,
        .stChatInput > div > div > div > div,
        div[data-testid="stChatInput"] > div,
        div[data-testid="stChatInput"] > div > div,
        div[data-testid="stChatInput"] > div > div > div,
        div[data-baseweb="input"],
        div[data-baseweb="input"] > div,
        div[data-baseweb="input"] > div > div {{
            background: {input_bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 1.5rem !important;
            transition: border-color 0.2s ease !important;
            box-shadow: none !important;
            outline: none !important;
        }}
        
        /* Focus states */
        .stChatInput > div:focus-within,
        .stChatInput > div > div:focus-within,
        .stChatInput > div > div > div:focus-within,
        .stChatInput > div > div > div > div:focus-within,
        div[data-testid="stChatInput"] > div:focus-within,
        div[data-baseweb="input"]:focus-within {{
            border-color: {text} !important;
            box-shadow: none !important;
        }}
        
        /* Textarea itself */
        .stChatInput textarea,
        div[data-testid="stChatInput"] textarea,
        textarea[data-testid="stChatInput"] {{
            background-color: transparent !important;
            color: {chat_text} !important;
            border: none !important;
            outline: none !important;
            padding: 0.75rem 1rem !important;
            font-size: 14px !important;
            caret-color: {chat_text} !important;
            border-radius: 1.5rem !important;
            resize: none !important;
        }}
        
        /* Placeholder text */
        .stChatInput textarea::placeholder,
        div[data-testid="stChatInput"] textarea::placeholder {{
            color: {placeholder_color} !important;
            opacity: 0.7 !important;
        }}
        
        /* Remove all focus outlines and validation styling */
        .stChatInput *,
        .stChatInput *:focus,
        .stChatInput *:hover,
        .stChatInput *:active,
        .stChatInput *:invalid,
        div[data-testid="stChatInput"] *,
        div[data-testid="stChatInput"] *:focus,
        div[data-testid="stChatInput"] *:hover {{
            outline: none !important;
            box-shadow: none !important;
        }}
        
        /* === SIDEBAR - COMPLETE COVERAGE === */
        .stSidebar,
        section[data-testid="stSidebar"],
        .stSidebar > div,
        section[data-testid="stSidebar"] > div {{
            background-color: {sidebar_bg} !important;
            border-right: 1px solid {border_color} !important;
            color: {text} !important;
        }}
        
        /* All sidebar elements */
        .stSidebar *,
        section[data-testid="stSidebar"] *,
        .stSidebar div,
        .stSidebar p,
        .stSidebar span,
        .stSidebar label,
        .stSidebar h1,
        .stSidebar h2,
        .stSidebar h3,
        .stSidebar h4,
        .stSidebar h5,
        .stSidebar h6 {{
            color: {text} !important;
            background-color: transparent !important;
        }}
        
        /* === FORM CONTROLS === */
        /* Selectbox */
        .stSelectbox,
        .stSelectbox > div,
        .stSelectbox > div > div,
        .stSelectbox select {{
            background-color: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
        }}
        
        /* Toggle switch and checkbox */
        .stToggle,
        .stCheckbox {{
            color: {text} !important;
        }}
        
        /* Buttons */
        .stButton button,
        button[data-testid="stButton"],
        .stButton > button {{
            background-color: {button_bg} !important;
            color: {button_text} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
            transition: background-color 0.2s ease !important;
        }}
        
        .stButton button:hover,
        button[data-testid="stButton"]:hover {{
            background-color: {hover_bg} !important;
        }}
        
        /* Text input and text area */
        .stTextInput input,
        .stTextArea textarea,
        input[data-testid="stTextInput"],
        textarea[data-testid="stTextArea"] {{
            background-color: {input_bg} !important;
            color: {text} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
        }}
        
        /* === STATUS AND INFO ELEMENTS === */
        .stSuccess {{
            background-color: rgba(0, 255, 0, 0.1) !important;
            color: {text} !important;
            border: 1px solid rgba(0, 255, 0, 0.3) !important;
        }}
        
        .stError {{
            background-color: rgba(255, 0, 0, 0.1) !important;
            color: {text} !important;
            border: 1px solid rgba(255, 0, 0, 0.3) !important;
        }}
        
        .stInfo {{
            background-color: rgba(0, 100, 255, 0.1) !important;
            color: {text} !important;
            border: 1px solid rgba(0, 100, 255, 0.3) !important;
        }}
        
        .stWarning {{
            background-color: rgba(255, 165, 0, 0.1) !important;
            color: {text} !important;
            border: 1px solid rgba(255, 165, 0, 0.3) !important;
        }}
        
        /* Expander */
        .stExpander,
        div[data-testid="stExpander"] {{
            background-color: {bg} !important;
            border: 1px solid {border_color} !important;
            border-radius: 0.5rem !important;
        }}
        
        .stExpander summary,
        div[data-testid="stExpander"] summary {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        /* === HIDE STREAMLIT ELEMENTS === */
        #MainMenu, footer,
        .stDeployButton,
        div[data-testid="stDecoration"],
        .stSpinner,
        div[data-testid="stSpinner"] {{
            visibility: hidden !important;
            display: none !important;
        }}
        
        /* === SIDEBAR BUTTON FIX === */
        /* Ensure sidebar toggle button is always visible and functional */
        button[data-testid="collapsedControl"],
        button[kind="header"],
        button[data-testid="stSidebarNav"],
        .stApp > header button,
        .stApp header button,
        header button {{
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
            position: relative !important;
            z-index: 9999 !important;
            pointer-events: auto !important;
        }}
        
        /* === CUSTOM COMPONENTS === */
        /* Engine icon */
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
        /* 🆕 Schedule Interview Pointer - FIXED VERSION */
        .schedule-pointer {{
            position: fixed;
            top: 180px;  /* 🔧 AJUSTADO para alinear con sidebar */
            left: 60px;  /* 🔧 AJUSTADO para apuntar al sidebar */
            z-index: 500;
            pointer-events: none;
            opacity: 0.85;  /* 🔧 VISIBLE inmediatamente */
            transition: all 0.3s ease;
            font-family: 'Georgia', 'Times New Roman', serif;
        }}

        .schedule-pointer.hidden {{
            opacity: 0;
            visibility: hidden;
            transform: scale(0.9);
        }}

        .schedule-pointer svg {{
            filter: drop-shadow(2px 2px 6px rgba(0,0,0,0.15));
        }}

        /* Theme-aware colors */
        .schedule-pointer .arrow-path {{
            stroke: {text};
            fill: none;
            stroke-width: 2.5;
            stroke-linecap: round;
            stroke-linejoin: round;
            opacity: 0.9;
        }}

        .schedule-pointer .text-element {{
            fill: {text};
            font-family: 'Georgia', 'Times New Roman', serif;
            font-size: 14px;  /* 🔧 Tamaño ajustado */
            font-style: italic;
            font-weight: 500;
            opacity: 0.95;
        }}

        .schedule-pointer .background-shape {{
            fill: {bg};
            fill-opacity: 0.92;
            stroke: {text};
            stroke-width: 1;
            stroke-opacity: 0.3;
        }}

        /* Floating animation */
        @keyframes schedulePointFloat {{
            0%, 100% {{ 
                transform: translateY(0px); 
            }}
            50% {{ 
                transform: translateY(-4px); 
            }}
        }}

        .schedule-pointer {{
            animation: schedulePointFloat 4s ease-in-out infinite;
        }}

        /* Responsive design */
        @media (max-width: 1200px) {{
            .schedule-pointer {{
                left: 50px;
                top: 160px;
            }}
        }}

        @media (max-width: 768px) {{
            .schedule-pointer {{
                display: none !important;
            }}
        }}
        
        /* Backend status */
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
        
        /* FIX 1: Validation bubble - FIXED CONTRAST */
        .validation-bubble {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: #ff4444 !important;
            color: #ffffff !important;
            padding: 12px 24px;
            border-radius: 25px;
            font-size: 14px;
            font-weight: 500;
            z-index: 1000;
            animation: fadeInOut 3s ease-in-out forwards;
            border: 2px solid #ffffff;
        }}
        
        @keyframes fadeInOut {{
            0% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); }}
            15% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            85% {{ opacity: 1; transform: translate(-50%, -50%) scale(1); }}
            100% {{ opacity: 0; transform: translate(-50%, -50%) scale(0.9); visibility: hidden; }}
        }}
        
        /* Loading dots animation */
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
        
        /* === MOBILE RESPONSIVE === */
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
            
            .main .block-container,
            div[data-testid="block-container"] {{
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }}
        }}
        
        /* === FORCE OVERRIDE ANY REMAINING ELEMENTS === */
        /* Catch-all for any missed elements - WITH EXCEPTIONS FOR SIDEBAR CONTROLS */
        [data-testid]:not([data-testid="collapsedControl"]):not([data-testid="stSidebarNav"]):not([data-testid="stToolbar"]) {{
            background-color: {bg} !important;
            color: {text} !important;
        }}
        
        /* Exception for chat input to maintain its styling */
        .stChatInput [data-testid],
        div[data-testid="stChatInput"] [data-testid] {{
            background-color: {input_bg} !important;
        }}
    </style>
    
    <script>
    // Enhanced device detection and theme management
    (function() {{
        const sessionId = '{st.session_state.session_id}';
        const cssVersion = '{st.session_state.css_version}';
        
        // Improved device detection
        function detectDevice() {{
            const userAgent = navigator.userAgent.toLowerCase();
            const isMobileUA = /android|webos|iphone|ipad|ipod|blackberry|iemobile|opera mini/i.test(userAgent);
            const isMobileScreen = window.innerWidth <= 768;
            const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
            
            return isMobileUA || (isMobileScreen && isTouchDevice);
        }}
        
        // Theme initialization
        function initializeTheme() {{
            const manualOverride = localStorage.getItem('manual_theme_override') === 'true';
            const hasDetected = localStorage.getItem(`device_detected_${{sessionId}}`) === 'true';
            
            if (!manualOverride && !hasDetected) {{
                const isMobile = detectDevice();
                const shouldBeDark = !isMobile;
                const currentIsDark = {str(st.session_state.dark_mode).lower()};
                
                if (currentIsDark !== shouldBeDark) {{
                    localStorage.setItem(`device_detected_${{sessionId}}`, 'true');
                    
                    const url = new URL(window.location);
                    url.searchParams.set('theme_auto', shouldBeDark ? 'dark' : 'light');
                    url.searchParams.set('s', sessionId);
                    
                    const cleanUrl = `${{url.origin}}${{url.pathname}}?theme_auto=${{shouldBeDark ? 'dark' : 'light'}}&s=${{sessionId}}`;
                    window.location.replace(cleanUrl);
                    return;
                }}
            }}
        }}
        
        // Enhanced CSS application
        function applyCSSFixes() {{
            // Remove old theme styles
            const oldStyles = document.querySelectorAll('[id^="main-theme-"]');
            oldStyles.forEach(style => {{
                if (style.id !== `main-theme-${{cssVersion}}`) {{
                    style.remove();
                }}
            }});
            
            // Force style reapplication
            const currentStyle = document.getElementById(`main-theme-${{cssVersion}}`);
            if (currentStyle) {{
                // Clone and reapply to force refresh
                const newStyle = currentStyle.cloneNode(true);
                currentStyle.remove();
                document.head.appendChild(newStyle);
            }}
            
            // Force reflow
            document.body.offsetHeight;
        }}

        // 🆕 Schedule Interview Pointer Management
        function initSchedulePointer() {{
            let hasUserInteracted = false;
            let hideTimeout;
            let sidebarCheckInterval;
            
            function createAndShowPointer() {{
                // Only show if no prior interaction and not on mobile
                if (window.innerWidth <= 768) return;
                
                const pointer = document.getElementById('schedule-pointer');
                if (pointer && !hasUserInteracted) {{
                    // Show pointer after initial page load
                    setTimeout(() => {{
                        pointer.style.opacity = '0.75';
                        startAutoHide();
                    }}, 3000);
                }}
            }}
            
            function startAutoHide() {{
                hideTimeout = setTimeout(() => {{
                    const pointer = document.getElementById('schedule-pointer');
                    if (pointer && !hasUserInteracted) {{
                        pointer.classList.add('hidden');
                    }}
                }}, 15000); // Hide after 15 seconds
            }}
            
            function hidePointerOnInteraction() {{
                if (!hasUserInteracted) {{
                    hasUserInteracted = true;
                    const pointer = document.getElementById('schedule-pointer');
                    if (pointer) {{
                        pointer.classList.add('user-interacted');
                    }}
                    clearTimeout(hideTimeout);
                    clearInterval(sidebarCheckInterval);
                }}
            }}
            
            function monitorSidebarState() {{
                const sidebar = document.querySelector('[data-testid="stSidebar"]');
                const pointer = document.getElementById('schedule-pointer');
                
                if (sidebar && pointer && !hasUserInteracted) {{
                    const sidebarRect = sidebar.getBoundingClientRect();
                    const isExpanded = sidebarRect.width > 100;
                    
                    if (isExpanded) {{
                        pointer.classList.add('sidebar-open');
                    }} else {{
                        pointer.classList.remove('sidebar-open');
                    }}
                }}
            }}
            
            // Setup event listeners
            ['click', 'scroll', 'keydown', 'touchstart'].forEach(eventType => {{
                document.addEventListener(eventType, hidePointerOnInteraction, {{ 
                    once: true, 
                    passive: true 
                }});
            }});
            
            // Initialize pointer
            setTimeout(() => {{
                createAndShowPointer();
                
                // Start monitoring sidebar
                sidebarCheckInterval = setInterval(monitorSidebarState, 800);
                
                // Initial sidebar check
                setTimeout(monitorSidebarState, 500);
            }}, 1000);
        }}
        
        // Initialize everything
        if (document.readyState === 'loading') {{
            document.addEventListener('DOMContentLoaded', function() {{
                applyCSSFixes();
                setTimeout(initializeTheme, 100);
                setTimeout(initSchedulePointer, 500);
            }});
        }} else {{
            applyCSSFixes();
            setTimeout(initializeTheme, 100);
            setTimeout(initSchedulePointer, 500);
        }}
        
        // Reapply styles on any DOM changes
        const observer = new MutationObserver(function(mutations) {{
            let shouldReapply = false;
            mutations.forEach(function(mutation) {{
                if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {{
                    shouldReapply = true;
                }}
            }});
            
            if (shouldReapply) {{
                setTimeout(applyCSSFixes, 100);
            }}
        }});
        
        observer.observe(document.body, {{ childList: true, subtree: true }});
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

# 🆕 Check if interview scheduling is available
if st.session_state.backend_connected and cv_client:
    try:
        health = cv_client.get_health_status()
        if health.get("interview_scheduling"):
            st.markdown('<div class="backend-status" style="background: #4CAF50; right: 120px;">SCHEDULING ONLINE</div>', unsafe_allow_html=True)
    except:
        pass

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

# Simple Arrow
# 🔥 SOLUCIÓN SIMPLE - BUSCA esta línea en tu app.py:
# st.markdown(f'<div class="engine-icon">{engine_svg}</div>', unsafe_allow_html=True)

# Y AGREGA JUSTO DESPUÉS de esa línea estas 3 líneas:

# Flecha simple que SÍ se ve
pointer_html = f'''
<div style="position: fixed; top: 300px; left: 200px; z-index: 1000; 
            background: {text}; color: {bg}; padding: 8px 15px; 
            border-radius: 20px; font-size: 14px; font-weight: bold;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3);
            animation: floatPointer 3s ease-in-out infinite;">
    ← Schedule Interview in Sidebar
</div>

<style>
@keyframes floatPointer {{
    0%, 100% {{ transform: translateY(0px); }}
    50% {{ transform: translateY(-5px); }}
}}
</style>
'''

st.markdown(pointer_html, unsafe_allow_html=True)

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
    
    # ALTERNATIVE SOLUTION: Custom Toggle Buttons - GUARANTEED VISIBLE
    st.write("**Theme Mode:**")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🌙 Dark", key="dark_btn", use_container_width=True, 
                    type="primary" if st.session_state.dark_mode else "secondary"):
            if not st.session_state.dark_mode:
                st.session_state.dark_mode = True
                st.session_state.manual_theme_override = True
                st.markdown('<script>localStorage.setItem("manual_theme_override", "true");</script>', unsafe_allow_html=True)
                st.rerun()
    
    with col2:
        if st.button("☀️ Light", key="light_btn", use_container_width=True,
                    type="primary" if not st.session_state.dark_mode else "secondary"):
            if st.session_state.dark_mode:
                st.session_state.dark_mode = False
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
            
            # 🆕 Real-time validation feedback
            if contact_info.strip():
                cv_client = get_user_cv_client()
                is_valid, validation_msg = cv_client.validate_interview_data(
                    st.session_state.selected_day or "temp",
                    st.session_state.selected_time or "temp", 
                    contact_info
                )
                
                if not is_valid and "contact" in validation_msg.lower():
                    st.warning(f"⚠️ {validation_msg}")
                elif contact_info.strip() and len(contact_info) >= 10:
                    has_email = "@" in contact_info
                    has_phone = any(char.isdigit() for char in contact_info)
                    if has_email or has_phone:
                        st.success("✅ Contact information looks good!")
            
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
                # 🔥 NUEVA INTEGRACIÓN CON API CLIENT
                if st.button("Request Interview", key="submit_int", type="primary", use_container_width=True):
                    # Get the CV client (same pattern as chat)
                    cv_client = get_user_cv_client()
                    
                    # Validate using the client's validation method
                    is_valid, error_msg = cv_client.validate_interview_data(
                        st.session_state.selected_day,
                        st.session_state.selected_time,
                        contact_info.strip()
                    )
                    
                    if not is_valid:
                        st.error(f"❌ {error_msg}")
                    else:
                        # Show loading state (same style as chat)
                        with st.spinner("Scheduling your interview..."):
                            # Schedule using the extended API client
                            result = cv_client.schedule_interview(
                                selected_day=st.session_state.selected_day,
                                selected_time=st.session_state.selected_time,
                                contact_info=contact_info.strip()
                            )
                            
                            if result.success:
                                # Success! 🎉
                                st.success(f"✅ {result.content}")
                                
                                # Show additional info if available
                                if result.reference_id:
                                    st.info(f"📋 Reference ID: {result.reference_id}")
                                
                                if result.processing_time:
                                    st.caption(f"⏱️ Processed in {result.processing_time:.2f}s")
                                
                                st.balloons()  # 🎈 Celebration!
                                
                                # Reset form state
                                st.session_state.show_calendar_picker = False
                                st.session_state.scheduling_step = 0
                                st.session_state.selected_day = None
                                st.session_state.selected_time = None
                                st.session_state.contact_info = ""
                                
                                # Auto-close after 3 seconds
                                time.sleep(3)
                                st.rerun()
                                
                            else:
                                # Error handling (same pattern as chat errors)
                                st.error(f"❌ {result.error or 'Failed to schedule interview'}")
                                
                                # Show specific error suggestions
                                if "timeout" in (result.error or "").lower():
                                    st.warning("⏰ Request timed out. Please try again.")
                                elif "connect" in (result.error or "").lower():
                                    st.warning("🌐 Connection issue. Check your internet and try again.")
                                elif "500" in (result.error or ""):
                                    st.warning("🔧 Server temporarily unavailable. Please try again in a moment.")
                                else:
                                    st.warning("🔄 Please try again in a moment.")
                                
                                # Show processing time if available (for debugging)
                                if result.processing_time:
                                    st.caption(f"⏱️ Failed after {result.processing_time:.2f}s")
                                
                                # Keep the form open for retry
                                logger.error(f"Interview scheduling failed: {result.error}")

        st.markdown("---")
        if st.button("Cancel", key="cancel_int", use_container_width=True):
            st.session_state.show_calendar_picker = False
            st.session_state.scheduling_step = 0
            st.rerun()

    st.markdown("---")
    
    # 🆕 DEBUG INFO (opcional - solo para testing)
    with st.expander("🔧 Debug Info", expanded=False):
        if st.button("Show Debug Info", key="debug_info"):
            try:
                from api_client import get_interview_debug_info, get_session_debug_info
                
                debug_info = get_session_debug_info()
                interview_info = get_interview_debug_info()
                
                st.json({
                    "session": debug_info,
                    "interview": interview_info
                })
            except Exception as e:
                st.error(f"Debug failed: {e}")

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
    greeting = ("Hey there! I'm Aldo* or at least his digital Twin ! "
                "Feel free to ask me anything about my work, skills, or projects. "
                "I'll try to keep the humble bragging to a minimum (no promises though).")
    
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
                
                # More natural, conversational offline responses
                if any(word in prompt.lower() for word in ['skill', 'technology', 'programming', 'language', 'tech']):
                    answer = "Oh, my tech stack? I'm pretty deep into Python - it's like my bread and butter. SQL for wrangling databases, Tableau for making data look pretty, and I've been diving into some cool AI stuff lately. I love automating boring tasks and building dashboards that actually make sense to people."
                
                elif any(word in prompt.lower() for word in ['experience', 'work', 'job', 'company', 'career']):
                    answer = "Right now I'm working as a Social Listening Analyst at Swarm Data, analyzing how different Tec de Monterrey campuses are performing online. Before that I did data analysis at Wii México and even tried my hand at content creation for a while. It's been quite the journey, honestly."
                
                elif any(word in prompt.lower() for word in ['education', 'degree', 'university', 'study', 'school']):
                    answer = "I studied Economics at Tecnológico de Monterrey - graduated in 2021. Loved working with Python and R for statistical projects. Also picked up some solid certifications along the way like Tableau Desktop and Power BI. The econ background really helps with data analysis."
                
                elif any(word in prompt.lower() for word in ['project', 'built', 'created', 'developed', 'portfolio']):
                    answer = "I've worked on some pretty cool stuff! Built a business growth dashboard tracking company density across Nuevo León, created an NFL betting index system (don't judge lol), and recently developed this AI-powered CV manager using Next.js. I love projects that solve real problems."
                
                elif any(word in prompt.lower() for word in ['day', 'doing', 'how', 'today', 'going']):
                    answer = "My day's been good, thanks for asking! Been working on some interesting data analysis projects and exploring new ways to visualize insights. Always something new to learn in this field. How's yours going?"
                
                elif any(word in prompt.lower() for word in ['location', 'where', 'live', 'from', 'based']):
                    answer = "I'm based in Monterrey, Mexico. Great city for tech and business - lots of opportunities here, especially with the proximity to the US market. Plus the food is incredible, can't complain about that!"
                
                elif any(word in prompt.lower() for word in ['contact', 'email', 'reach', 'connect', 'hire']):
                    answer = "You can reach me through this platform for now, but if you're interested in connecting professionally, feel free to ask about setting up a proper interview. I'm always open to discussing interesting opportunities or collaborations."
                
                else:
                    answer = f"Hmm, that's an interesting question about '{prompt}'. I'm an economist turned data analyst who loves working with Python and building things that make data useful. What would you like to know specifically? My background, projects, skills, or something else?"
                
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
