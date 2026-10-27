"""Assemble the investigation report of one case."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from docx.document import Document

from ..analytics import build_fact_sheet
from ..analytics.base import AnalysisContext
from ..analytics.charts import monthly_flows_chart, purpose_mix_chart
from ..models import CaseBundle, Enrichment
from ..rules import RuleSet, assess, load_rules
from .catalogs import load_catalog
from .data import ReportData
from .document import new_document
from .sections import SECTIONS


def build_report(
    bundle: CaseBundle,
    enrichments: Sequence[Enrichment],
    enricher: str,
    lang: str = "en",
    ruleset: RuleSet | None = None,
    generated_at: datetime | None = None,
) -> Document:
    """Compute facts, flags, and charts, then write every section.

    Args:
        bundle: Validated case bundle.
        enrichments: Fields extracted from its descriptions.
        enricher: Name of the enricher that produced them, shown in the report.
        lang: Report language, `en` or `it`.
        ruleset: Red-flag rules; the packaged illustrative rules by default.
        generated_at: Generation time; now, in UTC, by default.

    Returns:
        The report document, not yet saved.
    """
    sheet = build_fact_sheet(bundle, enrichments)
    context = AnalysisContext(bundle, {item.transaction_id: item for item in enrichments})
    data = ReportData(
        bundle=bundle,
        enrichments=tuple(enrichments),
        sheet=sheet,
        assessment=assess(sheet, ruleset or load_rules()),
        enricher=enricher,
        generated_at=generated_at or datetime.now(UTC),
        flows_chart=monthly_flows_chart(context),
        purposes_chart=purpose_mix_chart(context),
    )
    catalog = load_catalog(lang)
    document = new_document(catalog, bundle.case_id, data.generated_at)
    for write_section in SECTIONS:
        write_section(document, data, catalog)
    return document


def save_report(document: Document, path: Path) -> Path:
    """Write a report to disk, creating its folder.

    Args:
        document: Report to save.
        path: Destination `.docx` file.

    Returns:
        The path written.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    document.save(str(path))
    return path
