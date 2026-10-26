"""Contract shared by every LLM backend."""

from typing import Protocol

from pydantic import BaseModel, ValidationError


class LLMError(Exception):
    """A backend produced no usable answer: API failure, refusal, timeout, or invalid output.

    Messages never include prompt or answer text, so they are safe to log.
    """


class LLMClient(Protocol):
    """A chat model that answers with JSON matching a Pydantic schema."""

    def complete[T: BaseModel](self, system: str, user: str, schema: type[T]) -> T:
        """Ask one question and parse the answer.

        Args:
            system: Task instructions.
            user: The items to process, as JSON text.
            schema: Pydantic model the answer must match.

        Returns:
            The validated answer.

        Raises:
            LLMError: When no valid answer could be obtained.
        """
        ...


def parse_json[T: BaseModel](text: str, schema: type[T]) -> T:
    """Validate raw model output against a schema.

    Args:
        text: Raw JSON text returned by a model.
        schema: Pydantic model the answer must match.

    Returns:
        The validated answer.

    Raises:
        LLMError: When the text is not valid JSON or does not match the schema.
    """
    try:
        return schema.model_validate_json(text)
    except ValidationError as error:
        problems = error.error_count()
        raise LLMError(f"output does not match {schema.__name__} ({problems} problems)") from error
