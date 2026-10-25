"""Shared configuration for all domain models."""

from pydantic import BaseModel, ConfigDict


class DomainModel(BaseModel):
    """Base class for domain models.

    Models are immutable, so data cannot drift between pipeline stages, and they reject unknown
    fields, so typos in input files surface as errors instead of being silently dropped.
    """

    model_config = ConfigDict(frozen=True, extra="forbid", str_strip_whitespace=True)
