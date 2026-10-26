"""Counterparties: the people and companies a customer transacts with.

Company names are assembled from invented words; any match with a real company is coincidental.
"""

from dataclasses import dataclass

from ..models import CounterpartyType
from .context import SynthContext
from .identifiers import fake_iban
from .names import FEMALE_NAMES, LAST_NAMES, MALE_NAMES

BRAND_WORDS = (  # Invented brand-like words for company names
    "ACME",
    "ALFA",
    "NOVA",
    "DELTA",
    "ORION",
    "VEGA",
    "ZENIT",
    "ARGO",
    "ATLAS",
    "LUMEN",
)
ITALIAN_SECTORS = (  # Activity words in Italian company names
    "LOGISTICA",
    "SERVIZI",
    "IMPIANTI",
    "COSTRUZIONI",
    "TRASPORTI",
    "TECNOLOGIE",
    "ALIMENTARI",
)
FOREIGN_SECTORS = ("TRADING", "CONSULTING", "LOGISTICS", "HOLDING", "SERVICES")  # Same, abroad
LEGAL_FORMS = {  # Company suffixes per country
    "IT": ("SRL", "SPA", "SNC", "SAS"),
    "DE": ("GMBH",),
    "FR": ("SARL", "SAS"),
    "ES": ("SL", "SA"),
    "NL": ("BV",),
    "LT": ("UAB",),
    "CY": ("LTD",),
    "AE": ("LLC", "FZE"),
}
FOREIGN_COUNTRIES = ("DE", "FR", "ES", "NL", "LT", "CY", "AE")  # Countries of foreign parties


@dataclass(frozen=True)
class Party:
    """A counterparty as it appears in descriptions, with its ground-truth type."""

    name: str
    iban: str
    kind: CounterpartyType


def person(ctx: SynthContext, *, country: str = "IT", last_name: str | None = None) -> Party:
    """Create a natural person, written in one of the ways payment systems print names.

    Args:
        ctx: Generation context.
        country: Country of the person's bank account.
        last_name: Family name to reuse, e.g. for relatives.

    Returns:
        The new counterparty.
    """
    first = ctx.rng.choice(MALE_NAMES + FEMALE_NAMES)
    last = (last_name or ctx.rng.choice(LAST_NAMES)).upper()
    name = ctx.rng.choice((f"{first} {last}", f"{last} {first}", f"{first[0]}. {last}"))
    return Party(name, fake_iban(ctx.rng, country), CounterpartyType.NATURAL_PERSON)


def company(ctx: SynthContext, *, country: str = "IT", sector: str | None = None) -> Party:
    """Create a company with an invented name.

    Args:
        ctx: Generation context.
        country: Country of the company and of its bank account.
        sector: Activity word to use instead of a random one.

    Returns:
        The new counterparty.
    """
    sectors = ITALIAN_SECTORS if country == "IT" else FOREIGN_SECTORS
    words = (
        ctx.rng.choice(BRAND_WORDS),
        sector or ctx.rng.choice(sectors),
        ctx.rng.choice(LEGAL_FORMS[country]),
    )
    return Party(" ".join(words), fake_iban(ctx.rng, country), CounterpartyType.LEGAL_PERSON)
