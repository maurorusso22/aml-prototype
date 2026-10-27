"""Generate synthetic cases with their labels, and write them to disk."""

from collections.abc import Sequence
from pathlib import Path

from .assemble import GeneratedCase, assemble
from .context import SynthContext
from .scenarios import SCENARIOS


def generate_cases(names: Sequence[str], seed: int) -> list[GeneratedCase]:
    """Generate one case per scenario.

    Case numbers follow the registry order, not the order of `names`, so a case keeps its
    identifiers and content whichever subset of scenarios is generated.

    Args:
        names: Scenario names, each a key of `SCENARIOS`.
        seed: Global seed.

    Returns:
        Generated cases, in the order of `names`.
    """
    registry = list(SCENARIOS)
    cases = []
    for name in names:
        case_index = registry.index(name) + 1
        scenario = SCENARIOS[name]
        run = scenario.build(SynthContext.create(seed, case_index), case_index)
        cases.append(assemble(run, name, scenario.expected_outcome, scenario.expected_flags))
    return cases


def write_cases(cases: Sequence[GeneratedCase], out_dir: Path) -> list[Path]:
    """Write bundles to `samples/` and labels to `labels/`, one JSON file per scenario.

    Args:
        cases: Cases to write.
        out_dir: Folder that receives the two subfolders.

    Returns:
        Paths of the written files.
    """
    written = []
    for case in cases:
        for folder, model in (("samples", case.bundle), ("labels", case.labels)):
            path = out_dir / folder / f"{case.labels.scenario}.json"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(model.model_dump_json(indent=2) + "\n", encoding="utf-8")
            written.append(path)
    return written
