"""
MULTI-USER API Client - Session Isolated
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
    """Multi-User CV Client - Session isolated per user"""
    
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
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Session-specific health check"""
        try:
            result = asyncio.run(self._check_health())
            return {
                "status": "healthy" if result else "unhealthy",
                "session_id": self.session_id[:8],
                "failure_count": self.failure_count,
                "last_request": self.last_request_time
            }
        except Exception as e:
            return {
                "status": "error", 
                "error": str(e),
                "session_id": self.session_id[:8]
            }
    
    async def _check_health(self) -> bool:
        """Check backend health per session"""
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
                return response.status_code == 200
        except:
            return False

# ✅ Session-specific client management
def get_session_cv_client() -> CVBackendClient:
    """Get or create session-specific CV client - NO GLOBAL SHARING"""
    
    # ✅ Create unique session ID per Streamlit user session
    if "user_session_id" not in st.session_state:
        st.session_state.user_session_id = str(uuid.uuid4())
        logger.info(f"New user session created: {st.session_state.user_session_id[:8]}")
    
    # ✅ Create session-specific client (stored in user's session state)
    if "cv_client" not in st.session_state:
        st.session_state.cv_client = CVBackendClient(st.session_state.user_session_id)
        logger.info(f"CV client created for session: {st.session_state.user_session_id[:8]}")
    
    return st.session_state.cv_client

def initialize_session_backend():
    """Initialize backend per user session - NO GLOBAL STATE"""
    try:
        client = get_session_cv_client()
        health = client.get_health_status()
        
        # ✅ Session-specific backend connection status
        st.session_state.backend_connected = health["status"] == "healthy"
        
        logger.info(f"Backend initialized for session {client.session_id[:8]}: {health['status']}")
        
        return client
    except Exception as e:
        logger.error(f"Backend initialization failed: {e}")
        st.session_state.backend_connected = False
        return None

# ✅ Backward compatibility - but now session-isolated
def get_cv_client() -> CVBackendClient:
    """Backward compatibility function - now session-isolated"""
    return get_session_cv_client()
