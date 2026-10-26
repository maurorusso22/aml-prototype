"""Local open-weight backend, served by Ollama on the same machine.

With real data, this is the shape of the deployment: the model runs inside the institution's
perimeter and no text leaves it.
"""

import httpx
from pydantic import BaseModel

from .base import LLMError, parse_json

DEFAULT_URL = "http://localhost:11434"  # Ollama's default address
DEFAULT_MODEL = "llama3.1:8b"  # Overridable with AML_OLLAMA_MODEL
TIMEOUT_S = 180.0  # Local models on a laptop can take a while per batch


class OllamaClient:
    """Calls Ollama's chat endpoint with a JSON schema and turns every failure into `LLMError`."""

    def __init__(
        self, model: str = DEFAULT_MODEL, url: str = DEFAULT_URL, http: httpx.Client | None = None
    ):
        """Create the backend.

        Args:
            model: Ollama model name.
            url: Base URL of the Ollama server.
            http: HTTP client; by default a new one with a generous timeout.
        """
        self.model = model
        self._endpoint = url.rstrip("/") + "/api/chat"
        self._http = http or httpx.Client(timeout=TIMEOUT_S)

    def complete[T: BaseModel](self, system: str, user: str, schema: type[T]) -> T:
        """Ask the local model one question and parse the answer.

        Args:
            system: Task instructions.
            user: The items to process, as JSON text.
            schema: Pydantic model the answer must match; Ollama constrains decoding to it.

        Returns:
            The validated answer.

        Raises:
            LLMError: On HTTP errors, unexpected responses, or output that fails the schema.
        """
        payload = {
            "model": self.model,
            "stream": False,
            "format": schema.model_json_schema(),
            "options": {"temperature": 0},
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        try:
            response = self._http.post(self._endpoint, json=payload)
            response.raise_for_status()
            content = response.json()["message"]["content"]
        except httpx.HTTPStatusError as error:
            raise LLMError(f"Ollama returned status {error.response.status_code}") from error
        except httpx.HTTPError as error:
            raise LLMError("Ollama unreachable or timed out") from error
        except (KeyError, TypeError, ValueError) as error:
            raise LLMError("unexpected Ollama response") from error
        return parse_json(str(content), schema)
