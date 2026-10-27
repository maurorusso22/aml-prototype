"""Registry of synthetic scenarios, each with the red flags and the outcome it should produce."""

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
    """A synthetic story, the red flags it should raise, and the outcome it should reach."""

    build: Callable[[SynthContext, int], ScenarioRun]
    expected_outcome: Outcome
    expected_flags: tuple[str, ...] = ()


SCENARIOS = {  # Scenario name to definition; the order fixes case numbers
    "fp_salary_bonus": Scenario(salary_bonus, Outcome.CLOSE),
    "fp_property_sale": Scenario(property_sale, Outcome.CLOSE),
    "structuring_cash": Scenario(structuring_cash, Outcome.ESCALATE, ("RF-STRUCTURING",)),
    "pass_through": Scenario(
        pass_through, Outcome.ESCALATE, ("RF-PASS-THROUGH", "RF-OUTFLOW-SPIKE")
    ),
    "dormant_reactivation": Scenario(
        dormant_reactivation,
        Outcome.ESCALATE,
        (
            "RF-DORMANT-REACTIVATION",
            "RF-FOREIGN-INFLOWS",
            "RF-CASH-WITHDRAWALS",
            "RF-OUTFLOW-SPIKE",
        ),
    ),
    "profile_mismatch": Scenario(
        profile_mismatch, Outcome.REQUEST_INFORMATION, ("RF-PROFILE-MISMATCH",)
    ),
}
