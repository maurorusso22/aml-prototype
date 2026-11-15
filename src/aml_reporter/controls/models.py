"""What the production controls produce: data-quality issues, case checks, and run manifests."""

from enum import StrEnum

from pydantic import AwareDatetime, Field

from ..models import UnevaluatedRule
from ..models.base import DomainModel
from ..models.formats import CaseId, NonEmptyStr, TransactionId

type Sha256 = str  # Hexadecimal SHA-256 digest


class IssueCode(StrEnum):
    """Data-quality issue that limits what the analysis can say, without invalidating the case."""

    SHORT_HISTORY = "short_history"  # Too little earlier history to measure a usual level
    UNDESCRIBED = "undescribed"  # Transfers or debits with an empty description
    UNENRICHED = "unenriched"  # Transfers or debits the enricher returned nothing for
    FALLBACK = "fallback"  # Too many LLM answers replaced by the rule-based extractor
    DUPLICATES = "duplicates"  # Bookings that repeat another one field for field
    CARD_VALIDITY = "card_validity"  # Card transactions outside the card's validity


class QualityIssue(DomainModel):
    """One data-quality warning, with the values its message needs and the records concerned."""

    code: IssueCode = Field(description="Kind of issue; also selects the message template.")
    details: dict[str, int] = Field(
        default_factory=dict, description="Values for the placeholders of the message."
    )
    transactions: tuple[TransactionId, ...] = Field(
        default=(), description="Transactions concerned, when the issue is about records."
    )


class CaseCheck(DomainModel):
    """Everything that limits the conclusions on one case: data quality and undecided rules."""

    case_id: CaseId = Field(description="Case checked.")
    issues: tuple[QualityIssue, ...] = Field(description="Data-quality issues found.")
    unevaluated: tuple[UnevaluatedRule, ...] = Field(
        description="Rules the case lacks the data to decide."
    )

    @property
    def clean(self) -> bool:
        """Tell whether the case raised no issue at all.

        Returns:
            True when there is no data-quality issue and every rule was decided.
        """
        return not self.issues and not self.unevaluated


class RunManifest(DomainModel):
    """Fingerprints of the inputs and settings behind a report, so it can be reproduced.

    Equal digests mean equal inputs: two reports with the same manifest must show the same
    facts and flags, which an auditor can verify by running the tool again.
    """

    tool_version: NonEmptyStr = Field(description="Installed version of aml-reporter.")
    case_id: CaseId = Field(description="Case the report describes.")
    bundle_sha256: Sha256 = Field(description="Digest of the validated case bundle.")
    rules_sha256: Sha256 = Field(description="Digest of the validated red-flag rules.")
    prompts_sha256: Sha256 = Field(description="Digest of the packaged LLM prompt files.")
    enricher: NonEmptyStr = Field(description="Enricher name, as on the command line.")
    model: NonEmptyStr = Field(description="LLM behind the enricher, or `rules` without one.")
    generated_at: AwareDatetime = Field(description="When the report was generated.")
