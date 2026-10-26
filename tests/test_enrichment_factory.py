"""The factory builds the enricher named by the settings."""

import pytest

from aml_reporter.enrichment import BaselineEnricher, LLMEnricher, make_enricher
from aml_reporter.settings import Settings


def test_factory_builds_each_enricher(monkeypatch: pytest.MonkeyPatch) -> None:
    """Baseline is rule-based; local and anthropic are LLM enrichers with a baseline fallback.

    Args:
        monkeypatch: Provides a dummy API key, so no real credentials are needed.
    """
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key-not-real")
    settings = Settings()
    assert isinstance(make_enricher("baseline", settings), BaselineEnricher)
    assert isinstance(make_enricher("local", settings), LLMEnricher)
    assert isinstance(make_enricher("anthropic", settings), LLMEnricher)
    with pytest.raises(ValueError, match="unknown enricher"):
        make_enricher("magic", settings)


def test_settings_read_the_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    """The local model is the default; set variables override defaults, empty ones keep them.

    Args:
        monkeypatch: Sets environment variables for this test only.
    """
    assert Settings().enricher == "local"
    monkeypatch.setenv("AML_ENRICHER", "anthropic")
    monkeypatch.setenv("AML_OLLAMA_MODEL", "")
    settings = Settings.from_env()
    assert settings.enricher == "anthropic"
    assert settings.ollama_model == Settings().ollama_model
