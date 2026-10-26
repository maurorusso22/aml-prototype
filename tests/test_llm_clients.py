"""Backend clients turn every failure into an LLMError, without real network calls."""

import json
from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import httpx2
import pytest
from pydantic import ValidationError

from aml_reporter.enrichment.tasks import PurposeAnswers
from aml_reporter.llm import AnthropicClient, LLMError, OllamaClient
from aml_reporter.llm.anthropic_client import DEFAULT_MODEL

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")  # For SDK errors
EMPTY = PurposeAnswers(answers=[])  # A valid, empty answer


def fake_sdk(outcome: object) -> tuple[Any, list[dict[str, Any]]]:
    """Build a stand-in for the Anthropic SDK client.

    Args:
        outcome: Response to return, or exception to raise.

    Returns:
        The fake client and the list of keyword arguments it receives.
    """
    calls: list[dict[str, Any]] = []

    def parse(**kwargs: Any) -> object:
        """Record the request and play back the outcome.

        Args:
            **kwargs: Request parameters.

        Returns:
            The configured response.
        """
        calls.append(kwargs)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome

    return SimpleNamespace(messages=SimpleNamespace(parse=parse)), calls


def test_anthropic_success_uses_haiku_with_structured_output() -> None:
    """A normal answer is returned, requested from Haiku with the schema and low effort."""
    sdk, calls = fake_sdk(SimpleNamespace(stop_reason="end_turn", parsed_output=EMPTY))
    assert AnthropicClient(client=sdk).complete("s", "u", PurposeAnswers) is EMPTY
    request = calls[0]
    assert request["model"] == DEFAULT_MODEL == "claude-haiku-5-5"
    assert request["output_format"] is PurposeAnswers
    assert request["output_config"] == {"effort": "low"}
    assert "fallbacks" not in request


def _schema_error() -> ValidationError:
    """Produce a real Pydantic validation error.

    Returns:
        The error raised by parsing broken JSON.
    """
    try:
        PurposeAnswers.model_validate_json("{")
    except ValidationError as error:
        return error
    raise AssertionError("broken JSON was accepted")


@pytest.mark.parametrize(
    "outcome",
    [
        pytest.param(SimpleNamespace(stop_reason="refusal", parsed_output=None), id="refusal"),
        pytest.param(SimpleNamespace(stop_reason="max_tokens", parsed_output=None), id="cut"),
        pytest.param(anthropic.APIConnectionError(request=REQUEST), id="unreachable"),
        pytest.param(
            anthropic.InternalServerError(
                "boom", response=httpx2.Response(500, request=REQUEST), body=None
            ),
            id="server-error",
        ),
        pytest.param(_schema_error(), id="schema-mismatch"),
    ],
)
def test_anthropic_failures_become_llm_errors(outcome: object) -> None:
    """Refusals, truncation, API errors, and schema mismatches all raise LLMError.

    Args:
        outcome: What the fake SDK returns or raises.
    """
    sdk, _ = fake_sdk(outcome)
    with pytest.raises(LLMError):
        AnthropicClient(client=sdk).complete("s", "u", PurposeAnswers)


def ollama(handler: Any) -> OllamaClient:
    """Build an Ollama client whose HTTP calls go to a local handler.

    Args:
        handler: Function from request to response, or raising a transport error.

    Returns:
        The client.
    """
    return OllamaClient(
        "demo", "http://ollama", httpx.Client(transport=httpx.MockTransport(handler))
    )


def test_ollama_success_sends_the_schema() -> None:
    """The request carries the model, the JSON schema, and no streaming."""
    sent: list[dict[str, Any]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        """Record the request and answer with an empty batch.

        Args:
            request: Outgoing request.

        Returns:
            A successful Ollama response.
        """
        sent.append(json.loads(request.content))
        return httpx.Response(200, json={"message": {"content": '{"answers": []}'}})

    assert ollama(handler).complete("s", "u", PurposeAnswers) == EMPTY
    assert sent[0]["model"] == "demo"
    assert sent[0]["format"] == PurposeAnswers.model_json_schema()
    assert sent[0]["stream"] is False


@pytest.mark.parametrize(
    "response",
    [
        pytest.param(httpx.Response(500), id="server-error"),
        pytest.param(httpx.Response(200, json={"oops": 1}), id="unexpected-body"),
        pytest.param(httpx.Response(200, json={"message": {"content": "{"}}), id="bad-json"),
        pytest.param(httpx.ConnectError("refused"), id="unreachable"),
    ],
)
def test_ollama_failures_become_llm_errors(response: httpx.Response | Exception) -> None:
    """HTTP errors, odd bodies, invalid JSON, and connection errors all raise LLMError.

    Args:
        response: What the server answers, or the transport error it raises.
    """

    def handler(request: httpx.Request) -> httpx.Response:
        """Answer with the configured response, or raise the configured error.

        Args:
            request: Outgoing request.

        Returns:
            The configured response.
        """
        if isinstance(response, Exception):
            raise response
        return response

    with pytest.raises(LLMError):
        ollama(handler).complete("s", "u", PurposeAnswers)
