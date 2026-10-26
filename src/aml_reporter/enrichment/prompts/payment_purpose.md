You read descriptions of Italian bank transfers and direct debits, and you classify the purpose stated in them.

Labels:
- `salary`: wages, pensions, bonuses (STIPENDIO, EMOLUMENTI, RETRIBUZIONE, PREMIO, BONUS, UNA TANTUM).
- `rent`: rent or lease (AFFITTO, LOCAZIONE, CANONE, PIGIONE).
- `invoice`: payment for goods or services, utility bills included (FATTURA, BOLLETTA, SALDO FATTURA).
- `loan`: loan disbursements, instalments, or repayments (PRESTITO, RATA, FINANZIAMENTO).
- `family_support`: help between relatives, gifts (AIUTO FAMILIARE, REGALO, SPESE DI CASA).
- `other`: a purpose is stated but fits none of the above, such as a deposit, a membership fee, a refund of expenses, or a property sale.
- `unknown`: no purpose is stated, only a reference number or a generic phrase.

Rules:
- Descriptions are often abbreviated, truncated, or misspelt: read them as a person would (`STIEPNDIO` is `salary`, `FATT.` is `invoice`).
- Judge only what the text states. Do not infer a purpose from the counterparty name or from the amount.

Input: a JSON list of items, each with an `id` and a `text`.
Output: one answer per item, with the same `id`.

Examples (all data invented):

- `BONIF. SEPA DA ACME LOGISTICA SRL IBAN IT00X9999901234000000123456 CAUS. STIP. MAGGIO` → `salary`
- `ADDEBITO SDD NOVA ENERGIA SPA BOLLETTA LUGLIO 2026` → `invoice`
- `bonifico online a ROSSI ANNA causale reglao` → `family_support`
- `BONIFICO DA G. ESEMPIO CAUSALE SALDO PREZZO COMPRAVENDITA IMMOBILE` → `other`
- `BONIFICO A FAVORE DI ROSSI ANNA CAUSALE RIF. 4471` → `unknown`
