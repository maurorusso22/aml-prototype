# Implementation Plan

This plan breaks the prototype into small, independently testable phases. Each phase ends with a working, CI-green state.

> All code, data, rules, and prompts in this project are written from scratch and are fictional. See the disclaimer in the [README](../README.md).

## Guiding principles

| Principle | What it means in practice |
|---|---|
| The LLM reads, Python reasons | The LLM only extracts and classifies free-text fields. Every figure, red flag, and report sentence comes from deterministic code. |
| Validate every LLM answer | Schema-constrained output, closed label sets, verbatim check on extracted strings, abstention (`null`) always allowed. |
| Synthetic first | No real data, ever. Identifiers are invalid by construction and tests enforce it. |
| Local LLM by default | The default backend is a local model, as inside a bank's perimeter. The rule-based `baseline` takes over whenever no LLM answers, so CI and reviewers can run everything without any LLM or API key. |
| Small modules | Each source file stays within 100–150 lines; each analysis and each LLM task is its own module. |
| Human in the loop | The report presents evidence and a risk indicator; the decision stays with the analyst. |

## Phases

### Phase 0 — Repository foundation

- `uv` project with `pyproject.toml`; ruff, mypy, pytest configured.
- `pre-commit` hooks: ruff, mypy, gitleaks.
- `LICENSE` (MIT), `.gitignore` (`.env`, `output/`, caches), `.env.example`.
- GitHub Actions workflow: lint, type-check, tests, secret scan.

**Done when:** CI is green on an empty `aml_reporter` package.

### Phase 1 — Domain model

- Pydantic v2 schemas: `Customer` (individual or business), `Account`, `Card`, `Transaction` (with free-text `description`), `Alert`, `CaseBundle`.
- `Enrichment` schema: `counterparty_name`, `counterparty_iban`, `counterparty_type`, `payment_purpose`, `source` (`llm`, `baseline`).
- Enums for direction, channel (branch, ATM, online, POS, interbank), transaction type, and the LLM label sets.
- `Fact` schema: `id`, `category`, `label`, `value`, `unit`, `evidence` (transaction IDs).

**Done when:** hand-written fixtures validate, and invalid ones are rejected with clear errors.

### Phase 2 — Synthetic data generator

- Seeded generator with curated lists of common Italian names and fictitious streets, so output never depends on third-party data and never points to a recognisable person.
- Invalid-by-construction identifiers: IBAN with check digits `00` and a fictitious bank code, *codice fiscale* with wrong control character, card numbers failing Luhn and stored masked.
- Description writer: invented templates plus noise (abbreviations, truncation, typos, field order, missing IBAN), with a `hard` tag on the noisiest ones.
- Ground-truth labels written to `data/labels/`, separate from the case bundles.
- Scenario injectors for the six scenarios listed in the README, each labelled with its expected outcome.
- CLI command `aml-report synth`.

**Done when:** `data/samples/` and `data/labels/` regenerate byte-identical from the same seed, and tests prove every identifier fails real-world validation.

### Phase 3 — LLM enrichment

- `Enricher` interface: `enrich(transactions) -> list[Enrichment]`, with three backends in order of preference: `local` (Ollama, the default), `anthropic` (Claude via the official SDK, structured outputs with Pydantic schemas), `baseline` (regular expressions and keyword rules).
- One prompt file and output schema per task: IBAN extraction, counterparty extraction, counterparty type, payment purpose. Few-shot examples from synthetic data only.
- Several descriptions per request; cache keyed on the normalised description.
- Output validation: schema and label set; extracted strings must appear verbatim in the source text; IBAN structure check (country code, length, pattern, not the checksum, since synthetic IBANs are deliberately invalid). On failure, fall back to `baseline` and record it in `source`.
- Graceful handling of API errors, refusals, and timeouts: fallback, never crash.
- CLI command `aml-report enrich`, added early so backends can be tried by hand; smoke tests marked `integration` and excluded from the default run.

**Done when:** the `baseline` enricher runs on all scenarios, `local` and `anthropic` pass a smoke test on a sample, and validators are unit-tested against adversarial outputs (invented IBAN, label outside the set, malformed JSON).

### Phase 4 — Analytics engine

- Analyser interface: a function from the analysis context (case bundle plus enrichments) to facts, registered with a decorator; adding an analysis means writing one function.
- Initial analysers: alert in context (baseline comparison), flow summary, channel and cash mix, payment purpose mix, counterparties (grouping by name and IBAN, natural vs legal persons, concentration), geographic exposure (IBAN country code), customer and relationship, profile consistency, temporal patterns (inactivity, bursts).
- Plain Python with exact decimals rather than pandas: a case has a few hundred transactions, and the code stays fully typed.
- Charts rendered with matplotlib for the report, with a colour-blind-safe palette.
- Fact sheet export to JSON, and CLI command `aml-report analyze`.

**Done when:** every analyser has unit tests, and the fact sheet of each scenario matches a golden file.

### Phase 5 — Red-flag rules

- Rules defined in `src/aml_reporter/rules/rules.toml` (read with the standard library, validated with Pydantic): conditions on facts, severity, description, illustrative thresholds.
- No high-risk country list: the prototype does not designate real jurisdictions; geographic rules look at foreign flows instead.
- Expected flags stored with each scenario's ground truth; CLI command `aml-report assess`.
- Triggered flags carry their evidence (fact IDs and transaction IDs).
- Transparent additive risk indicator (low / medium / high), no black-box model.

**Done when:** each scenario triggers exactly its expected flags, and the false-positive scenarios trigger none beyond the original alert.

### Phase 6 — Report builder

- python-docx document with one builder module per section.
- Text from templates filled with facts, in English or Italian; no free-form generated prose.
- Tables and embedded charts; fields derived from LLM enrichment marked as such.
- Blank analyst assessment section; enrichment statistics (LLM vs fallback) in the appendix.
- Header or footer stating "Synthetic data — prototype".
- DOCX core properties (author, company, title) set explicitly, so no local metadata leaks.
- Wording in TOML catalogues per language; tests fail when an Italian translation is missing for a text, a fact, or a rule.
- Table borders and shading written into each table, so the layout does not depend on the viewer supporting named table styles.
- CLI command `aml-report generate`, added early so reports can be produced and reviewed.

**Done when:** a report for every scenario opens in Word and LibreOffice, and a structural test checks headings, tables, and metadata.

### Phase 7 — CLI and examples

- Typer CLI: `synth`, `enrich` (enriched transactions only), `analyze` (fact sheet only), `assess` (red flags and risk indicator), `generate` (full report), `evaluate`.
- Sample reports for each scenario committed to `examples/`, with screenshots for the README.
- CLI command `aml-report examples`, which enriches each sample case once and writes it in every language; `evaluate` comes with Phase 8.

**Done when:** the README Quickstart works on a clean clone.

### Phase 8 — Evaluation

- Per-task metrics against `data/labels/`: exact match for extraction; precision, recall, F1, and confusion matrix for classification; abstention and invention rates.
- Every metric for each enricher, on the full dataset and on the `hard` subset.
- End to end: expected red flags per scenario, risk indicator vs expected outcome.
- Cost and latency per 1,000 descriptions for the LLM backends.
- Runs with `baseline` in CI; with the LLM backends on demand. Results table in `docs/evaluation.md`.
- Metrics in plain Python, no scikit-learn. Abstention and invention are measured against the labels, as *missed* (label has a value, enricher none) and *invented* (label has none, enricher gives one); values absent from the text are already rejected by validation, so the enricher counts those rejections by reason instead.
- The Anthropic client counts input and output tokens; costs use list prices.
- CLI command `aml-report evaluate`, which writes the Markdown report and the raw results (`docs/evaluation.json`); the baseline evaluation runs in the default test suite with accuracy floors.

**Done when:** metrics are reproducible and published.

### Phase 9 — Documentation and polish

- `docs/architecture.md`, `docs/llm-tasks.md`, `docs/analysis-catalog.md`, `docs/privacy.md`, `docs/evaluation.md`.
- README updated with screenshots, real Quickstart output, and evaluation highlights.

**Done when:** a reviewer can understand, run, and evaluate the project from the docs alone.

## Pre-publication checklist

Run before every push to the public repository:

- [ ] No names of real institutions, people, internal systems, internal project names, or internal codes in code, comments, docs, commit messages, branch names, or file metadata.
- [ ] Transaction description templates and prompts are invented and do not reproduce any real institution's formats.
- [ ] Every file in `data/` and `examples/` is regenerated by the synthetic generator.
- [ ] Generated DOCX files carry only the explicitly set metadata.
- [ ] Screenshots show synthetic data only.
- [ ] Secret scan passes; no `.env` or API key committed.
- [ ] Rules and thresholds are marked as illustrative; no real jurisdiction is labelled high risk.

## Open points

- **LLM task catalogue.** Further extraction and classification tasks to add alongside the initial four; to be documented in `docs/llm-tasks.md`.
- **Analysis catalogue.** The full list of analyses and their specification is still to be detailed; it will extend Phases 4 and 5 and be documented in `docs/analysis-catalog.md`.
- **Default report language.** English or Italian.
- **Local model.** Which open-weight model to recommend for the `local` backend.
- **Stretch goal.** A small web UI (e.g. Streamlit) to upload a case bundle and download the report.
