"""
API Client for CV-AI Frontend
Simplified and reliable HTTP client
"""

import httpx
import asyncio
import time
import logging
import streamlit as st
from typing import Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class APIResponse:
    """Simple API response"""
    success: bool
    content: str
    error: Optional[str] = None
    processing_time: Optional[float] = None

class CVBackendClient:
    """Simplified CV Backend Client"""
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        self.max_retries = 2
        
    async def _make_request(self, question: str) -> APIResponse:
        """Make HTTP request to backend"""
        start_time = time.time()
        
        payload = {"question": question}
        url = f"{self.base_url}/query"
        
        for attempt in range(self.max_retries + 1):
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    response = await client.post(
                        url,
                        json=payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json"
                        }
                    )
                    
                    processing_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        return APIResponse(
                            success=True,
                            content=data.get("answer", ""),
                            processing_time=processing_time
                        )
                    else:
                        error_msg = f"HTTP {response.status_code}"
                        if attempt < self.max_retries:
                            await asyncio.sleep(1.0 * (attempt + 1))
                            continue
                        return APIResponse(
                            success=False,
                            content="",
                            error=error_msg,
                            processing_time=processing_time
                        )
            
            except httpx.TimeoutException:
                error_msg = f"Request timeout ({self.timeout}s)"
                if attempt < self.max_retries:
                    await asyncio.sleep(2.0)
                    continue
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except httpx.ConnectError:
                error_msg = "Cannot connect to backend"
                if attempt < self.max_retries:
                    await asyncio.sleep(2.0)
                    continue
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
            
            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
        
        # Should not reach here, but just in case
        return APIResponse(
            success=False,
            content="",
            error="Max retries exceeded",
            processing_time=time.time() - start_time
        )
    
    def query_cv(self, message: str) -> APIResponse:
        """Query CV with automatic retry"""
        try:
            return asyncio.run(self._make_request(message))
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    async def health_check(self) -> bool:
        """Check if backend is healthy"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception:
            return False
    
    def get_health_status(self) -> dict:
        """Get backend health status"""
        try:
            is_healthy = asyncio.run(self.health_check())
            return {
                "status": "healthy" if is_healthy else "unhealthy",
                "backend_url": self.base_url
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "backend_url": self.base_url
            }

def get_cv_client() -> CVBackendClient:
    """Get CV client instance"""
    if "cv_client" not in st.session_state:
        st.session_state.cv_client = CVBackendClient()
    return st.session_state.cv_client

def initialize_backend() -> CVBackendClient:
    """Initialize backend client"""
    client = get_cv_client()
    health = client.get_health_status()
    st.session_state.backend_connected = health.get("status") == "healthy"
    return client
