"""Validation tests for single transactions."""

import re
from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import Transaction


@pytest.mark.parametrize(
    ("index", "changes", "expected"),
    [
        pytest.param(
            3,
            {"channel": "online"},
            "cash_deposit must use one of [atm, branch], got online",
            id="cash-online",
        ),
        pytest.param(
            3,
            {"direction": "outbound"},
            "cash_deposit must be inbound, got outbound",
            id="deposit-outbound",
        ),
        pytest.param(
            2, {"card_id": None}, "card_payment requires card_id", id="card-payment-without-card"
        ),
        pytest.param(
            0, {"card_id": "CA-000001"}, "wire_transfer must not have card_id", id="wire-with-card"
        ),
        pytest.param(
            0,
            {"booked_at": "2026-08-27T09:15:00"},
            "Input should have timezone info",
            id="naive-timestamp",
        ),
        pytest.param(
            0, {"amount": "-10.00"}, "Input should be greater than 0", id="negative-amount"
        ),
        pytest.param(
            0,
            {"amount": "10.001"},
            "Decimal input should have no more than 2 decimal places",
            id="sub-cent-amount",
        ),
        pytest.param(
            0, {"transaction_id": "TX-1"}, "String should match pattern", id="malformed-id"
        ),
    ],
)
def test_invalid_transactions_are_rejected(
    case_data: dict[str, Any], index: int, changes: dict[str, Any], expected: str
) -> None:
    """Each inconsistent transaction fails with a message naming the problem.

    Args:
        case_data: Valid bundle providing the base transactions.
        index: Position of the transaction to break.
        changes: Fields to overwrite.
        expected: Text the validation error must contain.
    """
    raw = case_data["transactions"][index] | changes
    with pytest.raises(ValidationError, match=re.escape(expected)):
        Transaction.model_validate(raw)


def test_problems_are_reported_together(case_data: dict[str, Any]) -> None:
    """Several inconsistencies on one transaction surface in a single error."""
    raw = case_data["transactions"][3] | {"channel": "pos", "direction": "outbound"}
    with pytest.raises(ValidationError) as excinfo:
        Transaction.model_validate(raw)
    message = str(excinfo.value)
    assert "cash_deposit must use one of [atm, branch], got pos" in message
    assert "cash_deposit must be inbound, got outbound" in message
