"""Claude backend, through the official Anthropic SDK with structured outputs."""

from typing import Final

import anthropic
from pydantic import BaseModel, ValidationError

from .base import LLMError

DEFAULT_MODEL = "claude-haiku-5-5"  # Fast and cheap, enough for narrow tasks; AML_ANTHROPIC_MODEL
MAX_TOKENS = 16_000  # Ceiling per request; batch answers are short, but thinking counts too
EFFORT: Final = "low"  # Narrow extraction and classification need little reasoning


class AnthropicClient:
    """Calls Claude and turns every failure into an `LLMError`.

    No server-side model fallback is requested, since Claude Haiku 5.5 does not offer one: a
    refusal raises `LLMError`, and the caller falls back to the rule-based enricher.
    """

    def __init__(self, model: str = DEFAULT_MODEL, client: anthropic.Anthropic | None = None):
        """Create the backend.

        Args:
            model: Claude model identifier.
            client: SDK client; by default one that reads credentials from the environment.
        """
        self.model = model
        self.input_tokens = self.output_tokens = 0  # Usage so far, for cost estimates
        self._client = client or anthropic.Anthropic()

    def complete[T: BaseModel](self, system: str, user: str, schema: type[T]) -> T:
        """Ask Claude one question and parse the answer.

        Args:
            system: Task instructions.
            user: The items to process, as JSON text.
            schema: Pydantic model the answer must match.

        Returns:
            The validated answer.

        Raises:
            LLMError: On API errors, refusals, truncation, or output that fails the schema.
        """
        try:
            response = self._client.messages.parse(
                model=self.model,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=[{"role": "user", "content": user}],
                output_format=schema,
                output_config={"effort": EFFORT},
            )
        except anthropic.APIStatusError as error:
            raise LLMError(f"Anthropic API returned status {error.status_code}") from error
        except anthropic.APIConnectionError as error:
            raise LLMError("Anthropic API unreachable or timed out") from error
        except ValidationError as error:
            raise LLMError(f"output does not match {schema.__name__}") from error
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens
        if response.stop_reason != "end_turn" or response.parsed_output is None:
            raise LLMError(f"no usable answer (stop reason: {response.stop_reason})")
        return response.parsed_output
