"""Validation tests for whole case bundles."""

from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import BusinessCustomer, CaseBundle, IndividualCustomer


def test_valid_fixture_loads(case_data: dict[str, Any]) -> None:
    """The hand-written fixture passes every check."""
    case = CaseBundle.model_validate(case_data)
    assert isinstance(case.customer, IndividualCustomer)
    assert len(case.transactions) == 5


def test_json_round_trip(case_data: dict[str, Any]) -> None:
    """Serialising and parsing again yields an identical bundle."""
    case = CaseBundle.model_validate(case_data)
    assert CaseBundle.model_validate_json(case.model_dump_json()) == case


def test_business_customer_is_discriminated(
    case_data: dict[str, Any], business_customer: dict[str, Any]
) -> None:
    """The `kind` field selects the business customer model."""
    case_data["customer"] = business_customer
    assert isinstance(CaseBundle.model_validate(case_data).customer, BusinessCustomer)


def test_business_incorporated_after_onboarding_is_rejected(
    case_data: dict[str, Any], business_customer: dict[str, Any]
) -> None:
    """A business cannot become a customer before it exists."""
    case_data["customer"] = business_customer | {"incorporation_date": "2020-01-01"}
    with pytest.raises(ValidationError, match="incorporation_date must not follow"):
        CaseBundle.model_validate(case_data)


def test_models_are_immutable(case_data: dict[str, Any]) -> None:
    """Validated models cannot be changed in place."""
    case = CaseBundle.model_validate(case_data)
    with pytest.raises(ValidationError, match="frozen"):
        case.case_id = "CASE-000002"  # type: ignore[misc]


def test_reference_problems_are_reported_together(case_data: dict[str, Any]) -> None:
    """A single error lists every broken cross-reference."""
    case_data["alert"]["transaction_id"] = "TX-000099"
    case_data["cards"][0]["account_id"] = "AC-000099"
    with pytest.raises(ValidationError) as excinfo:
        CaseBundle.model_validate(case_data)
    message = str(excinfo.value)
    assert "alert references unknown transaction TX-000099" in message
    assert "card CA-000001 references unknown account AC-000099" in message
