"""Detailed report sections: per-class scores, confusion matrices, and rejected answers."""

from .markdown import TASK_NAMES, details, table
from .models import EvaluationRun, TaskScore

CLASS_TASKS = ("counterparty_type", "payment_purpose")  # Tasks scored class by class


def _confusion(score: TaskScore) -> list[str]:
    """Build a confusion matrix, labels in rows and predictions in columns.

    Args:
        score: Score of a classification task.

    Returns:
        Table lines.
    """
    classes = list(score.confusion)
    rows = [[f"**{label}**", *score.confusion[label].values()] for label in classes]
    return table(["Label \\ prediction", *classes], rows)


def class_sections(run: EvaluationRun) -> list[str]:
    """Build one section per classification task: F1 by class, then confusion matrices.

    Args:
        run: Evaluation run.

    Returns:
        Section lines.
    """
    lines = []
    for task in CLASS_TASKS:
        scores = [e.score(task) for e in run.enrichers]
        header = ["Class", "Labelled"]
        for e in run.enrichers:
            header += [f"{e.enricher}: precision", "recall", "F1"]
        rows = []
        for name, first in scores[0].classes.items():
            if not first.support:
                continue
            row: list[object] = [f"`{name}`", first.support]
            for score in scores:
                cls = score.classes[name]
                row += [f"{cls.precision:.2f}", f"{cls.recall:.2f}", f"{cls.f1:.2f}"]
            rows.append(row)
        macro = ", ".join(
            f"{e.enricher} {s.macro_f1:.2f}" for e, s in zip(run.enrichers, scores, strict=True)
        )
        lines += [
            f"## {TASK_NAMES[task]}, class by class",
            "",
            f"Macro F1, over the classes with labelled items except `none` and `unknown`: {macro}.",
            "",
        ]
        lines += table(header, rows)
        for e, score in zip(run.enrichers, scores, strict=True):
            lines += details(f"Confusion matrix, {e.enricher}", _confusion(score))
    return lines


def rejection_section(run: EvaluationRun) -> list[str]:
    """List the LLM answers that failed validation, which fell back to the baseline.

    Args:
        run: Evaluation run.

    Returns:
        Section lines; none when no enricher uses an LLM.
    """
    llms = [e for e in run.enrichers if e.model != "rules"]
    if not llms:
        return []
    rows = [
        [e.enricher, reason, count]
        for e in llms
        for reason, count in sorted(e.rejections.items(), key=lambda item: -item[1])
    ]
    intro = (
        "Answers that failed validation; those fields came from the baseline instead. A batch "
        "that failed as a whole counts once per description."
    )
    body = table(["Enricher", "Reason", "Descriptions"], rows, left=2) if rows else ["None.", ""]
    return ["## Rejected LLM answers", "", intro, "", *body]
