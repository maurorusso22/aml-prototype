"""The `aml-report` application object and the helpers its commands share."""

import logging
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from pydantic import ValidationError

from ..enrichment import Enricher, make_enricher
from ..models import CaseBundle
from ..settings import ENRICHERS, Settings

app = typer.Typer(help="AI-assisted AML investigation reports. Prototype on synthetic data.")

CaseFile = Annotated[Path, typer.Argument(help="Case bundle JSON file.")]
EnricherOption = Annotated[
    str | None, typer.Option(help="local, anthropic, or baseline; default AML_ENRICHER.")
]
OutputOption = Annotated[Path | None, typer.Option(help="Write JSON here, not stdout.")]
RulesOption = Annotated[
    Path | None, typer.Option(help="TOML rule file; packaged rules if omitted.")
]
LISTED_PROBLEMS = 10  # Validation problems spelled out when a bundle is rejected; the rest counted


@app.callback()
def main() -> None:
    """AI-assisted AML investigation reports. Prototype on synthetic data."""
    load_dotenv(Path.cwd() / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


def choose_enricher(name: str | None) -> Enricher:
    """Build the enricher chosen on the command line or in the settings.

    Args:
        name: Enricher name; the AML_ENRICHER setting when None.

    Returns:
        The enricher.
    """
    settings = Settings.from_env()
    chosen = name or settings.enricher
    if chosen not in ENRICHERS:
        raise typer.BadParameter(f"unknown enricher {chosen}; choose from {', '.join(ENRICHERS)}")
    return make_enricher(chosen, settings)


def read_bundle(path: Path) -> CaseBundle:
    """Load and validate a case bundle, rejecting it with a readable list of problems.

    Messages name fields and identifiers but never echo input values, which may be personal data.

    Args:
        path: Case bundle JSON file.

    Returns:
        The validated bundle.

    Raises:
        typer.BadParameter: When the file cannot be read or the bundle is invalid.
    """
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise typer.BadParameter(f"cannot read case bundle {path}: {error.strerror}") from error
    try:
        return CaseBundle.model_validate_json(text)
    except ValidationError as error:
        raise typer.BadParameter(f"invalid case bundle {path}: {_problems(error)}") from error


def _problems(error: ValidationError) -> str:
    """List validation problems by field, leaving out the offending input values.

    Args:
        error: Validation error of a case bundle.

    Returns:
        The first `LISTED_PROBLEMS` problems, separated by semicolons, and how many remain.
    """
    problems = []
    for item in error.errors():
        where = ".".join(str(part) for part in item["loc"])
        problems.append(f"{where}: {item['msg']}" if where else item["msg"])
    remaining = len(problems) - LISTED_PROBLEMS
    listed = "; ".join(problems[:LISTED_PROBLEMS])
    return listed + (f" (and {remaining} more)" if remaining > 0 else "")


def write_json(payload: str, output: Path | None) -> None:
    """Write JSON to a file, creating its folder, or to standard output.

    Args:
        payload: JSON text.
        output: Destination file; standard output when None.
    """
    if output is None:
        typer.echo(payload)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
