"""Prompt examples: written exactly as the model receives a batch and must answer it."""

import json
import re
from pathlib import Path

import pytest

from aml_reporter.enrichment.tasks import (
    COUNTERPARTY,
    COUNTERPARTY_TYPE,
    DESCRIPTION_TASKS,
    IBAN,
    PAYMENT_PURPOSE,
    Task,
)

TASKS = (IBAN, COUNTERPARTY, COUNTERPARTY_TYPE, PAYMENT_PURPOSE)  # Every task with a prompt file
EXAMPLE = re.compile(r"<input>\n(.+)\n</input>\n<output>\n(.+)\n</output>")  # One example batch
DATA_DIR = Path(__file__).parents[1] / "data"  # Synthetic cases scored by `aml-report evaluate`


def _example(task: Task) -> tuple[str, str]:
    """Read the only example of a prompt, as raw text.

    Args:
        task: Task whose prompt holds the example.

    Returns:
        The example user message and the example answer.
    """
    matches = EXAMPLE.findall(task.prompt)
    assert len(matches) == 1
    sent, returned = matches[0]
    return sent, returned


def _inputs(task: Task) -> list[str]:
    """Read the inputs of a prompt example.

    Args:
        task: Task whose prompt holds the example.

    Returns:
        Descriptions or names, in id order.
    """
    return [item[task.input_key] for item in json.loads(_example(task)[0])]


def _values(task: Task) -> list[object]:
    """Read the expected values of a prompt example, after schema validation.

    Args:
        task: Task whose prompt holds the example.

    Returns:
        One value per answer, in answer order.
    """
    answers = task.schema.model_validate_json(_example(task)[1]).answers
    return [getattr(answer, task.field) for answer in answers]


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.name)
def test_example_input_is_the_user_message(task: Task) -> None:
    """The example input is exactly what `Task.request` sends for those inputs.

    Args:
        task: Task under test.
    """
    assert _example(task)[0] == task.request(_inputs(task))


@pytest.mark.parametrize("task", TASKS, ids=lambda task: task.name)
def test_example_output_is_a_valid_answer(task: Task) -> None:
    """The example output fits the schema, answers every id in order, and passes every check.

    Args:
        task: Task under test.
    """
    returned = _example(task)[1]
    inputs, values = _inputs(task), _values(task)
    assert returned == json.dumps(json.loads(returned))
    ids = [answer["id"] for answer in json.loads(returned)["answers"]]
    assert ids == list(range(len(inputs)))
    for value, text in zip(values, inputs, strict=True):
        assert task.check(value, text) == value


def test_description_tasks_share_one_example_batch() -> None:
    """The three tasks that read descriptions show one batch, sorted as the enricher sends it."""
    batches = [_inputs(task) for task in DESCRIPTION_TASKS]
    assert all(batch == batches[0] for batch in batches)
    assert batches[0] == sorted(set(batches[0]))


def test_type_example_reads_the_names_found_by_the_counterparty_example() -> None:
    """The type example classifies the distinct names the counterparty example extracts."""
    names = {name for name in _values(COUNTERPARTY) if isinstance(name, str)}
    assert _inputs(COUNTERPARTY_TYPE) == sorted(names)


def test_examples_reuse_nothing_from_the_evaluation_data() -> None:
    """No example description or name comes from the scored cases, so scores stay honest."""
    texts: set[str] = set()
    names: set[str] = set()
    for path in (DATA_DIR / "samples").glob("*.json"):
        texts |= {tx["description"] for tx in json.loads(path.read_text("utf-8"))["transactions"]}
    for path in (DATA_DIR / "labels").glob("*.json"):
        labels = json.loads(path.read_text("utf-8"))["transactions"]
        names |= {label["counterparty_name"] for label in labels}
    assert texts and names
    assert not set(_inputs(COUNTERPARTY)) & texts
    assert not set(_inputs(COUNTERPARTY_TYPE)) & names
