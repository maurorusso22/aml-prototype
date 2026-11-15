"""Declared economic profile versus the activity actually observed."""

from decimal import Decimal

from ..models import Direction, Fact, FactCategory, IndividualCustomer, PaymentPurpose
from .base import AnalysisContext
from .facts import Facts, euros, ratio, total
from .registry import analyser

DAYS_PER_YEAR = 365  # Used to annualise flows observed over the look-back period


@analyser
def profile_consistency(context: AnalysisContext) -> list[Fact]:
    """Compare annualised inflows with the income or turnover declared at onboarding.

    Individuals are measured on salary inflows, businesses on invoice inflows. Flows are
    annualised over the observed history, so a new relationship is not diluted over months
    without an account; a declared figure of 0 makes any inflow exceed it (`no_baseline`).

    Args:
        context: Case under analysis.

    Returns:
        Facts F-PROF-001 to F-PROF-004.
    """
    facts = Facts("PROF", FactCategory.PROFILE_CONSISTENCY)
    customer = context.bundle.customer
    if isinstance(customer, IndividualCustomer):
        declared, purpose, word = customer.declared_annual_income, PaymentPurpose.SALARY, "salary"
    else:
        declared, purpose, word = (
            customer.declared_annual_turnover,
            PaymentPurpose.INVOICE,
            "invoice",
        )

    def annualise(amount: Decimal) -> Decimal:
        """Scale an amount observed over the history to one year.

        Args:
            amount: Amount observed since the start of the observed history.

        Returns:
            The yearly equivalent.
        """
        return amount * DAYS_PER_YEAR / context.observed_days

    inflows = context.flows(Direction.INBOUND)
    expected = [
        tx
        for tx in inflows
        if (enrichment := context.enrichments.get(tx.transaction_id))
        and enrichment.payment_purpose is purpose
    ]
    observed, typical = annualise(total(inflows)), annualise(total(expected))
    facts.add(1, "Annualised inflows", euros(observed), "EUR", inflows)
    facts.add(
        2,
        "Annualised inflows as a multiple of the declared figure",
        ratio(observed, declared),
        "times",
    )
    facts.add(3, f"Annualised {word} inflows", euros(typical), "EUR", expected)
    facts.add(
        4,
        f"Annualised {word} inflows as a multiple of the declared figure",
        ratio(typical, declared),
        "times",
    )
    return facts.items
