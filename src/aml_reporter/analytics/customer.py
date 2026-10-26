"""Who the customer is, and which products they hold."""

from ..models import Fact, FactCategory, IndividualCustomer
from .base import AnalysisContext
from .facts import Facts, euros
from .registry import analyser

DAYS_PER_YEAR = 365.25  # Average year length, leap years included


@analyser
def customer_profile(context: AnalysisContext) -> list[Fact]:
    """Summarise the KYC profile and the relationship with the bank.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-CUST-001 to F-CUST-005 and F-REL-001 to F-REL-004.
    """
    bundle, customer = context.bundle, context.bundle.customer
    profile = Facts("CUST", FactCategory.CUSTOMER)
    tenure = round((bundle.period_end - customer.onboarding_date).days / DAYS_PER_YEAR, 1)
    if isinstance(customer, IndividualCustomer):
        kind, declared = "individual", customer.declared_annual_income
        activity = ("Occupation", customer.occupation)
    else:
        kind, declared = f"business ({customer.legal_form})", customer.declared_annual_turnover
        activity = ("Sector", customer.sector)
    profile.add(1, "Customer kind", kind)
    profile.add(2, "Years as a customer", tenure, "years")
    profile.add(3, "Risk rating", str(customer.risk_rating))
    profile.add(4, "Declared annual income or turnover", euros(declared), "EUR")
    profile.add(5, activity[0], activity[1])
    relationship = Facts("REL", FactCategory.RELATIONSHIP)
    balance = sum((account.balance for account in bundle.accounts), declared * 0)
    relationship.add(1, "Accounts", len(bundle.accounts), "count")
    relationship.add(2, "Cards", len(bundle.cards), "count")
    relationship.add(3, "Balance at the end of the period", euros(balance), "EUR")
    relationship.add(4, "Transactions in the period", len(bundle.transactions), "count")
    return profile.items + relationship.items
