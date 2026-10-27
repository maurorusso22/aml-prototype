"""Evaluation: enrichers scored against the ground-truth labels of the synthetic cases."""

from .models import EnricherScore, EvaluationRun, TaskScore
from .report import render
from .runner import evaluate, load_cases

__all__ = [  # Public names of the evaluation package
    "EnricherScore",
    "EvaluationRun",
    "TaskScore",
    "evaluate",
    "load_cases",
    "render",
]
