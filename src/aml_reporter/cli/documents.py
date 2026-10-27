"""Command that writes the Word investigation report."""

from pathlib import Path
from typing import Annotated

import typer

from ..report import LANGUAGES, build_report, save_report
from ..settings import Settings
from .app import CaseFile, EnricherOption, app, choose_enricher, read_bundle

DEFAULT_REPORT_DIR = Path("output")  # Git-ignored folder for generated reports


@app.command(help="Write the Word investigation report of a case bundle.")
def generate(
    case_file: CaseFile,
    enricher: EnricherOption = None,
    lang: Annotated[str, typer.Option(help="Report language: en or it.")] = "en",
    output: Annotated[
        Path | None, typer.Option(help="Report file; output/<case>_<lang>.docx by default.")
    ] = None,
) -> None:
    """Enrich a case bundle, analyse it, raise red flags, and write the report.

    Args:
        case_file: Case bundle to read.
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        lang: Report language.
        output: Report file; a name built from the case and the language when omitted.
    """
    if lang not in LANGUAGES:
        raise typer.BadParameter(f"unknown language {lang}; choose from {', '.join(LANGUAGES)}")
    name = enricher or Settings.from_env().enricher
    chosen = choose_enricher(name)
    bundle = read_bundle(case_file)
    document = build_report(bundle, chosen.enrich(bundle.transactions), name, lang)
    path = output or DEFAULT_REPORT_DIR / f"{bundle.case_id}_{lang}.docx"
    typer.echo(save_report(document, path))
