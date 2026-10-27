"""Plain metrics on (label, prediction) pairs: accuracy, per-class scores, confusion."""

from collections import Counter
from collections.abc import Sequence

from .models import ClassScore

type Pair = tuple[str | None, str | None]


def accuracy(pairs: Sequence[Pair]) -> float:
    """Share of predictions equal to their label; two missing values count as equal.

    Args:
        pairs: Label and prediction of each item.

    Returns:
        Accuracy between 0 and 1, or 0 for no items.
    """
    return sum(label == prediction for label, prediction in pairs) / len(pairs) if pairs else 0.0


def missed(pairs: Sequence[Pair], empty: frozenset[str | None]) -> float:
    """Share of items with a labelled value that the prediction leaves empty.

    Args:
        pairs: Label and prediction of each item.
        empty: Values that mean "no value", such as None or "unknown".

    Returns:
        Miss rate between 0 and 1, over all items.
    """
    count = sum(label not in empty and prediction in empty for label, prediction in pairs)
    return count / len(pairs) if pairs else 0.0


def invented(pairs: Sequence[Pair], empty: frozenset[str | None]) -> float:
    """Share of items without a labelled value where the prediction still gives one.

    Args:
        pairs: Label and prediction of each item.
        empty: Values that mean "no value", such as None or "unknown".

    Returns:
        Invention rate between 0 and 1, over all items.
    """
    count = sum(label in empty and prediction not in empty for label, prediction in pairs)
    return count / len(pairs) if pairs else 0.0


def class_scores(pairs: Sequence[Pair], classes: Sequence[str]) -> dict[str, ClassScore]:
    """Compute precision, recall, and F1 of every class.

    Args:
        pairs: Label and prediction of each item.
        classes: Every class, in reporting order.

    Returns:
        Scores by class; a class never predicted or never labelled scores 0.
    """
    hits = Counter(label for label, prediction in pairs if label == prediction)
    labelled = Counter(label for label, _ in pairs)
    predicted = Counter(prediction for _, prediction in pairs)
    scores = {}
    for name in classes:
        precision = hits[name] / predicted[name] if predicted[name] else 0.0
        recall = hits[name] / labelled[name] if labelled[name] else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        scores[name] = ClassScore(
            precision=round(precision, 4),
            recall=round(recall, 4),
            f1=round(f1, 4),
            support=labelled[name],
        )
    return scores


def macro_f1(scores: dict[str, ClassScore]) -> float:
    """Average F1 over the classes that appear in the labels.

    Args:
        scores: Scores by class.

    Returns:
        Macro-averaged F1, or 0 when no class has support.
    """
    supported = [score.f1 for score in scores.values() if score.support]
    return round(sum(supported) / len(supported), 4) if supported else 0.0


def confusion(pairs: Sequence[Pair], classes: Sequence[str]) -> dict[str, dict[str, int]]:
    """Count predictions per label.

    Args:
        pairs: Label and prediction of each item.
        classes: Every class, in reporting order.

    Returns:
        Counts by label, then by prediction.
    """
    counts = Counter(pairs)
    return {label: {pred: counts[(label, pred)] for pred in classes} for label in classes}
