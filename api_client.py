"""
SIMPLE API Client - Just Questions!
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
   """Simple CV Client - Just send questions"""
   
   def __init__(self):
       self.base_url = "https://cvbrain-production.up.railway.app"
       self.timeout = 30.0
       self.endpoint = "/query"
       
       logger.info(f"Simple API Client - endpoint: {self.endpoint}")
   
   async def _make_request_async(self, question: str) -> APIResponse:
       """Make request with minimal payload"""
       
       # Minimal payload - just the question
       payload = {"question": question}
       
       start_time = time.time()
       url = f"{self.base_url}{self.endpoint}"
       
       async with httpx.AsyncClient(timeout=self.timeout, http2=False) as client:
           try:
               logger.info(f"POST {url}")
               
               response = await client.post(
                   url,
                   json=payload,
                   headers={
                       "Content-Type": "application/json",
                       "Accept": "application/json"
                   }
               )
               
               processing_time = time.time() - start_time
               logger.info(f"Response: {response.status_code} in {processing_time:.2f}s")
               
               if response.status_code == 200:
                   data = response.json()
                   answer = data.get("answer", "")
                   
                   logger.info(f"SUCCESS! Answer length: {len(answer)} chars")
                   
                   return APIResponse(
                       success=True,
                       content=answer,
                       processing_time=processing_time
                   )
               else:
                   error_msg = f"HTTP {response.status_code}: {response.text[:200]}"
                   logger.error(error_msg)
                   
                   return APIResponse(
                       success=False,
                       content="",
                       error=error_msg,
                       processing_time=processing_time
                   )
           
           except Exception as e:
               error_msg = f"Request failed: {str(e)}"
               logger.error(error_msg)
               
               return APIResponse(
                   success=False,
                   content="",
                   error=error_msg,
                   processing_time=time.time() - start_time
               )
   
   def query_cv(self, message: str, response_format: str = None) -> APIResponse:
       """Query CV - just send the question"""
       try:
           return asyncio.run(self._make_request_async(message))
       except Exception as e:
           return APIResponse(
               success=False,
               content="",
               error=f"Error: {str(e)}"
           )
   
   def get_health_status(self) -> Dict[str, Any]:
       """Health check"""
       try:
           result = asyncio.run(self._check_health())
           return {"status": "healthy" if result else "unhealthy"}
       except:
           return {"status": "error"}
   
   async def _check_health(self) -> bool:
       """Check backend health"""
       try:
           async with httpx.AsyncClient(timeout=5.0, http2=False) as client:
               response = await client.get(f"{self.base_url}/health")
               return response.status_code == 200
       except:
           return False

