"""Red flags raised by the rules, and the risk indicator derived from them."""

from pydantic import Field

from .base import DomainModel
from .enums import RiskLevel
from .formats import CaseId, FactId, NonEmptyStr, RuleId, TransactionId


class RedFlag(DomainModel):
    """A rule that fired, with the facts and transactions behind it."""

    rule_id: RuleId = Field(description="Rule that fired.")
    name: NonEmptyStr = Field(description="Short name of the red flag.")
    description: NonEmptyStr = Field(description="What the rule looks for.")
    severity: RiskLevel = Field(description="Weight of the flag in the risk indicator.")
    facts: tuple[FactId, ...] = Field(description="Facts that satisfied the rule's conditions.")
    evidence: tuple[TransactionId, ...] = Field(description="Transactions behind those facts.")


class RiskAssessment(DomainModel):
    """Triggered red flags and a transparent risk indicator: points per flag, summed.

    The indicator supports the analyst; it never decides the outcome of an alert.
    """

    case_id: CaseId = Field(description="Case the assessment refers to.")
    flags: tuple[RedFlag, ...] = Field(description="Red flags raised, in rule order.")
    score: int = Field(ge=0, description="Sum of the points of the raised flags.")
    level: RiskLevel = Field(description="Risk indicator derived from the score.")
