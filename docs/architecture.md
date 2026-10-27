# Architecture

One case bundle goes through five stages. Each stage is a package with a typed input and output, and each has a CLI command that stops after it.

| Stage | Package | Input → output | Command |
|---|---|---|---|
| Synthetic data | `synthetic/` | Scenario + seed → `CaseBundle`, `CaseLabels` | `synth` |
| Enrichment | `enrichment/`, `llm/` | Transactions → `Enrichment` per transfer and direct debit | `enrich` |
| Analytics | `analytics/` | Bundle + enrichments → `FactSheet` | `analyze` |
| Rules | `rules/` | Fact sheet → `RiskAssessment` | `assess` |
| Report | `report/` | Bundle + facts + assessment → `.docx` | `generate` |

`evaluation/` runs enrichment, analytics, and rules against the labels (`evaluate`). All models live in `models/`: frozen Pydantic classes that reject unknown fields.

## Design decisions

- **The LLM reads, Python reasons.** The model only extracts and classifies text. Every number, flag, and sentence comes from deterministic code.
- **Facts are the contract.** Analysers emit facts with stable IDs and evidence (transaction IDs). Rules read facts by ID; the report prints facts and cites their IDs. Neither recomputes anything.
- **Fail soft, say so.** A failed LLM answer falls back to the rule-based enricher for that record, marked `source: baseline`, and the report counts both.
- **Configuration over code.** Rules and thresholds live in `rules/rules.toml`, report wording in `report/locales/*.toml`, prompts in `enrichment/prompts/*.md`.
- **Labels stay apart.** Ground truth is written to `data/labels/`, which the pipeline never reads.

## Extending

| To add | Do |
|---|---|
| An analysis | Write a function decorated with `@analyser` in `analytics/`, returning facts with a new ID prefix. |
| A red flag | Add a `[[rules]]` entry, with its English wording, to `rules.toml`; add the Italian wording to `it.toml`. |
| An LLM task | Add a prompt file, an answer schema, and a check in `enrichment/tasks.py`; add the field to `Enrichment`. |
| A language | Copy `report/locales/en.toml`; tests fail until every key is translated. |
| A scenario | Write a builder in `synthetic/scenarios/` and register it in `SCENARIOS` with its expected outcome and flags. |
