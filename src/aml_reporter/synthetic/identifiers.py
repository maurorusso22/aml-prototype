"""Synthetic account, company, and card identifiers, invalid by construction.

Each generator computes the real check value and then uses a different one, so no synthetic
identifier can ever match a real company, account, or card.
"""

import random
import string

from .checks import iban_mod97_ok, luhn_check_digit

FICTITIOUS_BANK_CODE = "99999"  # Italian bank code (ABI) used in every synthetic Italian IBAN
INVALID_IBAN_CHECK = "00"  # Check digits no real IBAN can have: valid values are 02 to 98
BBAN_LENGTHS = {  # National account number length per country used by the generator
    "IT": 23,
    "DE": 18,
    "FR": 23,
    "ES": 20,
    "NL": 14,
    "LT": 16,
    "CY": 24,
    "AE": 19,
}
PAN_PREFIX = "999999"  # Card issuer prefix outside the ranges of the major card schemes


def fake_iban(rng: random.Random, country: str = "IT") -> str:
    """Generate an IBAN with impossible check digits and a fictitious bank code.

    Digits `00` still pass the bare mod-97 checksum about once in 97 draws, so those
    account numbers are drawn again: every IBAN fails both the range rule and the checksum.

    Args:
        rng: Seeded random source.
        country: ISO 3166-1 alpha-2 code, one of `BBAN_LENGTHS`.

    Returns:
        IBAN without spaces.
    """
    while True:
        if country == "IT":
            cin = rng.choice(string.ascii_uppercase)
            bban = cin + FICTITIOUS_BANK_CODE + _digits(rng, BBAN_LENGTHS["IT"] - 6)
        else:
            bban = "9999" + _digits(rng, BBAN_LENGTHS[country] - 4)
        iban = f"{country}{INVALID_IBAN_CHECK}{bban}"
        if not iban_mod97_ok(iban):
            return iban


def fake_vat_number(rng: random.Random) -> str:
    """Generate an 11-digit Italian VAT number with a wrong check digit.

    Args:
        rng: Seeded random source.

    Returns:
        VAT number (partita IVA).
    """
    partial = _digits(rng, 10)
    return partial + _wrong_digit(luhn_check_digit(partial))


def fake_pan(rng: random.Random) -> str:
    """Generate a 16-digit card number with a wrong check digit.

    Only its masked form is ever stored; the full number exists so tests can verify it.

    Args:
        rng: Seeded random source.

    Returns:
        Full card number.
    """
    partial = PAN_PREFIX + _digits(rng, 9)
    return partial + _wrong_digit(luhn_check_digit(partial))


def mask_pan(pan: str) -> str:
    """Hide every digit of a card number except the last four.

    Args:
        pan: Full card number.

    Returns:
        Masked card number, e.g. `**** **** **** 1234`.
    """
    return f"**** **** **** {pan[-4:]}"


def _wrong_digit(correct: str) -> str:
    """Pick a digit guaranteed to differ from the correct one.

    Args:
        correct: The correct check digit.

    Returns:
        A different digit.
    """
    return str((int(correct) + 1) % 10)


def _digits(rng: random.Random, count: int) -> str:
    """Draw random decimal digits.

    Args:
        rng: Seeded random source.
        count: How many digits to draw.

    Returns:
        String of digits.
    """
    return "".join(rng.choice(string.digits) for _ in range(count))
