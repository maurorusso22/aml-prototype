"""Closing sections: the blank analyst assessment, and the appendix."""

from collections import Counter

from docx.document import Document
from docx.shared import Cm

from ...models import Outcome
from ..blocks import DAGGER, key_values, note, page_break, paragraph, table
from ..data import ReportData, is_enriched
from ..i18n import Catalog

RATIONALE_HEIGHT_CM = 5.0  # Room left for the analyst's handwritten or typed rationale


def analyst_assessment(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Leave the decision, rationale, and signature fields blank for the analyst.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    page_break(document)
    document.add_heading(catalog.t("h_assessment"), level=1)
    paragraph(document, catalog.t("assessment_intro"), italic=True)
    choices = "\n".join(f"☐ {catalog.word(str(outcome))}" for outcome in Outcome)
    form = key_values(
        document,
        [
            (catalog.t("decision"), choices),
            (catalog.t("rationale"), ""),
            (catalog.t("analyst"), ""),
            (catalog.t("date"), ""),
            (catalog.t("signature"), ""),
        ],
    )
    form.rows[1].height = Cm(RATIONALE_HEIGHT_CM)


def appendix(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Explain the method, show enrichment statistics, index every fact, and list limits.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    page_break(document)
    document.add_heading(catalog.t("h_appendix"), level=1)
    document.add_heading(catalog.t("h_methodology"), level=2)
    paragraph(document, catalog.t("methodology_1", enricher=catalog.word(data.enricher)))
    paragraph(document, catalog.t("methodology_2"))
    paragraph(document, catalog.t("methodology_3"))
    document.add_heading(catalog.t("h_enrichment"), level=2)
    paragraph(document, catalog.t("enrichment_intro", total=len(data.enrichments)))
    sources = Counter(str(enrichment.source) for enrichment in data.enrichments)
    rows = [(catalog.word(source), str(count)) for source, count in sorted(sources.items())]
    table(document, [catalog.t("col_source"), catalog.t("col_count")], rows, (8.0, 4.0))
    document.add_heading(catalog.t("h_fact_index"), level=2)
    header = [catalog.t(key) for key in ("col_id", "col_measure", "col_value", "col_evidence")]
    index = [
        (
            fact.id,
            catalog.label(fact) + (DAGGER if is_enriched(fact.id) else ""),
            catalog.value(fact),
            str(len(fact.evidence)),
        )
        for fact in data.sheet.facts
    ]
    table(document, header, index, (2.8, 8.2, 3.8, 1.8))
    note(document, catalog.t("enriched_note"))
    document.add_heading(catalog.t("h_limitations"), level=2)
    for key in ("limitations_1", "limitations_2", "limitations_3"):
        paragraph(document, catalog.t(key))
    note(document, catalog.t("disclaimer"))
