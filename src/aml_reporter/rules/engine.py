"""Evaluate red-flag rules on a fact sheet and derive the risk indicator."""

import operator
from collections.abc import Callable, Mapping
from typing import Any

from ..models import Fact, FactSheet, RedFlag, RiskAssessment, RiskLevel
from .config import Condition, Rule, RuleSet

OPERATORS: dict[str, Callable[[Any, Any], Any]] = {  # Operator symbol to comparison
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


def assess(sheet: FactSheet, ruleset: RuleSet) -> RiskAssessment:
    """Run every rule, sum the points of the raised flags, and map the score to a level.

    Args:
        sheet: Facts of one case.
        ruleset: Rules and risk indicator settings.

    Returns:
        The red flags raised and the risk indicator.
    """
    facts = {fact.id: fact for fact in sheet.facts}
    flags = [flag for rule in ruleset.rules if (flag := _evaluate(rule, facts)) is not None]
    score = sum(ruleset.points[flag.severity] for flag in flags)
    if score >= ruleset.levels.high:
        level = RiskLevel.HIGH
    elif score >= ruleset.levels.medium:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    return RiskAssessment(case_id=sheet.case_id, flags=tuple(flags), score=score, level=level)


def _evaluate(rule: Rule, facts: Mapping[str, Fact]) -> RedFlag | None:
    """Check every condition of a rule; a missing fact makes the condition false.

    Args:
        rule: Rule to evaluate.
        facts: Facts of the case, by identifier.

    Returns:
        The red flag when every condition holds, otherwise None.
    """
    used: list[Fact] = []
    for condition in rule.when:
        fact = facts.get(condition.fact)
        if fact is None or not _holds(condition, fact.value):
            return None
        used.append(fact)
    evidence = dict.fromkeys(tx for fact in used for tx in fact.evidence)
    return RedFlag(
        rule_id=rule.id,
        name=rule.name,
        description=rule.description,
        severity=rule.severity,
        facts=tuple(fact.id for fact in used),
        evidence=tuple(evidence),
    )


def _holds(condition: Condition, value: bool | int | float | str) -> bool:
    """Compare a fact value with a condition; ordering applies to numbers only.

    Args:
        condition: Comparison to apply.
        value: Value of the fact.

    Returns:
        True when the comparison holds.
    """
    if condition.op in ("==", "!="):
        return bool(OPERATORS[condition.op](value, condition.value))
    numbers = (int, float)
    if isinstance(value, bool) or not isinstance(value, numbers):
        return False
    if not isinstance(condition.value, numbers):
        return False
    return bool(OPERATORS[condition.op](value, condition.value))
