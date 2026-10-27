"""Load the wording of each report language from the packaged TOML catalogues."""

import tomllib
from functools import cache
from importlib.resources import files
from typing import Any

from .i18n import Catalog

LANGUAGES = ("en", "it")  # Report languages with a catalogue


@cache
def load_catalog(lang: str) -> Catalog:
    """Read the catalogue of one language, completing it with English where it is silent.

    Args:
        lang: One of `LANGUAGES`.

    Returns:
        The catalogue.
    """
    english, own = _read("en"), _read(lang)
    return Catalog(
        lang=lang,
        text={**english.get("text", {}), **own.get("text", {})},
        facts=own.get("facts", {}),
        values={**english.get("values", {}), **own.get("values", {})},
        rules=own.get("rules", {}),
    )


def _read(lang: str) -> dict[str, Any]:
    """Parse a packaged locale file.

    Args:
        lang: Language code.

    Returns:
        The parsed TOML document.
    """
    path = files("aml_reporter.report").joinpath("locales", f"{lang}.toml")
    return tomllib.loads(path.read_text("utf-8"))
