"""
LLM Client for handling Large Language Model operations.
This module interfaces with the llama-cpp-python server for 
natural language to structured mitigation action translation.
"""

from ..core.settings import settings
import requests
import json
import logging

logger = logging.getLogger(__name__)


class LLMClient:
    """Client for interfacing with the LLM server via HTTP API"""
    
    def __init__(self, server_url: str = None):
        self.server_url = server_url or settings.LLM_SERVER_URL
        self._is_available = None
    
    def check_server_health(self) -> bool:
        """Check if the LLM server is available and healthy"""
        try:
            response = requests.get(f"{self.server_url}/health", timeout=5)
            self._is_available = response.status_code == 200
            return self._is_available
        except requests.RequestException as e:
            logger.error(f"LLM server health check failed: {e}")
            self._is_available = False
            return False
    
    def is_loaded(self) -> bool:
        """Check if the model is loaded and server is available"""
        if self._is_available is None:
            return self.check_server_health()
        return self._is_available
    
    def load_model(self):
        """Check server availability (model is loaded by the server on startup)"""
        if not self.check_server_health():
            raise ConnectionError(f"LLM server not available at {self.server_url}")
        logger.info(f"LLM server is available at {self.server_url}")
        
    def generate_chat_completion(self, messages: list, max_tokens: int = 512) -> str:
        """
        Generate chat completion using the OpenAI-compatible API
        
        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            
        Returns:
            str: Generated text
        """
        if not self.is_loaded():
            raise ConnectionError("LLM server is not available")
        
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/chat/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
            
        except requests.RequestException as e:
            logger.error(f"LLM chat completion request failed: {e}")
            raise
    
    def generate_completion(self, prompt: str, max_tokens: int = 512) -> str:
        """
        Generate text completion using the legacy completions endpoint
        
        Args:
            prompt: The input prompt
            max_tokens: Maximum tokens to generate
            
        Returns:
            str: Generated text
        """
        if not self.is_loaded():
            raise ConnectionError("LLM server is not available")
        
        payload = {
            "prompt": prompt,
            "max_tokens": max_tokens,
            "temperature": 0.3,
            "top_p": 0.9,
            "stop": ["</response>", "\n\n"],
            "stream": False
        }
        
        try:
            response = requests.post(
                f"{self.server_url}/v1/completions",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("choices", [{}])[0].get("text", "").strip()
            
        except requests.RequestException as e:
            logger.error(f"LLM completion request failed: {e}")
            raise
        
    def translate_to_action(self, natural_language_input: str) -> dict:
        """
        Translate natural language input to structured mitigation action
        
        Args:
            natural_language_input: Human-readable mitigation request
            
        Returns:
            dict: Structured mitigation action data
        """
        try:
            # Create a structured chat prompt for mitigation action extraction
            messages = [
                {
                    "role": "system",
                    "content": "You are a cybersecurity expert that converts natural language security mitigation requests into structured JSON format. Always respond with valid JSON only."
                },
                {
                    "role": "user", 
                    "content": f"""Convert this security mitigation request into JSON format:

"{natural_language_input}"

Extract these fields:
- action_type: Type of mitigation (rate_limit, block_ip, dns_filter, etc.)
- target: Target of action (IP, domain, service)
- parameters: Specific parameters (rate, duration, ports, etc.)
- confidence: Your confidence (0.0-1.0)

Example format:
{{"action_type": "rate_limit", "target": "10.10.2.1:123", "parameters": {{"rate": 20, "duration": 60, "unit": "requests_per_second"}}, "confidence": 0.9}}

JSON response:"""
                }
            ]

            # Generate completion using chat completions API
            response_text = self.generate_chat_completion(messages, max_tokens=256)
            
            # Try to parse JSON from response
            try:
                # Extract JSON from response (in case there's extra text)
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx != -1 and end_idx != 0:
                    json_str = response_text[start_idx:end_idx]
                    parsed_result = json.loads(json_str)
                else:
                    raise ValueError("No JSON found in response")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse LLM response as JSON: {e}")
                # Fallback to basic parsing
                parsed_result = {
                    "action_type": "unknown",
                    "target": "unknown",
                    "parameters": {"raw_input": natural_language_input},
                    "confidence": 0.3
                }
            
            # Return in the expected format
            return {
                "action": natural_language_input,
                "confidence": parsed_result.get("confidence", 0.5),
                "structured_format": {
                    "name": parsed_result.get("action_type", "unknown"),
                    "target": parsed_result.get("target", "unknown"),
                    "fields": parsed_result.get("parameters", {})
                },
                "raw_llm_response": response_text
            }
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            # Fallback response
            return {
                "action": natural_language_input,
                "confidence": 0.1,
                "structured_format": {
                    "name": "translation_failed",
                    "target": "unknown",
                    "fields": {"error": str(e), "raw_input": natural_language_input}
                },
                "error": str(e)
            }


# Global LLM client instance
llm_client = LLMClient()
