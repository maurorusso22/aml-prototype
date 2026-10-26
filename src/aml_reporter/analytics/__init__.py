"""Analytics: deterministic analysers that turn a case into traceable facts.

Importing this package registers every analyser; their order is the order of the facts.
"""

from . import (
    alert,
    cash,
    channels,
    counterparties,
    customer,
    flows,
    geography,
    profile,
    purposes,
    temporal,
)
from .registry import ANALYSERS, build_fact_sheet

__all__ = [  # Analyser modules are imported for their registration side effect
    "ANALYSERS",
    "alert",
    "build_fact_sheet",
    "cash",
    "channels",
    "counterparties",
    "customer",
    "flows",
    "geography",
    "profile",
    "purposes",
    "temporal",
]
