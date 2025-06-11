"""
API Client for CV-AI Backend Integration v2.0
Enhanced with endpoint discovery and robust error handling
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
    """Enhanced CV Backend Client with Railway Private Networking"""
    
    def __init__(self, base_url: str = None):
        # Try Railway internal networking first, fallback to public
        if base_url is None:
            # Railway private network (works if frontend is also on Railway)
            self.base_url = "https://cvbrain.railway.internal"
            self.use_private_network = True
        else:
            self.base_url = base_url
            self.use_private_network = False
            
        self.public_fallback = "https://cvbrain-production.up.railway.app"
        self.timeout = 30.0
        self.max_retries = 2
        self.retry_delay = 1.0
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_timeout = 60
        
        # Endpoint discovery
        self.query_endpoint = None
        self._endpoint_discovered = False
        
        logger.info(f"CV Backend Client initialized for {self.base_url}")
        if self.use_private_network:
            logger.info("🔒 Using Railway private networking")
    
    async def _discover_endpoints(self) -> Optional[str]:
        """Discover the correct query endpoint"""
        if self._endpoint_discovered and self.query_endpoint:
            return self.query_endpoint
        
        # Possible endpoint patterns to try
        possible_endpoints = [
            "/v1/query",           # Original attempt
            "/query",              # Simple path
            "/api/query",          # API prefix
            "/api/v1/query",       # API with version
            "/cv/query",           # CV specific
            "/chat",               # Chat endpoint
            "/ask",                # Ask endpoint
        ]
        
        logger.info("🔍 Discovering available endpoints...")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for endpoint in possible_endpoints:
                try:
                    # Test with a simple HEAD request first
                    test_url = f"{self.base_url}{endpoint}"
                    response = await client.head(test_url)
                    
                    if response.status_code in [200, 405]:  # 405 = Method Not Allowed (but endpoint exists)
                        logger.info(f"✅ Found endpoint: {endpoint}")
                        self.query_endpoint = endpoint
                        self._endpoint_discovered = True
                        return endpoint
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 405:  # Method not allowed means endpoint exists
                        logger.info(f"✅ Found endpoint (POST only): {endpoint}")
                        self.query_endpoint = endpoint
                        self._endpoint_discovered = True
                        return endpoint
                except:
                    continue
        
        # If no endpoint found, check API documentation
        try:
            docs_response = await client.get(f"{self.base_url}/docs")
            if docs_response.status_code == 200:
                logger.warning("📚 API docs available at /docs - check manually for endpoints")
        except:
            pass
        
        # Default fallback
        logger.warning("❌ No query endpoint discovered, using default /v1/query")
        self.query_endpoint = "/v1/query"
        return self.query_endpoint
    
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
        """Make async request to backend with endpoint discovery"""
        
        # Discover endpoint if not already done
        endpoint = await self._discover_endpoints()
        query_url = f"{self.base_url}{endpoint}"
        
        # Try multiple payload formats
        payload_formats = [
            # Format 1: Full structured payload
            {
                "question": message,
                "k": 3,
                "query_type": query_type.value,
                "response_format": response_format.value,
                "include_sources": True,
                "include_confidence_explanation": False,
                "language": "en",
                "max_response_length": 800
            },
            # Format 2: Simplified payload
            {
                "question": message,
                "k": 3
            },
            # Format 3: Just the question
            {
                "question": message
            },
            # Format 4: Different field names
            {
                "query": message,
                "num_results": 3
            }
        ]
        
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
            
            for i, request_payload in enumerate(payload_formats):
                try:
                    logger.info(f"🔄 Attempt {i+1}: Making request to {query_url}")
                    logger.debug(f"📤 Payload: {request_payload}")
                    
                    response = await client.post(
                        query_url,
                        json=request_payload,
                        headers={
                            "Content-Type": "application/json",
                            "Accept": "application/json",
                            "User-Agent": "CV-Assistant-Frontend/2.0"
                        }
                    )
                    
                    processing_time = time.time() - start_time
                    logger.info(f"📥 Response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        self._record_success()
                        response_data = response.json()
                        logger.info(f"✅ Successful response with payload format {i+1}")
                        
                        # Handle different response formats
                        content = (
                            response_data.get("answer") or 
                            response_data.get("response") or 
                            response_data.get("result") or
                            str(response_data)
                        )
                        
                        return APIResponse(
                            success=True,
                            content=content,
                            metadata={
                                "confidence_level": response_data.get("confidence_level"),
                                "query_type": response_data.get("query_type"),
                                "relevant_chunks": response_data.get("relevant_chunks"),
                                "model_used": response_data.get("model_used"),
                                "request_id": response_data.get("request_id"),
                                "endpoint_used": endpoint,
                                "payload_format": i+1
                            },
                            processing_time=processing_time,
                            confidence_score=response_data.get("confidence_score"),
                            sources_count=response_data.get("relevant_chunks", 0),
                            request_id=response_data.get("request_id")
                        )
                    
                    elif response.status_code == 422:
                        # Validation error - try next payload format
                        error_detail = response.text
                        logger.warning(f"⚠️  Validation error with format {i+1}: {error_detail}")
                        continue
                    
                    else:
                        # Other HTTP error
                        error_msg = f"HTTP {response.status_code}: {response.text}"
                        logger.error(f"❌ HTTP error: {error_msg}")
                        
                        # Don't try other formats for non-validation errors
                        self._record_failure()
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
                    logger.error(f"❌ Unexpected error with format {i+1}: {str(e)}")
                    continue
            
            # If all payload formats failed
            self._record_failure()
            return APIResponse(
                success=False,
                content="",
                error="All payload formats failed - API might expect different structure",
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
        
        # Retry logic with fewer attempts for faster feedback
        for attempt in range(self.max_retries):
            try:
                logger.info(f"🚀 Query attempt {attempt + 1}/{self.max_retries}")
                response = asyncio.run(
                    self._make_request_async(message, backend_format, query_type)
                )
                
                if response.success:
                    logger.info("✅ Query successful!")
                    return response
                
                # Log the specific error for debugging
                logger.warning(f"⚠️  Attempt {attempt + 1} failed: {response.error}")
                
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)
                    logger.info(f"⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
            
            except Exception as e:
                logger.error(f"❌ Attempt {attempt + 1} failed with exception: {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay * (2 ** attempt))
        
        # Final failure
        logger.error("❌ All attempts failed")
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
                "failure_count": self.failure_count,
                "endpoint_discovered": self._endpoint_discovered,
                "query_endpoint": self.query_endpoint
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "circuit_open": self.circuit_open,
                "failure_count": self.failure_count
            }
    
    async def debug_backend(self) -> Dict[str, Any]:
        """Debug backend endpoints and structure"""
        debug_info = {
            "base_url": self.base_url,
            "health_check": False,
            "available_endpoints": [],
            "api_docs": None,
            "discovered_endpoint": None
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Test health
            try:
                health_response = await client.get(f"{self.base_url}/health")
                debug_info["health_check"] = health_response.status_code == 200
            except:
                pass
            
            # Test common endpoints
            test_endpoints = ["/", "/docs", "/redoc", "/openapi.json", "/v1/query", "/query", "/api/query"]
            for endpoint in test_endpoints:
                try:
                    response = await client.head(f"{self.base_url}{endpoint}")
                    if response.status_code < 400:
                        debug_info["available_endpoints"].append(endpoint)
                except:
                    pass
            
            # Check for API docs
            try:
                docs_response = await client.get(f"{self.base_url}/docs")
                if docs_response.status_code == 200:
                    debug_info["api_docs"] = f"{self.base_url}/docs"
            except:
                pass
            
            # Discover query endpoint
            discovered = await self._discover_endpoints()
            debug_info["discovered_endpoint"] = discovered
        
        return debug_info
