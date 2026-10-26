"""Smoke tests against real LLM backends; run with `uv run pytest -m integration`.

Each test is skipped when its backend is not configured. The Anthropic test costs a fraction of a
cent with Claude Haiku.
"""

import os

import httpx
import pytest
from dotenv import load_dotenv

from aml_reporter.enrichment import enrichable, make_enricher
from aml_reporter.models import EnrichmentSource
from aml_reporter.settings import Settings
from aml_reporter.synthetic import GeneratedCase

pytestmark = pytest.mark.integration  # Excluded from the default test run

SAMPLE_SIZE = 10  # Descriptions sent to the backend
MIN_LLM_SHARE = 0.7  # Share of enrichments that must survive validation


def _ollama_running(url: str) -> bool:
    """Check whether an Ollama server answers.

    Args:
        url: Base URL of the server.

    Returns:
        True when the server lists its models.
    """
    try:
        return httpx.get(f"{url.rstrip('/')}/api/tags", timeout=2).is_success
    except httpx.HTTPError:
        return False


@pytest.mark.parametrize("backend", ["local", "anthropic"])
def test_backend_enriches_a_sample(backend: str, pass_through_case: GeneratedCase) -> None:
    """Most answers from a real backend pass validation on a small synthetic sample.

    Args:
        backend: Enricher name.
        pass_through_case: Synthetic case to sample from.
    """
    load_dotenv()
    settings = Settings.from_env()
    if backend == "local" and not _ollama_running(settings.ollama_url):
        pytest.skip("Ollama is not running")
    if backend == "anthropic" and not (
        os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")
    ):
        pytest.skip("no Anthropic credentials in the environment")
    sample = enrichable(pass_through_case.bundle.transactions)[:SAMPLE_SIZE]
    enrichments = make_enricher(backend, settings).enrich(sample)
    assert len(enrichments) == SAMPLE_SIZE
    from_llm = sum(enrichment.source is EnrichmentSource.LLM for enrichment in enrichments)
    assert from_llm >= MIN_LLM_SHARE * SAMPLE_SIZE
