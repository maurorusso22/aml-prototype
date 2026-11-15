"""The red flags in detail: what each rule looks for, and the facts that made it fire."""

from docx.document import Document

from ..blocks import facts_table, note, paragraph, table
from ..data import ReportData
from ..i18n import Catalog

LISTED_TRANSACTIONS = 10  # Transactions named under each flag; the rest are in the appendix


def red_flags(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Explain every raised flag with its description, facts, and evidence, then undecided rules.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_flags"), level=1)
    if not data.assessment.flags:
        paragraph(document, catalog.t("flag_none"))
    for flag in data.assessment.flags:
        name = catalog.rule(flag.rule_id, "name", flag.name)
        document.add_heading(f"{flag.rule_id}: {name}", level=2)
        severity = f"{catalog.t('col_severity')}: {catalog.word(str(flag.severity))}."
        description = catalog.rule(flag.rule_id, "description", flag.description)
        paragraph(document, f"{description} {severity}")
        facts_table(document, [data.sheet.get(fact_id) for fact_id in flag.facts], catalog)
        if flag.evidence:
            paragraph(document, catalog.t("flag_transactions", count=len(flag.evidence)))
            listed = ", ".join(flag.evidence[:LISTED_TRANSACTIONS])
            more = "…" if len(flag.evidence) > LISTED_TRANSACTIONS else ""
            note(document, catalog.t("flag_listing", ids=listed + more))
    _unevaluated(document, data, catalog)


def _unevaluated(document: Document, data: ReportData, catalog: Catalog) -> None:
    """List the rules the case lacks the data to decide, with the facts each one could not read.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    rules = data.assessment.unevaluated
    if not rules:
        return
    document.add_heading(catalog.t("h_unevaluated"), level=2)
    paragraph(document, catalog.t("unevaluated_intro"))
    rows = [
        (
            catalog.word(str(rule.severity)),
            f"{rule.rule_id}: {catalog.rule(rule.rule_id, 'name', rule.name)}",
            ", ".join(rule.facts),
        )
        for rule in rules
    ]
    header = [catalog.t("col_severity"), catalog.t("col_flag"), catalog.t("col_facts")]
    table(document, header, rows, (2.6, 9.0, 5.0))
