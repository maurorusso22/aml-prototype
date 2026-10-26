"""Every analyser, checked by hand on the five-transaction fixture.

Enrichment comes from the baseline, so the expected values follow from the rules: the direct
debit's counterparty is misread as "CANONE LOCAZIONE SETTEMBRE", exactly as the baseline does.
"""

from typing import Any

import pytest

from aml_reporter.analytics import build_fact_sheet
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import CaseBundle, FactSheet

EXPECTED = [  # (fact id, expected value), one or more per analyser
    ("F-ALERT-001", 9500.0),
    ("F-ALERT-002", "inbound cash deposit"),
    ("F-ALERT-003", 0),
    ("F-ALERT-005", 0.0),
    ("F-FLOW-001", 11600.0),
    ("F-FLOW-002", 9795.3),
    ("F-FLOW-003", 1804.7),
    ("F-FLOW-004", 953.42),
    ("F-CASH-002", 1),
    ("F-CASH-004", 1),
    ("F-CASH-007", 0.819),
    ("F-CHAN-003", 0.9188),
    ("F-CHAN-004", 0.0046),
    ("F-CHAN-005", 0.0766),
    ("F-PURP-001", 2100.0),
    ("F-PURP-102", 750.0),
    ("F-PURP-104", 9000.0),
    ("F-PURP-201", 0.0),
    ("F-CPTY-001", 1),
    ("F-CPTY-002", 2),
    ("F-CPTY-003", 0.181),
    ("F-CPTY-004", "ACME LOGISTICA SRL"),
    ("F-CPTY-006", 3),
    ("F-GEO-001", "DE"),
    ("F-GEO-003", 9000.0),
    ("F-GEO-101", 9000.0),
    ("F-CUST-001", "individual"),
    ("F-CUST-002", 11.3),
    ("F-CUST-004", 32000.0),
    ("F-REL-003", 5230.4),
    ("F-PROF-002", 0.3625),
    ("F-PROF-003", 2100.0),
    ("F-TIME-001", 9),
    ("F-TIME-002", 9),
    ("F-TIME-003", 2),
]


@pytest.fixture
def sheet(case_data: dict[str, Any]) -> FactSheet:
    """Compute the fact sheet of the hand-written fixture.

    Args:
        case_data: Raw fixture bundle.

    Returns:
        The fact sheet.
    """
    bundle = CaseBundle.model_validate(case_data)
    return build_fact_sheet(bundle, BaselineEnricher().enrich(bundle.transactions))


@pytest.mark.parametrize(("fact_id", "expected"), EXPECTED)
def test_fact_values(sheet: FactSheet, fact_id: str, expected: object) -> None:
    """Each fact holds the value computed by hand.

    Args:
        sheet: Fact sheet of the fixture.
        fact_id: Fact to check.
        expected: Value computed by hand.
    """
    assert sheet.get(fact_id).value == expected


def test_evidence_points_to_the_right_transactions(sheet: FactSheet) -> None:
    """Evidence lists the transactions behind each value, and nothing else."""
    assert sheet.get("F-ALERT-001").evidence == ("TX-000004",)
    assert sheet.get("F-FLOW-001").evidence == ("TX-000001", "TX-000004")
    assert sheet.get("F-GEO-003").evidence == ("TX-000005",)
    assert sheet.get("F-TIME-001").evidence == ("TX-000003", "TX-000004")
    assert sheet.get("F-ALERT-003").evidence == ()


def test_alert_without_counterparty_has_no_counterparty_facts(sheet: FactSheet) -> None:
    """A cash deposit has no counterparty, so F-ALERT-007 and 008 are absent."""
    ids = {fact.id for fact in sheet.facts}
    assert "F-ALERT-006" in ids
    assert not {"F-ALERT-007", "F-ALERT-008"} & ids
