"""Text normalisation shared by the generators."""

import unicodedata


def fold(text: str) -> str:
    """Convert text to uppercase ASCII, as payment systems print names.

    Args:
        text: Any text, possibly with accents.

    Returns:
        Uppercase text without diacritics.
    """
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().upper()
