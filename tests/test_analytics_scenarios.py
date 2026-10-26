"""Fact sheets of the synthetic scenarios: each story leaves its mark, and stays stable.

Golden files keep one fact per line. After an intended change, refresh them with
`UPDATE_GOLDEN=1 uv run pytest tests/test_analytics_scenarios.py` and review the diff.
"""

import json
import os
from pathlib import Path

import pytest

from aml_reporter.analytics import build_fact_sheet
from aml_reporter.analytics.base import AnalysisContext
from aml_reporter.analytics.charts import monthly_flows_chart, purpose_mix_chart
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import FactSheet
from aml_reporter.synthetic import SCENARIOS, GeneratedCase, generate_cases

GOLDEN_DIR = Path(__file__).parent / "golden"  # Expected fact sheets, one file per scenario
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"  # First bytes of every PNG file
SIGNALS = [  # (scenario, fact id, check): the fact that tells each story apart
    ("structuring_cash", "F-CASH-004", lambda value: value >= 6),
    ("pass_through", "F-CPTY-005", lambda value: value >= 5),
    ("pass_through", "F-GEO-003", lambda value: value > 0),
    ("dormant_reactivation", "F-TIME-001", lambda value: value >= 150),
    ("dormant_reactivation", "F-TIME-002", lambda value: value >= 150),
    ("profile_mismatch", "F-PROF-002", lambda value: value > 3),
    ("fp_salary_bonus", "F-ALERT-008", lambda value: value >= 6),
    ("fp_property_sale", "F-ALERT-008", lambda value: value == 0),
    ("fp_property_sale", "F-ALERT-005", lambda value: value > 20),
]


@pytest.fixture(scope="module")
def cases() -> dict[str, tuple[GeneratedCase, FactSheet]]:
    """Generate every scenario and compute its fact sheet with the baseline enricher.

    Returns:
        Case and fact sheet per scenario name.
    """
    result = {}
    for case in generate_cases(list(SCENARIOS), 42):
        enrichments = BaselineEnricher().enrich(case.bundle.transactions)
        result[case.labels.scenario] = (case, build_fact_sheet(case.bundle, enrichments))
    return result


@pytest.mark.parametrize(("scenario", "fact_id", "check"), SIGNALS)
def test_scenario_signals(
    cases: dict[str, tuple[GeneratedCase, FactSheet]], scenario: str, fact_id: str, check: object
) -> None:
    """The fact that characterises each scenario has the expected magnitude.

    Args:
        cases: Generated cases with their fact sheets.
        scenario: Scenario to inspect.
        fact_id: Fact that carries the signal.
        check: Predicate the value must satisfy.
    """
    value = cases[scenario][1].get(fact_id).value
    assert callable(check) and check(value), f"{scenario} {fact_id} = {value}"


def test_evidence_exists(cases: dict[str, tuple[GeneratedCase, FactSheet]]) -> None:
    """Every evidence identifier points to a transaction of the same case."""
    for case, sheet in cases.values():
        known = {tx.transaction_id for tx in case.bundle.transactions}
        assert all(set(fact.evidence) <= known for fact in sheet.facts)


@pytest.mark.parametrize("scenario", list(SCENARIOS))
def test_fact_sheet_matches_golden_file(
    cases: dict[str, tuple[GeneratedCase, FactSheet]], scenario: str
) -> None:
    """The fact sheet equals the reviewed golden file.

    Args:
        cases: Generated cases with their fact sheets.
        scenario: Scenario to compare.
    """
    path = GOLDEN_DIR / f"{scenario}.json"
    text = _golden_text(cases[scenario][1])
    if os.environ.get("UPDATE_GOLDEN"):
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8")
    assert path.read_text(encoding="utf-8") == text


def test_charts_render_as_png(cases: dict[str, tuple[GeneratedCase, FactSheet]]) -> None:
    """Both report charts render to non-trivial PNG images."""
    case = cases["pass_through"][0]
    enrichments = BaselineEnricher().enrich(case.bundle.transactions)
    context = AnalysisContext(case.bundle, {e.transaction_id: e for e in enrichments})
    for chart in (monthly_flows_chart(context), purpose_mix_chart(context)):
        assert chart.startswith(PNG_SIGNATURE)
        assert len(chart) > 10_000


def _golden_text(sheet: FactSheet) -> str:
    """Serialise a fact sheet with one fact per line, so diffs show which facts changed.

    Args:
        sheet: Fact sheet to serialise.

    Returns:
        JSON text ending with a newline.
    """
    facts = ",\n    ".join(json.dumps(fact.model_dump(mode="json")) for fact in sheet.facts)
    return f'{{\n  "case_id": "{sheet.case_id}",\n  "facts": [\n    {facts}\n  ]\n}}\n'
