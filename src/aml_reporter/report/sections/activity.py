"""Sections about activity: transaction behaviour, counterparties, geography, profile."""

from docx.document import Document

from ..blocks import fact_sentence, facts_table, figure, note, paragraph
from ..data import ReportData
from ..i18n import Catalog


def behaviour(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Summarise flows, cash, channels, timing, and payment purposes, with both charts.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_behaviour"), level=1)
    sheet = data.sheet
    intro = catalog.t(
        "behaviour_intro",
        inflows=catalog.value(sheet.get("F-FLOW-001")),
        outflows=catalog.value(sheet.get("F-FLOW-002")),
    )
    multiple = sheet.get("F-FLOW-006")
    paragraph(document, f"{intro} {fact_sentence(catalog, 'behaviour_multiple', multiple)}")
    figure(document, data.flows_chart, catalog.t("chart_flows"))
    facts_table(document, data.facts("F-FLOW-", "F-CASH-", "F-CHAN-", "F-TIME-"), catalog)
    figure(document, data.purposes_chart, catalog.t("chart_purposes"))
    purposes = [fact for fact in data.facts("F-PURP-") if fact.value or fact.id == "F-PURP-201"]
    facts_table(document, purposes, catalog)
    note(document, catalog.t("enriched_note"))


def counterparties(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Summarise who the customer transacts with.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_counterparties"), level=1)
    senders, receivers = data.sheet.get("F-CPTY-001"), data.sheet.get("F-CPTY-002")
    intro = catalog.t(
        "counterparties_intro", senders=catalog.value(senders), receivers=catalog.value(receivers)
    )
    paragraph(document, intro)
    facts_table(document, data.facts("F-CPTY-"), catalog)
    note(document, catalog.t("enriched_note"))


def geography(document: Document, data: ReportData, catalog: Catalog) -> None:
    """List the foreign countries involved and the flows with them.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_geography"), level=1)
    countries = data.sheet.get("F-GEO-001").value
    if countries == "none":
        paragraph(document, catalog.t("geography_none"))
    else:
        paragraph(document, catalog.t("geography_some", countries=countries))
    facts_table(document, data.facts("F-GEO-"), catalog)
    note(document, catalog.t("enriched_note"))


def profile(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Compare observed inflows with the declared income or turnover.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_profile"), level=1)
    paragraph(document, fact_sentence(catalog, "profile_intro", data.sheet.get("F-PROF-002")))
    facts_table(document, data.facts("F-PROF-"), catalog)
    note(document, catalog.t("enriched_note"))
