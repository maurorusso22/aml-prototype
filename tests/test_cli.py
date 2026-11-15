"""Tests for the `aml-report` command line."""

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from aml_reporter.cli import app

RUNNER = CliRunner()  # Invokes the CLI in-process
FIXTURES_DIR = Path(__file__).parent / "fixtures"  # Hand-written synthetic test data
ANSI_CODE = re.compile(r"\x1b\[[0-9;]*m")  # Colour codes Typer emits when it detects GitHub Actions


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


def test_analyze_writes_a_fact_sheet(tmp_path: Path) -> None:
    """`analyze` enriches a bundle and writes its fact sheet."""
    RUNNER.invoke(app, ["synth", "--scenario", "structuring_cash", "--out-dir", str(tmp_path)])
    bundle, output = tmp_path / "samples" / "structuring_cash.json", tmp_path / "facts.json"
    args = ["analyze", str(bundle), "--enricher", "baseline", "--output", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, result.output
    sheet = json.loads(output.read_text(encoding="utf-8"))
    assert sheet["case_id"] == "CASE-000003"
    assert "F-CASH-004" in {fact["id"] for fact in sheet["facts"]}


def test_assess_writes_flags_and_risk_level(tmp_path: Path) -> None:
    """`assess` writes the red flags and the risk indicator of a bundle."""
    RUNNER.invoke(app, ["synth", "--scenario", "structuring_cash", "--out-dir", str(tmp_path)])
    bundle, output = tmp_path / "samples" / "structuring_cash.json", tmp_path / "risk.json"
    args = ["assess", str(bundle), "--enricher", "baseline", "--output", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, result.output
    assessment = json.loads(output.read_text(encoding="utf-8"))
    assert [flag["rule_id"] for flag in assessment["flags"]] == ["RF-STRUCTURING"]
    assert assessment["level"] == "high"


def test_generate_writes_a_word_report(tmp_path: Path) -> None:
    """`generate` writes the report of a bundle in the requested language."""
    RUNNER.invoke(app, ["synth", "--scenario", "profile_mismatch", "--out-dir", str(tmp_path)])
    bundle, output = tmp_path / "samples" / "profile_mismatch.json", tmp_path / "out" / "r.docx"
    args = ["generate", str(bundle), "--enricher", "baseline", "--lang", "it", "--output"]
    result = RUNNER.invoke(app, [*args, str(output)])
    assert result.exit_code == 0, result.output
    assert output.read_bytes().startswith(b"PK")


def test_examples_writes_every_case_in_every_language(tmp_path: Path) -> None:
    """`examples` writes one report per sample case and language."""
    RUNNER.invoke(app, ["synth", "--scenario", "pass_through", "--out-dir", str(tmp_path)])
    args = ["examples", "--enricher", "baseline", "--data-dir", str(tmp_path)]
    result = RUNNER.invoke(app, [*args, "--out-dir", str(tmp_path / "examples")])
    assert result.exit_code == 0, result.output
    written = sorted(path.name for path in (tmp_path / "examples").iterdir())
    assert written == ["pass_through_en.docx", "pass_through_it.docx"]


def test_evaluate_writes_markdown_and_json(tmp_path: Path) -> None:
    """`evaluate` scores the baseline by default and writes both report formats."""
    RUNNER.invoke(app, ["synth", "--scenario", "pass_through", "--out-dir", str(tmp_path)])
    output = tmp_path / "docs" / "evaluation.md"
    args = ["evaluate", "--data-dir", str(tmp_path), "--output", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert "1/1 cases right" in result.output
    assert output.read_text(encoding="utf-8").startswith("# Evaluation")
    run = json.loads(output.with_suffix(".json").read_text(encoding="utf-8"))
    assert [score["enricher"] for score in run["enrichers"]] == ["baseline"]


def test_evaluate_needs_case_bundles(tmp_path: Path) -> None:
    """An empty data folder fails with a hint instead of an empty report."""
    result = RUNNER.invoke(app, ["evaluate", "--data-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "run synth first" in _plain(result.output)


def test_generate_rejects_unknown_languages(tmp_path: Path) -> None:
    """An unsupported language fails with a clear message."""
    result = RUNNER.invoke(app, ["generate", str(tmp_path / "x.json"), "--lang", "fr"])
    assert result.exit_code != 0
    assert "unknown language fr" in _plain(result.output)


def test_enrich_rejects_unknown_enrichers(tmp_path: Path) -> None:
    """An unknown enricher name fails with a clear message."""
    result = RUNNER.invoke(app, ["enrich", str(tmp_path / "x.json"), "--enricher", "magic"])
    assert result.exit_code != 0
    assert "unknown enricher magic" in _plain(result.output)


def test_synth_rejects_unknown_scenarios(tmp_path: Path) -> None:
    """An unknown scenario name fails before anything is written."""
    result = RUNNER.invoke(app, ["synth", "--scenario", "nope", "--out-dir", str(tmp_path)])
    assert result.exit_code != 0
    assert "unknown scenario nope" in _plain(result.output)
    assert not any(tmp_path.iterdir())


def _fixture_with(tmp_path: Path, **changes: str) -> Path:
    """Write the hand-written fixture bundle, with top-level fields changed, to a file.

    Args:
        tmp_path: Temporary folder.
        **changes: Top-level fields to overwrite.

    Returns:
        Path of the written bundle.
    """
    case = json.loads((FIXTURES_DIR / "case_valid.json").read_text(encoding="utf-8"))
    path = tmp_path / "case.json"
    path.write_text(json.dumps(case | changes), encoding="utf-8")
    return path


def test_check_passes_a_clean_case(tmp_path: Path) -> None:
    """`check --strict` exits 0 and writes an empty result for a complete case."""
    RUNNER.invoke(app, ["synth", "--scenario", "pass_through", "--out-dir", str(tmp_path)])
    bundle, output = tmp_path / "samples" / "pass_through.json", tmp_path / "check.json"
    args = ["check", str(bundle), "--enricher", "baseline", "--strict", "--output", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, result.output
    assert json.loads(output.read_text(encoding="utf-8"))["issues"] == []


def test_check_strict_fails_on_a_limited_case(tmp_path: Path) -> None:
    """A short history is a warning, and `--strict` turns it into exit status 1."""
    bundle = _fixture_with(tmp_path, period_start="2026-07-01")
    lenient = RUNNER.invoke(app, ["check", str(bundle), "--enricher", "baseline"])
    assert lenient.exit_code == 0, lenient.output
    assert "RF-OUTFLOW-SPIKE could not be evaluated" in lenient.output
    strict = RUNNER.invoke(app, ["check", str(bundle), "--enricher", "baseline", "--strict"])
    assert strict.exit_code == 1
    assert "Only 2 days of history" in strict.output


def test_assess_warns_about_undecided_rules(tmp_path: Path) -> None:
    """`assess` still writes the assessment, and warns that a rule could not be decided."""
    bundle = _fixture_with(tmp_path, period_start="2026-07-01")
    result = RUNNER.invoke(app, ["assess", str(bundle), "--enricher", "baseline"])
    assert result.exit_code == 0, result.output
    assert '"unevaluated"' in result.output
    assert "warning: RF-OUTFLOW-SPIKE could not be evaluated" in result.output


def test_invalid_bundles_are_rejected_without_their_values(tmp_path: Path) -> None:
    """A broken bundle fails with status 2, naming the problem but not the personal data."""
    case = json.loads((FIXTURES_DIR / "case_valid.json").read_text(encoding="utf-8"))
    case["transactions"][0]["currency"] = "USD"
    case["customer"]["tax_code"] = "SECRET-TAX-CODE"
    path = tmp_path / "broken.json"
    path.write_text(json.dumps(case), encoding="utf-8")
    result = RUNNER.invoke(app, ["assess", str(path), "--enricher", "baseline"])
    message = _plain(result.output)
    assert result.exit_code == 2
    assert "invalid case bundle" in message
    assert "tax_code" in message
    assert "SECRET-TAX-CODE" not in message


def test_missing_bundles_are_reported(tmp_path: Path) -> None:
    """A path that does not exist fails with a short message instead of a traceback."""
    result = RUNNER.invoke(app, ["check", str(tmp_path / "none.json"), "--enricher", "baseline"])
    assert result.exit_code == 2
    assert "cannot read case bundle" in _plain(result.output)


def _plain(output: str) -> str:
    """Reduce CLI output to plain text on one line.

    Typer prints errors in a Rich panel: colours, borders, and line wrapping depend on the
    terminal, so a message can be split across panel lines (e.g. by a long temporary path).

    Args:
        output: Text captured by the test runner.

    Returns:
        The words of the output, separated by single spaces.
    """
    return " ".join(ANSI_CODE.sub("", output).replace("│", " ").split())
