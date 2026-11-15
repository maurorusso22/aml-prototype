"""Edge cases where missing history or a zero reference must not hide a risk.

Each test changes the hand-written fixture so that a reference value is zero or a history is
missing, then checks the fact that carries the signal and the rule that reads it.
"""

from collections.abc import Callable
from typing import Any

import pytest

from aml_reporter.analytics import build_fact_sheet
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import CaseBundle, FactSheet, FactStatus, RiskAssessment
from aml_reporter.rules import assess, load_rules

OUTBOUND = ("TX-000002", "TX-000003", "TX-000005")  # Fixture transactions that move money out


def analyse(case_data: dict[str, Any]) -> tuple[FactSheet, RiskAssessment]:
    """Compute the fact sheet and the assessment of a raw bundle.

    Args:
        case_data: Raw case bundle.

    Returns:
        The fact sheet and the assessment with the packaged rules.
    """
    bundle = CaseBundle.model_validate(case_data)
    sheet = build_fact_sheet(bundle, BaselineEnricher().enrich(bundle.transactions))
    return sheet, assess(sheet, load_rules())


def drop(case_data: dict[str, Any], *ids: str) -> None:
    """Remove transactions from a raw bundle, in place.

    Args:
        case_data: Raw case bundle.
        *ids: Transaction identifiers to remove.
    """
    case_data["transactions"] = [
        tx for tx in case_data["transactions"] if tx["transaction_id"] not in ids
    ]


def test_outflows_from_a_zero_baseline_fire_the_spike_rule(case_data: dict[str, Any]) -> None:
    """Outflows after a history without any are above any multiple, not 0 times the usual."""
    sheet, assessment = analyse(case_data)
    spike = sheet.get("F-FLOW-008")
    assert (spike.value, spike.status) == (None, FactStatus.NO_BASELINE)
    assert "RF-OUTFLOW-SPIKE" in [flag.rule_id for flag in assessment.flags]


def test_no_outflows_at_all_is_not_a_spike(case_data: dict[str, Any]) -> None:
    """With nothing out in either window there is nothing to compare, and nothing to flag."""
    drop(case_data, *OUTBOUND)
    sheet, assessment = analyse(case_data)
    assert sheet.get("F-FLOW-008").status is FactStatus.NO_ACTIVITY
    assert sheet.get("F-CHAN-001").status is FactStatus.NO_ACTIVITY
    decided = [flag.rule_id for flag in assessment.flags]
    undecided = [rule.rule_id for rule in assessment.unevaluated]
    assert "RF-OUTFLOW-SPIKE" not in decided + undecided


def test_a_short_history_leaves_the_spike_rule_undecided(case_data: dict[str, Any]) -> None:
    """Without enough earlier days there is no usual level: the rule is reported, not skipped."""
    case_data["period_start"] = "2026-07-01"
    sheet, assessment = analyse(case_data)
    assert sheet.get("F-FLOW-008").status is FactStatus.UNAVAILABLE
    unevaluated = {rule.rule_id: rule.facts for rule in assessment.unevaluated}
    assert unevaluated == {"RF-OUTFLOW-SPIKE": ("F-FLOW-008",)}
    assert not assessment.complete


def test_zero_declared_income_makes_any_salary_a_mismatch(case_data: dict[str, Any]) -> None:
    """Salary received by a customer who declared no income exceeds the declared profile."""
    case_data["customer"]["declared_annual_income"] = "0.00"
    sheet, assessment = analyse(case_data)
    assert sheet.get("F-PROF-004").status is FactStatus.NO_BASELINE
    assert "RF-PROFILE-MISMATCH" in [flag.rule_id for flag in assessment.flags]


def test_a_new_relationship_is_annualised_over_its_own_history(case_data: dict[str, Any]) -> None:
    """Inflows of an account opened 42 days ago are scaled to a year from those 42 days."""
    case_data["accounts"][0]["opened_on"] = "2026-08-20"
    sheet, _ = analyse(case_data)
    assert sheet.get("F-PROF-001").value == round(11_600 * 365 / 42, 2)
    assert sheet.get("F-FLOW-008").status is FactStatus.UNAVAILABLE


@pytest.mark.parametrize(
    ("change", "silence", "fires"),
    [
        pytest.param(lambda d: None, 349, True, id="silent-since-period-start"),
        pytest.param(
            lambda d: d["accounts"][0].update(opened_on="2026-08-25"), 21, False, id="new-account"
        ),
    ],
)
def test_silence_without_earlier_activity_is_a_lower_bound(
    case_data: dict[str, Any], change: Callable[[dict[str, Any]], None], silence: int, fires: bool
) -> None:
    """With no earlier customer activity, the silence runs back to the start of the history.

    Args:
        case_data: Raw fixture bundle.
        change: Extra change to the bundle.
        silence: Expected days of silence before the alert.
        fires: Whether the dormant-reactivation rule should fire.
    """
    drop(case_data, "TX-000003")
    change(case_data)
    sheet, assessment = analyse(case_data)
    assert sheet.get("F-TIME-002").value == silence
    assert sheet.get("F-TIME-006").value is True
    raised = [flag.rule_id for flag in assessment.flags]
    assert ("RF-DORMANT-REACTIVATION" in raised) is fires


def test_first_transaction_of_its_kind_has_no_median(case_data: dict[str, Any]) -> None:
    """The alerted deposit has no earlier peer: median and maximum are absent, not zero."""
    sheet, _ = analyse(case_data)
    assert sheet.get("F-ALERT-004").status is FactStatus.NO_ACTIVITY
    assert sheet.get("F-ALERT-005").status is FactStatus.NO_BASELINE
    assert sheet.get("F-ALERT-006").status is FactStatus.NO_ACTIVITY
