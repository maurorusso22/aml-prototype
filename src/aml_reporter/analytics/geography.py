"""Countries involved, read from the country code of counterparty IBANs."""

from collections import defaultdict

from ..models import Direction, Fact, FactCategory, Transaction
from .base import AnalysisContext
from .facts import Facts, euros, ratio, total
from .registry import analyser

COUNTRY_OFFSET = 100  # Per-country facts are numbered from 101, in alphabetical order


@analyser
def geographic_exposure(context: AnalysisContext) -> list[Fact]:
    """Sum flows with accounts outside the customer's country of residence.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-GEO-001 to F-GEO-004, then one F-GEO-1xx fact per foreign country.
    """
    facts = Facts("GEO", FactCategory.GEOGRAPHY)
    home = context.bundle.customer.residence.country
    by_country: dict[str, list[Transaction]] = defaultdict(list)
    for tx in context.bundle.transactions:
        enrichment = context.enrichments.get(tx.transaction_id)
        if enrichment and enrichment.counterparty_iban and enrichment.counterparty_iban[:2] != home:
            by_country[enrichment.counterparty_iban[:2]].append(tx)
    foreign = [tx for group in by_country.values() for tx in group]
    inbound = [tx for tx in foreign if tx.direction is Direction.INBOUND]
    outbound = [tx for tx in foreign if tx.direction is Direction.OUTBOUND]
    countries = sorted(by_country)
    facts.add(
        1,
        "Foreign countries of counterparty accounts",
        ", ".join(countries) or "none",
        None,
        foreign,
    )
    facts.add(2, "Inflows from foreign accounts", euros(total(inbound)), "EUR", inbound)
    facts.add(3, "Outflows to foreign accounts", euros(total(outbound)), "EUR", outbound)
    share = ratio(total(outbound), total(context.flows(Direction.OUTBOUND)))
    facts.add(4, "Share of outflows going abroad", share, "ratio", outbound)
    for number, country in enumerate(countries, start=COUNTRY_OFFSET + 1):
        flows = by_country[country]
        facts.add(number, f"Flows with accounts in {country}", euros(total(flows)), "EUR", flows)
    return facts.items
