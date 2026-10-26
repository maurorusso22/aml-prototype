"""Runtime settings, read from environment variables; the CLI also loads them from `.env`."""

import os
from dataclasses import dataclass
from typing import Self

from .llm import anthropic_client, ollama_client

ENRICHERS = ("local", "anthropic", "baseline")  # Accepted enricher names, in order of preference


@dataclass(frozen=True)
class Settings:
    """Which enricher to use and how to reach each LLM backend.

    The local model is the default, as in a bank where the LLM runs on its own servers.
    """

    enricher: str = "local"
    anthropic_model: str = anthropic_client.DEFAULT_MODEL
    ollama_url: str = ollama_client.DEFAULT_URL
    ollama_model: str = ollama_client.DEFAULT_MODEL

    @classmethod
    def from_env(cls) -> Self:
        """Read settings from `AML_*` variables; empty or missing ones keep their default.

        Returns:
            The settings.
        """
        defaults = cls()
        return cls(
            enricher=os.environ.get("AML_ENRICHER") or defaults.enricher,
            anthropic_model=os.environ.get("AML_ANTHROPIC_MODEL") or defaults.anthropic_model,
            ollama_url=os.environ.get("AML_OLLAMA_URL") or defaults.ollama_url,
            ollama_model=os.environ.get("AML_OLLAMA_MODEL") or defaults.ollama_model,
        )
