"""
MULTI-USER API Client - Session Isolated - FIXED ERROR HANDLING
Each user gets their own session - no shared state!
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

class CVBackendClient:
    """Multi-User CV Client - Session isolated per user - FIXED"""
    
    def __init__(self, session_id: str = None):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        self.endpoint = "/query"
        
        # ✅ Each user gets unique session ID
        self.session_id = session_id or str(uuid.uuid4())
        
        # ✅ Per-session failure tracking (not shared between users)
        self.failure_count = 0
        self.last_request_time = None
        
        logger.info(f"Multi-user API Client - Session: {self.session_id[:8]} - endpoint: {self.endpoint}")
    
    async def _make_request_async(self, question: str) -> APIResponse:
        """Make request with session isolation"""
        
        # ✅ Include session info in payload
        payload = {
            "question": question,
            "session_id": self.session_id  # Backend can track per session
        }
        
        start_time = time.time()
        self.last_request_time = start_time
        url = f"{self.base_url}{self.endpoint}"
        
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
                logger.info(f"POST {url} [Session: {self.session_id[:8]}]")
                
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "X-Session-ID": self.session_id,     # Session tracking
                        "X-User-Agent": "CVApp-MultiUser",   # User agent
                        "Connection": "close"                # Force close
                    }
                )
                
                processing_time = time.time() - start_time
                logger.info(f"Response: {response.status_code} in {processing_time:.2f}s [Session: {self.session_id[:8]}]")
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    
                    # ✅ Reset failure count on success
                    self.failure_count = 0
                    
                    logger.info(f"SUCCESS! Answer length: {len(answer)} chars [Session: {self.session_id[:8]}]")
                    
                    return APIResponse(
                        success=True,
                        content=answer,
                        processing_time=processing_time
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
        """Query CV with session isolation"""
        try:
            return asyncio.run(self._make_request_async(message))
        except Exception as e:
            self.failure_count += 1
            logger.error(f"Query failed for session {self.session_id[:8]}: {e}")
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Session-specific health check - FIXED ERROR HANDLING"""
        try:
            result = asyncio.run(self._check_health())
            
            # ✅ Always return a proper dictionary
            health_status = {
                "status": "healthy" if result else "unhealthy",
                "session_id": self.session_id[:8] if self.session_id else "unknown", 
                "failure_count": getattr(self, 'failure_count', 0),
                "last_request": getattr(self, 'last_request_time', None),
                "backend_url": self.base_url,
                "endpoint": self.endpoint
            }
            
            logger.info(f"Health check for session {self.session_id[:8]}: {health_status['status']}")
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
                "endpoint": self.endpoint
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

# ✅ Session-specific client management - FIXED ERROR HANDLING
def get_session_cv_client() -> CVBackendClient:
    """Get or create session-specific CV client - NO GLOBAL SHARING - FIXED"""
    
    try:
        # ✅ Create unique session ID per Streamlit user session
        if "user_session_id" not in st.session_state:
            st.session_state.user_session_id = str(uuid.uuid4())
            logger.info(f"New user session created: {st.session_state.user_session_id[:8]}")
        
        # ✅ Create session-specific client (stored in user's session state)
        if "cv_client" not in st.session_state:
            st.session_state.cv_client = CVBackendClient(st.session_state.user_session_id)
            logger.info(f"CV client created for session: {st.session_state.user_session_id[:8]}")
        
        return st.session_state.cv_client
        
    except Exception as e:
        logger.error(f"Failed to create session CV client: {e}")
        # ✅ Fallback: create a basic client
        return CVBackendClient()

def initialize_session_backend():
    """Initialize backend per user session - FIXED ERROR HANDLING"""
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
        
        logger.info(f"Backend initialized for session {session_display}: {health.get('status', 'unknown')}")
        
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

# ✅ Backward compatibility - but now session-isolated
def get_cv_client() -> CVBackendClient:
    """Backward compatibility function - now session-isolated"""
    return get_session_cv_client()

# ✅ Additional utility functions for debugging
def reset_session_client():
    """Reset the session client (useful for debugging)"""
    try:
        if "cv_client" in st.session_state:
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

def get_session_debug_info() -> Dict[str, Any]:
    """Get debug information about the current session"""
    try:
        client = get_session_cv_client()
        health = client.get_health_status()
        
        return {
            "session_id": st.session_state.get("user_session_id", "unknown")[:8],
            "backend_connected": st.session_state.get("backend_connected", False),
            "client_session_id": getattr(client, 'session_id', 'unknown')[:8],
            "failure_count": getattr(client, 'failure_count', 0),
            "health_status": health,
            "streamlit_session_state_keys": list(st.session_state.keys())
        }
    except Exception as e:
        return {
            "error": str(e),
            "session_debug_failed": True
        }
