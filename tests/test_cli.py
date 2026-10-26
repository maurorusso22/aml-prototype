"""Tests for the `aml-report` command line."""

import json
from pathlib import Path

from typer.testing import CliRunner

from aml_reporter.cli import app

RUNNER = CliRunner()  # Invokes the CLI in-process


def test_synth_writes_samples_and_labels(tmp_path: Path) -> None:
    """`synth` writes one bundle and one label file per requested scenario."""
    result = RUNNER.invoke(app, ["synth", "--scenario", "pass_through", "--out-dir", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert (tmp_path / "samples" / "pass_through.json").is_file()
    assert (tmp_path / "labels" / "pass_through.json").is_file()
    assert not (tmp_path / "samples" / "fp_salary_bonus.json").exists()


def test_enrich_writes_baseline_enrichments(tmp_path: Path) -> None:
    """`enrich` reads a bundle and writes one enrichment per transfer or debit."""
    RUNNER.invoke(app, ["synth", "--scenario", "pass_through", "--out-dir", str(tmp_path)])
    bundle, output = tmp_path / "samples" / "pass_through.json", tmp_path / "out.json"
    args = ["enrich", str(bundle), "--enricher", "baseline", "--limit", "5", "--output"]
    result = RUNNER.invoke(app, [*args, str(output)])
    assert result.exit_code == 0, result.output
    enrichments = json.loads(output.read_text(encoding="utf-8"))
    assert len(enrichments) == 5
    assert {enrichment["source"] for enrichment in enrichments} == {"baseline"}


def test_enrich_rejects_unknown_enrichers(tmp_path: Path) -> None:
    """An unknown enricher name fails with a clear message."""
    result = RUNNER.invoke(app, ["enrich", str(tmp_path / "x.json"), "--enricher", "magic"])
    assert result.exit_code != 0
    assert "unknown enricher magic" in result.output


def test_synth_rejects_unknown_scenarios(tmp_path: Path) -> None:
    """An unknown scenario name fails before anything is written."""
    result = RUNNER.invoke(app, ["synth", "--scenario", "nope", "--out-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "unknown scenario nope" in result.output
    assert not any(tmp_path.iterdir())
