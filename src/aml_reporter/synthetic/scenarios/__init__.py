"""Registry of synthetic scenarios, each with the outcome an analyst should reach."""

from collections.abc import Callable
from dataclasses import dataclass

from ...models import Outcome
from ..builder import ScenarioRun
from ..context import SynthContext
from .business import profile_mismatch
from .cash import structuring_cash
from .false_positives import property_sale, salary_bonus
from .flows import dormant_reactivation, pass_through


@dataclass(frozen=True)
class Scenario:
    """A synthetic story and its expected outcome."""

    build: Callable[[SynthContext, int], ScenarioRun]
    expected_outcome: Outcome


SCENARIOS = {  # Scenario name to definition; the order fixes case numbers
    "fp_salary_bonus": Scenario(salary_bonus, Outcome.CLOSE),
    "fp_property_sale": Scenario(property_sale, Outcome.CLOSE),
    "structuring_cash": Scenario(structuring_cash, Outcome.ESCALATE),
    "pass_through": Scenario(pass_through, Outcome.ESCALATE),
    "dormant_reactivation": Scenario(dormant_reactivation, Outcome.ESCALATE),
    "profile_mismatch": Scenario(profile_mismatch, Outcome.REQUEST_INFORMATION),
}
