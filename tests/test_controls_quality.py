"""Data-quality checks: each issue on a case built to show it, and none on clean cases."""

from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.controls import IssueCode, QualityThresholds, check_quality, load_thresholds
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import CaseBundle, Enrichment
from aml_reporter.synthetic import SCENARIOS, generate_cases

type Change = Callable[[dict[str, Any]], None]


def duplicate_last(case_data: dict[str, Any]) -> None:
    """Book the last transaction a second time under a new identifier.

    Args:
        case_data: Raw case bundle, changed in place.
    """
    case_data["transactions"].append(
        {**case_data["transactions"][-1], "transaction_id": "TX-000099"}
    )


def issues_of(
    case_data: dict[str, Any], enricher: str = "baseline", keep: int | None = None
) -> dict[IssueCode, tuple[dict[str, int], tuple[str, ...]]]:
    """Run the checks on a raw bundle enriched by the baseline.

    Args:
        case_data: Raw case bundle.
        enricher: Enricher name the checks are told about.
        keep: Keep only the first enrichments, to simulate an enricher that dropped some.

    Returns:
        Details and transactions of each issue found, by code.
    """
    bundle = CaseBundle.model_validate(case_data)
    enrichments: list[Enrichment] = BaselineEnricher().enrich(bundle.transactions)[:keep]
    found = check_quality(bundle, enrichments, enricher, load_thresholds())
    return {issue.code: (issue.details, issue.transactions) for issue in found}


@pytest.mark.parametrize(
    ("change", "code", "details", "transactions"),
    [
        pytest.param(
            lambda d: d.update(period_start="2026-07-01"),
            IssueCode.SHORT_HISTORY,
            {"days": 2, "minimum": 30},
            (),
            id="short-history",
        ),
        pytest.param(
            lambda d: d["transactions"][0].update(description=""),
            IssueCode.UNDESCRIBED,
            {"count": 1, "total": 3},
            ("TX-000001",),
            id="undescribed",
        ),
        pytest.param(
            duplicate_last, IssueCode.DUPLICATES, {"count": 1}, ("TX-000099",), id="duplicate"
        ),
        pytest.param(
            lambda d: d["cards"][0].update(expires_on="2026-09-01"),
            IssueCode.CARD_VALIDITY,
            {"count": 1},
            ("TX-000003",),
            id="expired-card",
        ),
    ],
)
def test_each_issue_is_found(
    case_data: dict[str, Any],
    change: Change,
    code: IssueCode,
    details: dict[str, int],
    transactions: tuple[str, ...],
) -> None:
    """A bundle changed to show one issue raises exactly that issue.

    Args:
        case_data: Raw fixture bundle.
        change: Change that introduces the issue.
        code: Expected issue.
        details: Expected message values.
        transactions: Expected transactions concerned.
    """
    change(case_data)
    assert issues_of(case_data) == {code: (details, transactions)}


def test_dropped_enrichments_are_found(case_data: dict[str, Any]) -> None:
    """Transfers the enricher returned nothing for are listed."""
    found = issues_of(case_data, keep=2)
    assert found == {IssueCode.UNENRICHED: ({"count": 1, "total": 3}, ("TX-000005",))}


def test_fallback_counts_only_for_llm_enrichers(case_data: dict[str, Any]) -> None:
    """Rule-based records are a fallback for an LLM enricher, and the design of the baseline."""
    found = issues_of(case_data, enricher="local")
    assert found == {IssueCode.FALLBACK: ({"share": 100, "limit": 20}, ())}
    assert issues_of(case_data, enricher="baseline") == {}


@pytest.mark.parametrize("seed", range(42, 45))
def test_synthetic_cases_are_clean(seed: int) -> None:
    """Generated cases are complete, so every check passes on them.

    Args:
        seed: Generation seed.
    """
    for case in generate_cases(list(SCENARIOS), seed):
        enrichments = BaselineEnricher().enrich(case.bundle.transactions)
        assert check_quality(case.bundle, enrichments, "baseline", load_thresholds()) == ()


def test_thresholds_must_be_shares() -> None:
    """A tolerance outside 0 to 1 is rejected when the file is loaded."""
    with pytest.raises(ValidationError, match="less than or equal to 1"):
        QualityThresholds.model_validate({"max_fallback_share": 20, "max_undescribed_share": 0})
