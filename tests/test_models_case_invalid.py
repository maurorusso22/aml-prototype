"""Broken case bundles must fail with an error that names the problem."""

import re
from collections.abc import Callable
from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import CaseBundle

INVALID_BUNDLES = [  # (in-place mutation, expected error text) pairs
    pytest.param(
        lambda d: d.update(unexpected="x"), "Extra inputs are not permitted", id="unknown-field"
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(iban="IT00 X999"),
        "String should match pattern",
        id="malformed-iban",
    ),
    pytest.param(
        lambda d: d["customer"].update(kind="robot"),
        "does not match any of the expected tags",
        id="unknown-customer-kind",
    ),
    pytest.param(
        lambda d: d["customer"].update(birth_date="2020-01-01"),
        "birth_date must precede onboarding_date",
        id="born-after-onboarding",
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(status="closed"),
        "closed_on must be set if and only if status is closed",
        id="closed-without-date",
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(status="closed", closed_on="2010-01-01"),
        "closed_on must not precede opened_on",
        id="closed-before-opening",
    ),
    pytest.param(
        lambda d: d["cards"][0].update(expires_on="2023-01-01"),
        "expires_on must follow issued_on",
        id="card-expired-before-issue",
    ),
    pytest.param(
        lambda d: d.update(period_end="2025-01-01"),
        "period_end must not precede period_start",
        id="reversed-period",
    ),
    pytest.param(
        lambda d: d["cards"][0].update(account_id="AC-000099"),
        "card CA-000001 references unknown account AC-000099",
        id="card-unknown-account",
    ),
    pytest.param(
        lambda d: d["transactions"][1].update(account_id="AC-000099"),
        "transaction TX-000002 references unknown account",
        id="transaction-unknown-account",
    ),
    pytest.param(
        lambda d: d["transactions"][0].update(currency="USD"),
        "transaction TX-000001 is in USD, not EUR",
        id="foreign-currency-transaction",
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(currency="CHF"),
        "account AC-000001 is in CHF, not EUR",
        id="foreign-currency-account",
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(opened_on="2026-09-01"),
        "transaction TX-000001 booked on 2026-08-27, before account AC-000001 opened",
        id="booked-before-opening",
    ),
    pytest.param(
        lambda d: d["accounts"][0].update(status="closed", closed_on="2026-09-10"),
        "transaction TX-000004 booked on 2026-09-15, after account AC-000001 closed",
        id="booked-after-closing",
    ),
    pytest.param(
        lambda d: d["transactions"].append(dict(d["transactions"][0])),
        "duplicate transaction_id TX-000001",
        id="duplicate-transaction",
    ),
    pytest.param(
        lambda d: d["transactions"][0].update(booked_at="2024-01-01T10:00:00+01:00"),
        "transaction TX-000001 booked on 2024-01-01, outside the case period",
        id="outside-period",
    ),
    pytest.param(
        lambda d: d["alert"].update(transaction_id="TX-000099"),
        "alert references unknown transaction TX-000099",
        id="alert-unknown-transaction",
    ),
    pytest.param(
        lambda d: d["alert"].update(customer_id="CU-000099"),
        "alert refers to customer CU-000099",
        id="alert-other-customer",
    ),
    pytest.param(
        lambda d: d["alert"].update(raised_at="2026-09-15T10:00:00+02:00"),
        "alert raised before the alerted transaction was booked",
        id="alert-before-transaction",
    ),
    pytest.param(
        lambda d: d.update(transactions=[]), "should have at least 1 item", id="no-transactions"
    ),
]


@pytest.mark.parametrize(("mutate", "expected"), INVALID_BUNDLES)
def test_invalid_bundles_are_rejected(
    case_data: dict[str, Any], mutate: Callable[[dict[str, Any]], None], expected: str
) -> None:
    """Each broken bundle fails with a message naming the problem.

    Args:
        case_data: Valid bundle to break.
        mutate: In-place change that makes the bundle invalid.
        expected: Text the validation error must contain.
    """
    mutate(case_data)
    with pytest.raises(ValidationError, match=re.escape(expected)):
        CaseBundle.model_validate(case_data)
