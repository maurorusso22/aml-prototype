"""The four LLM tasks: prompt, answer schema, and the check each answer must pass.

Each task is evaluated on its own. Three read descriptions; the counterparty type task reads the
names found by the counterparty task.
"""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from functools import cache
from importlib.resources import files

from pydantic import BaseModel, ConfigDict

from ..models import CounterpartyType, PaymentPurpose
from .validation import check_iban, check_label, check_name


class Strict(BaseModel):
    """Answer schema that rejects unexpected fields."""

    model_config = ConfigDict(extra="forbid")


class Answer(Strict):
    """One answer, matched to its input item by `id`."""

    id: int


class Answers(Strict):
    """A batch of answers."""

    answers: Sequence[Answer]


class IbanAnswer(Answer):
    """Counterparty IBAN, or None when the text shows none."""

    iban: str | None


class IbanAnswers(Answers):
    """A batch of IBAN answers."""

    answers: list[IbanAnswer]


class CounterpartyAnswer(Answer):
    """Counterparty name as written, or None when the text names nobody."""

    counterparty_name: str | None


class CounterpartyAnswers(Answers):
    """A batch of counterparty answers."""

    answers: list[CounterpartyAnswer]


class TypeAnswer(Answer):
    """Legal nature of a counterparty."""

    counterparty_type: CounterpartyType


class TypeAnswers(Answers):
    """A batch of counterparty type answers."""

    answers: list[TypeAnswer]


class PurposeAnswer(Answer):
    """Purpose of a payment."""

    payment_purpose: PaymentPurpose


class PurposeAnswers(Answers):
    """A batch of payment purpose answers."""

    answers: list[PurposeAnswer]


@dataclass(frozen=True)
class Task:
    """How to ask one question and how to check its answers."""

    name: str
    input_key: str
    schema: type[Answers]
    field: str
    check: Callable[[object, str], object]

    @property
    def prompt(self) -> str:
        """Load the task instructions from the packaged prompt file.

        Returns:
            Prompt text.
        """
        return _load_prompt(self.name)


@cache
def _load_prompt(name: str) -> str:
    """Read a prompt file once.

    Args:
        name: Task name, which is also the prompt file stem.

    Returns:
        Prompt text.
    """
    return files("aml_reporter.enrichment").joinpath("prompts", f"{name}.md").read_text("utf-8")


IBAN = Task("iban", "text", IbanAnswers, "iban", check_iban)  # Counterparty IBAN
COUNTERPARTY = Task(  # Counterparty name
    "counterparty", "text", CounterpartyAnswers, "counterparty_name", check_name
)
COUNTERPARTY_TYPE = Task(  # Natural or legal person, from the name
    "counterparty_type", "name", TypeAnswers, "counterparty_type", check_label
)
PAYMENT_PURPOSE = Task(  # Purpose behind the description
    "payment_purpose", "text", PurposeAnswers, "payment_purpose", check_label
)
DESCRIPTION_TASKS = (IBAN, COUNTERPARTY, PAYMENT_PURPOSE)  # Tasks that read descriptions
