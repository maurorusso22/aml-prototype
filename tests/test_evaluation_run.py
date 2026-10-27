"""The baseline evaluation runs on every scenario and holds its published quality."""

from types import SimpleNamespace
from typing import Any

import pytest

from aml_reporter.enrichment import BaselineEnricher, LLMEnricher
from aml_reporter.evaluation import EvaluationRun, evaluate, render
from aml_reporter.evaluation.runner import api_cost
from aml_reporter.llm import AnthropicClient
from aml_reporter.rules import load_rules
from aml_reporter.synthetic import SCENARIOS, generate_cases

MIN_ACCURACY = {  # Floor for the baseline, on all descriptions, task by task
    "iban": 0.99,
    "counterparty": 0.6,
    "counterparty_type": 0.8,
    "payment_purpose": 0.8,
}


@pytest.fixture(scope="module")
def run() -> EvaluationRun:
    """Evaluate the baseline once on every scenario.

    Returns:
        The evaluation run.
    """
    cases = [(case.bundle, case.labels) for case in generate_cases(list(SCENARIOS), 42)]
    return evaluate({"baseline": BaselineEnricher()}, cases, load_rules(), "seed 42")


def test_baseline_scores_every_description_and_case(run: EvaluationRun) -> None:
    """Every labelled description is scored, and every case gets its expected flags and level."""
    score = run.enrichers[0]
    assert score.descriptions == score.score("iban").items > 0
    assert (
        score.score("iban", "easy").items + score.score("iban", "hard").items == score.descriptions
    )
    assert score.llm_share == 0.0
    assert score.cost_usd is None
    assert all(case.correct for case in score.cases), [c for c in score.cases if not c.correct]


@pytest.mark.parametrize("task", MIN_ACCURACY)
def test_baseline_accuracy_stays_above_its_floor(run: EvaluationRun, task: str) -> None:
    """The rule-based extractor never drops below the quality it is known for.

    Args:
        run: Evaluation run.
        task: Task name.
    """
    assert run.enrichers[0].score(task).accuracy >= MIN_ACCURACY[task]


def test_baseline_never_invents_values(run: EvaluationRun) -> None:
    """Rules extract only what they match, so they never fill an empty label."""
    assert all(score.invented == 0.0 for score in run.enrichers[0].tasks)


def test_report_has_every_section(run: EvaluationRun) -> None:
    """The Markdown names the command, every section, and every scenario."""
    text = render(run)
    assert "`uv run aml-report evaluate --enricher baseline`" in text
    for heading in (
        "Summary",
        "Accuracy",
        "Missed and invented values",
        "Red flags and risk level",
    ):
        assert f"## {heading}" in text
    assert all(f"`{name}`" in text for name in SCENARIOS)
    assert "Rejected LLM answers" not in text


def test_api_cost_uses_list_prices() -> None:
    """A million input and output tokens on Haiku cost the list price; other enrichers none."""
    sdk: Any = SimpleNamespace()  # Never called: only the token counters matter here
    client = AnthropicClient(client=sdk)
    client.input_tokens = client.output_tokens = 1_000_000
    assert api_cost(LLMEnricher(client)) == pytest.approx(0.10 + 0.50)
    assert api_cost(BaselineEnricher()) is None
