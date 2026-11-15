"""Run manifests: equal inputs give equal fingerprints, and any change to a value shows."""

from datetime import UTC, datetime
from typing import Any

from aml_reporter.controls import build_manifest, model_name
from aml_reporter.controls.audit import prompts_fingerprint
from aml_reporter.enrichment import BaselineEnricher, LLMEnricher
from aml_reporter.llm import OllamaClient
from aml_reporter.models import CaseBundle
from aml_reporter.rules import RuleSet, load_rules

GENERATED_AT = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)  # Any fixed generation time
SHA256_HEX = 64  # Length of a hexadecimal SHA-256 digest


def manifest_of(case_data: dict[str, Any], ruleset: RuleSet | None = None) -> dict[str, Any]:
    """Build the manifest of a raw bundle, as a plain dictionary.

    Args:
        case_data: Raw case bundle.
        ruleset: Rules; the packaged ones when omitted.

    Returns:
        The manifest fields.
    """
    bundle = CaseBundle.model_validate(case_data)
    rules = ruleset or load_rules()
    return build_manifest(bundle, rules, "baseline", "rules", GENERATED_AT).model_dump()


def test_manifest_is_reproducible(case_data: dict[str, Any]) -> None:
    """The same inputs give the same digests, whatever the JSON formatting of the file."""
    first = manifest_of(case_data)
    reparsed = CaseBundle.model_validate_json(
        CaseBundle.model_validate(case_data).model_dump_json()
    )
    second = build_manifest(reparsed, load_rules(), "baseline", "rules", GENERATED_AT).model_dump()
    assert first == second
    assert all(len(first[key]) == SHA256_HEX for key in ("bundle_sha256", "rules_sha256"))


def test_any_change_to_the_inputs_shows(case_data: dict[str, Any]) -> None:
    """Changing one amount or one threshold changes the matching digest, and only that one."""
    base = manifest_of(case_data)
    case_data["transactions"][0]["amount"] = "2100.01"
    assert manifest_of(case_data)["bundle_sha256"] != base["bundle_sha256"]
    raw = load_rules().model_dump(mode="json")
    raw["rules"][0]["when"][0]["value"] = 4
    changed = manifest_of(case_data, RuleSet.model_validate(raw))
    assert changed["rules_sha256"] != base["rules_sha256"]
    assert changed["prompts_sha256"] == base["prompts_sha256"] == prompts_fingerprint()


def test_model_name_follows_the_enricher() -> None:
    """LLM enrichers record their model; the baseline records that it uses rules."""
    assert model_name(BaselineEnricher()) == "rules"
    assert model_name(LLMEnricher(OllamaClient("llama3.1:8b"))) == "llama3.1:8b"
