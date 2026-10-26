"""Noise operations that make descriptions harder to read, like real ones.

Each operation receives a description template and a purpose text and returns both, changed or
not. Placeholders such as `{name}` and `{iban}` are never altered.
"""

import random
from collections.abc import Callable

type NoiseOperation = Callable[[random.Random, str, str], tuple[str, str]]

ABBREVIATIONS = {  # Short forms used by payment systems and by hurried customers
    "BONIFICO": "BONIF.",
    "CAUSALE": "CAUS.",
    "ORDINANTE": "ORD.",
    "BENEFICIARIO": "BEN.",
    "FATTURA": "FATT.",
    "PAGAMENTO": "PAG.",
    "STIPENDIO": "STIP.",
    "ACCREDITO": "ACCR.",
    "DISPOSIZIONE": "DISP.",
    "CREDITORE": "CRED.",
    "PRESTITO": "PREST.",
}


def abbreviate(rng: random.Random, template: str, purpose: str) -> tuple[str, str]:
    """Replace known words with their short forms.

    Args:
        rng: Unused; keeps the noise operation signature.
        template: Description template.
        purpose: Purpose text.

    Returns:
        Updated template and purpose.
    """
    return _shorten(template), _shorten(purpose)


def lowercase(rng: random.Random, template: str, purpose: str) -> tuple[str, str]:
    """Lowercase the fixed words and the purpose.

    Args:
        rng: Unused; keeps the noise operation signature.
        template: Description template; placeholders are already lowercase.
        purpose: Purpose text.

    Returns:
        Updated template and purpose.
    """
    return template.lower(), purpose.lower()


def typo(rng: random.Random, template: str, purpose: str) -> tuple[str, str]:
    """Swap two adjacent letters in one word of the purpose.

    Args:
        rng: Seeded random source.
        template: Description template, unchanged.
        purpose: Purpose text.

    Returns:
        Template and updated purpose.
    """
    words = purpose.split(" ")
    candidates = [i for i, word in enumerate(words) if len(word) >= 4 and word.isalpha()]
    if not candidates:
        return template, purpose
    index = rng.choice(candidates)
    word, cut = words[index], rng.randrange(len(words[index]) - 1)
    words[index] = word[:cut] + word[cut + 1] + word[cut] + word[cut + 2 :]
    return template, " ".join(words)


def truncate(rng: random.Random, template: str, purpose: str) -> tuple[str, str]:
    """Drop the second half of the purpose, as fixed-length fields do.

    Args:
        rng: Unused; keeps the noise operation signature.
        template: Description template, unchanged.
        purpose: Purpose text.

    Returns:
        Template and updated purpose.
    """
    words = purpose.split(" ")
    return template, " ".join(words[: max(1, len(words) // 2)])


def _shorten(text: str) -> str:
    """Abbreviate every known word in a text.

    Args:
        text: Text made of space-separated words.

    Returns:
        Text with short forms.
    """
    return " ".join(ABBREVIATIONS.get(word, word) for word in text.split(" "))


NOISE_OPERATIONS: tuple[NoiseOperation, ...] = (abbreviate, lowercase, typo, truncate)  # In order
