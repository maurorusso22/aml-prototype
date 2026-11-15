"""Edge cases where missing history or a zero reference must not hide a risk.

Each test changes the hand-written fixture so that a reference value is zero or a history is
missing, then checks the fact that carries the signal and the rule that reads it.
"""

from typing import Any

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


def test_zero_declared_income_makes_any_salary_a_mismatch(case_data: dict[str, Any]) -> None:
    """Salary received by a customer who declared no income exceeds the declared profile."""
    case_data["customer"]["declared_annual_income"] = "0.00"
    sheet, assessment = analyse(case_data)
    assert sheet.get("F-PROF-004").status is FactStatus.NO_BASELINE
    assert "RF-PROFILE-MISMATCH" in [flag.rule_id for flag in assessment.flags]


def test_first_transaction_of_its_kind_has_no_median(case_data: dict[str, Any]) -> None:
    """The alerted deposit has no earlier peer: median and maximum are absent, not zero."""
    sheet, _ = analyse(case_data)
    assert sheet.get("F-ALERT-004").status is FactStatus.NO_ACTIVITY
    assert sheet.get("F-ALERT-005").status is FactStatus.NO_BASELINE
    assert sheet.get("F-ALERT-006").status is FactStatus.NO_ACTIVITY
