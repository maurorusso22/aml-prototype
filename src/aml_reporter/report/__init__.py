"""The Word investigation report: template text filled with facts, in English or Italian."""

from .builder import build_report, save_report
from .catalogs import LANGUAGES

__all__ = ["LANGUAGES", "build_report", "save_report"]  # Public names of the report package
