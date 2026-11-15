"""Run manifests: fingerprints that tie a report to the exact inputs and settings behind it."""

import hashlib
import json
from datetime import datetime
from importlib.resources import files

from .. import __version__
from ..enrichment import Enricher
from ..models import CaseBundle
from ..rules import RuleSet
from .models import RunManifest

NO_MODEL = "rules"  # Model name recorded for enrichers that call no LLM


def fingerprint(text: str) -> str:
    """Hash a text with SHA-256.

    Args:
        text: Text to hash, encoded as UTF-8.

    Returns:
        The hexadecimal digest.
    """
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def prompts_fingerprint() -> str:
    """Hash every packaged prompt file, with its name, so a change to any prompt shows.

    Returns:
        The hexadecimal digest.
    """
    folder = files("aml_reporter.enrichment").joinpath("prompts")
    prompts = sorted(
        (entry.name, entry.read_text("utf-8"))
        for entry in folder.iterdir()
        if entry.name.endswith(".md")
    )
    return fingerprint(json.dumps(prompts))


def model_name(enricher: Enricher) -> str:
    """Name the LLM behind an enricher.

    Args:
        enricher: Any enricher.

    Returns:
        The model name, or `rules` for enrichers that call no LLM.
    """
    return str(getattr(getattr(enricher, "client", None), "model", NO_MODEL))


def build_manifest(
    bundle: CaseBundle, ruleset: RuleSet, enricher: str, model: str, generated_at: datetime
) -> RunManifest:
    """Fingerprint the inputs and settings of one report.

    Digests are taken on the validated models, so formatting changes to the input files do
    not change them, while any change to a value does.

    Args:
        bundle: Validated case bundle.
        ruleset: Red-flag rules used.
        enricher: Enricher name, as on the command line.
        model: LLM behind the enricher, or `rules`.
        generated_at: Generation time.

    Returns:
        The run manifest.
    """
    return RunManifest(
        tool_version=__version__,
        case_id=bundle.case_id,
        bundle_sha256=fingerprint(bundle.model_dump_json()),
        rules_sha256=fingerprint(ruleset.model_dump_json()),
        prompts_sha256=prompts_fingerprint(),
        enricher=enricher,
        model=model,
        generated_at=generated_at,
    )
