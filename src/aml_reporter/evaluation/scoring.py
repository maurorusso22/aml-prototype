"""Score enrichments against ground-truth labels, task by task and subset by subset."""

from collections.abc import Callable, Sequence

from ..models import CounterpartyType, Enrichment, PaymentPurpose
from ..synthetic import TransactionLabel
from .metrics import Pair, accuracy, class_scores, confusion, invented, macro_f1, missed
from .models import TaskScore

type Item = tuple[TransactionLabel, Enrichment]
type Reader = Callable[[TransactionLabel, Enrichment], Pair]

NONE = "none"  # Class name of a missing counterparty type
TYPE_CLASSES = (*[str(kind) for kind in CounterpartyType], NONE)  # Counterparty type classes
PURPOSE_CLASSES = tuple(str(purpose) for purpose in PaymentPurpose)  # Payment purpose classes
EMPTY = frozenset({None, NONE, str(PaymentPurpose.UNKNOWN)})  # Values that mean "no value"


def _name(value: str | None) -> str | None:
    """Normalise a name for comparison: case and spacing do not count.

    Args:
        value: Name or None.

    Returns:
        Case-folded name with single spaces, or None.
    """
    return " ".join(value.casefold().split()) if value else None


TASKS: dict[str, tuple[Reader, tuple[str, ...] | None]] = {  # Task: (pair reader, classes)
    "iban": (lambda label, got: (label.counterparty_iban, got.counterparty_iban), None),
    "counterparty": (
        lambda label, got: (_name(label.counterparty_name), _name(got.counterparty_name)),
        None,
    ),
    "counterparty_type": (
        lambda label, got: (
            str(label.counterparty_type or NONE),
            str(got.counterparty_type or NONE),
        ),
        TYPE_CLASSES,
    ),
    "payment_purpose": (
        lambda label, got: (str(label.payment_purpose), str(got.payment_purpose)),
        PURPOSE_CLASSES,
    ),
}


def score_tasks(items: Sequence[Item]) -> list[TaskScore]:
    """Score every task on all descriptions, then on the easy and the hard ones.

    Args:
        items: Each label with the enrichment of the same transaction.

    Returns:
        One score per task and subset.
    """
    subsets = (
        ("all", list(items)),
        ("easy", [item for item in items if not item[0].hard]),
        ("hard", [item for item in items if item[0].hard]),
    )
    scores = []
    for subset, selected in subsets:
        for task, (read, classes) in TASKS.items():
            pairs = [read(label, got) for label, got in selected]
            score = TaskScore(
                task=task,
                subset=subset,
                items=len(pairs),
                accuracy=round(accuracy(pairs), 4),
                missed=round(missed(pairs, EMPTY), 4),
                invented=round(invented(pairs, EMPTY), 4),
            )
            if classes:
                per_class = class_scores(pairs, classes)
                score.classes = per_class
                # Empty values are not a class: the missed and invented rates cover them
                score.macro_f1 = macro_f1({k: v for k, v in per_class.items() if k not in EMPTY})
                score.confusion = confusion(pairs, classes)
            scores.append(score)
    return scores
