# Production readiness

This prototype is not a production system. This page lists the controls that make its output safe to rely on within its scope, and the gaps a real deployment would still have to close.

The guiding rule: **reject what would corrupt the figures, warn about what limits them, and never let missing data read as absence of risk.**

## Controls in place

### Input validation: reject

A case bundle that fails any of these checks is rejected before analysis, with every problem listed at once.

| Check | Catches | Where |
|---|---|---|
| Schema | Wrong types, malformed identifiers, unknown fields, negative amounts | `models/` |
| Cross-references | Cards, transactions, or the alert pointing to records outside the bundle; bookings outside the period | `models/case_checks.py` |
| Ledger | Amounts not in EUR, which the analytics would add up without conversion; bookings before an account opened or after it closed | `models/ledger_checks.py` |

The CLI prints the problems by field and exits with status 2. Messages name fields and identifiers but never echo input values, which may be personal data.

### Data quality: warn

A valid case can still have gaps that limit what some figures show. The report opens with a **Data quality** section, and the CLI prints one warning per issue.

| Issue | Meaning | Tolerance |
|---|---|---|
| `short_history` | Fewer than 30 days of history before the last 90: no usual level to compare recent flows with | — |
| `undescribed` | Transfers or debits with an empty description, which enrichment cannot read | `max_undescribed_share` |
| `unenriched` | Transfers or debits the enricher returned nothing for | — |
| `fallback` | Too many LLM answers replaced by the rule-based extractor | `max_fallback_share` |
| `duplicates` | Bookings that repeat another one field for field, which would be counted twice | — |
| `card_validity` | Card transactions outside the card's issue and expiry dates | — |

Tolerances live in [`controls/thresholds.toml`](../src/aml_reporter/controls/thresholds.toml); like the red-flag thresholds, they are illustrative.

### Missing is not zero

A measure that cannot be computed is never written as 0, because 0 is a real value that rules compare. Each fact carries a status:

| Status | Example | How rules read it |
|---|---|---|
| `measured` | Outflows are 2.4× the usual level | Compared normally |
| `no_baseline` | Outflows of €100,000 after a history with none; salary received by a customer who declared no income | Above any multiple: `>`, `>=`, `!=` hold |
| `no_activity` | Share of outflows by channel when there are no outflows | No condition holds: nothing to flag |
| `unavailable` | Recent outflows vs usual level when the history is too short | Unknown |

Rules use three-valued logic. A rule **fires** when every condition holds, **does not fire** when any condition fails, and is otherwise **not evaluable**: a fact is missing, unavailable, or of a type the operator cannot compare. Not-evaluable rules are listed in the assessment (`unevaluated`), in the key findings, and in a dedicated table; the risk indicator is then a lower bound, and the report advises against closing the alert before checking them.

History also starts where the customer's relationship does: baselines and annualised figures run from the later of the period start and the first account opening, so a new account is neither diluted over months without one nor read as dormant. When the customer initiated nothing before the alert, the silence before it runs back to that start, flagged as a lower bound (`F-TIME-006`).

### Rule configuration

Rule files are validated when loaded: unique identifiers, positive points, `high` above `medium`, and numeric thresholds for ordering operators, so `> "5"` fails at load time rather than silently never firing. A CI test checks that every fact a packaged rule reads is produced by the analysers.

### Audit and reproducibility

Every report ends with an **Audit trail**: the tool version, the enricher and its model, and SHA-256 fingerprints of the validated case bundle, the rule set, and the LLM prompt files. Digests are taken on the validated models, so reformatting an input file does not change them while any change to a value does. Running the same version on inputs with the same fingerprints gives the same facts and flags.

### Pipeline gate

`aml-report check` validates a bundle, enriches it, and writes the data-quality issues and undecided rules as JSON:

| Exit status | Meaning |
|---|---|
| 0 | The check ran; with `--strict`, the case is also clean |
| 1 | `--strict` and at least one issue or undecided rule |
| 2 | The bundle is invalid or unreadable |

A batch pipeline can run it before `generate` and route cases with issues to manual handling.

## Gaps before a real deployment

| Area | Missing |
|---|---|
| Data | Real feeds and their reconciliation with core-banking balances; currency conversion; lineage from source systems |
| Evaluation | Measurement on real, governed descriptions; a second, independent synthetic generator; sensitivity of decisions to enrichment errors |
| Model risk | Independent validation of the LLM tasks and the rules; monitoring of fallback share, rejections, and drift over time |
| Rule calibration | Thresholds set and back-tested on historical alerts with known outcomes |
| Security | Authentication and authorisation, access logging, encryption of stored reports, retention policy, secrets in a vault |
| Operations | Batch orchestration, throughput and latency at volume, observability of issues and undecided rules |
| Compliance | Sanctions, PEP, and adverse-media screening; four-eyes review; integration with suspicious transaction reporting |
