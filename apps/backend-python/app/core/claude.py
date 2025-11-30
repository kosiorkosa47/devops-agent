"""
Claude API Integration
"""
import logging
from typing import List, Dict, Any, AsyncGenerator
from anthropic import AsyncAnthropic
from tenacity import retry, stop_after_attempt, wait_exponential

from app.config import settings

logger = logging.getLogger(__name__)


class ClaudeClient:
    """Claude API client wrapper"""
    
    def __init__(self):
        self.client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        self.model = settings.CLAUDE_MODEL
        self.max_tokens = settings.CLAUDE_MAX_TOKENS
        self.temperature = settings.CLAUDE_TEMPERATURE
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10)
    )
    async def chat(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = None,
        max_tokens: int = None,
        temperature: float = None,
        stream: bool = False
    ) -> Dict[str, Any]:
        """
        Send chat message to Claude
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            system_prompt: Optional system prompt
            max_tokens: Override default max tokens
            temperature: Override default temperature
            stream: Whether to stream the response
            
        Returns:
            Response from Claude API
        """
        try:
            kwargs = {
                "model": self.model,
                "messages": messages,
                "max_tokens": max_tokens or self.max_tokens,
                "temperature": temperature or self.temperature
            }
            
            if system_prompt:
                kwargs["system"] = system_prompt
            
            if stream:
                return await self._stream_chat(**kwargs)
            
            response = await self.client.messages.create(**kwargs)
            
            logger.info(f"Claude API call successful. Model: {self.model}")
            
            return {
                "id": response.id,
                "role": response.role,
                "content": response.content[0].text,
                "model": response.model,
                "stop_reason": response.stop_reason,
                "usage": {
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens
                }
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {e}", exc_info=True)
            raise
    
    async def _stream_chat(self, **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat response from Claude"""
        try:
            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Claude streaming error: {e}", exc_info=True)
            raise
    
    async def chat_with_context(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]] = None,
        system_prompt: str = None
    ) -> Dict[str, Any]:
        """
        Chat with conversation context
        
        Args:
            user_message: Current user message
            conversation_history: Previous messages
            system_prompt: System prompt for context
            
        Returns:
            Claude response
        """
        messages = conversation_history or []
        messages.append({"role": "user", "content": user_message})
        
        return await self.chat(
            messages=messages,
            system_prompt=system_prompt or self._default_system_prompt()
        )
    
    @staticmethod
    def _default_system_prompt() -> str:
        """Default system prompt for DevOps Agent"""
        return """You are ATLAS, a Senior DevOps Engineer with 15+ years of experience.
        
Your expertise includes:
- CI/CD Pipeline Design & Implementation
- Infrastructure as Code (Terraform, Ansible)
- Container Orchestration (Kubernetes, Docker)
- Cloud Platforms (AWS, GCP, Azure)
- Monitoring & Observability (Prometheus, Grafana)
- Security (DevSecOps)
- Incident Management & On-Call

You provide clear, actionable advice and implement best practices.
Always consider:
- Security best practices
- Cost optimization
- Scalability
- Reliability (99.9% SLA target)
- Documentation

Be concise, technical, and practical in your responses."""


# Global Claude client instance
claude_client = ClaudeClient()
