"""Shared fixtures for the test suite."""

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"  # Hand-written synthetic test data


def _load(name: str) -> dict[str, Any]:
    """Parse a JSON fixture file.

    Args:
        name: File name inside the fixtures directory.

    Returns:
        Parsed JSON object.
    """
    data: dict[str, Any] = json.loads((FIXTURES_DIR / name).read_text("utf-8"))
    return data


@pytest.fixture
def case_data() -> dict[str, Any]:
    """Load a fresh copy of the valid case bundle, with an individual customer.

    Returns:
        Raw case bundle, safe to mutate.
    """
    return _load("case_valid.json")


@pytest.fixture
def business_customer() -> dict[str, Any]:
    """Load a valid business customer that can replace the bundle's individual one.

    Returns:
        Raw customer, safe to mutate.
    """
    return _load("customer_business.json")
