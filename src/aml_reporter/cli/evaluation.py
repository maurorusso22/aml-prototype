"""The `evaluate` command: enrichers scored against the labels of the synthetic cases."""

from pathlib import Path
from typing import Annotated

import typer

from ..evaluation import evaluate, load_cases, render
from ..rules import load_rules
from .app import app, choose_enricher
from .data import DEFAULT_DATA_DIR

DEFAULT_OUTPUT = Path("docs") / "evaluation.md"  # Published results; JSON goes next to it


@app.command("evaluate", help="Score enrichers against the ground truth of the synthetic cases.")
def evaluate_enrichers(
    enricher: Annotated[
        list[str] | None,
        typer.Option(help="Enricher to score; repeat to compare. Default: baseline."),
    ] = None,
    data_dir: Annotated[Path, typer.Option(help="Folder written by synth.")] = DEFAULT_DATA_DIR,
    output: Annotated[Path, typer.Option(help="Markdown report to write.")] = DEFAULT_OUTPUT,
) -> None:
    """Enrich every labelled case with each enricher and publish the metrics.

    Args:
        enricher: Enricher names, in reporting order; the baseline when omitted.
        data_dir: Folder with `samples/` and `labels/`.
        output: Markdown file; the raw results go to the same path with a `.json` suffix.
    """
    chosen = {name: choose_enricher(name) for name in enricher or ["baseline"]}
    cases = load_cases(data_dir)
    if not cases:
        raise typer.BadParameter(f"no case bundles in {data_dir / 'samples'}; run synth first")
    run = evaluate(chosen, cases, load_rules(None), dataset=f"{data_dir.as_posix()}/")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render(run), encoding="utf-8")
    output.with_suffix(".json").write_text(run.model_dump_json(indent=2) + "\n", encoding="utf-8")
    for score in run.enrichers:
        right = sum(case.correct for case in score.cases)
        typer.echo(
            f"{score.enricher}: {score.llm_share:.0%} from the LLM, {score.seconds:.0f} s, "
            f"{right}/{len(score.cases)} cases right",
            err=True,
        )
    typer.echo(f"written {output}", err=True)
