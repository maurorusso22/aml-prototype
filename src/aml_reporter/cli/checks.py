"""Command that checks a case before anyone relies on it, and the warnings other commands print.

Exit status: 0 when the check ran, 1 with `--strict` when it found any issue, 2 when the bundle
is invalid or unreadable; batch pipelines can gate report delivery on it.
"""

from typing import Annotated

import typer

from ..analytics import build_fact_sheet
from ..controls import CaseCheck, check_quality, load_thresholds
from ..report.catalogs import load_catalog
from ..rules import assess, load_rules
from ..settings import Settings
from .app import (
    CaseFile,
    EnricherOption,
    OutputOption,
    RulesOption,
    app,
    choose_enricher,
    read_bundle,
    write_json,
)


@app.command(help="Check data quality and whether every rule can be decided.")
def check(
    case_file: CaseFile,
    enricher: EnricherOption = None,
    rules: RulesOption = None,
    strict: Annotated[bool, typer.Option(help="Exit with status 1 on any issue.")] = False,
    output: OutputOption = None,
) -> None:
    """Validate a case bundle, enrich it, and list what limits the conclusions on it.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        rules: Rule file; the packaged illustrative rules when omitted.
        strict: Fail when the case has any data-quality issue or undecided rule.
        output: File to write; standard output when omitted.
    """
    name = enricher or Settings.from_env().enricher
    chosen, ruleset = choose_enricher(name), load_rules(rules)
    bundle = read_bundle(case_file)
    enrichments = chosen.enrich(bundle.transactions)
    assessment = assess(build_fact_sheet(bundle, enrichments), ruleset)
    result = CaseCheck(
        case_id=bundle.case_id,
        issues=check_quality(bundle, enrichments, name, load_thresholds()),
        unevaluated=assessment.unevaluated,
    )
    write_json(result.model_dump_json(indent=2), output)
    warn(result)
    issues, undecided = len(result.issues), len(result.unevaluated)
    typer.echo(
        f"{bundle.case_id}: {issues} data-quality issues, {undecided} rules undecided", err=True
    )
    if strict and not result.clean:
        raise typer.Exit(1)


def warn(result: CaseCheck) -> None:
    """Print one warning per data-quality issue and undecided rule, in English, on stderr.

    Args:
        result: Issues and undecided rules of one case.
    """
    catalog = load_catalog("en")
    for issue in result.issues:
        typer.echo(f"warning: {catalog.t(f'dq_{issue.code}', **issue.details)}", err=True)
    for rule in result.unevaluated:
        facts = ", ".join(rule.facts)
        typer.echo(f"warning: {rule.rule_id} could not be evaluated, missing {facts}", err=True)
