"""LLM Adapters Module.

This module provides LLM service implementations for Scout.
Currently supports Ollama for local inference.
"""

from scout.infrastructure.llm.ollama_service import OllamaService

__all__ = ["OllamaService"]
