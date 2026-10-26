"""Regular expressions and keyword rules: the baseline the LLM is measured against.

The keyword lists were written by reading the synthetic descriptions, as a rules engineer would.
They work on clean text and break on typos, missing field labels, and unusual word order.
"""

import re

from ..models import CounterpartyType, PaymentPurpose

IBAN_REGEX = r"[A-Z]{2}\d{2}[A-Z0-9]{11,30}"  # IBAN as printed, uppercase and without spaces
NAME_ANCHORS = (  # Words that introduce the counterparty name
    r"SEPA DA|BONIFICO DA|BONIF\. DA|ORDINANTE|ORD\.|A FAVORE DI|BENEFICIARIO|BEN\.|"
    r"ONLINE A|CREDITORE|CRED\.|SDD"
)
NAME_STOPS = (  # What may follow the name: a field label, an IBAN, or the end of the text
    rf"(?=\s+(?:IBAN|CAUSALE|CAUS\.|MANDATO)(?:\s|$)|\s+{IBAN_REGEX}\b|\s*$)"
)
NAME_PATTERN = re.compile(  # Shortest text between an anchor and a stop
    rf"(?:{NAME_ANCHORS})\s+(?P<name>.+?){NAME_STOPS}", re.IGNORECASE
)
IBAN_PATTERN = re.compile(rf"\b{IBAN_REGEX}\b")  # First IBAN-looking token
LEGAL_FORMS = frozenset(  # Company suffixes that mark a legal person
    {
        "SRL",
        "SRLS",
        "SPA",
        "SNC",
        "SAS",
        "GMBH",
        "SARL",
        "SL",
        "SA",
        "BV",
        "UAB",
        "LTD",
        "LLC",
        "FZE",
    }
)
PURPOSE_KEYWORDS = (  # Checked in order; the first purpose with a matching keyword wins
    (PaymentPurpose.LOAN, ("PRESTITO", "PREST.", "RATA", "FINANZIAMENTO")),
    (PaymentPurpose.SALARY, ("STIPENDIO", "STIP.", "EMOLUMENTI", "RETRIBUZIONE", "PREMIO")),
    (PaymentPurpose.SALARY, ("BONUS", "UNA TANTUM")),
    (PaymentPurpose.RENT, ("AFFITTO", "LOCAZIONE", "PIGIONE")),
    (PaymentPurpose.INVOICE, ("FATTURA", "FATT.", "BOLLETTA")),
    (PaymentPurpose.FAMILY_SUPPORT, ("AIUTO FAMILIARE", "REGALO", "SPESE DI CASA", "CONTRIBUTO")),
    (PaymentPurpose.OTHER, ("RIMBORSO SPESE", "QUOTA", "CAUZIONE", "ACQUISTO", "COMPRAVENDITA")),
    (PaymentPurpose.OTHER, ("ROGITO",)),
)


def extract_iban(text: str) -> str | None:
    """Find the first IBAN-looking token.

    Args:
        text: Normalised description.

    Returns:
        The IBAN, or None.
    """
    match = IBAN_PATTERN.search(text)
    return match.group() if match else None


def extract_counterparty(text: str) -> str | None:
    """Take the words between a name anchor and the next field label or IBAN.

    Args:
        text: Normalised description.

    Returns:
        The counterparty name as written, or None when no anchor is found.
    """
    match = NAME_PATTERN.search(text)
    return match.group("name").strip() if match else None


def classify_counterparty(name: str) -> CounterpartyType:
    """Call a name a legal person when it contains a company suffix.

    Args:
        name: Counterparty name.

    Returns:
        Legal person with a suffix, natural person otherwise.
    """
    words = {word.strip(".,").upper() for word in name.split()}
    return CounterpartyType.LEGAL_PERSON if words & LEGAL_FORMS else CounterpartyType.NATURAL_PERSON


def classify_purpose(text: str) -> PaymentPurpose:
    """Look for purpose keywords as whole words.

    Args:
        text: Normalised description.

    Returns:
        The first matching purpose, or unknown.
    """
    for purpose, keywords in PURPOSE_KEYWORDS:
        for keyword in keywords:
            if re.search(rf"(?<!\w){re.escape(keyword)}(?!\w)", text, re.IGNORECASE):
                return purpose
    return PaymentPurpose.UNKNOWN
