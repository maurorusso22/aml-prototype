"""Adversarial answers must be rejected before they reach an enrichment."""

import pytest
from pydantic import BaseModel

from aml_reporter.enrichment.tasks import IbanAnswers, PurposeAnswers
from aml_reporter.enrichment.validation import InvalidAnswerError, check_iban, check_name
from aml_reporter.llm import LLMError, parse_json

TEXT = "BONIFICO SEPA DA ACME LOGISTICA SRL IBAN IT00X9999901234000000123456 CAUSALE STIPENDIO"


def test_iban_found_in_text_is_accepted() -> None:
    """A well-formed IBAN copied from the text passes, with spaces removed."""
    assert check_iban("IT00X9999901234000000123456", TEXT) == "IT00X9999901234000000123456"
    assert check_iban("IT00 X999 9901 2340 0000 0123 456", TEXT) == "IT00X9999901234000000123456"
    assert check_iban(None, TEXT) is None


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        pytest.param("IT00X9999999999999999999999", "does not appear", id="invented-iban"),
        pytest.param("IT00X99999", "invalid structure", id="truncated-iban"),
        pytest.param("ACME LOGISTICA SRL", "invalid structure", id="name-as-iban"),
        pytest.param(42, "not text", id="number"),
    ],
)
def test_bad_ibans_are_rejected(value: object, reason: str) -> None:
    """Invented, malformed, or mistyped IBANs never pass.

    Args:
        value: Answer returned by a misbehaving model.
        reason: Text the rejection must contain.
    """
    with pytest.raises(InvalidAnswerError, match=reason):
        check_iban(value, TEXT)


def test_names_are_returned_as_written() -> None:
    """Matching ignores case and spacing, but the returned name is the text's own."""
    assert check_name("ACME LOGISTICA SRL", TEXT) == "ACME LOGISTICA SRL"
    assert check_name("acme  logistica srl", TEXT) == "ACME LOGISTICA SRL"
    assert check_name(None, TEXT) is None


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        pytest.param("ACME SERVIZI SRL", "does not appear", id="invented-name"),
        pytest.param("   ", "blank", id="blank"),
        pytest.param(["ACME"], "blank", id="not-text"),
    ],
)
def test_bad_names_are_rejected(value: object, reason: str) -> None:
    """Names absent from the text, blank, or not text never pass.

    Args:
        value: Answer returned by a misbehaving model.
        reason: Text the rejection must contain.
    """
    with pytest.raises(InvalidAnswerError, match=reason):
        check_name(value, TEXT)


@pytest.mark.parametrize(
    ("raw", "schema"),
    [
        pytest.param('{"answers": [{"id": 0, "iban": null}', IbanAnswers, id="malformed-json"),
        pytest.param(
            '{"answers": [{"id": 0, "payment_purpose": "gambling"}]}',
            PurposeAnswers,
            id="label-outside-set",
        ),
        pytest.param(
            '{"answers": [{"id": 0, "iban": null, "note": "sure"}]}',
            IbanAnswers,
            id="extra-field",
        ),
        pytest.param('{"answers": [{"iban": null}]}', IbanAnswers, id="missing-id"),
    ],
)
def test_unparseable_output_raises_llm_error(raw: str, schema: type[BaseModel]) -> None:
    """Output that is not valid JSON for the schema becomes an LLMError, never a crash.

    Args:
        raw: Raw model output.
        schema: Expected answer schema.
    """
    with pytest.raises(LLMError, match=schema.__name__):
        parse_json(raw, schema)
