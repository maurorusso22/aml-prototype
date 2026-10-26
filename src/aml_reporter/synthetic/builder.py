"""Collect the drafted transactions of one case, including labelled transfers and debits."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from ..models import Channel, Direction, PaymentPurpose, TransactionType
from .descriptions import (
    DIRECT_DEBIT_TEMPLATES,
    INBOUND_TEMPLATES,
    OUTBOUND_TEMPLATES,
    Template,
    describe,
)
from .drafts import Draft, LabelDraft
from .ledger import Ledger
from .parties import Party
from .purposes import purpose_text


class CaseBuilder(Ledger):
    """Ledger that also writes wire transfers and direct debits, each with its label."""

    def wire(
        self,
        day: date,
        amount: Decimal,
        direction: Direction,
        party: Party,
        purpose: PaymentPurpose,
        text: str | None = None,
    ) -> Draft:
        """Add a wire transfer received from or sent to a counterparty.

        Args:
            day: Booking date.
            amount: Amount in euros.
            direction: Inbound or outbound.
            party: Counterparty.
            purpose: Ground-truth purpose.
            text: Purpose text to use instead of a random one.

        Returns:
            The new draft.
        """
        inbound = direction is Direction.INBOUND
        templates = INBOUND_TEMPLATES if inbound else OUTBOUND_TEMPLATES
        channel = (
            Channel.INTERBANK if inbound else self.ctx.rng.choice((Channel.ONLINE, Channel.BRANCH))
        )
        description, label = self._describe(day, templates, party, purpose, text)
        kind = TransactionType.WIRE_TRANSFER
        when = self.ctx.at(day)
        return self.add(Draft(when, amount, direction, channel, kind, description, label=label))

    def direct_debit(
        self, day: date, amount: Decimal, party: Party, purpose: PaymentPurpose
    ) -> Draft:
        """Add a collection initiated by a creditor.

        Args:
            day: Booking date.
            amount: Amount in euros.
            party: Creditor.
            purpose: Ground-truth purpose.

        Returns:
            The new draft.
        """
        description, label = self._describe(day, DIRECT_DEBIT_TEMPLATES, party, purpose, None)
        direction, channel = Direction.OUTBOUND, Channel.INTERBANK
        kind = TransactionType.DIRECT_DEBIT
        when = self.ctx.at(day)
        return self.add(Draft(when, amount, direction, channel, kind, description, label=label))

    def _describe(
        self,
        day: date,
        templates: tuple[Template, ...],
        party: Party,
        purpose: PaymentPurpose,
        text: str | None,
    ) -> tuple[str, LabelDraft]:
        """Write a description and the label an ideal enricher would extract from it.

        Args:
            day: Booking date, used in purpose texts.
            templates: Description templates to choose from.
            party: Counterparty, written verbatim in the description.
            purpose: Ground-truth purpose.
            text: Purpose text to use instead of a random one.

        Returns:
            Description text and its label.
        """
        rng = self.ctx.rng
        written_purpose = text if text is not None else purpose_text(rng, purpose, day)
        written = describe(rng, templates, party.name, party.iban, written_purpose)
        iban = party.iban if written.shows_iban else None
        return written.text, LabelDraft(party.name, iban, party.kind, purpose, written.hard)


@dataclass(frozen=True)
class ScenarioRun:
    """What a scenario hands back: its builder, the alerted draft, and why the alert fired."""

    builder: CaseBuilder
    alerted: Draft
    alert_scenario: str
    alert_reason: str
