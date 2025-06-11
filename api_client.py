"""
API Client for CV-AI Backend Integration
Centralized backend communication and response handling
"""

import httpx
import asyncio
import time
import logging
from typing import Dict, Any, Optional, List
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
    sources_count: Optional[int] = None
    request_id: Optional[str] = None

class CVBackendClient:
    """Enhanced CV Backend Client for Railway Integration"""
    
    def __init__(self, base_url: str = "https://cvbrain-production.up.railway.app"):
        self.base_url = base_url
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
                            "request_id": response_data.get("request_id"),
                        },
                        processing_time=processing_time,
                        confidence_score=response_data.get("confidence_score"),
                        sources_count=response_data.get("relevant_chunks", 0),
                        request_id=response_data.get("request_id")
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
    
    async def check_health_async(self) -> bool:
        """Async health check"""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except:
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get backend health status"""
        try:
            response = asyncio.run(self.check_health_async())
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
