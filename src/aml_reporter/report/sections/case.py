"""Sections about the alert and the customer: the alert in context, KYC data, products."""

from docx.document import Document

from ...models import Address, IndividualCustomer
from ..blocks import facts_table, key_values, note, paragraph, table
from ..data import ReportData
from ..i18n import Catalog
from .front import display_name


def alert_context(document: Document, data: ReportData, catalog: Catalog) -> None:
    """Describe the alerted transaction and compare it with the customer's history.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_alert"), level=1)
    sheet, bundle = data.sheet, data.bundle
    alerted = next(
        tx for tx in bundle.transactions if tx.transaction_id == bundle.alert.transaction_id
    )
    kind = catalog.value(sheet.get("F-ALERT-002"))
    amount = catalog.value(sheet.get("F-ALERT-001"))
    date = catalog.date(alerted.booked_at.date())
    paragraph(document, catalog.t("alert_sentence", kind=kind, amount=amount, date=date))
    if sheet.get("F-ALERT-003").value:
        multiple = catalog.value(sheet.get("F-ALERT-005"))
        paragraph(document, catalog.t("alert_multiple", multiple=multiple))
    else:
        paragraph(document, catalog.t("alert_first"))
    facts_table(document, data.facts("F-ALERT-"), catalog)
    if data.has("F-ALERT-007"):
        note(document, catalog.t("enriched_note"))


def customer_profile(document: Document, data: ReportData, catalog: Catalog) -> None:
    """List the KYC data of the customer, then the profile facts.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_customer"), level=1)
    customer = data.bundle.customer
    since = (catalog.t("customer_since"), catalog.date(customer.onboarding_date))
    rating = (catalog.t("risk_rating"), catalog.word(str(customer.risk_rating)))
    if isinstance(customer, IndividualCustomer):
        rows = [
            (catalog.t("name"), display_name(customer)),
            (catalog.t("customer_id"), customer.customer_id),
            (catalog.t("tax_code"), customer.tax_code),
            (catalog.t("birth_date"), catalog.date(customer.birth_date)),
            (catalog.t("residence"), _address(customer.residence)),
            (catalog.t("occupation"), customer.occupation),
            (catalog.t("declared_income"), catalog.money(float(customer.declared_annual_income))),
        ]
    else:
        rows = [
            (catalog.t("legal_name"), display_name(customer)),
            (catalog.t("customer_id"), customer.customer_id),
            (catalog.t("vat_number"), customer.vat_number),
            (catalog.t("legal_form"), customer.legal_form),
            (catalog.t("incorporation_date"), catalog.date(customer.incorporation_date)),
            (catalog.t("registered_office"), _address(customer.residence)),
            (catalog.t("sector"), customer.sector),
            (
                catalog.t("declared_turnover"),
                catalog.money(float(customer.declared_annual_turnover)),
            ),
        ]
    key_values(document, [*rows, rating, since])
    facts_table(document, data.facts("F-CUST-"), catalog)


def relationship(document: Document, data: ReportData, catalog: Catalog) -> None:
    """List the accounts and cards, then the relationship facts.

    Args:
        document: Report under construction.
        data: Case data.
        catalog: Wording of the report language.
    """
    document.add_heading(catalog.t("h_relationship"), level=1)
    bundle = data.bundle
    document.add_heading(catalog.t("accounts"), level=2)
    columns = ("col_account", "col_iban", "col_status", "col_opened", "col_balance")
    rows = [
        (
            account.account_id,
            account.iban,
            catalog.word(str(account.status)),
            catalog.date(account.opened_on),
            catalog.money(float(account.balance)),
        )
        for account in bundle.accounts
    ]
    table(document, [catalog.t(key) for key in columns], rows, (2.4, 6.0, 2.2, 2.6, 3.4))
    document.add_heading(catalog.t("cards"), level=2)
    columns = ("col_card", "col_type", "col_number", "col_issued", "col_expires")
    rows = [
        (
            card.card_id,
            catalog.word(str(card.card_type)),
            card.masked_pan,
            catalog.date(card.issued_on),
            catalog.date(card.expires_on),
        )
        for card in bundle.cards
    ]
    table(document, [catalog.t(key) for key in columns], rows, (2.4, 2.4, 5.0, 3.4, 3.4))
    facts_table(document, data.facts("F-REL-"), catalog)


def _address(address: Address) -> str:
    """Write an address on one line.

    Args:
        address: Postal address.

    Returns:
        Street, postal code, city, and country.
    """
    return f"{address.street}, {address.postal_code} {address.city} ({address.country})"
