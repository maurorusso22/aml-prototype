"""Explicit table formatting: borders, header shading, and fixed column widths.

Formatting is written into each table rather than borrowed from a named table style, so the
report looks the same in Word, LibreOffice, and lighter viewers that ignore table styles.
"""

from collections.abc import Sequence

from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.oxml.table import CT_Tc
from docx.shared import Cm, Pt
from docx.table import Table

BORDER_COLOUR = "C3C2B7"  # Hairline borders, the same grey as the chart baseline
HEADER_FILL = "E8EFF8"  # Light tint of the heading blue, for header rows and key columns
BORDER_SIZE = "4"  # Border width in eighths of a point
CELL_SPACING_PT = 1.5  # Space above and below text in a cell, for compact rows
LATER_TABLE_PROPERTIES = ("shd", "tblLayout", "tblCellMar", "tblLook")  # Follow the borders


def format_table(table: Table, widths_cm: Sequence[float], header: bool) -> None:
    """Fix column widths, draw hairline borders, and shade the header row or key column.

    Args:
        table: Table to format.
        widths_cm: Width of each column in centimetres.
        header: True to shade the first row, False to shade the first column.
    """
    table.autofit = False
    for column, width in zip(table.columns, widths_cm, strict=True):
        column.width = Cm(width)
    for row in table.rows:
        for cell, width in zip(row.cells, widths_cm, strict=True):
            cell.width = Cm(width)
            for paragraph in cell.paragraphs:
                paragraph.paragraph_format.space_before = Pt(CELL_SPACING_PT)
                paragraph.paragraph_format.space_after = Pt(CELL_SPACING_PT)
    _borders(table)
    key_cells = table.rows[0].cells if header else [row.cells[0] for row in table.rows]
    for cell in key_cells:
        _shade(cell._tc)
        for paragraph in cell.paragraphs:
            for run in paragraph.runs:
                run.bold = True


def _borders(table: Table) -> None:
    """Add single hairline borders around and between all cells.

    The borders element is inserted before any table property the schema places after it.

    Args:
        table: Table to draw borders on.
    """
    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        line = OxmlElement(f"w:{edge}")
        for name, value in (("val", "single"), ("sz", BORDER_SIZE), ("color", BORDER_COLOUR)):
            line.set(qn(f"w:{name}"), value)
        line.set(qn("w:space"), "0")
        borders.append(line)
    properties = table._tbl.tblPr
    later = [
        child for child in properties if child.tag in {qn(f"w:{n}") for n in LATER_TABLE_PROPERTIES}
    ]
    if later:
        later[0].addprevious(borders)
    else:
        properties.append(borders)


def _shade(cell_element: CT_Tc) -> None:
    """Fill a cell with the header tint.

    Args:
        cell_element: The cell's `w:tc` element; its properties only hold a width so far.
    """
    shading = OxmlElement("w:shd")
    for name, value in (("val", "clear"), ("color", "auto"), ("fill", HEADER_FILL)):
        shading.set(qn(f"w:{name}"), value)
    cell_element.get_or_add_tcPr().append(shading)
