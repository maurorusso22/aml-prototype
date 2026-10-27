"""Commands that run the pipeline on one case bundle, step by step."""

from collections import Counter
from pathlib import Path
from typing import Annotated

import typer
from pydantic import TypeAdapter

from ..analytics import build_fact_sheet
from ..enrichment import enrichable
from ..models import Enrichment
from ..rules import assess, load_rules
from .app import (
    CaseFile,
    EnricherOption,
    OutputOption,
    app,
    choose_enricher,
    read_bundle,
    write_json,
)

ENRICHMENTS = TypeAdapter(list[Enrichment])  # Serialises enrichment lists to JSON


@app.command(help="Extract counterparties, IBANs, and payment purposes from a case bundle.")
def enrich(
    case_file: CaseFile,
    enricher: EnricherOption = None,
    limit: Annotated[int | None, typer.Option(help="Only the first N transfers.")] = None,
    output: OutputOption = None,
) -> None:
    """Enrich the transfers and direct debits of one case bundle.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        limit: Enrich only this many transactions, e.g. for a quick smoke test.
        output: File to write; standard output when omitted.
    """
    chosen = choose_enricher(enricher)
    bundle = read_bundle(case_file)
    enrichments = chosen.enrich(enrichable(bundle.transactions)[:limit])
    write_json(ENRICHMENTS.dump_json(enrichments, indent=2).decode(), output)
    sources = Counter(str(enrichment.source) for enrichment in enrichments)
    typer.echo(f"{len(enrichments)} enriched: {dict(sources)}", err=True)


@app.command(help="Compute every fact of a case bundle: the fact sheet.")
def analyze(
    case_file: CaseFile, enricher: EnricherOption = None, output: OutputOption = None
) -> None:
    """Enrich one case bundle and run every analyser on it.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        output: File to write; standard output when omitted.
    """
    chosen = choose_enricher(enricher)
    bundle = read_bundle(case_file)
    sheet = build_fact_sheet(bundle, chosen.enrich(bundle.transactions))
    write_json(sheet.model_dump_json(indent=2), output)
    typer.echo(f"{len(sheet.facts)} facts for {sheet.case_id}", err=True)


@app.command("assess", help="Raise red flags on a case bundle and rate its risk.")
def assess_case(
    case_file: CaseFile,
    enricher: EnricherOption = None,
    rules: Annotated[
        Path | None, typer.Option(help="TOML rule file; packaged rules if omitted.")
    ] = None,
    output: OutputOption = None,
) -> None:
    """Enrich one case bundle, compute its facts, and evaluate the red-flag rules.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        rules: Rule file; the packaged illustrative rules when omitted.
        output: File to write; standard output when omitted.
    """
    chosen, ruleset = choose_enricher(enricher), load_rules(rules)
    bundle = read_bundle(case_file)
    assessment = assess(build_fact_sheet(bundle, chosen.enrich(bundle.transactions)), ruleset)
    write_json(assessment.model_dump_json(indent=2), output)
    flags = ", ".join(flag.rule_id for flag in assessment.flags) or "none"
    typer.echo(f"risk {assessment.level} (score {assessment.score}); flags: {flags}", err=True)
