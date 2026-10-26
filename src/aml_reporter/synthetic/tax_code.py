"""Synthetic Italian personal tax codes (codice fiscale) with a wrong check character."""

from datetime import date

from .checks import tax_code_check_char
from .text import fold

MONTH_LETTERS = "ABCDEHLMPRST"  # Month codes of Italian tax codes, January to December
VOWELS = frozenset("AEIOU")  # Vowels, which follow consonants in name codes
FEMALE_DAY_OFFSET = 40  # Added to the birth day of women in Italian tax codes


def fake_tax_code(
    first_name: str, last_name: str, birth_date: date, female: bool, municipality: str
) -> str:
    """Build a structurally correct tax code whose check character is always wrong.

    Args:
        first_name: Given name.
        last_name: Family name.
        birth_date: Date of birth.
        female: Whether the person is a woman.
        municipality: Four-character code of the municipality of birth.

    Returns:
        16-character tax code.
    """
    day = birth_date.day + (FEMALE_DAY_OFFSET if female else 0)
    body = (
        _surname_code(last_name)
        + _name_code(first_name)
        + f"{birth_date.year % 100:02d}"
        + MONTH_LETTERS[birth_date.month - 1]
        + f"{day:02d}"
        + municipality
    )
    correct = tax_code_check_char(body)
    return body + chr(ord("A") + (ord(correct) - ord("A") + 1) % 26)


def _surname_code(surname: str) -> str:
    """Encode a family name: consonants first, then vowels, padded with X.

    Args:
        surname: Family name.

    Returns:
        Three-letter code.
    """
    consonants, vowels = _split_letters(surname)
    return (consonants + vowels + "XXX")[:3]


def _name_code(name: str) -> str:
    """Encode a given name; with four or more consonants, the second one is skipped.

    Args:
        name: Given name.

    Returns:
        Three-letter code.
    """
    consonants, vowels = _split_letters(name)
    if len(consonants) >= 4:
        return consonants[0] + consonants[2] + consonants[3]
    return (consonants + vowels + "XXX")[:3]


def _split_letters(text: str) -> tuple[str, str]:
    """Separate the consonants and vowels of a name, ignoring accents and symbols.

    Args:
        text: Name to split.

    Returns:
        Consonants and vowels, each in original order.
    """
    letters = [char for char in fold(text) if "A" <= char <= "Z"]
    consonants = "".join(char for char in letters if char not in VOWELS)
    vowels = "".join(char for char in letters if char in VOWELS)
    return consonants, vowels
