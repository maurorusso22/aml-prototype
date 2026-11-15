"""Red-flag rule definitions, loaded from a TOML file and validated before use."""

import tomllib
from collections import Counter
from importlib.resources import files
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, model_validator

from ..models import RiskLevel
from ..models.base import DomainModel
from ..models.formats import FactId, NonEmptyStr, RuleId

type Operator = Literal[">", ">=", "<", "<=", "==", "!="]

ORDERING = frozenset({">", ">=", "<", "<="})  # Operators that only make sense between numbers


class Condition(DomainModel):
    """A comparison between one fact and a threshold."""

    fact: FactId = Field(description="Fact to read.")
    op: Operator = Field(description="Comparison operator.")
    value: int | float | str = Field(description="Threshold or expected value.")

    @model_validator(mode="after")
    def check_threshold(self) -> Self:
        """Require a numeric threshold for ordering operators, so `> "5"` fails at load time.

        Returns:
            The validated condition.
        """
        if self.op in ORDERING and not isinstance(self.value, int | float):
            raise ValueError(f"{self.fact} {self.op} needs a numeric threshold")
        return self


class Rule(DomainModel):
    """A red flag: it fires when every one of its conditions holds."""

    id: RuleId = Field(description="Rule identifier, e.g. RF-STRUCTURING.")
    name: NonEmptyStr = Field(description="Short name of the red flag.")
    description: NonEmptyStr = Field(description="What the rule looks for, in plain words.")
    severity: RiskLevel = Field(description="Weight of the flag in the risk indicator.")
    when: tuple[Condition, ...] = Field(min_length=1, description="Conditions, all required.")


class Levels(DomainModel):
    """Minimum scores of the medium and high risk levels."""

    medium: int = Field(gt=0, description="Lowest score rated medium.")
    high: int = Field(gt=0, description="Lowest score rated high.")

    @model_validator(mode="after")
    def check_order(self) -> Self:
        """Require the high threshold to sit above the medium one.

        Returns:
            The validated levels.
        """
        if self.high <= self.medium:
            raise ValueError("levels.high must be greater than levels.medium")
        return self


class RuleSet(DomainModel):
    """Every rule, with the points and levels of the risk indicator."""

    points: dict[RiskLevel, int] = Field(description="Points added by a flag of each severity.")
    levels: Levels = Field(description="Score thresholds of the risk levels.")
    rules: tuple[Rule, ...] = Field(min_length=1, description="Rules, evaluated in order.")

    @model_validator(mode="after")
    def check_consistency(self) -> Self:
        """Require points for every severity and unique rule identifiers.

        Returns:
            The validated rule set.
        """
        if set(self.points) != set(RiskLevel):
            raise ValueError("points must give a value for low, medium, and high")
        if any(points <= 0 for points in self.points.values()):
            raise ValueError("points must be positive, or a raised flag would lower the score")
        duplicates = [rule_id for rule_id, n in Counter(r.id for r in self.rules).items() if n > 1]
        if duplicates:
            raise ValueError(f"duplicate rule ids: {', '.join(sorted(duplicates))}")
        return self


def load_rules(path: Path | None = None) -> RuleSet:
    """Read and validate a rule file.

    Args:
        path: TOML file; the packaged illustrative rules when omitted.

    Returns:
        The validated rule set.
    """
    if path is None:
        text = files("aml_reporter.rules").joinpath("rules.toml").read_text("utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    return RuleSet.model_validate(tomllib.loads(text))
