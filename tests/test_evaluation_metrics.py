"""Evaluation metrics on small, hand-checked label and prediction pairs."""

import pytest

from aml_reporter.evaluation.metrics import (
    accuracy,
    class_scores,
    confusion,
    invented,
    macro_f1,
    missed,
)

EMPTY = frozenset({None, "unknown"})  # Values that mean "no value" in these tests
PAIRS = [  # Label, prediction
    ("rent", "rent"),
    ("rent", "unknown"),
    ("salary", "salary"),
    ("salary", "rent"),
    ("unknown", "salary"),
    ("unknown", "unknown"),
]
CLASSES = ("rent", "salary", "unknown")  # Every class of the pairs above


def test_accuracy_counts_exact_matches_and_empty_agreement() -> None:
    """Two missing values agree; an empty list scores zero instead of failing."""
    assert accuracy(PAIRS) == pytest.approx(3 / 6)
    assert accuracy([(None, None), ("x", None)]) == pytest.approx(0.5)
    assert accuracy([]) == 0.0


def test_missed_and_invented_split_the_empty_cases() -> None:
    """A miss empties a labelled value; an invention fills an empty one."""
    assert missed(PAIRS, EMPTY) == pytest.approx(1 / 6)
    assert invented(PAIRS, EMPTY) == pytest.approx(1 / 6)
    assert missed([], EMPTY) == invented([], EMPTY) == 0.0


def test_class_scores_and_macro_f1() -> None:
    """Precision, recall, and F1 follow their definitions, class by class."""
    scores = class_scores(PAIRS, CLASSES)
    rent, salary = scores["rent"], scores["salary"]
    assert (rent.precision, rent.recall, rent.support) == (0.5, 0.5, 2)
    assert (salary.precision, salary.recall, salary.f1) == (0.5, 0.5, 0.5)
    assert macro_f1(scores) == pytest.approx(0.5)


def test_classes_without_labels_do_not_count_in_macro_f1() -> None:
    """A class that is only ever predicted scores zero but leaves the average alone."""
    scores = class_scores([("rent", "rent"), ("rent", "salary")], CLASSES)
    assert scores["salary"].support == 0
    assert scores["salary"].f1 == 0.0
    assert macro_f1(scores) == scores["rent"].f1


def test_confusion_counts_every_label_and_prediction_pair() -> None:
    """Rows are labels, columns are predictions, and every pair is counted once."""
    matrix = confusion(PAIRS, CLASSES)
    assert matrix["rent"] == {"rent": 1, "salary": 0, "unknown": 1}
    assert matrix["unknown"]["salary"] == 1
    assert sum(sum(row.values()) for row in matrix.values()) == len(PAIRS)
