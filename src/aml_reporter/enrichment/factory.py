"""Build the enricher selected by name."""

from ..llm import AnthropicClient, OllamaClient
from ..settings import ENRICHERS, Settings
from .base import Enricher
from .baseline import BaselineEnricher
from .llm_enricher import LLMEnricher


def make_enricher(name: str, settings: Settings) -> Enricher:
    """Create an enricher; LLM-backed ones fall back to the baseline on any failure.

    Args:
        name: One of `ENRICHERS`.
        settings: Backend configuration.

    Returns:
        The enricher.

    Raises:
        ValueError: When the name is unknown.
    """
    if name == "local":
        return LLMEnricher(OllamaClient(settings.ollama_model, settings.ollama_url))
    if name == "anthropic":
        return LLMEnricher(AnthropicClient(settings.anthropic_model))
    if name == "baseline":
        return BaselineEnricher()
    raise ValueError(f"unknown enricher {name!r}; choose from {', '.join(ENRICHERS)}")
