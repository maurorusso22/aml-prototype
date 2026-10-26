"""Synthetic identifiers are well-formed but always fail real-world check-digit validation."""

import random
from datetime import date

import pytest
from pydantic import TypeAdapter

from aml_reporter.models.formats import Iban, MaskedPan, TaxCode, VatNumber
from aml_reporter.synthetic.checks import (
    iban_is_valid,
    iban_mod97_ok,
    luhn_is_valid,
    tax_code_check_char,
)
from aml_reporter.synthetic.identifiers import (
    BBAN_LENGTHS,
    fake_iban,
    fake_pan,
    fake_vat_number,
    mask_pan,
)
from aml_reporter.synthetic.tax_code import fake_tax_code

SAMPLES = 300  # Identifiers drawn per test


def test_check_algorithms_accept_published_examples() -> None:
    """The validators agree with well-known valid reference values."""
    assert iban_is_valid("GB82WEST12345698765432")
    assert not iban_is_valid("GB82WEST12345698765433")
    assert iban_mod97_ok("GB00WEST12345698765432") is iban_mod97_ok("GB97WEST12345698765432")
    assert not iban_is_valid("GB00WEST12345698765432")
    assert tax_code_check_char("RSSMRA80A01H501") == "U"
    assert luhn_is_valid("4111111111111111")
    assert not luhn_is_valid("4111111111111112")


@pytest.mark.parametrize("country", sorted(BBAN_LENGTHS))
def test_ibans_are_well_formed_but_invalid(country: str) -> None:
    """IBANs match the structural pattern and fail even the bare mod-97 checksum.

    Args:
        country: Country of the generated IBANs.
    """
    rng, adapter = random.Random(country), TypeAdapter(Iban)
    for _ in range(SAMPLES):
        iban = adapter.validate_python(fake_iban(rng, country))
        assert iban.startswith(country)
        assert not iban_mod97_ok(iban)


def test_tax_codes_have_a_wrong_check_character() -> None:
    """Tax codes are structurally valid, but their 16th character is never the right one."""
    rng, adapter = random.Random(0), TypeAdapter(TaxCode)
    for _ in range(SAMPLES):
        birth = date(rng.randint(1950, 2005), rng.randint(1, 12), rng.randint(1, 28))
        names = rng.choice((("Anna", "Verdi"), ("Luca", "De Luca"), ("Niccolò", "D'Angelo")))
        code = adapter.validate_python(fake_tax_code(*names, birth, rng.random() < 0.5, "F205"))
        assert code[15] != tax_code_check_char(code[:15])


def test_vat_numbers_fail_the_check_digit() -> None:
    """VAT numbers have eleven digits and a wrong check digit."""
    rng, adapter = random.Random(0), TypeAdapter(VatNumber)
    for _ in range(SAMPLES):
        assert not luhn_is_valid(adapter.validate_python(fake_vat_number(rng)))


def test_card_numbers_fail_luhn_and_are_stored_masked() -> None:
    """Full card numbers fail the Luhn check, and only the last four digits survive masking."""
    rng, adapter = random.Random(0), TypeAdapter(MaskedPan)
    for _ in range(SAMPLES):
        pan = fake_pan(rng)
        assert not luhn_is_valid(pan)
        assert adapter.validate_python(mask_pan(pan)).endswith(pan[-4:])
