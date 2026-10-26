"""Descriptions of card and cash transactions, which are not enriched by the LLM."""

import random

MERCHANTS = (  # Invented shop names for card payments at a terminal
    "SUPERMERCATO ESEMPIO",
    "FARMACIA CENTRALE",
    "BAR DEL CORSO",
    "DISTRIBUTORE CARBURANTE",
    "LIBRERIA CENTRALE",
    "TRATTORIA DEMO",
    "PANIFICIO SAN ROCCO",
)
ONLINE_SHOPS = ("SHOP ONLINE DEMO", "MARKETPLACE DEMO", "STREAMING DEMO")  # Invented web shops
CASH_DEPOSIT_TEXTS = ("VERSAMENTO CONTANTI", "VERS. CONTANTI SPORTELLO")  # Branch or ATM deposits
CASH_WITHDRAWAL_TEXTS = ("PRELIEVO CONTANTI SPORTELLO", "PRELEVAMENTO CONTANTI")  # At a branch


def card_payment_text(rng: random.Random, city: str, online: bool) -> str:
    """Describe a card payment.

    Args:
        rng: Seeded random source.
        city: Customer's city, printed for terminal payments.
        online: Whether the payment was made on the web.

    Returns:
        Description text.
    """
    if online:
        return f"PAGAMENTO CARTA {rng.choice(ONLINE_SHOPS)}"
    return f"POS {rng.choice(MERCHANTS)} {city.upper()}"


def atm_withdrawal_text(city: str) -> str:
    """Describe an ATM withdrawal.

    Args:
        city: City of the ATM.

    Returns:
        Description text.
    """
    return f"PRELIEVO ATM {city.upper()}"


def cash_text(rng: random.Random, deposit: bool) -> str:
    """Describe a cash deposit or withdrawal at a branch or ATM.

    Args:
        rng: Seeded random source.
        deposit: True for deposits, False for withdrawals.

    Returns:
        Description text.
    """
    return rng.choice(CASH_DEPOSIT_TEXTS if deposit else CASH_WITHDRAWAL_TEXTS)
