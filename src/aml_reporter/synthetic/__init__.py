"""Synthetic data: case bundles with realistic noise, and the ground truth to evaluate against.

Everything here is invented. Identifiers are invalid by construction, so they cannot match real
people, companies, accounts, or cards.
"""

from .assemble import GeneratedCase
from .generate import generate_cases, write_cases
from .labels import CaseLabels, TransactionLabel
from .scenarios import SCENARIOS

__all__ = [  # Public names of the synthetic data package
    "SCENARIOS",
    "CaseLabels",
    "GeneratedCase",
    "TransactionLabel",
    "generate_cases",
    "write_cases",
]
