"""
MULTI-USER API Client - Session Isolated - CONVERSATIONAL MEMORY EDITION
Each user gets their own session - WITH MEMORY SUPPORT!
Backend-compatible payload WITH session_id for conversational memory
"""

import httpx
import asyncio
import time
import logging
import uuid
import streamlit as st
from typing import Dict, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Simple response"""
    success: bool
    content: str
    error: Optional[str] = None
    processing_time: Optional[float] = None
    session_id: Optional[str] = None  # ← NUEVO: Para rastrear session_id
    conversation_turn: Optional[int] = None  # ← NUEVO: Para rastrear turnos

class CVBackendClient:
    """Multi-User CV Client - Session isolated per user - WITH CONVERSATIONAL MEMORY"""
    
    def __init__(self, session_id: str = None):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        self.endpoint = "/query"
        
        # ✅ Each user gets unique session ID FOR CONVERSATION MEMORY
        self.session_id = session_id or str(uuid.uuid4())
        self.conversation_session_id = f"conversation_{self.session_id}"  # ← NUEVO: Para conversaciones
        
        # ✅ Per-session failure tracking (not shared between users)
        self.failure_count = 0
        self.last_request_time = None
        
        # 🆕 Conversational memory tracking
        self.conversation_started = False
        self.message_count = 0
        
        logger.info(f"🗣️  Conversational API Client - Session: {self.session_id[:8]} - Conversation: {self.conversation_session_id[:16]} - endpoint: {self.endpoint}")
    
    async def _make_request_async(self, question: str) -> APIResponse:
        """Make request with session isolation AND CONVERSATIONAL MEMORY - BACKEND COMPATIBLE"""
        
        # 🔥 FIXED: Send session_id for conversational memory
        payload = {
            "question": question,
            "session_id": self.conversation_session_id,  # ← CRÍTICO: Enviar session_id
            "maintain_context": True  # ← NUEVO: Mantener contexto conversacional
        }
        
        start_time = time.time()
        self.last_request_time = start_time
        self.message_count += 1
        url = f"{self.base_url}{self.endpoint}"
        
        logger.info(f"🗣️  Conversational POST {url} [Session: {self.session_id[:8]}, Msg: {self.message_count}]")
        
        # ✅ Fresh client each time - no persistent connections
        async with httpx.AsyncClient(
            timeout=self.timeout, 
            http2=False,
            limits=httpx.Limits(
                max_connections=2,           # Limited per user
                max_keepalive_connections=0, # No connection reuse
                keepalive_expiry=0.0        # Immediate expiry
            )
        ) as client:
            try:
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "X-Session-ID": self.session_id,          # User tracking
                        "X-Conversation-ID": self.conversation_session_id,  # ← NUEVO: Conversation tracking
                        "X-User-Agent": "CVApp-Conversational",   # Updated user agent
                        "Connection": "close"                     # Force close
                    }
                )
                
                processing_time = time.time() - start_time
                logger.info(f"Response: {response.status_code} in {processing_time:.2f}s [Session: {self.session_id[:8]}, Msg: {self.message_count}]")
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    
                    # ✅ Reset failure count on success
                    self.failure_count = 0
                    self.conversation_started = True
                    
                    # 🆕 Extract conversational metadata
                    session_id_returned = data.get("session_id") or data.get("metadata", {}).get("session_id")
                    conversation_turn = data.get("conversation_turn") or data.get("metadata", {}).get("conversation_turn", self.message_count)
                    
                    logger.info(f"✅ SUCCESS! Answer: {len(answer)} chars, Turn: {conversation_turn} [Session: {self.session_id[:8]}]")
                    
                    # 🔍 Log for debugging conversational memory
                    if self.message_count > 1:
                        logger.info(f"🧠 Conversational context: Message #{self.message_count}, Session: {session_id_returned[:16] if session_id_returned else 'none'}")
                    
                    return APIResponse(
                        success=True,
                        content=answer,
                        processing_time=processing_time,
                        session_id=session_id_returned,
                        conversation_turn=conversation_turn
                    )
                else:
                    # ✅ Track failures per session (not globally)
                    self.failure_count += 1
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"{error_msg} [Session: {self.session_id[:8]}]")
                    
                    return APIResponse(
                        success=False,
                        content="",
                        error=error_msg,
                        processing_time=processing_time
                    )
            
            except httpx.TimeoutException:
                self.failure_count += 1
                error_msg = f"Request timeout after {self.timeout}s"
                logger.error(f"{error_msg} [Session: {self.session_id[:8]}]")
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except httpx.ConnectError:
                self.failure_count += 1
                error_msg = "Cannot connect to backend"
                logger.error(f"{error_msg} [Session: {self.session_id[:8]}]")
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except Exception as e:
                self.failure_count += 1
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"{error_msg} [Session: {self.session_id[:8]}]")
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
    
    def query_cv(self, message: str, response_format: str = None) -> APIResponse:
        """Query CV with session isolation AND CONVERSATIONAL MEMORY"""
        try:
            if not self.conversation_started:
                logger.info(f"🆕 Starting new conversation [Session: {self.session_id[:8]}]")
            
            return asyncio.run(self._make_request_async(message))
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Conversational query failed for session {self.session_id[:8]}: {e}")
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    def start_new_conversation(self):
        """🆕 Start a new conversation (reset memory)"""
        old_conversation = self.conversation_session_id[:16]
        self.conversation_session_id = f"conversation_{str(uuid.uuid4())}"
        self.conversation_started = False
        self.message_count = 0
        
        logger.info(f"🔄 New conversation started [Session: {self.session_id[:8]}] Old: {old_conversation} → New: {self.conversation_session_id[:16]}")
    
    def get_conversation_info(self) -> Dict[str, Any]:
        """🆕 Get conversation status information"""
        return {
            "session_id": self.session_id[:8],
            "conversation_session_id": self.conversation_session_id[:16],
            "conversation_started": self.conversation_started,
            "message_count": self.message_count,
            "failure_count": self.failure_count
        }
    
    def get_health_status(self) -> Dict[str, Any]:
        """Session-specific health check - ROBUST ERROR HANDLING WITH CONVERSATION INFO"""
        try:
            result = asyncio.run(self._check_health())
            
            # ✅ Always return a proper dictionary
            health_status = {
                "status": "healthy" if result else "unhealthy",
                "session_id": self.session_id[:8] if self.session_id else "unknown", 
                "conversation_session_id": self.conversation_session_id[:16] if hasattr(self, 'conversation_session_id') else "none",
                "failure_count": getattr(self, 'failure_count', 0),
                "message_count": getattr(self, 'message_count', 0),
                "conversation_started": getattr(self, 'conversation_started', False),
                "last_request": getattr(self, 'last_request_time', None),
                "backend_url": self.base_url,
                "endpoint": self.endpoint,
                "conversational_memory": True  # ← NUEVO: Indica soporte conversacional
            }
            
            logger.info(f"Health check for session {self.session_id[:8]}: {health_status['status']} (Conversation: {health_status['conversation_started']})")
            return health_status
            
        except Exception as e:
            logger.error(f"Health check failed for session {self.session_id[:8]}: {e}")
            
            # ✅ Always return a dictionary, even on error
            return {
                "status": "error", 
                "error": str(e),
                "session_id": self.session_id[:8] if self.session_id else "unknown",
                "failure_count": getattr(self, 'failure_count', 0),
                "backend_url": self.base_url,
                "endpoint": self.endpoint,
                "conversational_memory": True
            }
    
    async def _check_health(self) -> bool:
        """Check backend health per session - ROBUST ERROR HANDLING"""
        try:
            async with httpx.AsyncClient(
                timeout=5.0, 
                http2=False,
                limits=httpx.Limits(max_connections=1, max_keepalive_connections=0)
            ) as client:
                response = await client.get(
                    f"{self.base_url}/health",
                    headers={
                        "X-Session-ID": self.session_id,
                        "X-Conversation-ID": getattr(self, 'conversation_session_id', 'none'),
                        "Connection": "close"
                    }
                )
                
                is_healthy = response.status_code == 200
                logger.debug(f"Health check for session {self.session_id[:8]}: {response.status_code} -> {'healthy' if is_healthy else 'unhealthy'}")
                
                return is_healthy
                
        except httpx.TimeoutException:
            logger.warning(f"Health check timeout for session {self.session_id[:8]}")
            return False
        except httpx.ConnectError:
            logger.warning(f"Health check connection error for session {self.session_id[:8]}")
            return False
        except Exception as e:
            logger.warning(f"Health check failed for session {self.session_id[:8]}: {e}")
            return False

# ✅ Session-specific client management WITH CONVERSATIONAL MEMORY - ROBUST ERROR HANDLING
def get_session_cv_client() -> CVBackendClient:
    """Get or create session-specific CV client WITH CONVERSATIONAL MEMORY - NO GLOBAL SHARING"""
    
    try:
        # ✅ Create unique session ID per Streamlit user session
        if "user_session_id" not in st.session_state:
            st.session_state.user_session_id = str(uuid.uuid4())
            logger.info(f"🆕 New user session created: {st.session_state.user_session_id[:8]}")
        
        # ✅ Create session-specific client (stored in user's session state) WITH CONVERSATION SUPPORT
        if "cv_client" not in st.session_state:
            st.session_state.cv_client = CVBackendClient(st.session_state.user_session_id)
            logger.info(f"🗣️  Conversational CV client created for session: {st.session_state.user_session_id[:8]}")
        
        return st.session_state.cv_client
        
    except Exception as e:
        logger.error(f"Failed to create session CV client: {e}")
        # ✅ Fallback: create a basic client
        return CVBackendClient()

def initialize_session_backend():
    """Initialize backend per user session WITH CONVERSATIONAL MEMORY - ROBUST ERROR HANDLING"""
    try:
        client = get_session_cv_client()
        
        # ✅ FIXED: Handle None response from get_health_status
        health = client.get_health_status()
        
        if health is None or not isinstance(health, dict):
            # Fallback if health check fails completely
            logger.warning("Health check returned invalid response, assuming offline")
            st.session_state.backend_connected = False
            return client  # Still return client for potential use
        
        # ✅ Safe access to health status
        is_healthy = health.get("status") == "healthy"
        st.session_state.backend_connected = is_healthy
        
        session_id = getattr(client, 'session_id', 'unknown')
        session_display = session_id[:8] if session_id != 'unknown' else 'unknown'
        
        # 🆕 Log conversational info
        conversation_info = client.get_conversation_info()
        logger.info(f"🗣️  Backend initialized for user session: {session_display} (Conversation: {conversation_info['conversation_session_id']}, Status: {health.get('status', 'unknown')})")
        
        return client
        
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        st.session_state.backend_connected = False
        
        # ✅ Still return a client even if health check fails  
        try:
            return get_session_cv_client()
        except Exception as fallback_error:
            logger.error(f"Fallback client creation failed: {fallback_error}")
            return None

# ✅ Backward compatibility - but now session-isolated WITH CONVERSATION MEMORY
def get_cv_client() -> CVBackendClient:
    """Backward compatibility function - now session-isolated with conversational memory"""
    return get_session_cv_client()

# ✅ Additional utility functions for debugging CONVERSATION SUPPORT
def reset_session_client():
    """Reset the session client (useful for debugging) - MAINTAINS CONVERSATION SUPPORT"""
    try:
        if "cv_client" in st.session_state:
            # Log conversation info before reset
            old_client = st.session_state.cv_client
            if hasattr(old_client, 'get_conversation_info'):
                old_info = old_client.get_conversation_info()
                logger.info(f"🔄 Resetting client with conversation: {old_info}")
            
            del st.session_state.cv_client
            
        if "user_session_id" in st.session_state:
            old_session = st.session_state.user_session_id[:8]
            del st.session_state.user_session_id
            logger.info(f"Reset session client for session: {old_session}")
        
        # Create new client
        return get_session_cv_client()
    except Exception as e:
        logger.error(f"Failed to reset session client: {e}")
        return None

def start_new_conversation():
    """🆕 Start a new conversation (reset conversational memory)"""
    try:
        client = get_session_cv_client()
        if hasattr(client, 'start_new_conversation'):
            client.start_new_conversation()
            logger.info(f"🔄 Started new conversation for session: {client.session_id[:8]}")
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to start new conversation: {e}")
        return False

def get_session_debug_info() -> Dict[str, Any]:
    """Get debug information about the current session WITH CONVERSATION INFO"""
    try:
        client = get_session_cv_client()
        health = client.get_health_status()
        conversation_info = client.get_conversation_info() if hasattr(client, 'get_conversation_info') else {}
        
        return {
            "session_id": st.session_state.get("user_session_id", "unknown")[:8],
            "backend_connected": st.session_state.get("backend_connected", False),
            "client_session_id": getattr(client, 'session_id', 'unknown')[:8],
            "conversation_session_id": conversation_info.get('conversation_session_id', 'none'),
            "conversation_started": conversation_info.get('conversation_started', False),
            "message_count": conversation_info.get('message_count', 0),
            "failure_count": getattr(client, 'failure_count', 0),
            "health_status": health,
            "conversational_memory_enabled": True,
            "streamlit_session_state_keys": list(st.session_state.keys())
        }
    except Exception as e:
        return {
            "error": str(e),
            "session_debug_failed": True,
            "conversational_memory_enabled": True
        }
