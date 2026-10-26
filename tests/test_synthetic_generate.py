"""Generated cases are reproducible, privacy-safe, and labelled consistently."""

import re
from pathlib import Path

import pytest

from aml_reporter.models import (
    BusinessCustomer,
    Direction,
    IndividualCustomer,
    Outcome,
    TransactionType,
)
from aml_reporter.synthetic import SCENARIOS, GeneratedCase, generate_cases, write_cases
from aml_reporter.synthetic.checks import iban_mod97_ok, luhn_is_valid, tax_code_check_char

SEED = 42  # Seed of the committed sample data
IBAN_IN_TEXT = re.compile(r"\b[A-Z]{2}\d{2}[A-Z0-9]{11,30}\b")  # Any IBAN-looking token
LABELLED_TYPES = {TransactionType.WIRE_TRANSFER, TransactionType.DIRECT_DEBIT}  # Have free text
EXPECTED_OUTCOMES = {  # Scenario table published in the README
    "fp_salary_bonus": Outcome.CLOSE,
    "fp_property_sale": Outcome.CLOSE,
    "structuring_cash": Outcome.ESCALATE,
    "pass_through": Outcome.ESCALATE,
    "dormant_reactivation": Outcome.ESCALATE,
    "profile_mismatch": Outcome.REQUEST_INFORMATION,
}
ALERTED_KINDS = {  # (type, direction) of the alerted transaction per scenario
    "fp_salary_bonus": (TransactionType.WIRE_TRANSFER, Direction.INBOUND),
    "fp_property_sale": (TransactionType.WIRE_TRANSFER, Direction.INBOUND),
    "structuring_cash": (TransactionType.CASH_DEPOSIT, Direction.INBOUND),
    "pass_through": (TransactionType.WIRE_TRANSFER, Direction.OUTBOUND),
    "dormant_reactivation": (TransactionType.WIRE_TRANSFER, Direction.INBOUND),
    "profile_mismatch": (TransactionType.WIRE_TRANSFER, Direction.INBOUND),
}


@pytest.fixture(scope="module")
def cases() -> list[GeneratedCase]:
    """Generate every scenario once for the whole module.

    Returns:
        One generated case per scenario.
    """
    return generate_cases(list(SCENARIOS), SEED)


def test_scenarios_match_the_readme(cases: list[GeneratedCase]) -> None:
    """Each scenario has the expected outcome and alerts on the expected kind of transaction."""
    for case in cases:
        scenario = case.labels.scenario
        assert case.labels.expected_outcome is EXPECTED_OUTCOMES[scenario]
        alerted = next(
            tx
            for tx in case.bundle.transactions
            if tx.transaction_id == case.bundle.alert.transaction_id
        )
        assert (alerted.transaction_type, alerted.direction) == ALERTED_KINDS[scenario]


def test_same_seed_writes_identical_files(tmp_path: Path) -> None:
    """Two runs with the same seed produce byte-identical files; another seed does not."""
    first = write_cases(generate_cases(list(SCENARIOS), SEED), tmp_path / "a")
    second = write_cases(generate_cases(list(SCENARIOS), SEED), tmp_path / "b")
    other = write_cases(generate_cases(list(SCENARIOS), SEED + 1), tmp_path / "c")
    assert [path.read_bytes() for path in first] == [path.read_bytes() for path in second]
    assert [path.read_bytes() for path in first] != [path.read_bytes() for path in other]


def test_case_does_not_depend_on_the_selection(cases: list[GeneratedCase]) -> None:
    """A scenario generated alone equals the same scenario generated with all the others."""
    alone = generate_cases(["pass_through"], SEED)[0]
    together = next(case for case in cases if case.labels.scenario == "pass_through")
    assert alone == together


def test_identifiers_fail_real_world_validation(cases: list[GeneratedCase]) -> None:
    """Every IBAN, tax code, and VAT number in the output fails its check-digit algorithm."""
    for case in cases:
        bundle = case.bundle
        ibans = {account.iban for account in bundle.accounts}
        for tx in bundle.transactions:
            ibans.update(IBAN_IN_TEXT.findall(tx.description))
        assert len(ibans) > 1
        assert not any(iban_mod97_ok(iban) for iban in ibans)
        customer = bundle.customer
        if isinstance(customer, IndividualCustomer):
            assert customer.tax_code[15] != tax_code_check_char(customer.tax_code[:15])
        if isinstance(customer, BusinessCustomer):
            assert not luhn_is_valid(customer.vat_number)


def test_labels_appear_verbatim(cases: list[GeneratedCase]) -> None:
    """Labelled names and IBANs are found, unchanged, in the description they label."""
    for case in cases:
        descriptions = {tx.transaction_id: tx.description for tx in case.bundle.transactions}
        for label in case.labels.transactions:
            text = descriptions[label.transaction_id]
            assert label.counterparty_name is not None
            assert label.counterparty_name in text
            assert label.counterparty_iban is None or label.counterparty_iban in text


def test_every_transfer_and_debit_is_labelled(cases: list[GeneratedCase]) -> None:
    """Labels cover exactly the transactions whose free text the LLM will read."""
    for case in cases:
        expected = {
            tx.transaction_id
            for tx in case.bundle.transactions
            if tx.transaction_type in LABELLED_TYPES
        }
        assert {label.transaction_id for label in case.labels.transactions} == expected


def test_dataset_mixes_easy_and_hard_descriptions(cases: list[GeneratedCase]) -> None:
    """Both difficulty levels and every way of hiding the IBAN are represented."""
    labels = [label for case in cases for label in case.labels.transactions]
    assert 0.1 < sum(label.hard for label in labels) / len(labels) < 0.6
    assert any(label.counterparty_iban is None for label in labels)
    assert any(label.counterparty_iban is not None for label in labels)
