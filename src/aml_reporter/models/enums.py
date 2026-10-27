"""Enumerations used by the domain models, including the LLM label sets."""

from enum import StrEnum


class Direction(StrEnum):
    """Money flow direction, from the customer's point of view."""

    INBOUND = "inbound"  # Credited to the customer's account
    OUTBOUND = "outbound"  # Debited from the customer's account


class Channel(StrEnum):
    """How a transaction reached the account."""

    BRANCH = "branch"  # Teller operation at a branch
    ATM = "atm"  # Automated teller machine
    ONLINE = "online"  # Home banking, mobile app, or e-commerce
    POS = "pos"  # Card terminal at a merchant
    INTERBANK = "interbank"  # Initiated at another bank, e.g. incoming transfer or direct debit


class TransactionType(StrEnum):
    """Kind of banking operation."""

    WIRE_TRANSFER = "wire_transfer"  # Domestic or international credit transfer
    CASH_DEPOSIT = "cash_deposit"  # Cash paid into the account
    CASH_WITHDRAWAL = "cash_withdrawal"  # Cash taken out of the account
    CARD_PAYMENT = "card_payment"  # Purchase made with a card
    DIRECT_DEBIT = "direct_debit"  # Collection initiated by a creditor


class CustomerKind(StrEnum):
    """Legal nature of the customer."""

    INDIVIDUAL = "individual"  # Natural person
    BUSINESS = "business"  # Company or sole trader


class RiskRating(StrEnum):
    """Risk rating assigned by customer due diligence."""

    LOW = "low"  # Standard due diligence
    MEDIUM = "medium"  # Standard due diligence with closer monitoring
    HIGH = "high"  # Enhanced due diligence


class AccountStatus(StrEnum):
    """Lifecycle state of an account."""

    ACTIVE = "active"  # Open and in regular use
    DORMANT = "dormant"  # Open, but with no customer-initiated activity for a long period
    CLOSED = "closed"  # No longer operational


class CardType(StrEnum):
    """Kind of payment card."""

    DEBIT = "debit"  # Charged directly to the account balance
    CREDIT = "credit"  # Charges settled periodically
    PREPAID = "prepaid"  # Spends a preloaded balance


class CounterpartyType(StrEnum):
    """LLM label set: legal nature of a counterparty."""

    NATURAL_PERSON = "natural_person"  # An individual
    LEGAL_PERSON = "legal_person"  # A company, association, or public body


class PaymentPurpose(StrEnum):
    """LLM label set: purpose of a payment, as stated in its description."""

    SALARY = "salary"  # Wages or pension
    RENT = "rent"  # Rent or lease payment
    INVOICE = "invoice"  # Payment for goods or services
    LOAN = "loan"  # Loan disbursement or repayment
    FAMILY_SUPPORT = "family_support"  # Transfer between relatives
    OTHER = "other"  # Purpose stated, but outside the categories above
    UNKNOWN = "unknown"  # Not determinable from the available text


class EnrichmentSource(StrEnum):
    """Which component produced an enrichment."""

    LLM = "llm"  # An LLM backend, after output validation
    BASELINE = "baseline"  # The rule-based extractor


class RiskLevel(StrEnum):
    """Severity of a red flag, and level of the overall risk indicator."""

    LOW = "low"  # Worth noting
    MEDIUM = "medium"  # Needs an explanation from the customer
    HIGH = "high"  # Points to a known money-laundering typology


class Outcome(StrEnum):
    """Analyst decision on an alert."""

    ESCALATE = "escalate"  # Investigate further, towards a suspicious transaction report
    CLOSE = "close"  # False positive
    REQUEST_INFORMATION = "request_information"  # Ask the customer for supporting documents


class FactCategory(StrEnum):
    """Report area a fact belongs to."""

    ALERT = "alert"  # The alerted transaction in context
    CUSTOMER = "customer"  # KYC profile
    RELATIONSHIP = "relationship"  # Accounts and cards
    TRANSACTION_BEHAVIOUR = "transaction_behaviour"  # Flows, channels, cash, purposes
    COUNTERPARTY = "counterparty"  # Who the customer transacts with
    GEOGRAPHY = "geography"  # Countries involved
    PROFILE_CONSISTENCY = "profile_consistency"  # Declared profile vs observed activity
    RED_FLAG = "red_flag"  # Triggered red-flag rules
