"""Small Markdown helpers for the evaluation report."""

from collections.abc import Iterable, Sequence

TASK_NAMES = {  # Task names as shown in the report, in reporting order
    "iban": "IBAN",
    "counterparty": "Counterparty",
    "counterparty_type": "Natural or legal person",
    "payment_purpose": "Payment purpose",
}
SUBSETS = ("all", "easy", "hard")  # Description subsets, in reporting order


def table(header: Sequence[str], rows: Iterable[Sequence[object]], left: int = 1) -> list[str]:
    """Build a Markdown table: text columns first, left-aligned, then numbers, right-aligned.

    Args:
        header: Column titles.
        rows: Cells of each row.
        left: How many leading columns hold text.

    Returns:
        Table lines, followed by a blank line.
    """
    rule = "|" + "---|" * left + "---:|" * (len(header) - left)
    lines = ["| " + " | ".join(header) + " |", rule]
    lines += ["| " + " | ".join(str(cell) for cell in row) + " |" for row in rows]
    return [*lines, ""]


def pct(value: float) -> str:
    """Format a share as a percentage.

    Args:
        value: Share between 0 and 1.

    Returns:
        Percentage with one decimal.
    """
    return f"{value:.1%}"


def details(summary: str, lines: Sequence[str]) -> list[str]:
    """Wrap lines in a collapsible block, closed by default.

    Args:
        summary: Text shown when collapsed.
        lines: Markdown content.

    Returns:
        Block lines, followed by a blank line.
    """
    return ["<details>", f"<summary>{summary}</summary>", "", *lines, "</details>", ""]
