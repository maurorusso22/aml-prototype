"""Opening sections: the cover with the case summary, and the key findings."""

from docx.document import Document

from ...models import BusinessCustomer, Customer
from ..blocks import key_values, note, paragraph, table
from ..data import ReportData
from ..i18n import Catalog


def cover(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Write the title, the case summary, and the disclaimer.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    bundle, alert = data.bundle, data.bundle.alert
    document.add_heading(catalog.t("title"), level=0)
    paragraph(document, catalog.t("subtitle", case_id=bundle.case_id))
    raised = catalog.date(alert.raised_at.date())
    period = catalog.t(
        "period_value", start=catalog.date(bundle.period_start), end=catalog.date(bundle.period_end)
    )
    customer = f"{display_name(bundle.customer)} ({bundle.customer.customer_id})"
    generated = f"{catalog.date(data.generated_at.date())} {data.generated_at:%H:%M} UTC"
    key_values(
        document,
        [
            (catalog.t("alert"), catalog.t("alert_raised", alert_id=alert.alert_id, date=raised)),
            (catalog.t("scenario"), alert.scenario),
            (catalog.t("reason"), alert.reason),
            (catalog.t("customer"), customer),
            (catalog.t("period"), period),
            (catalog.t("generated"), generated),
            (catalog.t("enricher"), catalog.word(data.enricher)),
        ],
    )
    note(document, catalog.t("disclaimer"))


def findings(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Write the risk indicator and the list of red flags raised.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    assessment = data.assessment
    document.add_heading(catalog.t("h_findings"), level=1)
    level = catalog.word(str(assessment.level))
    paragraph(document, catalog.t("risk_summary", level=level, score=assessment.score))
    flags = assessment.flags
    if not flags:
        paragraph(document, catalog.t("no_flags"))
        return
    count = len(flags)
    paragraph(
        document, catalog.t("flags_one") if count == 1 else catalog.t("flags_many", count=count)
    )
    rows = [
        (
            catalog.word(str(flag.severity)),
            catalog.rule(flag.rule_id, "name", flag.name),
            ", ".join(flag.facts),
        )
        for flag in flags
    ]
    header = [catalog.t("col_severity"), catalog.t("col_flag"), catalog.t("col_facts")]
    table(document, header, rows, (2.6, 9.0, 5.0))


def display_name(customer: Customer) -> str:
    """Name a customer as the report shows it.

    Args:
        customer: Individual or business customer.

    Returns:
        Legal name for businesses, first and last name for individuals.
    """
    if isinstance(customer, BusinessCustomer):
        return customer.legal_name
    return f"{customer.first_name} {customer.last_name}"
