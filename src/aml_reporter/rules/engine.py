"""Evaluate red-flag rules on a fact sheet and derive the risk indicator.

Each condition is true, false, or unknown. Unknown means the case lacks the data: the fact is
missing or of a type the operator cannot compare. A rule fires when every condition is true,
does not fire when any is false, and is otherwise not evaluable: it is reported as such instead
of being read as an absence of risk.
"""

import operator
from collections.abc import Callable, Mapping
from typing import Any

from ..models import (
    Fact,
    FactSheet,
    RedFlag,
    RiskAssessment,
    RiskLevel,
    UnevaluatedRule,
)
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
        The red flags raised, the rules that could not be decided, and the risk indicator.
    """
    facts = {fact.id: fact for fact in sheet.facts}
    flags: list[RedFlag] = []
    unevaluated: list[UnevaluatedRule] = []
    for rule in ruleset.rules:
        outcome = _evaluate(rule, facts)
        if isinstance(outcome, RedFlag):
            flags.append(outcome)
        elif isinstance(outcome, UnevaluatedRule):
            unevaluated.append(outcome)
    score = sum(ruleset.points[flag.severity] for flag in flags)
    if score >= ruleset.levels.high:
        level = RiskLevel.HIGH
    elif score >= ruleset.levels.medium:
        level = RiskLevel.MEDIUM
    else:
        level = RiskLevel.LOW
    return RiskAssessment(
        case_id=sheet.case_id,
        flags=tuple(flags),
        unevaluated=tuple(unevaluated),
        score=score,
        level=level,
    )


def _evaluate(rule: Rule, facts: Mapping[str, Fact]) -> RedFlag | UnevaluatedRule | None:
    """Combine the conditions of a rule with three-valued logic.

    A false condition settles the rule even when others are unknown, as in `False and x`.

    Args:
        rule: Rule to evaluate.
        facts: Facts of the case, by identifier.

    Returns:
        The red flag when it fires, the unevaluated rule when data is missing, else None.
    """
    checks = [(condition, _holds(condition, facts.get(condition.fact))) for condition in rule.when]
    if any(result is False for _, result in checks):
        return None
    unknown = [condition.fact for condition, result in checks if result is None]
    if unknown:
        return UnevaluatedRule(
            rule_id=rule.id,
            name=rule.name,
            severity=rule.severity,
            facts=tuple(dict.fromkeys(unknown)),
        )
    used = [facts[condition.fact] for condition in rule.when]
    evidence = dict.fromkeys(tx for fact in used for tx in fact.evidence)
    return RedFlag(
        rule_id=rule.id,
        name=rule.name,
        description=rule.description,
        severity=rule.severity,
        facts=tuple(dict.fromkeys(fact.id for fact in used)),
        evidence=tuple(evidence),
    )


def _holds(condition: Condition, fact: Fact | None) -> bool | None:
    """Compare a fact with a condition, or tell that the comparison cannot be made.

    Args:
        condition: Comparison to apply.
        fact: Fact the condition reads; None when the case has no such fact.

    Returns:
        True or False, or None when the fact is missing or of the wrong type.
    """
    if fact is None:
        return None
    value = fact.value
    if condition.op in ("==", "!="):
        return bool(OPERATORS[condition.op](value, condition.value))
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    return bool(OPERATORS[condition.op](value, condition.value))
