# Enhanced API client with Railway service name discovery
"""
API Client with Railway Service Name Discovery
Debug version to find the correct internal URLs
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
    """Railway Service Discovery Client"""
    
    def __init__(self):
        # Railway internal service name possibilities
        self.possible_internal_urls = [
            # Based on your frontend URL pattern
            "https://cvbrain-production.railway.internal",
            "http://cvbrain-production.railway.internal",
            "https://cvbrain.railway.internal", 
            "http://cvbrain.railway.internal",
            "https://cv-ai-backend.railway.internal",
            "http://cv-ai-backend.railway.internal",
            "https://backend.railway.internal",
            "http://backend.railway.internal",
            # With ports
            "https://cvbrain-production.railway.internal:8000",
            "http://cvbrain-production.railway.internal:8000",
            "https://cvbrain.railway.internal:8000",
            "http://cvbrain.railway.internal:8000"
        ]
        
        # Public URLs as fallback
        self.public_urls = [
            "https://cvbrain-production.up.railway.app",
            "https://cvbrain-production.railway.app"
        ]
        
        self.active_url = None
        self.timeout = 15.0
        self.max_retries = 2
        self.retry_delay = 1.0
        
        # Circuit breaker state
        self.failure_count = 0
        self.last_failure_time = None
        self.circuit_open = False
        self.circuit_timeout = 60
        
        logger.info("🔍 Railway Service Discovery Client initialized")
    
    async def discover_backend_service(self) -> Dict[str, Any]:
        """Discover the correct Railway backend service URL"""
        discovery_results = {
            "working_urls": [],
            "failed_urls": [],
            "error_details": {},
            "recommended_url": None
        }
        
        print("🔍 Discovering Railway backend service...")
        print("=" * 60)
        
        # Test internal URLs first (since we're on Railway)
        all_urls = self.possible_internal_urls + self.public_urls
        
        async with httpx.AsyncClient(timeout=5.0) as client:
            for i, url in enumerate(all_urls, 1):
                try:
                    print(f"[{i:2d}/{len(all_urls)}] Testing: {url}")
                    
                    # Test health endpoint
                    health_url = f"{url}/health"
                    start_time = time.time()
                    
                    response = await client.get(health_url)
                    response_time = time.time() - start_time
                    
                    if response.status_code == 200:
                        print(f"         ✅ SUCCESS! ({response.status_code}) - {response_time:.2f}s")
                        discovery_results["working_urls"].append({
                            "url": url,
                            "response_time": response_time,
                            "status_code": response.status_code,
                            "type": "internal" if "railway.internal" in url else "public"
                        })
                        
                        # Set first working URL as recommended
                        if not discovery_results["recommended_url"]:
                            discovery_results["recommended_url"] = url
                            self.active_url = url
                    else:
                        print(f"         ❌ HTTP {response.status_code}")
                        discovery_results["failed_urls"].append(url)
                        discovery_results["error_details"][url] = f"HTTP {response.status_code}"
                
                except httpx.ConnectError as e:
                    print(f"         ❌ Connection failed")
                    discovery_results["failed_urls"].append(url)
                    discovery_results["error_details"][url] = "Connection failed"
                    
                except httpx.TimeoutException:
                    print(f"         ❌ Timeout")
                    discovery_results["failed_urls"].append(url)
                    discovery_results["error_details"][url] = "Timeout"
                    
                except Exception as e:
                    print(f"         ❌ {type(e).__name__}: {str(e)[:50]}")
                    discovery_results["failed_urls"].append(url)
                    discovery_results["error_details"][url] = f"{type(e).__name__}: {str(e)[:50]}"
        
        print("=" * 60)
        print(f"🎯 Discovery complete!")
        print(f"   Working URLs: {len(discovery_results['working_urls'])}")
        print(f"   Failed URLs: {len(discovery_results['failed_urls'])}")
        
        if discovery_results["working_urls"]:
            recommended = discovery_results["recommended_url"]
            network_type = "Railway Internal" if "railway.internal" in recommended else "Public"
            print(f"   📡 Recommended: {recommended} ({network_type})")
        else:
            print("   ❌ No working URLs found!")
        
        return discovery_results
    
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
    
    async def _make_request_async(
        self, 
        message: str, 
        response_format: ResponseFormat,
        query_type: QueryType
    ) -> APIResponse:
        """Make async request to discovered backend"""
        
        if not self.active_url:
            # Try to discover if not already done
            discovery = await self.discover_backend_service()
            if not discovery["recommended_url"]:
                return APIResponse(
                    success=False,
                    content="",
                    error="No working backend URL found during discovery"
                )
        
        # Simple payload to start
        request_payload = {
            "question": message,
            "k": 3
        }
        
        start_time = time.time()
        query_url = f"{self.active_url}/v1/query"
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                logger.info(f"🚀 Making request to: {query_url}")
                
                response = await client.post(
                    query_url,
                    json=request_payload,
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "application/json"
                    }
                )
                
                processing_time = time.time() - start_time
                
                if response.status_code == 200:
                    response_data = response.json()
                    content = response_data.get("answer", str(response_data))
                    
                    return APIResponse(
                        success=True,
                        content=content,
                        metadata={
                            "url_used": self.active_url,
                            "network_type": "Railway Internal" if "railway.internal" in self.active_url else "Public",
                            "query_type": response_data.get("query_type"),
                            "confidence_level": response_data.get("confidence_level")
                        },
                        processing_time=processing_time,
                        confidence_score=response_data.get("confidence_score")
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
                    error=f"Request failed: {str(e)}",
                    processing_time=time.time() - start_time
                )
    
    def query_cv(self, message: str, response_format: str = "Detailed") -> APIResponse:
        """Main method to query the CV backend"""
        backend_format = self._map_response_format(response_format)
        query_type = self._classify_query(message)
        
        try:
            return asyncio.run(
                self._make_request_async(message, backend_format, query_type)
            )
        except Exception as e:
            return APIResponse(
                success=False,
                content="",
                error=f"Query processing error: {str(e)}"
            )
    
    async def check_health_async(self) -> bool:
        """Async health check"""
        if not self.active_url:
            discovery = await self.discover_backend_service()
            return discovery["recommended_url"] is not None
        
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.active_url}/health")
                return response.status_code == 200
        except:
            return False
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status with discovery info"""
        try:
            response = asyncio.run(self.check_health_async())
            return {
                "status": "healthy" if response else "unhealthy",
                "active_url": self.active_url,
                "network_type": "Railway Internal" if self.active_url and "railway.internal" in self.active_url else "Public"
            }
        except Exception as e:
            return {
                "status": "error",
                "error": str(e)
            }
