"""The rule engine and the rule file format, on small hand-made fact sheets."""

from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import Fact, FactCategory, FactSheet, FactStatus, RiskLevel
from aml_reporter.rules import RuleSet, assess, load_rules

CASE_ID = "CASE-000001"  # Any valid case identifier
RULES: dict[
    str, Any
] = {  # A two-rule set: one high rule with two conditions, one low rule on a string
    "points": {"low": 1, "medium": 2, "high": 3},
    "levels": {"medium": 2, "high": 3},
    "rules": [
        {
            "id": "RF-TEST-HIGH",
            "name": "Two conditions",
            "description": "Fires when both facts are large enough.",
            "severity": "high",
            "when": [
                {"fact": "F-TEST-001", "op": ">=", "value": 5},
                {"fact": "F-TEST-002", "op": ">", "value": 0.5},
            ],
        },
        {
            "id": "RF-TEST-LOW",
            "name": "Text match",
            "description": "Fires when a country list matches.",
            "severity": "low",
            "when": [{"fact": "F-TEST-003", "op": "==", "value": "DE"}],
        },
    ],
}


def sheet(**values: Any) -> FactSheet:
    """Build a fact sheet from fact numbers and values.

    Args:
        **values: Values keyed by `f1`, `f2`, ...; each becomes fact F-TEST-00n. A
            `FactStatus` builds a fact without a value, for that reason.

    Returns:
        The fact sheet; every fact cites TX-000001 and its own transaction.
    """
    facts = [
        Fact(
            id=f"F-TEST-{int(key[1:]):03d}",
            category=FactCategory.TRANSACTION_BEHAVIOUR,
            label=key,
            value=None if isinstance(value, FactStatus) else value,
            status=value if isinstance(value, FactStatus) else FactStatus.MEASURED,
            evidence=("TX-000001", f"TX-00000{int(key[1:]) + 1}"),
        )
        for key, value in values.items()
    ]
    return FactSheet(case_id=CASE_ID, facts=tuple(facts))


@pytest.mark.parametrize(
    ("values", "flags", "level"),
    [
        pytest.param({"f1": 5, "f2": 0.6, "f3": "DE"}, ["RF-TEST-HIGH", "RF-TEST-LOW"], "high"),
        pytest.param({"f1": 5, "f2": 0.5, "f3": "DE"}, ["RF-TEST-LOW"], "low", id="strict-gt"),
        pytest.param({"f2": 0.9, "f3": "FR"}, [], "low", id="missing-fact"),
        pytest.param({"f1": "many", "f2": 0.9}, [], "low", id="text-for-number"),
        pytest.param(
            {"f1": FactStatus.NO_BASELINE, "f2": 0.6}, ["RF-TEST-HIGH"], "high", id="from-zero"
        ),
        pytest.param({"f1": FactStatus.NO_ACTIVITY, "f2": 0.6}, [], "low", id="no-activity"),
        pytest.param({"f1": 9, "f2": 1.0}, ["RF-TEST-HIGH"], "high", id="high-only"),
    ],
)
def test_rules_fire_only_when_every_condition_holds(
    values: dict[str, Any], flags: list[str], level: str
) -> None:
    """Conditions are combined with AND; a missing or non-numeric fact never fires.

    Args:
        values: Fact values of the test sheet.
        flags: Rules expected to fire.
        level: Expected risk level.
    """
    assessment = assess(sheet(**values), RuleSet.model_validate(RULES))
    assert [flag.rule_id for flag in assessment.flags] == flags
    assert assessment.level is RiskLevel(level)


def test_flags_carry_facts_and_deduplicated_evidence() -> None:
    """A flag cites the facts it used and the union of their evidence, without repeats."""
    flag = assess(sheet(f1=5, f2=0.6), RuleSet.model_validate(RULES)).flags[0]
    assert flag.facts == ("F-TEST-001", "F-TEST-002")
    assert flag.evidence == ("TX-000001", "TX-000002", "TX-000003")


@pytest.mark.parametrize(
    ("values", "unevaluated"),
    [
        pytest.param({"f2": 0.9, "f3": "DE"}, {"RF-TEST-HIGH": ("F-TEST-001",)}, id="missing"),
        pytest.param(
            {"f1": FactStatus.UNAVAILABLE, "f2": 0.9, "f3": "DE"},
            {"RF-TEST-HIGH": ("F-TEST-001",)},
            id="unavailable",
        ),
        pytest.param(
            {"f1": "many", "f2": 0.9, "f3": "DE"},
            {"RF-TEST-HIGH": ("F-TEST-001",)},
            id="wrong-type",
        ),
        pytest.param({"f2": 0.1, "f3": "DE"}, {}, id="false-settles-unknown"),
        pytest.param({"f1": FactStatus.NO_ACTIVITY, "f3": "DE"}, {}, id="no-activity-settles"),
        pytest.param(
            {"f1": 5, "f2": 0.9}, {"RF-TEST-LOW": ("F-TEST-003",)}, id="flag-and-unevaluated"
        ),
    ],
)
def test_rules_without_data_are_reported_not_dropped(
    values: dict[str, Any], unevaluated: dict[str, tuple[str, ...]]
) -> None:
    """A rule some of whose facts cannot be read is not evaluable, unless another condition fails.

    Args:
        values: Fact values of the test sheet.
        unevaluated: Rules expected to be undecided, with the facts they could not read.
    """
    assessment = assess(sheet(**values), RuleSet.model_validate(RULES))
    assert {rule.rule_id: rule.facts for rule in assessment.unevaluated} == unevaluated
    assert assessment.complete == (not unevaluated)


@pytest.mark.parametrize(
    ("op", "fires"),
    [(">", True), (">=", True), ("!=", True), ("<", False), ("<=", False), ("==", False)],
)
def test_an_increase_from_zero_exceeds_any_threshold(op: str, fires: bool) -> None:
    """A fact with no baseline reads as above any multiple, whatever the operator.

    Args:
        op: Comparison operator.
        fires: Whether the rule should fire.
    """
    rule = {**RULES["rules"][0], "when": [{"fact": "F-TEST-001", "op": op, "value": 1000}]}
    ruleset = RuleSet.model_validate(RULES | {"rules": [rule]})
    assessment = assess(sheet(f1=FactStatus.NO_BASELINE), ruleset)
    assert bool(assessment.flags) is fires
    assert assessment.complete


def test_packaged_rules_load() -> None:
    """The illustrative rule file is valid and every rule has a distinct identifier."""
    ruleset = load_rules()
    assert len(ruleset.rules) == 7
    assert ruleset.levels.high > ruleset.levels.medium


@pytest.mark.parametrize(
    ("change", "message"),
    [
        pytest.param({"levels": {"medium": 3, "high": 2}}, "greater than", id="levels-reversed"),
        pytest.param({"points": {"low": 1, "high": 3}}, "low, medium, and high", id="no-medium"),
        pytest.param({"rules": RULES["rules"] * 2}, "duplicate rule ids", id="duplicate-ids"),
        pytest.param(
            {"rules": [{**RULES["rules"][0], "id": "flag-1"}]}, "String should match", id="bad-id"
        ),
        pytest.param(
            {
                "rules": [
                    {**RULES["rules"][0], "when": [{"fact": "F-TEST-001", "op": "~", "value": 1}]}
                ]
            },
            "Input should be",
            id="bad-operator",
        ),
        pytest.param(
            {
                "rules": [
                    {**RULES["rules"][0], "when": [{"fact": "F-TEST-001", "op": ">", "value": "5"}]}
                ]
            },
            "needs a numeric threshold",
            id="text-threshold",
        ),
        pytest.param(
            {"points": {"low": 0, "medium": 2, "high": 3}}, "must be positive", id="zero-points"
        ),
    ],
)
def test_invalid_rule_files_are_rejected(change: dict[str, Any], message: str) -> None:
    """Rule files that are inconsistent fail at load time, with a clear message.

    Args:
        change: Keys to overwrite in the valid rule set.
        message: Text the validation error must contain.
    """
    with pytest.raises(ValidationError, match=message):
        RuleSet.model_validate(RULES | change)
