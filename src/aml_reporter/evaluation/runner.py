"""Run enrichers over the labelled synthetic cases and measure quality, time, and cost."""

from collections import Counter
from collections.abc import Sequence
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter

from ..analytics import build_fact_sheet
from ..enrichment import Enricher, LLMEnricher
from ..llm import AnthropicClient
from ..models import CaseBundle, EnrichmentSource, Outcome, RiskLevel
from ..rules import RuleSet, assess
from ..synthetic import CaseLabels
from .models import CaseOutcome, EnricherScore, EvaluationRun
from .scoring import Item, score_tasks

type Case = tuple[CaseBundle, CaseLabels]

PRICES = {  # USD per million input and output tokens, for prompts under 100K tokens
    "claude-haiku-5-5": (0.10, 0.50),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-opus-5-5": (4.00, 20.00),
}
LEVEL_FOR_OUTCOME = {  # Risk level the indicator should reach for each expected outcome
    Outcome.CLOSE: RiskLevel.LOW,
    Outcome.REQUEST_INFORMATION: RiskLevel.MEDIUM,
    Outcome.ESCALATE: RiskLevel.HIGH,
}


def load_cases(data_dir: Path) -> list[Case]:
    """Read every case bundle in `samples/` with its labels from `labels/`.

    Args:
        data_dir: Folder written by `aml-report synth`.

    Returns:
        Bundles with their ground truth, sorted by file name.
    """
    cases = []
    for sample in sorted((data_dir / "samples").glob("*.json")):
        labels = data_dir / "labels" / sample.name
        cases.append(
            (
                CaseBundle.model_validate_json(sample.read_text(encoding="utf-8")),
                CaseLabels.model_validate_json(labels.read_text(encoding="utf-8")),
            )
        )
    return cases


def api_cost(enricher: Enricher) -> float | None:
    """Price the tokens an API-backed enricher used, at list prices.

    Args:
        enricher: Enricher after the run.

    Returns:
        Cost in USD, or None when there is no metered API behind it.
    """
    if not isinstance(enricher, LLMEnricher) or not isinstance(enricher.client, AnthropicClient):
        return None
    client = enricher.client
    price_in, price_out = PRICES.get(client.model, (0.0, 0.0))
    return (client.input_tokens * price_in + client.output_tokens * price_out) / 1_000_000


def evaluate_enricher(
    name: str, enricher: Enricher, cases: Sequence[Case], ruleset: RuleSet
) -> EnricherScore:
    """Enrich every case, score the fields, and check the red flags and risk level.

    Args:
        name: Enricher name, as on the command line.
        enricher: Enricher to evaluate.
        cases: Bundles with their ground truth.
        ruleset: Red-flag rules for the end-to-end check.

    Returns:
        Everything measured for this enricher.
    """
    items: list[Item] = []
    outcomes, sources, seconds = [], Counter[str](), 0.0
    for bundle, labels in cases:
        start = perf_counter()
        enrichments = enricher.enrich(bundle.transactions)
        seconds += perf_counter() - start
        sources.update(str(enrichment.source) for enrichment in enrichments)
        by_id = {enrichment.transaction_id: enrichment for enrichment in enrichments}
        items += [(label, by_id[label.transaction_id]) for label in labels.transactions]
        assessment = assess(build_fact_sheet(bundle, enrichments), ruleset)
        outcomes.append(
            CaseOutcome(
                scenario=labels.scenario,
                expected_flags=list(labels.expected_flags),
                raised_flags=[flag.rule_id for flag in assessment.flags],
                expected_level=str(LEVEL_FOR_OUTCOME[labels.expected_outcome]),
                level=str(assessment.level),
            )
        )
    llm = enricher.client if isinstance(enricher, LLMEnricher) else None
    total = sum(sources.values())
    return EnricherScore(
        enricher=name,
        model=getattr(llm, "model", "rules"),
        descriptions=total,
        seconds=round(seconds, 2),
        llm_share=round(sources[str(EnrichmentSource.LLM)] / total, 4) if total else 0.0,
        cost_usd=api_cost(enricher),
        rejections=dict(enricher.rejections) if isinstance(enricher, LLMEnricher) else {},
        tasks=score_tasks(items),
        cases=outcomes,
    )


def evaluate(
    enrichers: dict[str, Enricher], cases: Sequence[Case], ruleset: RuleSet, dataset: str
) -> EvaluationRun:
    """Evaluate several enrichers on the same cases.

    Args:
        enrichers: Enrichers by name, in reporting order.
        cases: Bundles with their ground truth.
        ruleset: Red-flag rules for the end-to-end check.
        dataset: Where the cases came from, for the report.

    Returns:
        The evaluation run.
    """
    return EvaluationRun(
        generated_at=datetime.now(UTC).replace(microsecond=0),
        dataset=dataset,
        hard_items=sum(label.hard for _, labels in cases for label in labels.transactions),
        enrichers=[evaluate_enricher(name, e, cases, ruleset) for name, e in enrichers.items()],
    )
