"""
CV-AI Backend Client for Railway Integration
Connects Streamlit frontend to cvbrain-production.up.railway.app
"""

import httpx
import asyncio
import streamlit as st
import json
import time
from typing import Dict, Any, Optional, AsyncGenerator, Generator
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
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

class CVBackendClient:
    """
    Ultimate CV Backend Client for Railway Integration
    
    Features:
    - Async HTTP/2 support with connection pooling
    - Streaming response handling
    - Comprehensive error handling with retries
    - Circuit breaker pattern for resilience
    - Request/response caching
    """
    
    def __init__(self):
        self.base_url = "https://cvbrain-production.up.railway.app"
        self.timeout = 60.0  # Increased for AI processing
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Connection pool settings optimized for Railway
        self.limits = httpx.Limits(
            max_connections=10,
            max_keepalive_connections=5,
            keepalive_expiry=30.0
        )
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_timeout = 60  # 1 minute
        
        # Request cache
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
        logger.info(f"CV Backend Client initialized for {self.base_url}")
    
    def _get_cache_key(self, message: str, response_format: str) -> str:
        """Generate cache key for request"""
        return f"{message[:100]}:{response_format}".replace(" ", "_")
    
    def _is_cache_valid(self, cache_entry: Dict[str, Any]) -> bool:
        """Check if cache entry is still valid"""
        return time.time() - cache_entry["timestamp"] < self.cache_ttl
    
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
    
    def _classify_query(self, message: str) -> QueryType:
        """Intelligently classify user query"""
        message_lower = message.lower()
        
        # Technical skills keywords
        if any(word in message_lower for word in [
            'skill', 'technology', 'programming', 'language', 'framework', 
            'python', 'javascript', 'sql', 'tableau', 'tool'
        ]):
            return QueryType.TECHNICAL
        
        # Experience keywords
        elif any(word in message_lower for word in [
            'experience', 'work', 'job', 'company', 'role', 'position', 
            'career', 'employment', 'professional'
        ]):
            return QueryType.EXPERIENCE
        
        # Education keywords
        elif any(word in message_lower for word in [
            'education', 'degree', 'university', 'study', 'academic', 
            'school', 'learning', 'course', 'certification'
        ]):
            return QueryType.EDUCATION
        
        # Projects keywords
        elif any(word in message_lower for word in [
            'project', 'built', 'created', 'developed', 'portfolio', 
            'application', 'system', 'dashboard'
        ]):
            return QueryType.PROJECTS
        
        # Summary keywords
        elif any(word in message_lower for word in [
            'summary', 'overview', 'background', 'about', 'introduction', 
            'profile', 'bio', 'who are you'
        ]):
            return QueryType.SUMMARY
        
        # Contact keywords
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
    
    async def _make_request_async(
        self, 
        message: str, 
        response_format: ResponseFormat,
        query_type: QueryType
    ) -> APIResponse:
        """Make async request to backend"""
        
        # Prepare request payload matching backend schema
        request_payload = {
            "question": message,
            "k": 3,  # Number of relevant chunks
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
            limits=self.limits,
            http2=True  # Enable HTTP/2 for better performance
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
                
                # Check response status
                if response.status_code == 200:
                    self._record_success()
                    
                    response_data = response.json()
                    
                    return APIResponse(
                        success=True,
                        content=response_data.get("answer", "No response received"),
                        metadata={
                            "request_id": response_data.get("request_id"),
                            "confidence_level": response_data.get("confidence_level"),
                            "query_type": response_data.get("query_type"),
                            "relevant_chunks": response_data.get("relevant_chunks"),
                            "model_used": response_data.get("model_used"),
                            "cache_hit": response_data.get("cache_hit", False)
                        },
                        processing_time=processing_time,
                        confidence_score=response_data.get("confidence_score"),
                        sources_count=response_data.get("relevant_chunks", 0)
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
    
    def _make_request_with_retry(
        self, 
        message: str, 
        response_format: str
    ) -> APIResponse:
        """Make request with retry logic and circuit breaker"""
        
        # Check circuit breaker
        if not self._check_circuit_breaker():
            return APIResponse(
                success=False,
                content="",
                error="Service temporarily unavailable. Please try again in a minute."
            )
        
        # Check cache
        cache_key = self._get_cache_key(message, response_format)
        if cache_key in self.cache and self._is_cache_valid(self.cache[cache_key]):
            logger.info("Returning cached response")
            cached = self.cache[cache_key]
            cached["metadata"]["cache_hit"] = True
            return cached["response"]
        
        # Map formats and classify query
        backend_format = self._map_response_format(response_format)
        query_type = self._classify_query(message)
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                # Run async request in sync context
                response = asyncio.run(
                    self._make_request_async(message, backend_format, query_type)
                )
                
                if response.success:
                    # Cache successful response
                    self.cache[cache_key] = {
                        "timestamp": time.time(),
                        "response": response
                    }
                    return response
                
                # If not last attempt, wait before retry
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))  # Exponential backoff
            
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        # All retries failed
        return APIResponse(
            success=False,
            content="",
            error="Service temporarily unavailable after multiple attempts"
        )
    
    def query_cv(self, message: str, response_format: str = "Detailed") -> APIResponse:
        """
        Main method to query the CV backend
        
        Args:
            message: User's question
            response_format: Desired response format from Streamlit UI
            
        Returns:
            APIResponse with result or error information
        """
        return self._make_request_with_retry(message, response_format)
    
    def stream_response(self, response_content: str, delay: float = 0.02) -> Generator[str, None, None]:
        """
        Stream response content word by word for Streamlit
        
        Args:
            response_content: Full response to stream
            delay: Delay between words in seconds
            
        Yields:
            Individual words for streaming effect
        """
        words = response_content.split()
        for i, word in enumerate(words):
            # Add space except for first word
            if i > 0:
                yield " " + word
            else:
                yield word
            time.sleep(delay)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get backend health status"""
        try:
            response = asyncio.run(self._check_health_async())
            return {
                "status": "healthy" if response else "unhealthy",
                "circuit_open": self.circuit_open,
                "failure_count": self.failure_count,
                "cache_size": len(self.cache)
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

# Global client instance for Streamlit app
@st.cache_resource
def get_cv_client() -> CVBackendClient:
    """Get cached CV backend client instance"""
    return CVBackendClient()
