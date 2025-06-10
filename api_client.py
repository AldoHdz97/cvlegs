import streamlit as st
import time
from datetime import datetime, timedelta

# Backend integration imports
import httpx
import asyncio
import json
from typing import Dict, Any, Optional, Generator
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- BACKEND INTEGRATION CLASSES ---
class QueryType(str, Enum):
    """Query types matching backend schema"""
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    SUMMARY = "summary"
    CONTACT = "contact"
    ACHIEVEMENTS = "achievements"
    CERTIFICATIONS = "certifications"
    LANGUAGES = "languages"
    TOOLS = "tools"
    METHODOLOGIES = "methodologies"
    TECHNICAL = "technical"
    GENERAL = "general"
    CLARIFICATION = "clarification"

class ResponseFormat(str, Enum):
    """Response format options"""
    DETAILED = "detailed"
    SUMMARY = "summary"
    BULLET_POINTS = "bullet_points"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"

@dataclass
class APIResponse:
    """Structured API response"""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None

class CVBackendClient:
    """CV Backend Client for Railway Integration"""
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 60.0
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_timeout = 60
        
        logger.info(f"CV Backend Client initialized for {self.base_url}")
    
    def _classify_query(self, message: str) -> QueryType:
        """Intelligently classify user query"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in [
            'skill', 'technology', 'programming', 'language', 'framework', 
            'python', 'javascript', 'sql', 'tableau', 'tool'
        ]):
            return QueryType.TECHNICAL
        elif any(word in message_lower for word in [
            'experience', 'work', 'job', 'company', 'role', 'position', 
            'career', 'employment', 'professional'
        ]):
            return QueryType.EXPERIENCE
        elif any(word in message_lower for word in [
            'education', 'degree', 'university', 'study', 'academic', 
            'school', 'learning', 'course', 'certification'
        ]):
            return QueryType.EDUCATION
        elif any(word in message_lower for word in [
            'project', 'built', 'created', 'developed', 'portfolio', 
            'application', 'system', 'dashboard'
        ]):
            return QueryType.PROJECTS
        elif any(word in message_lower for word in [
            'summary', 'overview', 'background', 'about', 'introduction', 
            'profile', 'bio', 'who are you'
        ]):
            return QueryType.SUMMARY
        elif any(word in message_lower for word in [
            'contact', 'email', 'phone', 'location', 'address', 'linkedin', 
            'reach', 'connect'
        ]):
            return QueryType.CONTACT
        else:
            return QueryType.GENERAL
    
    def _map_response_format(self, streamlit_format: str) -> ResponseFormat:
        """Map Streamlit response format to backend format"""
        format_mapping = {
            "Detailed": ResponseFormat.DETAILED,
            "Summary": ResponseFormat.SUMMARY,
            "Bullet points": ResponseFormat.BULLET_POINTS,
            "Technical": ResponseFormat.TECHNICAL,
            "Conversational": ResponseFormat.CONVERSATIONAL
        }
        return format_mapping.get(streamlit_format, ResponseFormat.DETAILED)
    
    def _check_circuit_breaker(self) -> bool:
        """Check if circuit breaker should allow requests"""
        if not self.circuit_open:
            return True
        
        if self.last_failure_time and time.time() - self.last_failure_time > self.circuit_timeout:
            self.circuit_open = False
            self.failure_count = 0
            logger.info("Circuit breaker reset - allowing requests")
            return True
        
        return False
    
    def _record_failure(self):
        """Record API failure for circuit breaker"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.failure_count >= 3:
            self.circuit_open = True
            logger.warning("Circuit breaker opened due to repeated failures")
    
    def _record_success(self):
        """Record API success for circuit breaker"""
        self.failure_count = 0
        self.circuit_open = False
    
    async def _make_request_async(
        self, 
        message: str, 
        response_format: ResponseFormat,
        query_type: QueryType
    ) -> APIResponse:
        """Make async request to backend"""
        
        request_payload = {
            "question": message,
            "k": 3,
            "query_type": query_type.value,
            "response_format": response_format.value,
            "include_sources": True,
            "include_confidence_explanation": False,
            "language": "en",
            "max_response_length": 800
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(
            timeout=self.timeout,
            limits=httpx.Limits(
                max_connections=10,
                max_keepalive_connections=5,
                keepalive_expiry=30.0
            ),
            http2=True
        ) as client:
            
            try:
                logger.info(f"Making request to {self.base_url}/v1/query")
                
                response = await client.post(
                    f"{self.base_url}/v1/query",
                    json=request_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    self._record_success()
                    response_data = response.json()
                    
                    return APIResponse(
                        success=True,
                        content=response_data.get("answer", "No response received"),
                        metadata={
                            "confidence_level": response_data.get("confidence_level"),
                            "query_type": response_data.get("query_type"),
                            "relevant_chunks": response_data.get("relevant_chunks"),
                            "model_used": response_data.get("model_used"),
                        },
                        processing_time=processing_time,
                        confidence_score=response_data.get("confidence_score")
                    )
                
                else:
                    self._record_failure()
                    error_msg = f"API error {response.status_code}: {response.text}"
                    logger.error(error_msg)
                    
                    return APIResponse(
                        success=False,
                        content="",
                        error=error_msg,
                        processing_time=processing_time
                    )
            
            except httpx.TimeoutException:
                self._record_failure()
                error_msg = f"Request timeout after {self.timeout}s"
                logger.error(error_msg)
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except httpx.ConnectError:
                self._record_failure()
                error_msg = "Cannot connect to CV backend service"
                logger.error(error_msg)
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except Exception as e:
                self._record_failure()
                error_msg = f"Unexpected error: {str(e)}"
                logger.error(error_msg)
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
    
    def query_cv(self, message: str, response_format: str = "Detailed") -> APIResponse:
        """Main method to query the CV backend"""
        
        # Check circuit breaker
        if not self._check_circuit_breaker():
            return APIResponse(
                success=False,
                content="",
                error="Service temporarily unavailable. Please try again in a minute."
            )
        
        # Map formats and classify query
        backend_format = self._map_response_format(response_format)
        query_type = self._classify_query(message)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                response = asyncio.run(
                    self._make_request_async(message, backend_format, query_type)
                )
                
                if response.success:
                    return response
                
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        return APIResponse(
            success=False,
            content="",
            error="Service temporarily unavailable after multiple attempts"
        )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get backend health status"""
        try:
            response = asyncio.run(self._check_health_async())
            return {
                "status": "healthy" if response else "unhealthy",
                "circuit_open": self.circuit_open,
                "failure_count": self.failure_count
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "circuit_open": self.circuit_open,
                "failure_count": self.failure_count
            }
    
    async def _check_health_async(self) -> bool:
        """Async health check"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

# Global client instance
@st.cache_resource
def get_cv_client() -> CVBackendClient:
    """Get cached CV backend client instance"""
    return CVBackendClient()

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
    f"<h2 style='font-family:Roboto,sans-serif;font-weight:300;margin-bottom:8px;margin-top:8px;color:{text};text-align:center;'>CV Assistant</h2>",
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
    f'<div class="engine-icon" style="width:38px;height:38px;" title="CV Assistant Engine">{engine_svg}</div>',
    unsafe_allow_html=True
)

# --- BACKGROUND CALENDAR (LARGE, CENTERED-RIGHT, SKELETON STYLE) ---
def make_background_calendar():
    # Get today's date to start the calendar
    today = datetime.now()
    start_date = today.replace(day=1)  # Start from first day of current month
    current_day = today.day
    
    # Calculate how many days in current month
    if today.month == 12:
        next_month = today.replace(year=today.year + 1, month=1, day=1)
    else:
        next_month = today.replace(month=today.month + 1, day=1)
    days_in_month = (next_month - start_date).days
    
    # Find what day of week the month starts on (0=Monday, 6=Sunday)
    first_day_weekday = start_date.weekday()
    # Convert to Sunday=0 format for calendar display
    first_day_offset = (first_day_weekday + 1) % 7
    
    # Color scheme based on theme
    if st.session_state.dark_mode:
        calendar_color = "#ffffff"
        calendar_opacity = "0.40"
        text_opacity = "0.45"
        current_day_opacity = "0.65"
    else:
        calendar_color = "#333333"
        calendar_opacity = "0.40"
        text_opacity = "0.50"
        current_day_opacity = "0.70"
    
    # Calendar dimensions - larger and more prominent
    cal_width = 420
    cal_height = 320
    cell_size = 50
    start_x = 40
    start_y = 80
    
    # Build calendar grid
    calendar_elements = []
    
    # Weekday headers with casual font
    weekdays = ['SUN', 'MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
    for col, day_name in enumerate(weekdays):
        x = start_x + col * cell_size + 25
        y = start_y - 20
        calendar_elements.append(
            f'<text x="{x}" y="{y}" text-anchor="middle" font-family="Inter, -apple-system, BlinkMacSystemFont, sans-serif" '
            f'font-size="13" font-weight="400" fill="{calendar_color}" fill-opacity="{text_opacity}">{day_name}</text>'
        )
    
    # Calendar days - skeleton style with rounded corners
    day_counter = 1
    for row in range(6):  # 6 rows to accommodate all possible month layouts
        for col in range(7):  # 7 days per week
            x = start_x + col * cell_size
            y = start_y + row * cell_size
            
            # Skip cells before month starts
            if row == 0 and col < first_day_offset:
                continue
            
            # Stop after month ends
            if day_counter > days_in_month:
                break
            
            # Determine if this is today
            is_today = day_counter == current_day
            opacity = current_day_opacity if is_today else calendar_opacity
            stroke_width = "2.5" if is_today else "1.5"
            
            # Hollow square with rounded corners
            calendar_elements.append(
                f'<rect x="{x}" y="{y}" width="{cell_size-8}" height="{cell_size-8}" '
                f'rx="8" ry="8" fill="none" stroke="{calendar_color}" '
                f'stroke-opacity="{opacity}" stroke-width="{stroke_width}"/>'
            )
            
            # Day number with casual, friendly font
            text_x = x + (cell_size-8) // 2
            text_y = y + (cell_size-8) // 2 + 5
            font_weight = "600" if is_today else "400"
            calendar_elements.append(
                f'<text x="{text_x}" y="{text_y}" text-anchor="middle" '
                f'font-family="Inter, -apple-system, BlinkMacSystemFont, sans-serif" '
                f'font-size="16" font-weight="{font_weight}" fill="{calendar_color}" '
                f'fill-opacity="{opacity}">{day_counter}</text>'
            )
            
            day_counter += 1
    
    # Create the complete SVG
    svg = f'''
    <svg width="{cal_width}" height="{cal_height}" viewBox="0 0 {cal_width} {cal_height}" 
         fill="none" xmlns="http://www.w3.org/2000/svg">
        {''.join(calendar_elements)}
    </svg>
    '''
    return svg

# Display the enhanced calendar with better positioning
st.markdown(f'''
<div class="calendar-bg" style="
    position: fixed;
    top: 50%;
    right: 8%;
    transform: translateY(-50%);
    z-index: 1;
    opacity: 0.85;
    pointer-events: none;
    transition: all 0.3s ease;
">
{make_background_calendar()}
</div>
''', unsafe_allow_html=True)

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

# --- ENHANCED STREAMING FUNCTION ---
def stream_message(msg, role="assistant", delay=0.016):
    """Enhanced streaming with better error handling"""
    try:
        with st.chat_message(role):
            output = st.empty()
            txt = ""
            for char in msg:
                txt += char
                output.markdown(txt)
                time.sleep(delay)
            return txt
    except Exception as e:
        st.error(f"Error displaying message: {e}")
        return msg

# --- GREETING & CHAT HISTORY ---
# Handle initial greeting (only once)
if not st.session_state.greeting_streamed:
    greeting = "Hi there! I'm Aldo*—or at least, my digital twin. Go ahead and ask me anything about my professional life, projects, or skills. I promise not to humblebrag too much (okay, maybe just a little)."
    streamed_greeting = stream_message(greeting, role="assistant")
    st.session_state.messages.append({"role": "assistant", "content": streamed_greeting})
    st.session_state.greeting_streamed = True
else:
    # Show message history
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
                    
                    # Show metadata if available
                    if api_response.metadata:
                        with st.expander("📊 Response Details", expanded=False):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                if api_response.confidence_score:
                                    st.metric("Confidence Score", f"{api_response.confidence_score:.1%}")
                                if api_response.metadata.get("relevant_chunks"):
                                    st.metric("Sources Used", api_response.metadata["relevant_chunks"])
                            
                            with col2:
                                if api_response.processing_time:
                                    st.metric("Response Time", f"{api_response.processing_time:.2f}s")
                                if api_response.metadata.get("query_type"):
                                    st.metric("Query Type", api_response.metadata["query_type"].title())
                
                else:
                    # Handle API errors gracefully
                    error_message = f"⚠️ Having trouble accessing my knowledge base right now. {api_response.error or 'Please try again in a moment.'}"
                    streamed = stream_message(error_message)
                    st.session_state.messages.append({"role": "assistant", "content": streamed})
