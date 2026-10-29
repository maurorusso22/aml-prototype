# LLM tasks

Four narrow tasks, each with its own prompt file in [`enrichment/prompts/`](../src/aml_reporter/enrichment/prompts/), answer schema, and check ([`tasks.py`](../src/aml_reporter/enrichment/tasks.py)).

| Task | Reads | Answers | Check |
|---|---|---|---|
| `iban` | Description | IBAN or `null` | Valid structure, and present verbatim in the description (spaces ignored) |
| `counterparty` | Description | Name or `null` | Present in the description (case and spacing ignored), kept as written there |
| `counterparty_type` | Name from `counterparty` | `natural_person` or `legal_person` | Closed set, enforced by the schema |
| `payment_purpose` | Description | `salary`, `rent`, `invoice`, `loan`, `family_support`, `other`, `unknown` | Closed set, enforced by the schema |

Only wire transfers and direct debits are enriched; card and cash operations have no counterparty text.

## What the model sees

The prompt file is the system message. Each batch is the user message, a JSON list of items numbered from 0 ([`Task.request`](../src/aml_reporter/enrichment/tasks.py)); the answer is a JSON object with one entry per item. For `iban`:

```json
[{"id": 0, "text": "BONIFICO SEPA DA VEGA TRASPORTI SPA IBAN IT00C9999970215538846120931 CAUSALE STIEPNDIO OTTOBRE"}, {"id": 1, "text": "SDD MND730215 ZENIT FINANZIARIA SPA RATA PRESTITO 2214"}]
```

```json
{"answers": [{"id": 0, "iban": "IT00C9999970215538846120931"}, {"id": 1, "iban": null}]}
```

Each prompt ends with one example batch in exactly this form, made of invented data in the style of the synthetic descriptions: abbreviations, typos, truncated purposes, missing field labels, lowercase text, foreign IBANs. The three description tasks share the same 14 descriptions; the `counterparty_type` example classifies the names that the `counterparty` example extracts. [`test_enrichment_prompts.py`](../tests/test_enrichment_prompts.py) checks that every example matches `Task.request`, fits the answer schema, passes the task's check, and reuses no description or name from the evaluation data.

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
