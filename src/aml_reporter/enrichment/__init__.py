"""Enrichment: structured fields read from free-text transaction descriptions."""

from .base import Enricher, enrichable
from .baseline import BaselineEnricher
from .factory import make_enricher
from .llm_enricher import LLMEnricher

__all__ = [  # Public names of the enrichment package
    "BaselineEnricher",
    "Enricher",
    "LLMEnricher",
    "enrichable",
    "make_enricher",
]
