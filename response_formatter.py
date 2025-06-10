"""
Response Formatter for CV-AI Backend Integration
Handles response processing, formatting, and enhancement
"""

import streamlit as st
import re
import time
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
from api_client import APIResponse

class ResponseFormatter:
    """
    Advanced response formatter for CV Assistant
    
    Features:
    - Intelligent content enhancement
    - Confidence score visualization
    - Source attribution
    - Error message formatting
    - Performance metrics display
    """
    
    def __init__(self):
        self.confidence_thresholds = {
            "very_high": 0.9,
            "high": 0.8,
            "medium": 0.65,
            "low": 0.5
        }
        
        self.emoji_mapping = {
            "skills": "🔧",
            "experience": "💼",
            "education": "🎓",
            "projects": "🚀",
            "summary": "📋",
            "contact": "📞",
            "achievements": "🏆",
            "certifications": "📜",
            "technical": "⚡",
            "general": "💭"
        }
    
    def _get_confidence_indicator(self, score: Optional[float]) -> Tuple[str, str]:
        """Get confidence indicator emoji and color"""
        if not score:
            return "❓", "#999999"
        
        if score >= self.confidence_thresholds["very_high"]:
            return "🟢", "#4CAF50"  # Green
        elif score >= self.confidence_thresholds["high"]:
            return "🔵", "#2196F3"  # Blue
        elif score >= self.confidence_thresholds["medium"]:
            return "🟡", "#FF9800"  # Orange
        elif score >= self.confidence_thresholds["low"]:
            return "🟠", "#FF5722"  # Red-Orange
        else:
            return "🔴", "#F44336"  # Red
    
    def _enhance_content(self, content: str, query_type: str) -> str:
        """Enhance content with better formatting and structure"""
        
        # Add query-specific emoji
        emoji = self.emoji_mapping.get(query_type, "💭")
        
        # Basic formatting improvements
        content = content.strip()
        
        # Enhance bullet points if they exist
        content = re.sub(r'^- ', '• ', content, flags=re.MULTILINE)
        content = re.sub(r'^\* ', '• ', content, flags=re.MULTILINE)
        
        # Enhance section headers
        content = re.sub(r'^(\w+:)\s*', r'**\1** ', content, flags=re.MULTILINE)
        
        # Add emphasis to key terms
        technical_terms = [
            'Python', 'SQL', 'Tableau', 'JavaScript', 'React', 'FastAPI',
            'Economics', 'Data Analysis', 'Machine Learning', 'APIs',
            'Monterrey', 'Mexico', 'TEC', 'Tecnológico'
        ]
        
        for term in technical_terms:
            # Only emphasize if not already emphasized
            if f"**{term}**" not in content and f"*{term}*" not in content:
                content = re.sub(
                    f'\\b{re.escape(term)}\\b', 
                    f'**{term}**', 
                    content, 
                    flags=re.IGNORECASE
                )
        
        return f"{emoji} {content}"
    
    def _format_metadata_info(self, metadata: Dict[str, Any]) -> str:
        """Format metadata into readable information"""
        if not metadata:
            return ""
        
        info_parts = []
        
        # Query type
        if query_type := metadata.get("query_type"):
            emoji = self.emoji_mapping.get(query_type, "💭")
            info_parts.append(f"{emoji} **Query Type:** {query_type.title()}")
        
        # Confidence level
        if confidence_level := metadata.get("confidence_level"):
            info_parts.append(f"🎯 **Confidence:** {confidence_level.title()}")
        
        # Sources used
        if sources_count := metadata.get("relevant_chunks"):
            info_parts.append(f"📚 **Sources:** {sources_count} documents")
        
        # Model used
        if model := metadata.get("model_used"):
            info_parts.append(f"🤖 **Model:** {model}")
        
        # Cache status
        if metadata.get("cache_hit"):
            info_parts.append("⚡ **Cache:** Hit")
        
        return " • ".join(info_parts) if info_parts else ""
    
    def _format_performance_metrics(self, response: APIResponse) -> str:
        """Format performance metrics"""
        if not response.processing_time:
            return ""
        
        time_str = f"{response.processing_time:.2f}s"
        
        # Color code based on response time
        if response.processing_time < 1.0:
            icon = "🚀"
        elif response.processing_time < 3.0:
            icon = "⚡"
        elif response.processing_time < 5.0:
            icon = "⏱️"
        else:
            icon = "🐌"
        
        return f"{icon} **Response Time:** {time_str}"
    
    def format_success_response(
        self, 
        response: APIResponse, 
        show_metadata: bool = True,
        show_confidence: bool = True
    ) -> str:
        """Format successful API response"""
        
        if not response.success or not response.content:
            return self.format_error_response("No content received from backend")
        
        # Get metadata
        metadata = response.metadata or {}
        query_type = metadata.get("query_type", "general")
        
        # Enhance main content
        enhanced_content = self._enhance_content(response.content, query_type)
        
        # Build formatted response
        formatted_parts = [enhanced_content]
        
        # Add confidence indicator if available and requested
        if show_confidence and response.confidence_score:
            confidence_emoji, confidence_color = self._get_confidence_indicator(response.confidence_score)
            confidence_text = f"{confidence_emoji} **Confidence:** {response.confidence_score:.1%}"
            formatted_parts.append(f"\n---\n{confidence_text}")
        
        # Add metadata information if requested
        if show_metadata:
            metadata_info = self._format_metadata_info(metadata)
            performance_info = self._format_performance_metrics(response)
            
            if metadata_info or performance_info:
                info_parts = [info for info in [metadata_info, performance_info] if info]
                info_text = " • ".join(info_parts)
                formatted_parts.append(f"\n*{info_text}*")
        
        return "\n".join(formatted_parts)
    
    def format_error_response(self, error: str) -> str:
        """Format error message with helpful context"""
        
        error_emoji = "⚠️"
        
        # Categorize errors and provide helpful messages
        if "timeout" in error.lower():
            error_emoji = "⏰"
            helpful_msg = "The request took too long. The AI might be processing a complex query. Please try again."
        elif "connect" in error.lower() or "connection" in error.lower():
            error_emoji = "🌐"
            helpful_msg = "Unable to reach the AI service. Please check your internet connection and try again."
        elif "503" in error or "502" in error or "500" in error:
            error_emoji = "🛠️"
            helpful_msg = "The AI service is temporarily unavailable. Please try again in a moment."
        elif "temporarily unavailable" in error.lower():
            error_emoji = "🔄"
            helpful_msg = "Service is recovering from high load. Please wait a moment and try again."
        else:
            error_emoji = "❌"
            helpful_msg = "An unexpected error occurred. Please try rephrasing your question."
        
        return f"{error_emoji} **Oops!** {helpful_msg}\n\n*Technical details: {error}*"
    
    def format_loading_message(self, query_type: str = "general") -> str:
        """Format loading message based on query type"""
        
        emoji = self.emoji_mapping.get(query_type, "🤔")
        
        loading_messages = {
            "skills": f"{emoji} Analyzing technical skills and expertise...",
            "experience": f"{emoji} Reviewing work experience and career highlights...",
            "education": f"{emoji} Examining educational background and certifications...",
            "projects": f"{emoji} Exploring project portfolio and achievements...",
            "summary": f"{emoji} Compiling comprehensive professional overview...",
            "contact": f"{emoji} Retrieving contact information...",
            "technical": f"{emoji} Processing technical query...",
            "general": f"{emoji} Thinking about your question..."
        }
        
        return loading_messages.get(query_type, loading_messages["general"])
    
    def format_streamed_word(self, word: str, is_first: bool = False) -> str:
        """Format individual word for streaming"""
        if is_first:
            return word
        return f" {word}"
    
    def create_response_container(self, response: APIResponse, container_key: str = None):
        """Create a response container with full formatting"""
        
        if response.success:
            # Success response with full formatting
            formatted_content = self.format_success_response(
                response,
                show_metadata=True,
                show_confidence=True
            )
            
            # Create expandable sections for detailed metadata
            if response.metadata:
                with st.expander("📊 Response Details", expanded=False):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric("Confidence Score", f"{response.confidence_score:.1%}" if response.confidence_score else "N/A")
                        st.metric("Sources Used", response.sources_count or 0)
                    
                    with col2:
                        st.metric("Response Time", f"{response.processing_time:.2f}s" if response.processing_time else "N/A")
                        st.metric("Query Type", response.metadata.get("query_type", "general").title())
                    
                    if response.metadata.get("request_id"):
                        st.code(f"Request ID: {response.metadata['request_id']}")
            
            return formatted_content
        
        else:
            # Error response
            return self.format_error_response(response.error or "Unknown error")

# Global formatter instance
@st.cache_resource
def get_response_formatter() -> ResponseFormatter:
    """Get cached response formatter instance"""
    return ResponseFormatter()
