"""Synthetic customers: individuals and sole traders."""

from datetime import date, timedelta

from ..models import BusinessCustomer, CustomerKind, IndividualCustomer, RiskRating
from .context import CENT, SynthContext
from .identifiers import fake_vat_number
from .names import CITIES, FEMALE_NAMES, LAST_NAMES, MALE_NAMES, OCCUPATIONS, SOLE_TRADES
from .products import Persona, fictitious_address, open_products
from .tax_code import fake_tax_code


def make_individual(
    ctx: SynthContext,
    case_index: int,
    *,
    birth_years: tuple[int, int] = (1960, 1995),
    occupation: str | None = None,
    income: tuple[int, int] = (22_000, 45_000),
) -> Persona:
    """Create an individual customer.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.
        birth_years: Range of birth years, at most 2005.
        occupation: Declared occupation; random when omitted.
        income: Range of declared annual income in euros.

    Returns:
        The persona.
    """
    rng = ctx.rng
    female = rng.random() < 0.5
    first = rng.choice(FEMALE_NAMES if female else MALE_NAMES).title()
    last = rng.choice(LAST_NAMES).title()
    birth = date(rng.randint(*birth_years), rng.randint(1, 12), rng.randint(1, 28))
    city, postal_code, municipality = rng.choice(CITIES)
    onboarding = date(rng.randint(max(birth.year + 18, 2008), 2023), rng.randint(1, 12), 1)
    annual = ctx.round_money(income[0], income[1], 500)
    customer = IndividualCustomer(
        kind=CustomerKind.INDIVIDUAL,
        customer_id=f"CU-{case_index:06d}",
        first_name=first,
        last_name=last,
        birth_date=birth,
        nationality="IT",
        tax_code=fake_tax_code(first, last, birth, female, municipality),
        occupation=occupation or rng.choice(OCCUPATIONS),
        declared_annual_income=annual,
        residence=fictitious_address(ctx, city, postal_code),
        risk_rating=RiskRating.LOW,
        onboarding_date=onboarding,
    )
    return open_products(ctx, case_index, customer, city, (annual / 13).quantize(CENT))


def make_business(
    ctx: SynthContext, case_index: int, *, turnover: tuple[int, int] = (30_000, 50_000)
) -> Persona:
    """Create a sole trader.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.
        turnover: Range of declared annual turnover in euros.

    Returns:
        The persona.
    """
    rng = ctx.rng
    trade, sector = rng.choice(SOLE_TRADES)
    owner = f"{rng.choice(MALE_NAMES + FEMALE_NAMES)} {rng.choice(LAST_NAMES)}"
    city, postal_code, _ = rng.choice(CITIES)
    incorporation = date(rng.randint(2005, 2018), rng.randint(1, 12), rng.randint(1, 28))
    declared = ctx.round_money(turnover[0], turnover[1], 1000)
    customer = BusinessCustomer(
        kind=CustomerKind.BUSINESS,
        customer_id=f"CU-{case_index:06d}",
        legal_name=f"{trade} DI {owner}",
        legal_form="sole trader",
        sector=sector,
        vat_number=fake_vat_number(rng),
        incorporation_date=incorporation,
        declared_annual_turnover=declared,
        residence=fictitious_address(ctx, city, postal_code),
        risk_rating=RiskRating.MEDIUM,
        onboarding_date=incorporation + timedelta(days=rng.randint(10, 400)),
    )
    return open_products(ctx, case_index, customer, city, (declared / 12).quantize(CENT))
