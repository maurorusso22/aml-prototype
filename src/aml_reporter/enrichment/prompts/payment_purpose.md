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
Output: a JSON object with an `answers` list holding exactly one answer for every item: its `id` and the `payment_purpose`. Never skip an item.

Example (all data invented): a batch exactly as you receive it, then the answer exactly as you must return it.

<input>
[{"id": 0, "text": "ACCR. BONIF. SALDO FATT. 4410 ORD. DELTA LOGISTICA SRL IT00M9999931874402956613027"}, {"id": 1, "text": "ADDEBITO DIRETTO CREDITORE NOVA ENERGIA SRL MANDATO MND482913 BOLLETTA OTTOBRE 2026"}, {"id": 2, "text": "BONIFICO A FAVORE DI LUMEN SERVICES BV IBAN NL0099990427718530 CAUSALE FATTURA 318 DEL 14/07/2026"}, {"id": 3, "text": "BONIFICO A VOSTRO FAVORE ORDINANTE MARIANI ELISA IBAN IT00K9999907731648205519384 SALDO PREZZO COMPRAVENDITA IMMOBILE"}, {"id": 4, "text": "BONIFICO A VOSTRO FAVORE RIF. 5531"}, {"id": 5, "text": "BONIFICO ONLINE A DAVIDE ESPOSITO CAUSALE"}, {"id": 6, "text": "BONIFICO SEPA DA VEGA TRASPORTI SPA IBAN IT00C9999970215538846120931 CAUSALE STIEPNDIO OTTOBRE"}, {"id": 7, "text": "DISP. BONIF. BEN. F. FONTANA IBAN IT00S9999948120937756210448 CANONE"}, {"id": 8, "text": "PAGAMENTO AFFITTO SETTEMBRE STEFANO LOMBARDI"}, {"id": 9, "text": "RIMBORSO SPESE C. MANCINI IT00P9999915520893304761258"}, {"id": 10, "text": "SDD MND730215 ZENIT FINANZIARIA SPA RATA PRESTITO 2214"}, {"id": 11, "text": "aiuto familiare beneficiario COLOMBO ILARIA IT00G9999920584417039962815"}, {"id": 12, "text": "bonif. a favore di DE LUCA MARTINA iban IT00E9999962047813395520716 caus. reglao"}, {"id": 13, "text": "fattura 7731 del 02/03/2026 ATLAS CONSULTING LTD CY00999904417726395081624473"}]
</input>
<output>
{"answers": [{"id": 0, "payment_purpose": "invoice"}, {"id": 1, "payment_purpose": "invoice"}, {"id": 2, "payment_purpose": "invoice"}, {"id": 3, "payment_purpose": "other"}, {"id": 4, "payment_purpose": "unknown"}, {"id": 5, "payment_purpose": "unknown"}, {"id": 6, "payment_purpose": "salary"}, {"id": 7, "payment_purpose": "rent"}, {"id": 8, "payment_purpose": "rent"}, {"id": 9, "payment_purpose": "other"}, {"id": 10, "payment_purpose": "loan"}, {"id": 11, "payment_purpose": "family_support"}, {"id": 12, "payment_purpose": "family_support"}, {"id": 13, "payment_purpose": "invoice"}]}
</output>
