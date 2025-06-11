"""
CORRECTED API Client - Using the RIGHT endpoint!
"""

import httpx
import asyncio
import time
import logging
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
    """CORRECTED CV Client - Using /query not /v1/query"""
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        
        # THE FIX: Use /query not /v1/query
        self.endpoint = "/query"
        
        logger.info(f"🎯 CORRECTED API Client - endpoint: {self.endpoint}")
    
    async def _make_request_async(self, question: str) -> APIResponse:
        """Make request to the CORRECT endpoint"""
        
        # Minimal payload matching UltimateQueryRequest
        payload = {
            "question": question,
            "k": 3,
            "query_type": "general",
            "response_format": "detailed",
            "include_sources": True,
            "language": "en"
        }
        
        start_time = time.time()
        
        # THE FIX: Use the correct endpoint
        url = f"{self.base_url}{self.endpoint}"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"🚀 POST {url}")
                logger.debug(f"📤 Payload: {payload}")
                
                response = await client.post(
                    url,
                    json=payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                processing_time = time.time() - start_time
                logger.info(f"📥 Response: {response.status_code} in {processing_time:.2f}s")
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", "")
                    
                    logger.info(f"✅ SUCCESS! Answer length: {len(answer)} chars")
                    
                    return APIResponse(
                        success=True,
                        content=answer,
                        processing_time=processing_time
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                    logger.error(f"❌ {error_msg}")
                    
                    return APIResponse(
                        success=False,
                        content="",
                        error=error_msg,
                        processing_time=processing_time
                    )
            
            except Exception as e:
                error_msg = f"Request failed: {str(e)}"
                logger.error(f"❌ {error_msg}")
                
                return APIResponse(
                    success=False,
                    content="",
                    error=error_msg,
                    processing_time=time.time() - start_time
                )
    
    def query_cv(self, message: str, response_format: str = None) -> APIResponse:
        """Query CV using the CORRECT endpoint"""
        try:
            return asyncio.run(self._make_request_async(message))
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Health check using the correct backend"""
        try:
            result = asyncio.run(self._check_health())
            return {"status": "healthy" if result else "unhealthy"}
        except:
            return {"status": "error"}
    
    async def _check_health(self) -> bool:
        """Check backend health"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

