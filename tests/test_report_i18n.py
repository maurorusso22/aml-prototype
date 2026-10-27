"""Report wording: number formats per language, and Italian catalogue completeness."""

import pytest

from aml_reporter.analytics import build_fact_sheet
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import Fact, FactCategory
from aml_reporter.report.catalogs import _read, load_catalog
from aml_reporter.report.i18n import COUNTRY_FACT
from aml_reporter.rules import load_rules
from aml_reporter.synthetic import SCENARIOS, generate_cases


def fact(value: bool | int | float | str, unit: str | None = None) -> Fact:
    """Build a throwaway fact for formatting tests.

    Args:
        value: Fact value.
        unit: Unit of measure.

    Returns:
        The fact.
    """
    return Fact(id="F-TEST-001", category=FactCategory.ALERT, label="x", value=value, unit=unit)


@pytest.mark.parametrize(
    ("value", "unit", "english", "italian"),
    [
        (9346.91, "EUR", "€9,346.91", "9.346,91 €"),
        (-14490.89, "EUR", "-€14,490.89", "-14.490,89 €"),
        (0.819, "ratio", "81.9%", "81,9%"),
        (2.9706, "times", "2.97×", "2,97×"),
        (13, "days", "13 days", "13 giorni"),
        (11.3, "years", "11.3 years", "11,3 anni"),
        (1234, "count", "1,234", "1.234"),
        ("inbound cash deposit", None, "inbound cash deposit", "versamento di contanti"),
        ("high", None, "high", "alto"),
    ],
)
def test_values_are_written_per_language(
    value: float | str, unit: str | None, english: str, italian: str
) -> None:
    """Separators, currency position, units, and known words follow each language.

    Args:
        value: Fact value.
        unit: Unit of measure.
        english: Expected English text.
        italian: Expected Italian text.
    """
    assert load_catalog("en").value(fact(value, unit)) == english
    assert load_catalog("it").value(fact(value, unit)) == italian


def test_italian_catalogue_covers_every_text_key() -> None:
    """Every English sentence and heading has an Italian translation."""
    assert set(_read("en")["text"]) <= set(_read("it")["text"])


def test_italian_catalogue_covers_every_fact_and_rule() -> None:
    """Every fact the analysers produce and every rule has an Italian name."""
    italian = load_catalog("it")
    ids = set()
    for case in generate_cases(list(SCENARIOS), 42):
        enrichments = BaselineEnricher().enrich(case.bundle.transactions)
        ids |= {f.id for f in build_fact_sheet(case.bundle, enrichments).facts}
    missing = sorted(i for i in ids if i not in italian.facts and not COUNTRY_FACT.match(i))
    assert not missing
    for rule in load_rules().rules:
        assert {"name", "description"} <= set(italian.rules[rule.id])


def test_country_facts_are_translated_with_their_country() -> None:
    """Per-country facts keep the country code inside the translated label."""
    country_fact = Fact(
        id="F-GEO-101",
        category=FactCategory.GEOGRAPHY,
        label="Flows with accounts in LT",
        value=1.0,
    )
    assert load_catalog("it").label(country_fact) == "Flussi con conti in LT"
