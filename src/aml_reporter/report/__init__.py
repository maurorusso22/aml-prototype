"""The Word investigation report: template text filled with facts, in English or Italian."""

from .builder import build_report, prepare_report, render_report, save_report
from .catalogs import LANGUAGES

__all__ = [  # Public names of the report package
    "LANGUAGES",
    "build_report",
    "prepare_report",
    "render_report",
    "save_report",
]
