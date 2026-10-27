# Analysis catalogue

Every analyser in [`analytics/`](../src/aml_reporter/analytics/) emits facts: a stable ID, a label, a value, a unit, and the transactions behind it. A case has about 70. Facts marked † depend on enrichment; the report marks them the same way.

| IDs | Analyser | Facts |
|---|---|---|
| `F-ALERT-001`–`009` | `alert.py` | Alerted amount and kind; earlier transactions of that kind, their median and maximum, and the alerted amount as a multiple of the median; counterparty†, earlier transactions with it†, its type† |
| `F-CUST-001`–`005` | `customer.py` | Customer kind, years as a customer, risk rating, declared income or turnover, occupation or sector |
| `F-REL-001`–`004` | `customer.py` | Accounts, cards, balance at the end of the period, transactions in the period |
| `F-FLOW-001`–`008` | `flows.py` | Total inflows, outflows, and net flow; average monthly inflows; last 90 days of inflows and outflows, each as a multiple of the usual level |
| `F-CASH-001`–`007` | `cash.py` | Cash deposits, recent ones, and those just below EUR 10,000; cash withdrawn, overall and recent; cash share of inflows |
| `F-CHAN-001`–`005` | `channels.py` | Share of outflows by channel: branch, ATM, online, card terminal, collection by other banks |
| `F-PURP-001`–`201` | `purposes.py` | Inflows (`0xx`) and outflows (`1xx`) by payment purpose†; share of transfers and debits with no stated purpose† |
| `F-CPTY-001`–`007` | `counterparties.py` | Distinct senders and receivers†; share and name of the largest sender†; distinct people sending money in the last 90 days†; new counterparties†; share of inflows from natural persons† |
| `F-GEO-001`–`004`, `1xx` | `geography.py` | Foreign countries of counterparty accounts†; inflows from and outflows to foreign accounts†; share of outflows going abroad†; one fact per country† |
| `F-PROF-001`–`004` | `profile.py` | Annualised inflows, and as a multiple of the declared figure; the same for salary or invoice inflows† |
| `F-TIME-001`–`005` | `temporal.py` | Longest inactivity, inactivity before the alert, busiest 7 days, average per 7 days, and their ratio |

"Recent" means the last 90 days of the look-back period; "the usual level" is the flow of the earlier days, scaled to 90 days.

## Facts read by the rules

| Rule | Condition |
|---|---|
| `RF-STRUCTURING` | `F-CASH-004` ≥ 3 |
| `RF-PASS-THROUGH` | `F-CPTY-005` ≥ 5 and `F-FLOW-008` ≥ 2 |
| `RF-DORMANT-REACTIVATION` | `F-TIME-002` ≥ 90 |
| `RF-FOREIGN-INFLOWS` | `F-GEO-002` ≥ 10,000 |
| `RF-CASH-WITHDRAWALS` | `F-CASH-006` ≥ 5,000 |
| `RF-PROFILE-MISMATCH` | `F-PROF-004` ≥ 3 |
| `RF-OUTFLOW-SPIKE` | `F-FLOW-008` ≥ 2 |

Thresholds are illustrative, set in [`rules.toml`](../src/aml_reporter/rules/rules.toml).
