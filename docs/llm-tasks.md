# LLM tasks

Four narrow tasks, each with its own prompt file in [`enrichment/prompts/`](../src/aml_reporter/enrichment/prompts/), answer schema, and check ([`tasks.py`](../src/aml_reporter/enrichment/tasks.py)).

| Task | Reads | Answers | Check |
|---|---|---|---|
| `iban` | Description | IBAN or `null` | Valid structure, and present verbatim in the description (spaces ignored) |
| `counterparty` | Description | Name or `null` | Present in the description (case and spacing ignored), kept as written there |
| `counterparty_type` | Name from `counterparty` | `natural_person` or `legal_person` | Closed set, enforced by the schema |
| `payment_purpose` | Description | `salary`, `rent`, `invoice`, `loan`, `family_support`, `other`, `unknown` | Closed set, enforced by the schema |

Only wire transfers and direct debits are enriched; card and cash operations have no counterparty text.

## How a case is enriched

1. Descriptions are normalised (single spaces) and deduplicated; answers are cached by task and text.
2. Inputs go out in batches of 20, each with an `id`; the model answers with the same ids.
3. Each answer passes its check, or is rejected with a reason. `null`, `"null"`, `"none"`, `"n/a"`, and `""` all mean "no value".
4. Inputs the model skipped are asked once more.
5. A transaction gets `source: llm` only when every task answered it validly; otherwise the rule-based enricher fills the whole record and marks it `source: baseline`.

API errors, timeouts, refusals, and malformed JSON raise `LLMError`, which fails the batch and triggers the same fallback. Rejections are counted by reason and reported by `aml-report evaluate`.

## Backends

| Setting | Default |
|---|---|
| `AML_ENRICHER` | `local` (`anthropic`, `baseline`) |
| `AML_OLLAMA_URL`, `AML_OLLAMA_MODEL` | `http://localhost:11434`, `llama3.1:8b` |
| `AML_ANTHROPIC_MODEL` | `claude-haiku-5-5`, structured outputs, effort `low` |

The local backend passes the answer's JSON schema to Ollama's `format`; the Anthropic backend uses the SDK's structured-output parsing. Both return the same Pydantic objects.
