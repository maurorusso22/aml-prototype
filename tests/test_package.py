"""Smoke tests for the package skeleton."""

import re

import aml_reporter


def test_version_is_semantic() -> None:
    """The package exposes its installed version as MAJOR.MINOR.PATCH."""
    assert re.fullmatch(r"\d+\.\d+\.\d+", aml_reporter.__version__)
