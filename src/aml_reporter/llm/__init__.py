"""LLM backends behind one small interface: Claude through the API, or a local model."""

from .anthropic_client import AnthropicClient
from .base import LLMClient, LLMError, parse_json
from .ollama_client import OllamaClient

__all__ = ["AnthropicClient", "LLMClient", "LLMError", "OllamaClient", "parse_json"]  # Public API
