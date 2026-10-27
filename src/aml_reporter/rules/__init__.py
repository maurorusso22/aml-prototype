"""Red-flag rules: transparent, configurable checks on the facts of a case."""

from .config import Condition, Rule, RuleSet, load_rules
from .engine import assess

__all__ = ["Condition", "Rule", "RuleSet", "assess", "load_rules"]  # Public names
