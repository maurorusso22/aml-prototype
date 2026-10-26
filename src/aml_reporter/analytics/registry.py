"""Plug-in registry of analysers, and the entry point that runs them all."""

from collections.abc import Callable, Sequence

from ..models import CaseBundle, Enrichment, Fact, FactSheet
from .base import AnalysisContext

type Analyser = Callable[[AnalysisContext], list[Fact]]

ANALYSERS: list[Analyser] = []  # Filled by @analyser, in module import order


def analyser(function: Analyser) -> Analyser:
    """Register an analyser; adding an analysis means writing one decorated function.

    Args:
        function: Function from the analysis context to facts.

    Returns:
        The same function, unchanged.
    """
    ANALYSERS.append(function)
    return function


def build_fact_sheet(bundle: CaseBundle, enrichments: Sequence[Enrichment]) -> FactSheet:
    """Run every registered analyser on a case.

    Args:
        bundle: Validated case bundle.
        enrichments: Structured fields extracted from its descriptions.

    Returns:
        The fact sheet, with fact identifiers checked for uniqueness.
    """
    by_transaction = {enrichment.transaction_id: enrichment for enrichment in enrichments}
    context = AnalysisContext(bundle, by_transaction)
    return FactSheet(
        case_id=bundle.case_id, facts=tuple(fact for run in ANALYSERS for fact in run(context))
    )
