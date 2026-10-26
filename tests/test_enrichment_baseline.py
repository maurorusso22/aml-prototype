"""The rule-based baseline: correct on clean text, limited on noisy text."""

import pytest

from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.enrichment.rules import (
    classify_counterparty,
    classify_purpose,
    extract_counterparty,
)
from aml_reporter.models import CounterpartyType, EnrichmentSource, PaymentPurpose
from aml_reporter.synthetic import GeneratedCase


@pytest.mark.parametrize(
    ("text", "name"),
    [
        ("BONIFICO SEPA DA ACME SRL IBAN IT00X9999901234000000123456 CAUSALE X", "ACME SRL"),
        ("BONIF. A FAVORE DI ROSSI ANNA CAUS. AFFITTO", "ROSSI ANNA"),
        ("ADDEBITO DIRETTO CRED. NOVA SPA MANDATO MND123456 BOLLETTA", "NOVA SPA"),
        ("AFFITTO GIUGNO ROSSI ANNA IT00B9999905678000000654321", None),
    ],
)
def test_counterparty_rules(text: str, name: str | None) -> None:
    """Names are found after a field label; without a label the rules give up.

    Args:
        text: Description.
        name: Expected extraction.
    """
    assert extract_counterparty(text) == name


def test_type_and_purpose_rules() -> None:
    """Legal forms mark companies; keywords mark purposes; typos defeat keywords."""
    assert classify_counterparty("ATLAS TRADING UAB") is CounterpartyType.LEGAL_PERSON
    assert classify_counterparty("G. ESEMPIO") is CounterpartyType.NATURAL_PERSON
    assert classify_purpose("CAUS. STIP. MAGGIO") is PaymentPurpose.SALARY
    assert classify_purpose("rimborso prestito") is PaymentPurpose.LOAN
    assert classify_purpose("STIEPNDIO MAGGIO") is PaymentPurpose.UNKNOWN


def test_baseline_covers_every_labelled_transaction(pass_through_case: GeneratedCase) -> None:
    """One baseline enrichment per transfer or debit, with every shown IBAN found."""
    enrichments = BaselineEnricher().enrich(pass_through_case.bundle.transactions)
    labels = {label.transaction_id: label for label in pass_through_case.labels.transactions}
    assert [enrichment.transaction_id for enrichment in enrichments] == list(labels)
    for enrichment in enrichments:
        assert enrichment.source is EnrichmentSource.BASELINE
        assert enrichment.counterparty_iban == labels[enrichment.transaction_id].counterparty_iban
