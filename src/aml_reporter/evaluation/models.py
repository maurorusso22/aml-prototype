"""Evaluation results: scores per task, outcomes per case, and run metadata."""

from datetime import datetime

from pydantic import BaseModel, Field


class ClassScore(BaseModel):
    """Precision, recall, and F1 of one class of a classification task."""

    precision: float
    recall: float
    f1: float
    support: int = Field(description="Labelled items of this class.")


class TaskScore(BaseModel):
    """How one enricher did on one task, over one subset of descriptions."""

    task: str
    subset: str = Field(description="all, easy, or hard.")
    items: int
    accuracy: float = Field(description="Share of exact matches with the label.")
    missed: float = Field(description="Share left empty although the label has a value.")
    invented: float = Field(description="Share given a value although the label has none.")
    macro_f1: float | None = Field(default=None, description="Classification tasks only.")
    classes: dict[str, ClassScore] = Field(default_factory=dict)
    confusion: dict[str, dict[str, int]] = Field(
        default_factory=dict, description="Counts by label (outer) and prediction (inner)."
    )


class CaseOutcome(BaseModel):
    """Red flags and risk level of one case, against its ground truth."""

    scenario: str
    expected_flags: list[str]
    raised_flags: list[str]
    expected_level: str
    level: str

    @property
    def correct(self) -> bool:
        """Whether both the flags and the level match the ground truth."""
        return self.raised_flags == self.expected_flags and self.level == self.expected_level


class EnricherScore(BaseModel):
    """Everything measured for one enricher."""

    enricher: str
    model: str
    descriptions: int
    seconds: float = Field(description="Wall-clock time spent enriching.")
    llm_share: float = Field(description="Share of enrichments produced by the LLM.")
    cost_usd: float | None = Field(default=None, description="API cost at list prices, if any.")
    rejections: dict[str, int] = Field(default_factory=dict)
    tasks: list[TaskScore]
    cases: list[CaseOutcome]

    def per_thousand(self, value: float) -> float:
        """Scale a total to 1,000 descriptions.

        Args:
            value: Total over the evaluated descriptions.

        Returns:
            The value for 1,000 descriptions.
        """
        return value * 1000 / self.descriptions if self.descriptions else 0.0

    def score(self, task: str, subset: str = "all") -> TaskScore:
        """Find the score of one task on one subset.

        Args:
            task: Task name.
            subset: all, easy, or hard.

        Returns:
            The task score.
        """
        return next(s for s in self.tasks if s.task == task and s.subset == subset)


class EvaluationRun(BaseModel):
    """One evaluation of several enrichers on the same labelled data."""

    generated_at: datetime
    dataset: str = Field(description="Where the labelled data came from.")
    hard_items: int
    enrichers: list[EnricherScore]
