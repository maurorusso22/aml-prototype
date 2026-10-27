"""A blank A4 report: styles, a "synthetic data" header on every page, and clean metadata."""

from datetime import datetime
from typing import cast

from docx import Document
from docx.document import Document as DocxDocument
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.styles.style import ParagraphStyle
from docx.text.paragraph import Paragraph
from docx.text.run import Run

from .i18n import Catalog

AUTHOR = "AML Case Reporter (prototype)"  # Written as author: never the local user's name
FONT = "Arial"  # Body and heading font, available wherever the report is opened
BODY_SIZE = Pt(10)  # Body text size
INK = RGBColor(0x0B, 0x0B, 0x0B)  # Primary text colour
ACCENT = RGBColor(0x1C, 0x5C, 0xAB)  # Heading colour, from the chart palette's blue ramp
MUTED = RGBColor(0x52, 0x51, 0x4E)  # Header, footer, and captions
PAGE_MARGIN = Cm(2.2)  # All four page margins


def new_document(catalog: Catalog, case_id: str, generated_at: datetime) -> DocxDocument:
    """Create an empty report with page setup, styles, header, footer, and metadata.

    Args:
        catalog: Wording of the report language.
        case_id: Case identifier, printed in the footer and the title property.
        generated_at: Generation time, stored as creation and modification time.

    Returns:
        The document, ready for sections.
    """
    document = Document()
    section = document.sections[0]
    section.page_width, section.page_height = Cm(21), Cm(29.7)
    for side in ("left_margin", "right_margin", "top_margin", "bottom_margin"):
        setattr(section, side, PAGE_MARGIN)
    _styles(document)
    header = section.header.paragraphs[0]
    _muted(header.add_run(catalog.t("header")))
    header.alignment = WD_ALIGN_PARAGRAPH.CENTER
    footer = section.footer.paragraphs[0]
    _muted(footer.add_run(catalog.t("footer", case_id=case_id)))
    _page_number(footer)
    footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _metadata(document, catalog, case_id, generated_at)
    _fix_zoom(document)
    return document


def _fix_zoom(document: DocxDocument) -> None:
    """Add the zoom percentage that python-docx's template omits but the schema requires.

    Args:
        document: Document whose settings to repair.
    """
    for zoom in document.settings.element.iter(qn("w:zoom")):
        zoom.set(qn("w:percent"), "100")


def _styles(document: DocxDocument) -> None:
    """Set fonts and colours of the body and heading styles.

    Args:
        document: Document to style.
    """
    normal = cast(ParagraphStyle, document.styles["Normal"])
    normal.font.name, normal.font.size, normal.font.color.rgb = FONT, BODY_SIZE, INK
    for level, size in ((0, 22), (1, 14), (2, 11.5)):
        style = cast(ParagraphStyle, document.styles["Title" if level == 0 else f"Heading {level}"])
        style.font.name, style.font.size, style.font.color.rgb = FONT, Pt(size), ACCENT


def _muted(run: Run) -> None:
    """Make a run small and grey, for header and footer text.

    Args:
        run: Run to format.
    """
    run.font.size, run.font.color.rgb = Pt(8), MUTED


def _page_number(paragraph: Paragraph) -> None:
    """Append a PAGE field, which Word and LibreOffice replace with the page number.

    Args:
        paragraph: Footer paragraph.
    """
    field = OxmlElement("w:fldSimple")
    field.set(qn("w:instr"), "PAGE")
    run, text = OxmlElement("w:r"), OxmlElement("w:t")
    text.text = "1"
    run.append(text)
    field.append(run)
    paragraph._p.append(field)


def _metadata(
    document: DocxDocument, catalog: Catalog, case_id: str, generated_at: datetime
) -> None:
    """Overwrite every core property, so no local or template details leak into the file.

    Args:
        document: Document to describe.
        catalog: Wording of the report language.
        case_id: Case identifier.
        generated_at: Generation time.
    """
    properties = document.core_properties
    properties.author = properties.last_modified_by = AUTHOR
    properties.title = f"{catalog.t('title')} {case_id}"
    properties.subject = catalog.t("header")
    properties.keywords = "AML; synthetic data; prototype"
    properties.comments = catalog.t("header")
    properties.category = "Prototype"
    properties.language = catalog.lang
    properties.created = properties.modified = generated_at
    properties.revision = 1
