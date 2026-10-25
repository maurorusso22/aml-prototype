"""Validation tests for the models produced by the pipeline: enrichments and facts."""

import re
from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import (
    CounterpartyType,
    Enrichment,
    EnrichmentSource,
    Fact,
    FactCategory,
    PaymentPurpose,
)

README_ENRICHMENT = {  # Example shown in the README, kept valid by this test module
    "transaction_id": "TX-000812",
    "counterparty_name": "ACME LOGISTICA SRL",
    "counterparty_iban": "IT00X9999901234000000123456",
    "counterparty_type": "legal_person",
    "payment_purpose": "invoice",
    "source": "llm",
}


def test_readme_enrichment_is_valid() -> None:
    """The enrichment example published in the README validates."""
    enrichment = Enrichment.model_validate(README_ENRICHMENT)
    assert enrichment.counterparty_type is CounterpartyType.LEGAL_PERSON
    assert enrichment.payment_purpose is PaymentPurpose.INVOICE


def test_enrichment_defaults_to_empty() -> None:
    """With nothing extracted, values are `None` and the purpose is `unknown`."""
    enrichment = Enrichment(transaction_id="TX-000002", source=EnrichmentSource.BASELINE)
    assert enrichment.counterparty_type is None
    assert enrichment.payment_purpose is PaymentPurpose.UNKNOWN


@pytest.mark.parametrize(
    ("changes", "expected"),
    [
        pytest.param(
            {"counterparty_name": None},
            "counterparty_type requires counterparty_name",
            id="type-without-name",
        ),
        pytest.param(
            {"counterparty_type": "unknown"},
            "Input should be 'natural_person' or 'legal_person'",
            id="unknown-counterparty-type",
        ),
        pytest.param(
            {"source": "unknown"}, "Input should be 'llm' or 'baseline'", id="unknown-source"
        ),
        pytest.param({"payment_purpose": "gambling"}, "Input should be", id="label-outside-set"),
        pytest.param({"counterparty_name": "   "}, "at least 1 character", id="blank-counterparty"),
        pytest.param(
            {"counterparty_iban": "not an iban"}, "String should match pattern", id="bad-iban"
        ),
    ],
)
def test_invalid_enrichments_are_rejected(changes: dict[str, Any], expected: str) -> None:
    """Each inconsistent enrichment fails with a message naming the problem.

    Args:
        changes: Fields to overwrite on the README example.
        expected: Text the validation error must contain.
    """
    with pytest.raises(ValidationError, match=re.escape(expected)):
        Enrichment.model_validate(README_ENRICHMENT | changes)


@pytest.mark.parametrize("value", [27, 1.5, "IT", True])
def test_fact_values_keep_their_type_through_json(value: bool | int | float | str) -> None:
    """Fact values come back from JSON with the same Python type.

    Args:
        value: Value to store in the fact.
    """
    fact = Fact(
        id="F-CASH-002",
        category=FactCategory.TRANSACTION_BEHAVIOUR,
        label="Cash deposits in the last 90 days",
        value=value,
        evidence=("TX-000812",),
    )
    restored = Fact.model_validate_json(fact.model_dump_json())
    assert restored.value == value
    assert type(restored.value) is type(value)


def test_fact_id_format_is_enforced() -> None:
    """Fact identifiers must follow the F-<AREA>-<NNN> format."""
    with pytest.raises(ValidationError, match="String should match pattern"):
        Fact.model_validate({"id": "F-cash-2", "category": "alert", "label": "x", "value": 1})
