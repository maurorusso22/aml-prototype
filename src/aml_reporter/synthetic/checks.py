"""Real-world check-digit algorithms.

The generator uses them to make sure every synthetic identifier is invalid, and the tests use
them to prove it.
"""

TAX_CODE_ODD_VALUES = dict(  # Values of characters in odd positions of an Italian tax code
    zip(
        "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ",
        (1, 0, 5, 7, 9, 13, 15, 17, 19, 21, 1, 0, 5, 7, 9, 13, 15, 17, 19, 21)
        + (2, 4, 18, 20, 11, 3, 6, 8, 12, 14, 16, 10, 22, 25, 24, 23),
        strict=True,
    )
)


def iban_mod97_ok(iban: str) -> bool:
    """Run the ISO 7064 mod-97 checksum on an IBAN.

    Args:
        iban: IBAN without spaces.

    Returns:
        True when the checksum holds.
    """
    rearranged = iban[4:] + iban[:4]
    return int("".join(str(int(char, 36)) for char in rearranged)) % 97 == 1


def iban_is_valid(iban: str) -> bool:
    """Validate IBAN check digits as a bank would: allowed range and mod-97 checksum.

    The range matters: digits `00` pass the bare checksum whenever the correct ones are `97`.

    Args:
        iban: IBAN without spaces.

    Returns:
        True when the check digits are correct.
    """
    return "02" <= iban[2:4] <= "98" and iban_mod97_ok(iban)


def tax_code_check_char(body: str) -> str:
    """Compute the check character of an Italian personal tax code (codice fiscale).

    Args:
        body: First 15 characters of the tax code.

    Returns:
        The correct 16th character.
    """
    total = 0
    for position, char in enumerate(body):
        if position % 2 == 0:
            total += TAX_CODE_ODD_VALUES[char]
        else:
            total += int(char) if char.isdigit() else ord(char) - ord("A")
    return chr(ord("A") + total % 26)


def luhn_is_valid(number: str) -> bool:
    """Check a number with the Luhn algorithm, used by card numbers and Italian VAT numbers.

    Args:
        number: Digits only.

    Returns:
        True when the last digit is the correct check digit.
    """
    total = 0
    for position, char in enumerate(reversed(number)):
        digit = int(char)
        if position % 2 == 1:
            digit = digit * 2 - 9 if digit > 4 else digit * 2
        total += digit
    return total % 10 == 0


def luhn_check_digit(partial: str) -> str:
    """Compute the digit that makes a number Luhn-valid.

    Args:
        partial: All digits except the check digit.

    Returns:
        The correct check digit.
    """
    return next(digit for digit in "0123456789" if luhn_is_valid(partial + digit))
