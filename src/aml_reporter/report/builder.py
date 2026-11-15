"""Assemble the investigation report of one case: compute once, then write in any language."""

from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path

from docx.document import Document

from ..analytics import build_fact_sheet
from ..analytics.base import AnalysisContext
from ..analytics.charts import monthly_flows_chart, purpose_mix_chart
from ..controls import QualityThresholds, build_manifest, check_quality, load_thresholds
from ..controls.audit import NO_MODEL
from ..models import CaseBundle, Enrichment
from ..rules import RuleSet, assess, load_rules
from .catalogs import load_catalog
from .data import ReportData
from .document import new_document
from .sections import SECTIONS


def prepare_report(
    bundle: CaseBundle,
    enrichments: Sequence[Enrichment],
    enricher: str,
    *,
    model: str = NO_MODEL,
    ruleset: RuleSet | None = None,
    thresholds: QualityThresholds | None = None,
    generated_at: datetime | None = None,
) -> ReportData:
    """Compute facts, flags, data-quality issues, the run manifest, and charts.

    Args:
        bundle: Validated case bundle.
        enrichments: Fields extracted from its descriptions.
        enricher: Name of the enricher that produced them, shown in the report.
        model: LLM behind the enricher, recorded in the audit trail.
        ruleset: Red-flag rules; the packaged illustrative rules by default.
        thresholds: Data-quality tolerances; the packaged ones by default.
        generated_at: Generation time; now, in UTC, by default.

    Returns:
        Everything the report sections draw on.
    """
    rules = ruleset or load_rules()
    sheet = build_fact_sheet(bundle, enrichments)
    context = AnalysisContext(bundle, {item.transaction_id: item for item in enrichments})
    generated = generated_at or datetime.now(UTC)
    return ReportData(
        bundle=bundle,
        enrichments=tuple(enrichments),
        sheet=sheet,
        assessment=assess(sheet, rules),
        quality=check_quality(bundle, enrichments, enricher, thresholds or load_thresholds()),
        manifest=build_manifest(bundle, rules, enricher, model, generated),
        flows_chart=monthly_flows_chart(context),
        purposes_chart=purpose_mix_chart(context),
    )


def render_report(data: ReportData, lang: str = "en") -> Document:
    """Write every section of a prepared report in one language.

    Args:
        data: Prepared case data.
        lang: Report language, `en` or `it`.

    Returns:
        The report document, not yet saved.
    """
    catalog = load_catalog(lang)
    document = new_document(catalog, data.bundle.case_id, data.generated_at)
    for write_section in SECTIONS:
        write_section(document, data, catalog)
    return document


def build_report(
    bundle: CaseBundle,
    enrichments: Sequence[Enrichment],
    enricher: str,
    lang: str = "en",
    ruleset: RuleSet | None = None,
    generated_at: datetime | None = None,
) -> Document:
    """Prepare and write a report in one step.

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
    data = prepare_report(bundle, enrichments, enricher, ruleset=ruleset, generated_at=generated_at)
    return render_report(data, lang)


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
