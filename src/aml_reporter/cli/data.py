"""Command that generates the synthetic data."""

from pathlib import Path
from typing import Annotated

import typer

from ..synthetic import SCENARIOS, generate_cases, write_cases
from .app import app

DEFAULT_SEED = 42  # Seed of the committed sample data and of the README examples
DEFAULT_DATA_DIR = Path("data")  # Folder that receives samples/ and labels/


@app.command(help="Generate synthetic case bundles and their ground-truth labels.")
def synth(
    scenario: Annotated[
        list[str] | None, typer.Option(help="Scenario to generate; repeat it, or use 'all'.")
    ] = None,
    seed: Annotated[int, typer.Option(help="Random seed.")] = DEFAULT_SEED,
    out_dir: Annotated[Path, typer.Option(help="Output folder.")] = DEFAULT_DATA_DIR,
) -> None:
    """Generate synthetic case bundles and their ground-truth labels.

    Args:
        scenario: Scenario names; all scenarios when omitted or 'all'.
        seed: Random seed; the same seed always produces the same files.
        out_dir: Folder that receives samples/ and labels/.
    """
    names = list(SCENARIOS) if not scenario or "all" in scenario else scenario
    unknown = sorted(set(names) - set(SCENARIOS))
    if unknown:
        choices = ", ".join(SCENARIOS)
        raise typer.BadParameter(f"unknown scenario {', '.join(unknown)}; choose from {choices}")
    for path in write_cases(generate_cases(names, seed), out_dir):
        typer.echo(path)
