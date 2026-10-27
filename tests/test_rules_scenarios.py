"""Each synthetic scenario raises exactly its expected red flags, over several seeds."""

import pytest

from aml_reporter.analytics import build_fact_sheet
from aml_reporter.enrichment import BaselineEnricher
from aml_reporter.models import Outcome, RiskLevel
from aml_reporter.rules import assess, load_rules
from aml_reporter.synthetic import SCENARIOS, generate_cases

SEEDS = range(42, 47)  # Several seeds, so thresholds are not tuned to a single draw
LEVEL_FOR_OUTCOME = {  # Risk level the indicator should reach for each expected outcome
    Outcome.CLOSE: RiskLevel.LOW,
    Outcome.REQUEST_INFORMATION: RiskLevel.MEDIUM,
    Outcome.ESCALATE: RiskLevel.HIGH,
}


@pytest.mark.parametrize("seed", SEEDS)
def test_scenarios_raise_their_expected_flags(seed: int) -> None:
    """Flags match the ground truth exactly, and the risk level matches the expected outcome.

    False-positive scenarios raise no flag at all.

    Args:
        seed: Generation seed.
    """
    ruleset = load_rules()
    for case in generate_cases(list(SCENARIOS), seed):
        enrichments = BaselineEnricher().enrich(case.bundle.transactions)
        assessment = assess(build_fact_sheet(case.bundle, enrichments), ruleset)
        raised = tuple(flag.rule_id for flag in assessment.flags)
        scenario = case.labels.scenario
        assert raised == case.labels.expected_flags, f"{scenario} with seed {seed}"
        assert assessment.level is LEVEL_FOR_OUTCOME[case.labels.expected_outcome], scenario
