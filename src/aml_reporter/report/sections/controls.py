"""Sections on the controls: data quality near the top, the audit trail at the very end."""

from docx.document import Document

from ..blocks import key_values, note, paragraph
from ..data import ReportData
from ..i18n import Catalog
from .flags import LISTED_TRANSACTIONS


def data_quality(document: Document, data: ReportData, catalog: Catalog) -> None:
    """List the data-quality issues that limit the findings, or state that there are none.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_quality"), level=1)
    if not data.quality:
        paragraph(document, catalog.t("quality_none"))
        return
    paragraph(document, catalog.t("quality_intro"))
    for issue in data.quality:
        paragraph(document, catalog.t(f"dq_{issue.code}", **issue.details))
        if issue.transactions:
            listed = ", ".join(issue.transactions[:LISTED_TRANSACTIONS])
            more = "…" if len(issue.transactions) > LISTED_TRANSACTIONS else ""
            note(document, catalog.t("flag_listing", ids=listed + more))


def audit_trail(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Record the fingerprints of the inputs and settings behind the report.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    manifest = data.manifest
    document.add_heading(catalog.t("h_audit"), level=2)
    paragraph(document, catalog.t("audit_intro"))
    generated = f"{catalog.date(manifest.generated_at.date())} {manifest.generated_at:%H:%M} UTC"
    key_values(
        document,
        [
            (catalog.t("audit_version"), manifest.tool_version),
            (catalog.t("enricher"), catalog.word(manifest.enricher)),
            (catalog.t("audit_model"), manifest.model),
            (catalog.t("audit_bundle"), manifest.bundle_sha256),
            (catalog.t("audit_rules"), manifest.rules_sha256),
            (catalog.t("audit_prompts"), manifest.prompts_sha256),
            (catalog.t("generated"), generated),
        ],
    )
