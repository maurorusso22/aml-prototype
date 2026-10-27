"""Commands that write Word investigation reports: one case, or every example."""

from pathlib import Path
from typing import Annotated

import typer

from ..report import LANGUAGES, build_report, save_report
from ..settings import Settings
from .app import CaseFile, EnricherOption, app, choose_enricher, read_bundle
from .data import DEFAULT_DATA_DIR

DEFAULT_REPORT_DIR = Path("output")  # Git-ignored folder for generated reports
DEFAULT_EXAMPLES_DIR = Path("examples")  # Committed example reports, one per case and language


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


@app.command(help="Write the example reports: every sample case, in every language.")
def examples(
    enricher: EnricherOption = None,
    data_dir: Annotated[Path, typer.Option(help="Folder holding samples/.")] = DEFAULT_DATA_DIR,
    out_dir: Annotated[Path, typer.Option(help="Folder for the reports.")] = DEFAULT_EXAMPLES_DIR,
) -> None:
    """Enrich each sample case once, then write its report in every language.

    Args:
        enricher: Enricher name; the AML_ENRICHER setting when omitted.
        data_dir: Folder whose samples/ subfolder holds the case bundles.
        out_dir: Folder receiving `<scenario>_<lang>.docx` files.
    """
    name = enricher or Settings.from_env().enricher
    chosen = choose_enricher(name)
    for sample in sorted((data_dir / "samples").glob("*.json")):
        bundle = read_bundle(sample)
        enrichments = chosen.enrich(bundle.transactions)
        for lang in LANGUAGES:
            document = build_report(bundle, enrichments, name, lang)
            typer.echo(save_report(document, out_dir / f"{sample.stem}_{lang}.docx"))
