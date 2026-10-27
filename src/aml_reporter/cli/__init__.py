"""Command-line interface: `aml-report`.

Importing the command modules registers their commands on the application.
"""

from . import data, documents, pipeline
from .app import app

__all__ = ["app", "data", "documents", "pipeline"]  # Command modules register their commands
