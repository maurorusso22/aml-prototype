"""Command-line interface: `aml-report`."""

import logging
from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from dotenv import load_dotenv
from pydantic import TypeAdapter

from .analytics import build_fact_sheet
from .enrichment import Enricher, enrichable, make_enricher
from .models import CaseBundle, Enrichment
from .settings import ENRICHERS, Settings
from .synthetic import SCENARIOS, generate_cases, write_cases

DEFAULT_SEED = 42  # Seed of the committed sample data and of the README examples
DEFAULT_DATA_DIR = Path("data")  # Folder that receives samples/ and labels/
ENRICHMENTS = TypeAdapter(list[Enrichment])  # Serialises enrichment lists to JSON

app = typer.Typer(help="AI-assisted AML investigation reports. Prototype on synthetic data.")


@app.callback()
def main() -> None:
    """AI-assisted AML investigation reports. Prototype on synthetic data."""
    load_dotenv(Path.cwd() / ".env")
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


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


@app.command(help="Extract counterparties, IBANs, and payment purposes from a case bundle.")
def enrich(
    case_file: Annotated[Path, typer.Argument(help="Case bundle JSON file.")],
    enricher: Annotated[
        str | None, typer.Option(help="local, anthropic, or baseline; default AML_ENRICHER.")
    ] = None,
    limit: Annotated[int | None, typer.Option(help="Only the first N transfers.")] = None,
    output: Annotated[Path | None, typer.Option(help="Write JSON here, not stdout.")] = None,
) -> None:
    """Enrich the transfers and direct debits of one case bundle.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        limit: Enrich only this many transactions, e.g. for a quick smoke test.
        output: File to write; standard output when omitted.
    """
    chosen = _enricher(enricher)
    bundle = CaseBundle.model_validate_json(case_file.read_text(encoding="utf-8"))
    enrichments = chosen.enrich(enrichable(bundle.transactions)[:limit])
    _write(ENRICHMENTS.dump_json(enrichments, indent=2).decode(), output)
    sources = Counter(str(enrichment.source) for enrichment in enrichments)
    typer.echo(f"{len(enrichments)} enriched: {dict(sources)}", err=True)


@app.command(help="Compute every fact of a case bundle: the fact sheet.")
def analyze(
    case_file: Annotated[Path, typer.Argument(help="Case bundle JSON file.")],
    enricher: Annotated[
        str | None, typer.Option(help="local, anthropic, or baseline; default AML_ENRICHER.")
    ] = None,
    output: Annotated[Path | None, typer.Option(help="Write JSON here, not stdout.")] = None,
) -> None:
    """Enrich one case bundle and run every analyser on it.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        output: File to write; standard output when omitted.
    """
    chosen = _enricher(enricher)
    bundle = CaseBundle.model_validate_json(case_file.read_text(encoding="utf-8"))
    sheet = build_fact_sheet(bundle, chosen.enrich(bundle.transactions))
    _write(sheet.model_dump_json(indent=2), output)
    typer.echo(f"{len(sheet.facts)} facts for {sheet.case_id}", err=True)


def _enricher(name: str | None) -> Enricher:
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


def _write(payload: str, output: Path | None) -> None:
    """Write JSON to a file, or to standard output.

    Args:
        payload: JSON text.
        output: Destination file; standard output when None.
    """
    if output is None:
        typer.echo(payload)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload + "\n", encoding="utf-8")
