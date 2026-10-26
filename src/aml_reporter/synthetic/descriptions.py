"""Wire transfer and direct debit descriptions, with realistic noise.

Templates are invented for this project. Noise only touches the template and the purpose, never
the counterparty name or the IBAN, so ground-truth labels always appear verbatim in the text.
"""

import random
from dataclasses import dataclass

from .noise import NOISE_OPERATIONS

type Template = tuple[str, int]

INBOUND_TEMPLATES: tuple[Template, ...] = (  # (template, difficulty); 1 when field labels miss
    ("BONIFICO SEPA DA {name} IBAN {iban} CAUSALE {purpose}", 0),
    ("BONIFICO A VOSTRO FAVORE ORDINANTE {name} IBAN {iban} {purpose}", 0),
    ("BONIFICO DA {name} CAUSALE {purpose}", 0),
    ("ACCREDITO BONIFICO {purpose} ORDINANTE {name} {iban}", 1),
    ("{purpose} {name} {iban}", 1),
)
OUTBOUND_TEMPLATES: tuple[Template, ...] = (  # Same, for transfers sent by the customer
    ("BONIFICO A FAVORE DI {name} IBAN {iban} CAUSALE {purpose}", 0),
    ("DISPOSIZIONE BONIFICO BENEFICIARIO {name} IBAN {iban} {purpose}", 0),
    ("BONIFICO ONLINE A {name} CAUSALE {purpose}", 0),
    ("{purpose} BENEFICIARIO {name} {iban}", 1),
    ("PAGAMENTO {purpose} {name}", 1),
)
DIRECT_DEBIT_TEMPLATES: tuple[Template, ...] = (  # Same, for collections by a creditor
    ("ADDEBITO SDD {name} {purpose}", 0),
    ("ADDEBITO DIRETTO CREDITORE {name} MANDATO {ref} {purpose}", 0),
    ("SDD {ref} {name} {purpose}", 1),
)
NOISE_PROBABILITY = 0.25  # Chance of applying each noise operation to a description
HARD_DIFFICULTY = 2  # Difficulty from which a description is tagged as hard


@dataclass(frozen=True)
class Description:
    """A written description and what it reveals."""

    text: str
    shows_iban: bool
    hard: bool


def describe(
    rng: random.Random, templates: tuple[Template, ...], name: str, iban: str, purpose: str
) -> Description:
    """Write a description from a random template, then apply random noise.

    Difficulty starts from the template's own and grows by one for every noise operation that
    actually changes the text.

    Args:
        rng: Seeded random source.
        templates: Templates suited to the transaction kind.
        name: Counterparty name, inserted verbatim.
        iban: Counterparty IBAN, inserted verbatim if the template has a slot for it.
        purpose: Purpose text, which noise may alter.

    Returns:
        The description with its difficulty tag.
    """
    template, difficulty = rng.choice(templates)
    for operation in NOISE_OPERATIONS:
        if rng.random() < NOISE_PROBABILITY:
            changed = operation(rng, template, purpose)
            if changed != (template, purpose):
                template, purpose = changed
                difficulty += 1
    ref = f"MND{rng.randint(100000, 999999)}"
    text = template.format(name=name, iban=iban, purpose=purpose, ref=ref)
    return Description(" ".join(text.split()), "{iban}" in template, difficulty >= HARD_DIFFICULTY)
