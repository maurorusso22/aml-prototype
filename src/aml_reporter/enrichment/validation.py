"""Checks applied to every LLM answer before it is trusted.

The schema already guarantees types and label sets; these checks catch what a schema cannot,
above all values the model invented instead of reading them from the text.
"""

import re

from pydantic import TypeAdapter, ValidationError

from ..models.formats import Iban

IBAN_FORMAT = TypeAdapter(Iban)  # Structural IBAN check shared with the domain model
NO_VALUE = frozenset({"", "null", "none", "n/a"})  # How small models write null as text


class InvalidAnswerError(ValueError):
    """An LLM answer that breaks a validation rule."""


def check_iban(value: object, text: str) -> str | None:
    """Accept an IBAN only if it is well-formed and present in the description.

    Check digits are not verified: synthetic IBANs are invalid on purpose.

    Args:
        value: IBAN returned by the model, or None.
        text: Description the IBAN was extracted from.

    Returns:
        The IBAN without spaces, or None.

    Raises:
        InvalidAnswerError: When the IBAN is malformed or not in the text.
    """
    if _absent(value):
        return None
    if not isinstance(value, str):
        raise InvalidAnswerError("IBAN is not text")
    compact = value.replace(" ", "")
    try:
        IBAN_FORMAT.validate_python(compact)
    except ValidationError as error:
        raise InvalidAnswerError("IBAN has an invalid structure") from error
    if compact not in text.replace(" ", ""):
        raise InvalidAnswerError("IBAN does not appear in the description")
    return compact


def check_name(value: object, text: str) -> str | None:
    """Accept a counterparty name only if it appears in the description.

    The match ignores case and spacing, and the name is returned as written in the text.

    Args:
        value: Name returned by the model, or None.
        text: Description the name was extracted from.

    Returns:
        The name exactly as it appears in the text, or None.

    Raises:
        InvalidAnswerError: When the name is not text or not in the text.
    """
    if _absent(value):
        return None
    if not isinstance(value, str):
        raise InvalidAnswerError("counterparty name is not text")
    pattern = r"\s+".join(re.escape(word) for word in value.split())
    match = re.search(pattern, text, re.IGNORECASE)
    if match is None:
        raise InvalidAnswerError("counterparty name does not appear in the description")
    return match.group()


def _absent(value: object) -> bool:
    """Tell whether an answer means "no value", as null or as text like "null" or "".

    Args:
        value: Answer returned by the model.

    Returns:
        True when the answer carries no value.
    """
    return value is None or (isinstance(value, str) and value.strip().lower() in NO_VALUE)


def check_label(value: object, text: str) -> object:
    """Accept a label as is: the schema has already restricted it to the allowed set.

    Args:
        value: Label returned by the model.
        text: Unused; keeps the check signature.

    Returns:
        The label.
    """
    return value
