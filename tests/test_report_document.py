"""Structure of the generated Word report: sections, tables, charts, and metadata."""

import getpass
from datetime import UTC, datetime
from pathlib import Path

import pytest
from docx import Document
from docx.document import Document as DocxDocument

from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.report import build_report, save_report
from aml_reporter.report.catalogs import load_catalog
from aml_reporter.report.document import AUTHOR
from aml_reporter.synthetic import GeneratedCase

GENERATED_AT = datetime(2026, 10, 28, 9, 0, tzinfo=UTC)  # Fixed, so metadata can be checked
HEADINGS = (  # Catalogue keys of the section headings every report must contain
    "h_findings",
    "h_alert",
    "h_customer",
    "h_relationship",
    "h_behaviour",
    "h_counterparties",
    "h_geography",
    "h_flags",
    "h_profile",
    "h_assessment",
    "h_appendix",
    "h_fact_index",
)


def write_and_reopen(case: GeneratedCase, lang: str, folder: Path) -> DocxDocument:
    """Build a report, save it, and open the saved file again.

    Args:
        case: Synthetic case.
        lang: Report language.
        folder: Where to save the file.

    Returns:
        The document as read back from disk.
    """
    enrichments = BaselineEnricher().enrich(case.bundle.transactions)
    document = build_report(case.bundle, enrichments, "baseline", lang, generated_at=GENERATED_AT)
    path = save_report(document, folder / f"report_{lang}.docx")
    return Document(str(path))


@pytest.mark.parametrize("lang", ["en", "it"])
def test_report_has_every_section(
    pass_through_case: GeneratedCase, tmp_path: Path, lang: str
) -> None:
    """Every section heading appears, in the report language.

    Args:
        pass_through_case: Synthetic case to report on.
        tmp_path: Temporary folder.
        lang: Report language.
    """
    document = write_and_reopen(pass_through_case, lang, tmp_path)
    catalog = load_catalog(lang)
    headings = {
        p.text
        for p in document.paragraphs
        if p.style is not None and p.style.name.startswith("Heading")
    }
    assert {catalog.t(key) for key in HEADINGS} <= headings


def test_report_has_tables_charts_and_every_fact(
    pass_through_case: GeneratedCase, tmp_path: Path
) -> None:
    """The report embeds both charts and indexes every fact of the case."""
    document = write_and_reopen(pass_through_case, "en", tmp_path)
    assert len(document.inline_shapes) == 2
    assert len(document.tables) >= 12
    cells = {cell.text for table in document.tables for row in table.rows for cell in row.cells}
    assert pass_through_case.bundle.alert.alert_id in " ".join(cells)
    assert {"F-ALERT-001", "F-CPTY-005", "F-TIME-005"} <= cells


def test_report_metadata_is_clean(pass_through_case: GeneratedCase, tmp_path: Path) -> None:
    """Core properties are set explicitly and never name the local user."""
    properties = write_and_reopen(pass_through_case, "en", tmp_path).core_properties
    assert properties.author == properties.last_modified_by == AUTHOR
    assert pass_through_case.bundle.case_id in properties.title
    assert properties.created == GENERATED_AT
    assert getpass.getuser() not in f"{properties.author} {properties.last_modified_by}"
    assert "python-docx" not in f"{properties.author} {properties.comments}"


def test_every_page_says_synthetic(pass_through_case: GeneratedCase, tmp_path: Path) -> None:
    """The header of every page states that the data is synthetic."""
    document = write_and_reopen(pass_through_case, "it", tmp_path)
    header = document.sections[0].header.paragraphs[0].text
    assert header == load_catalog("it").t("header")
    assert "sintetici" in header
