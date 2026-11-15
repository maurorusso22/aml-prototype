"""Report wording per language, and how numbers, dates, and fact values are written.

English labels come from the facts themselves; other languages translate them by fact id.
"""

import re
from dataclasses import dataclass
from datetime import date

from ..models import Fact, FactStatus

COUNTRY_FACT = re.compile(r"^F-GEO-1\d\d$")  # Per-country facts, whose label embeds the country


@dataclass(frozen=True)
class Catalog:
    """Every string the report writes in one language."""

    lang: str
    text: dict[str, str]
    facts: dict[str, str]
    values: dict[str, str]
    rules: dict[str, dict[str, str]]

    def t(self, key: str, **fields: object) -> str:
        """Look up a sentence or heading and fill its placeholders.

        Args:
            key: Entry of the `[text]` table.
            **fields: Values for the placeholders.

        Returns:
            The localised text.
        """
        return self.text[key].format(**fields)

    def label(self, fact: Fact) -> str:
        """Name a fact in the report language.

        Args:
            fact: Fact to name.

        Returns:
            The translated label, or the original English one.
        """
        if COUNTRY_FACT.match(fact.id) and "F-GEO-1xx" in self.facts:
            return self.facts["F-GEO-1xx"].format(country=fact.label.split()[-1])
        return self.facts.get(fact.id, fact.label)

    def word(self, value: str) -> str:
        """Translate a known word, such as a risk level or a transaction kind.

        Args:
            value: Word as stored in the data.

        Returns:
            The translation, or the word itself when unknown.
        """
        return self.values.get(value, value)

    def rule(self, rule_id: str, field: str, default: str) -> str:
        """Translate the name or description of a red-flag rule.

        Args:
            rule_id: Rule identifier.
            field: `name` or `description`.
            default: Text from the rule file, used when no translation exists.

        Returns:
            The localised text.
        """
        return self.rules.get(rule_id, {}).get(field, default)

    def number(self, value: float, decimals: int = 0) -> str:
        """Write a number with the language's separators.

        Args:
            value: Number to write.
            decimals: Digits after the decimal separator.

        Returns:
            Text such as `9,346.91` in English or `9.346,91` in Italian.
        """
        text = f"{value:,.{decimals}f}"
        if self.text["decimal_separator"] == ",":
            text = text.replace(",", "\0").replace(".", ",").replace("\0", ".")
        return text

    def money(self, amount: float) -> str:
        """Write an amount in euros.

        Args:
            amount: Amount in euros.

        Returns:
            The amount with its currency, in the language's style.
        """
        text = self.t("money", amount=self.number(abs(amount), 2))
        return f"-{text}" if amount < 0 else text

    def date(self, day: date) -> str:
        """Write a date in the language's style.

        Args:
            day: Date to write.

        Returns:
            The formatted date.
        """
        return day.strftime(self.text["date_format"])

    def value(self, fact: Fact) -> str:
        """Write a fact value with its unit.

        Args:
            fact: Fact to write.

        Returns:
            Text such as `€9,346.91`, `81.9%`, `2.97×`, or `13 days`; for a fact without a
            value, the localised reason, such as `n/a (no activity)`.
        """
        value, unit = fact.value, fact.unit
        if fact.status is not FactStatus.MEASURED or value is None:
            return self.word(str(fact.status))
        if isinstance(value, bool):
            return self.word("yes" if value else "no")
        if isinstance(value, str):
            return self.word(value)
        if unit == "EUR":
            return self.money(value)
        if unit == "ratio":
            return self.number(value * 100, 1) + "%"
        if unit == "times":
            return self.number(value, 2) + "×"
        if unit in ("days", "years"):
            return self.t(unit, n=self.number(value, 1 if unit == "years" else 0))
        return self.number(value, 0 if float(value).is_integer() else 2)
