"""A synthetic customer's banking products: one current account and one debit card."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..models import Address, BusinessCustomer, Card, CardType, IndividualCustomer
from .context import SynthContext
from .identifiers import fake_iban, fake_pan, mask_pan
from .names import STREETS


@dataclass(frozen=True)
class Persona:
    """A synthetic customer together with the products a case needs."""

    case_index: int
    customer: IndividualCustomer | BusinessCustomer
    account_id: str
    iban: str
    opened_on: date
    card: Card
    city: str
    monthly_income: Decimal


def open_products(
    ctx: SynthContext,
    case_index: int,
    customer: IndividualCustomer | BusinessCustomer,
    city: str,
    monthly_income: Decimal,
) -> Persona:
    """Open an account and issue a debit card for a new customer.

    Args:
        ctx: Generation context.
        case_index: Case number, used to build identifiers.
        customer: The customer.
        city: City of residence, printed in card descriptions.
        monthly_income: Typical monthly inflow in euros.

    Returns:
        The persona.
    """
    account_id = f"AC-{case_index:04d}01"
    issued = date(2024, ctx.rng.randint(1, 12), 1)
    card = Card(
        card_id=f"CA-{case_index:04d}01",
        account_id=account_id,
        card_type=CardType.DEBIT,
        masked_pan=mask_pan(fake_pan(ctx.rng)),
        issued_on=issued,
        expires_on=issued.replace(year=issued.year + 5),
    )
    iban = fake_iban(ctx.rng)
    opened_on = customer.onboarding_date
    return Persona(case_index, customer, account_id, iban, opened_on, card, city, monthly_income)


def fictitious_address(ctx: SynthContext, city: str, postal_code: str) -> Address:
    """Draw an address on a fictitious street of a real city.

    Args:
        ctx: Generation context.
        city: City name.
        postal_code: Postal code of the city.

    Returns:
        The address.
    """
    street = f"{ctx.rng.choice(STREETS).title()} {ctx.rng.randint(1, 180)}"
    return Address(street=street, city=city, postal_code=postal_code, country="IT")
