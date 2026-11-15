"""Everything a report section can draw on, computed once per case."""

from dataclasses import dataclass
from datetime import datetime

from ..controls import QualityIssue, RunManifest
from ..models import CaseBundle, Enrichment, Fact, FactSheet, RiskAssessment

ENRICHED_PREFIXES = ("F-PURP-", "F-CPTY-", "F-GEO-")  # Fact areas built on enrichment
ENRICHED_FACTS = frozenset(  # Single facts built on enrichment, outside those areas
    {"F-ALERT-007", "F-ALERT-008", "F-ALERT-009", "F-PROF-003", "F-PROF-004"}
)


@dataclass(frozen=True)
class ReportData:
    """A case with its enrichments, facts, assessment, controls, and charts.

    Everything here is independent of the report language, so one instance serves every one.
    """

    bundle: CaseBundle
    enrichments: tuple[Enrichment, ...]
    sheet: FactSheet
    assessment: RiskAssessment
    quality: tuple[QualityIssue, ...]
    manifest: RunManifest
    flows_chart: bytes
    purposes_chart: bytes

    @property
    def enricher(self) -> str:
        """Name of the enricher that read the descriptions."""
        return self.manifest.enricher

    @property
    def generated_at(self) -> datetime:
        """When the report was generated."""
        return self.manifest.generated_at

    def facts(self, *prefixes: str) -> list[Fact]:
        """Select facts by identifier prefix, in the order of the prefixes given.

        Args:
            *prefixes: Prefixes such as `F-CASH-`.

        Returns:
            Matching facts, grouped by prefix.
        """
        return [
            fact for prefix in prefixes for fact in self.sheet.facts if fact.id.startswith(prefix)
        ]

    def has(self, fact_id: str) -> bool:
        """Tell whether the fact sheet contains a fact.

        Args:
            fact_id: Fact identifier.

        Returns:
            True when present.
        """
        return any(fact.id == fact_id for fact in self.sheet.facts)


def is_enriched(fact_id: str) -> bool:
    """Tell whether a fact depends on fields read by the enrichment stage.

    Args:
        fact_id: Fact identifier.

    Returns:
        True for facts the report marks with a dagger.
    """
    return fact_id.startswith(ENRICHED_PREFIXES) or fact_id in ENRICHED_FACTS
