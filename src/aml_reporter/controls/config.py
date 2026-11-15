"""Tolerances of the data-quality checks, loaded from a TOML file and validated before use."""

import tomllib
from importlib.resources import files
from pathlib import Path

from pydantic import Field

from ..models.base import DomainModel


class QualityThresholds(DomainModel):
    """How much degradation the checks tolerate before warning."""

    max_fallback_share: float = Field(
        ge=0, le=1, description="Share of enriched records allowed to come from the fallback."
    )
    max_undescribed_share: float = Field(
        ge=0, le=1, description="Share of transfers and debits allowed an empty description."
    )


def load_thresholds(path: Path | None = None) -> QualityThresholds:
    """Read and validate a thresholds file.

    Args:
        path: TOML file; the packaged illustrative thresholds when omitted.

    Returns:
        The validated thresholds.
    """
    if path is None:
        text = files("aml_reporter.controls").joinpath("thresholds.toml").read_text("utf-8")
    else:
        text = path.read_text(encoding="utf-8")
    return QualityThresholds.model_validate(tomllib.loads(text))
