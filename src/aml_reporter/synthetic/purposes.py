"""Free-text payment purposes, as a customer would type them in a transfer."""

import random
from datetime import date

from ..models import PaymentPurpose

MONTHS = (  # Italian month names, as they appear in descriptions
    "GENNAIO",
    "FEBBRAIO",
    "MARZO",
    "APRILE",
    "MAGGIO",
    "GIUGNO",
    "LUGLIO",
    "AGOSTO",
    "SETTEMBRE",
    "OTTOBRE",
    "NOVEMBRE",
    "DICEMBRE",
)
PURPOSE_TEXTS = {  # Templates per purpose; placeholders are filled at random
    PaymentPurpose.SALARY: (
        "STIPENDIO {month}",
        "STIPENDIO MESE DI {month} {year}",
        "EMOLUMENTI {month}",
        "RETRIBUZIONE {month} {year}",
    ),
    PaymentPurpose.RENT: (
        "CANONE LOCAZIONE {month}",
        "AFFITTO {month}",
        "AFFITTO APPARTAMENTO {month} {year}",
        "PIGIONE {month}",
    ),
    PaymentPurpose.INVOICE: (
        "SALDO FATTURA {n}",
        "PAGAMENTO FATTURA N. {n}",
        "FATTURA {n} DEL {day}/{mm}/{year}",
        "BOLLETTA {month} {year}",
    ),
    PaymentPurpose.LOAN: (
        "RATA PRESTITO {n}",
        "RIMBORSO PRESTITO",
        "RESTITUZIONE PRESTITO",
        "RATA FINANZIAMENTO {n}",
    ),
    PaymentPurpose.FAMILY_SUPPORT: (
        "AIUTO FAMILIARE",
        "PER LE SPESE DI CASA",
        "REGALO",
        "CONTRIBUTO MENSILE {month}",
    ),
    PaymentPurpose.OTHER: (
        "RIMBORSO SPESE",
        "QUOTA ASSOCIATIVA {year}",
        "CAUZIONE",
        "ACQUISTO AUTO",
    ),
    PaymentPurpose.UNKNOWN: ("RIF. {n}", "VS DISPOSIZIONE", "{n}", ""),
}


def purpose_text(rng: random.Random, purpose: PaymentPurpose, day: date) -> str:
    """Write the purpose of a payment the way a customer would.

    Args:
        rng: Seeded random source.
        purpose: Ground-truth purpose.
        day: Booking date, used for months and invoice dates.

    Returns:
        Purpose text, possibly empty.
    """
    return rng.choice(PURPOSE_TEXTS[purpose]).format(
        month=MONTHS[day.month - 1],
        year=day.year,
        mm=f"{day.month:02d}",
        day=f"{day.day:02d}",
        n=rng.randint(10, 9999),
    )
