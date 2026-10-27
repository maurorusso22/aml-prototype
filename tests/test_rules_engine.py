"""The rule engine and the rule file format, on small hand-made fact sheets."""

from typing import Any

import pytest
from pydantic import ValidationError

from aml_reporter.models import Fact, FactCategory, FactSheet, RiskLevel
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
        **values: Values keyed by `f1`, `f2`, ...; each becomes fact F-TEST-00n.

    Returns:
        The fact sheet; every fact cites TX-000001 and its own transaction.
    """
    facts = [
        Fact(
            id=f"F-TEST-{int(key[1:]):03d}",
            category=FactCategory.TRANSACTION_BEHAVIOUR,
            label=key,
            value=value,
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
