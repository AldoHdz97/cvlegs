"""
API Client for CV-AI Backend - STABLE VERSION
Consistent imports, based on cvbrain7L.md backend structure
"""

import httpx
import asyncio
import time
import logging
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class QueryType(str, Enum):
    """Query types matching backend schema"""
    SKILLS = "skills"
    EXPERIENCE = "experience"
    EDUCATION = "education"
    PROJECTS = "projects"
    SUMMARY = "summary"
    CONTACT = "contact"
    TECHNICAL = "technical"
    GENERAL = "general"

class ResponseFormat(str, Enum):
    """Response format options"""
    DETAILED = "detailed"
    SUMMARY = "summary"
    BULLET_POINTS = "bullet_points"
    TECHNICAL = "technical"
    CONVERSATIONAL = "conversational"

@dataclass
class APIResponse:
    """Simple response structure"""
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    processing_time: Optional[float] = None
    confidence_score: Optional[float] = None

class CVBackendClient:
    """STABLE CV Backend Client - No more import changes!"""
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        
        logger.info("🔒 STABLE API Client initialized")
    
    def _classify_query(self, message: str) -> QueryType:
        """Simple query classification"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ['skill', 'technology', 'programming', 'python', 'sql']):
            return QueryType.TECHNICAL
        elif any(word in message_lower for word in ['experience', 'work', 'job', 'company']):
            return QueryType.EXPERIENCE
        elif any(word in message_lower for word in ['education', 'degree', 'university']):
            return QueryType.EDUCATION
        elif any(word in message_lower for word in ['project', 'built', 'created', 'developed']):
            return QueryType.PROJECTS
        elif any(word in message_lower for word in ['summary', 'overview', 'about']):
            return QueryType.SUMMARY
        elif any(word in message_lower for word in ['contact', 'email', 'phone']):
            return QueryType.CONTACT
        else:
            return QueryType.GENERAL
    
    def _map_response_format(self, streamlit_format: str) -> ResponseFormat:
        """Map format"""
        mapping = {
            "Detailed": ResponseFormat.DETAILED,
            "Summary": ResponseFormat.SUMMARY,
            "Bullet points": ResponseFormat.BULLET_POINTS,
            "Technical": ResponseFormat.TECHNICAL,
            "Conversational": ResponseFormat.CONVERSATIONAL
        }
        return mapping.get(streamlit_format, ResponseFormat.DETAILED)
    
    async def _make_request_async(self, message: str, response_format: ResponseFormat, query_type: QueryType) -> APIResponse:
        """Make the actual request - SIMPLE version"""
        
        # Simple, working payload
        payload = {
            "question": message,
            "k": 3,
            "query_type": query_type.value,
            "response_format": response_format.value,
            "include_sources": True,
            "language": "en"
        }
        
        start_time = time.time()
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/v1/query",
                    json=payload,
                    headers={"Content-Type": "application/json"}
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    return APIResponse(
                        success=True,
                        content=data.get("answer", ""),
                        metadata={
                            "query_type": data.get("query_type"),
                            "confidence_level": data.get("confidence_level")
                        },
                        processing_time=processing_time,
                        confidence_score=data.get("confidence_score")
                    )
                else:
                    return APIResponse(
                        success=False,
                        content="",
                        error=f"HTTP {response.status_code}: {response.text[:200]}",
                        processing_time=processing_time
                    )
            
            except Exception as e:
                return APIResponse(
                    success=False,
                    content="",
                    error=str(e),
                    processing_time=time.time() - start_time
                )
    
    def query_cv(self, message: str, response_format: str = "Detailed") -> APIResponse:
        """Main query method - STABLE"""
        backend_format = self._map_response_format(response_format)
        query_type = self._classify_query(message)
        
        try:
            return asyncio.run(self._make_request_async(message, backend_format, query_type))
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Processing error: {str(e)}"
            )
    
    async def check_health_async(self) -> bool:
        """Health check"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status"""
        try:
            response = asyncio.run(self.check_health_async())
            return {"status": "healthy" if response else "unhealthy"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
