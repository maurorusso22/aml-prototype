# Privacy controls

All data in this repository is synthetic. The controls below are built as they would be for real data, and most are enforced by a test or a hook rather than by convention.

| Control | How | Enforced by |
|---|---|---|
| Invented people and places | Curated very common first names and surnames; fictitious street names | `synthetic/names.py`, review |
| Identifiers that cannot be real | IBANs with check digits `00`, a fictitious bank code, and a failing mod-97; fiscal codes with a wrong control character; VAT numbers with a wrong check digit; card numbers failing Luhn, stored masked | `tests/test_synthetic_identifiers.py` |
| LLM inside the perimeter | Default backend is a local model; the Claude API is opt-in | `settings.py`, `.env.example` |
| Data minimisation | Each LLM call sees only a description or a counterparty name, never the customer profile or history | `enrichment/tasks.py` |
| No invented values | Extracted IBANs and names must appear in the source text | `enrichment/validation.py`, `tests/test_enrichment_validation.py` |
| Quiet logs | Logs carry counts and fixed error reasons, never prompt or answer text | `llm/base.py`, `enrichment/llm_enricher.py` |
| Quiet rejections | Invalid bundles are rejected naming fields and identifiers, never echoing input values | `cli/app.py`, `tests/test_cli.py` |
| Clean documents | DOCX core properties overwritten (the author is the tool, never the local user), company left empty; a "synthetic data" header on every page | `tests/test_report_document.py` |
| No secrets in git | `.env` and `output/` git-ignored; gitleaks on every commit and on the full history in CI | `.pre-commit-config.yaml`, `.github/workflows/ci.yml` |
| Labels apart | Ground truth lives in `data/labels/`, never read by the pipeline | `synthetic/generate.py` |

Before each push, run the pre-publication checklist in the [implementation plan](implementation-plan.md#pre-publication-checklist).

These are engineering measures in the spirit of GDPR Article 25 (data protection by design), not a legal compliance assessment.
