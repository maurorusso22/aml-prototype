"""Building blocks shared by report sections: paragraphs, tables, and figures."""

import io
from collections.abc import Sequence

from docx.document import Document
from docx.enum.text import WD_BREAK
from docx.shared import Cm, Pt
from docx.table import Table
from docx.text.paragraph import Paragraph

from ..models import Fact
from .data import is_enriched
from .document import MUTED
from .i18n import Catalog
from .tables import format_table

TEXT_WIDTH_CM = 16.6  # Usable width of an A4 page with the report margins
FACT_COLUMNS_CM = (2.8, 9.4, 4.4)  # Widths of the ID, measure, and value columns
DAGGER = " †"  # Marks values derived from enrichment


def paragraph(document: Document, text: str, *, italic: bool = False) -> Paragraph:
    """Add a body paragraph.

    Args:
        document: Report under construction.
        text: Paragraph text.
        italic: Write the text in italics.

    Returns:
        The paragraph.
    """
    added = document.add_paragraph()
    added.add_run(text).italic = italic
    return added


def note(document: Document, text: str) -> None:
    """Add a small grey note, such as a caption or the dagger legend.

    Args:
        document: Report under construction.
        text: Note text.
    """
    run = document.add_paragraph().add_run(text)
    run.italic, run.font.size, run.font.color.rgb = True, Pt(8.5), MUTED


def page_break(document: Document) -> None:
    """Start the next content on a new page.

    Args:
        document: Report under construction.
    """
    document.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def figure(document: Document, png: bytes, caption: str) -> None:
    """Add a chart across the text width, followed by its caption.

    Args:
        document: Report under construction.
        png: Chart image.
        caption: Caption text.
    """
    document.add_picture(io.BytesIO(png), width=Cm(TEXT_WIDTH_CM))
    note(document, caption)


def table(
    document: Document,
    header: Sequence[str] | None,
    rows: Sequence[Sequence[str]],
    widths_cm: Sequence[float],
) -> Table:
    """Add a table with a shaded header row, or a shaded key column when there is no header.

    Args:
        document: Report under construction.
        header: Column titles, or None for a key-value table.
        rows: Cell texts, one sequence per row.
        widths_cm: Width of each column in centimetres.

    Returns:
        The table.
    """
    contents = ([header] if header else []) + list(rows)
    added: Table = document.add_table(rows=len(contents), cols=len(widths_cm))
    for row, values in zip(added.rows, contents, strict=True):
        for cell, value in zip(row.cells, values, strict=True):
            cell.text = value
    format_table(added, widths_cm, header is not None)
    document.add_paragraph()
    return added


def key_values(document: Document, pairs: Sequence[tuple[str, str]]) -> Table:
    """Add a two-column table of labels and values.

    Args:
        document: Report under construction.
        pairs: Label and value of each row.

    Returns:
        The table.
    """
    return table(document, None, pairs, (5.6, TEXT_WIDTH_CM - 5.6))


def facts_table(document: Document, facts: Sequence[Fact], catalog: Catalog) -> None:
    """Add a table of facts: identifier, translated label, and formatted value.

    Args:
        document: Report under construction.
        facts: Facts to list.
        catalog: Wording of the report language.
    """
    header = [catalog.t("col_id"), catalog.t("col_measure"), catalog.t("col_value")]
    rows = [
        (
            fact.id,
            catalog.label(fact) + (DAGGER if is_enriched(fact.id) else ""),
            catalog.value(fact),
        )
        for fact in facts
    ]
    table(document, header, rows, FACT_COLUMNS_CM)
