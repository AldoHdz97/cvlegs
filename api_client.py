"""
SIMPLE API Client - Just Ask Questions!
ChromaDB handles the complexity, we just ask questions.
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
    """SIMPLE CV Client - Just Ask Questions!"""
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        
        logger.info("🎯 SIMPLE API Client - ChromaDB does the heavy lifting!")
    
    async def _make_request_async(self, question: str) -> APIResponse:
        """Simple request - just send the question!"""
        
        # MINIMAL payload - let the backend handle everything else
        payload = {"question": question}
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"❓ Asking: {question[:50]}...")
                
                response = await client.post(
                    f"{self.base_url}/v1/query",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer") or data.get("response") or str(data)
                    
                    logger.info(f"✅ Got answer ({len(answer)} chars)")
                    
                    return APIResponse(
                        success=True,
                        content=answer,
                        processing_time=processing_time
                    )
                else:
                    error_msg = f"HTTP {response.status_code}: {response.text[:100]}"
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
        """Just ask a question - that's it!"""
        try:
            return asyncio.run(self._make_request_async(message))
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Error: {str(e)}"
            )
    
    def get_health_status(self) -> Dict[str, Any]:
        """Simple health check"""
        try:
            result = asyncio.run(self._check_health())
            return {"status": "healthy" if result else "unhealthy"}
        except:
            return {"status": "error"}
    
    async def _check_health(self) -> bool:
        """Check if backend is alive"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False

