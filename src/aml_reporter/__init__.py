"""AML Case Reporter: AI-assisted investigation reports for AML alerts.

Portfolio prototype. Every piece of data this package handles is synthetic.
"""

from importlib.metadata import version

__version__ = version("aml-reporter")  # Installed distribution version, from package metadata
__all__ = ["__version__"]  # Public names exported by the package
