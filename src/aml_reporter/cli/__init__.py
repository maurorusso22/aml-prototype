"""Command-line interface: `aml-report`.

Importing the command modules registers their commands on the application.
"""

from . import checks, data, documents, evaluation, pipeline
from .app import app

__all__ = [
    "app",
    "checks",
    "data",
    "documents",
    "evaluation",
    "pipeline",
]  # Command modules register their commands
