"""Tests for the `aml-report` command line."""

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


def test_synth_rejects_unknown_scenarios(tmp_path: Path) -> None:
    """An unknown scenario name fails before anything is written."""
    result = RUNNER.invoke(app, ["synth", "--scenario", "nope", "--out-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "unknown scenario nope" in result.output
    assert not any(tmp_path.iterdir())
