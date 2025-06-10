"""
Configuration settings for CV Assistant Frontend
"""

import os
import streamlit as st
from typing import Optional

class Config:
    """Configuration class for CV Assistant"""
    
    # Backend API Configuration
    BACKEND_URL: str = "https://cvbrain-production.up.railway.app"
    API_TIMEOUT: float = 60.0
    MAX_RETRIES: int = 3
    
    # UI Configuration
    DEFAULT_RESPONSE_FORMAT: str = "Detailed"
    DEFAULT_THEME: str = "dark"
    
    # Feature Flags
    ENABLE_METADATA_DISPLAY: bool = True
    ENABLE_CONFIDENCE_SCORES: bool = True
    ENABLE_INTERVIEW_SCHEDULING: bool = True
    ENABLE_PERFORMANCE_METRICS: bool = True
    
    # Cache Configuration
    CACHE_TTL_SECONDS: int = 300  # 5 minutes
    MAX_CACHE_SIZE: int = 100
    
    # Circuit Breaker Configuration
    CIRCUIT_FAILURE_THRESHOLD: int = 3
    CIRCUIT_TIMEOUT_SECONDS: int = 60
    
    # Streaming Configuration
    STREAM_DELAY: float = 0.02  # Delay between words
    
    @classmethod
    def get_backend_url(cls) -> str:
        """Get backend URL from environment or default"""
        # Check Streamlit secrets first (for deployment)
        if hasattr(st, 'secrets') and 'BACKEND_URL' in st.secrets:
            return st.secrets['BACKEND_URL']
        
        # Check environment variables
        return os.getenv('BACKEND_URL', cls.BACKEND_URL)
    
    @classmethod
    def is_development(cls) -> bool:
        """Check if running in development mode"""
        return os.getenv('ENVIRONMENT', 'production').lower() == 'development'
    
    @classmethod
    def get_api_timeout(cls) -> float:
        """Get API timeout from environment or default"""
        try:
            return float(os.getenv('API_TIMEOUT', cls.API_TIMEOUT))
        except (ValueError, TypeError):
            return cls.API_TIMEOUT

# Global configuration instance
config = Config()
