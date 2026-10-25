"""Constrained types for identifiers, codes, and amounts.

Identifier formats are invented for this project. IBANs, tax codes, and VAT numbers are checked
for structure only, never for check digits: synthetic identifiers are invalid by design.
"""

from decimal import Decimal
from typing import Annotated

from pydantic import Field, StringConstraints

type CaseId = Annotated[str, StringConstraints(pattern=r"^CASE-\d{6}$")]
type CustomerId = Annotated[str, StringConstraints(pattern=r"^CU-\d{6}$")]
type AccountId = Annotated[str, StringConstraints(pattern=r"^AC-\d{6}$")]
type CardId = Annotated[str, StringConstraints(pattern=r"^CA-\d{6}$")]
type TransactionId = Annotated[str, StringConstraints(pattern=r"^TX-\d{6}$")]
type AlertId = Annotated[str, StringConstraints(pattern=r"^AL-\d{6}$")]
type FactId = Annotated[str, StringConstraints(pattern=r"^F-[A-Z]+-\d{3}$")]
type ScenarioName = Annotated[str, StringConstraints(pattern=r"^[a-z][a-z0-9_]*$")]

# Country code, two check digits, then the national account number (BBAN)
type Iban = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")]
type TaxCode = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{16}$")]
type VatNumber = Annotated[str, StringConstraints(pattern=r"^\d{11}$")]
# Only the last four digits of a card number are ever stored
type MaskedPan = Annotated[str, StringConstraints(pattern=r"^(\*{4} ){3}\d{4}$")]
type CountryCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{2}$")]
type CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]

type NonEmptyStr = Annotated[str, StringConstraints(min_length=1)]
type Money = Annotated[Decimal, Field(max_digits=15, decimal_places=2)]
type PositiveMoney = Annotated[Decimal, Field(gt=0, max_digits=15, decimal_places=2)]
type NonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=15, decimal_places=2)]
