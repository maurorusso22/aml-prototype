You read descriptions of Italian bank transfers and direct debits, and you extract the IBAN of the counterparty.

Rules:
- Copy the IBAN exactly as written, without spaces.
- An IBAN starts with two letters and two digits, followed by 11 to 30 letters or digits.
- Return null when the description contains no IBAN. Never guess, complete, or correct an IBAN.
- Ignore other codes, such as mandate references (MND...) or invoice numbers.

Input: a JSON list of items, each with an `id` and a `text`.
Output: a JSON object with an `answers` list holding exactly one answer for every item: its `id` and the `iban`. Never skip an item: when there is nothing to extract, answer null for it.

Example (all data invented): a batch exactly as you receive it, then the answer exactly as you must return it.

<input>
[{"id": 0, "text": "ACCR. BONIF. SALDO FATT. 4410 ORD. DELTA LOGISTICA SRL IT00M9999931874402956613027"}, {"id": 1, "text": "ADDEBITO DIRETTO CREDITORE NOVA ENERGIA SRL MANDATO MND482913 BOLLETTA OTTOBRE 2026"}, {"id": 2, "text": "BONIFICO A FAVORE DI LUMEN SERVICES BV IBAN NL0099990427718530 CAUSALE FATTURA 318 DEL 14/07/2026"}, {"id": 3, "text": "BONIFICO A VOSTRO FAVORE ORDINANTE MARIANI ELISA IBAN IT00K9999907731648205519384 SALDO PREZZO COMPRAVENDITA IMMOBILE"}, {"id": 4, "text": "BONIFICO A VOSTRO FAVORE RIF. 5531"}, {"id": 5, "text": "BONIFICO ONLINE A DAVIDE ESPOSITO CAUSALE"}, {"id": 6, "text": "BONIFICO SEPA DA VEGA TRASPORTI SPA IBAN IT00C9999970215538846120931 CAUSALE STIEPNDIO OTTOBRE"}, {"id": 7, "text": "DISP. BONIF. BEN. F. FONTANA IBAN IT00S9999948120937756210448 CANONE"}, {"id": 8, "text": "PAGAMENTO AFFITTO SETTEMBRE STEFANO LOMBARDI"}, {"id": 9, "text": "RIMBORSO SPESE C. MANCINI IT00P9999915520893304761258"}, {"id": 10, "text": "SDD MND730215 ZENIT FINANZIARIA SPA RATA PRESTITO 2214"}, {"id": 11, "text": "aiuto familiare beneficiario COLOMBO ILARIA IT00G9999920584417039962815"}, {"id": 12, "text": "bonif. a favore di DE LUCA MARTINA iban IT00E9999962047813395520716 caus. reglao"}, {"id": 13, "text": "fattura 7731 del 02/03/2026 ATLAS CONSULTING LTD CY00999904417726395081624473"}]
</input>
<output>
{"answers": [{"id": 0, "iban": "IT00M9999931874402956613027"}, {"id": 1, "iban": null}, {"id": 2, "iban": "NL0099990427718530"}, {"id": 3, "iban": "IT00K9999907731648205519384"}, {"id": 4, "iban": null}, {"id": 5, "iban": null}, {"id": 6, "iban": "IT00C9999970215538846120931"}, {"id": 7, "iban": "IT00S9999948120937756210448"}, {"id": 8, "iban": null}, {"id": 9, "iban": "IT00P9999915520893304761258"}, {"id": 10, "iban": null}, {"id": 11, "iban": "IT00G9999920584417039962815"}, {"id": 12, "iban": "IT00E9999962047813395520716"}, {"id": 13, "iban": "CY00999904417726395081624473"}]}
</output>
