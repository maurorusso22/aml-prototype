"""Command-line interface: `aml-report`.

Importing the command modules registers their commands on the application.
"""

from . import data, pipeline
from .app import app

__all__ = ["app", "data", "pipeline"]  # Command modules are imported for their registration
