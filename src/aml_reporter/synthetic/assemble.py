"""Turn a finished scenario into a validated case bundle and its labels."""

from dataclasses import asdict
from datetime import timedelta
from decimal import Decimal
from typing import NamedTuple

from ..models import Account, AccountStatus, Alert, CaseBundle, Direction, Outcome, Transaction
from .builder import ScenarioRun
from .context import SynthContext
from .drafts import Draft
from .labels import CaseLabels, TransactionLabel
from .products import Persona

ALERT_HOUR = 6  # Hour of the morning when the overnight monitoring batch raises alerts


class GeneratedCase(NamedTuple):
    """A case bundle with its ground truth."""

    bundle: CaseBundle
    labels: CaseLabels


def assemble(
    run: ScenarioRun, scenario: str, outcome: Outcome, flags: tuple[str, ...]
) -> GeneratedCase:
    """Sort the drafts, assign identifiers, and build the bundle and its labels.

    Args:
        run: Result of a scenario.
        scenario: Scenario name, stored in the labels.
        outcome: Decision an analyst should reach.
        flags: Red-flag rules the case should raise.

    Returns:
        The validated case and its labels.
    """
    ctx, persona = run.builder.ctx, run.builder.persona
    index = persona.case_index
    ordered = sorted(run.builder.drafts, key=lambda draft: draft.booked_at)
    ids = {draft: f"TX-{index:02d}{number:04d}" for number, draft in enumerate(ordered, 1)}
    raised_at = (run.alerted.booked_at + timedelta(days=1)).replace(hour=ALERT_HOUR, minute=0)
    alert = Alert(
        alert_id=f"AL-{index:06d}",
        customer_id=persona.customer.customer_id,
        transaction_id=ids[run.alerted],
        raised_at=raised_at,
        scenario=run.alert_scenario,
        reason=run.alert_reason,
    )
    bundle = CaseBundle(
        case_id=f"CASE-{index:06d}",
        period_start=ctx.period_start,
        period_end=ctx.period_end,
        alert=alert,
        customer=persona.customer,
        accounts=(_account(ctx, persona, ordered),),
        cards=(persona.card,),
        transactions=tuple(_transaction(draft, ids[draft], persona) for draft in ordered),
    )
    labels = tuple(
        TransactionLabel(transaction_id=ids[draft], **asdict(draft.label))
        for draft in ordered
        if draft.label is not None
    )
    case_labels = CaseLabels(
        case_id=bundle.case_id,
        scenario=scenario,
        expected_outcome=outcome,
        expected_flags=flags,
        transactions=labels,
    )
    return GeneratedCase(bundle, case_labels)


def _account(ctx: SynthContext, persona: Persona, ordered: list[Draft]) -> Account:
    """Build the account, with an opening balance that never lets it go overdrawn.

    Args:
        ctx: Generation context.
        persona: Account holder.
        ordered: Drafts in booking order.

    Returns:
        The account with its end-of-period balance.
    """
    running = lowest = Decimal(0)
    for draft in ordered:
        running += draft.amount if draft.direction is Direction.INBOUND else -draft.amount
        lowest = min(lowest, running)
    opening = -lowest + ctx.money(500, 5000)
    return Account(
        account_id=persona.account_id,
        iban=persona.iban,
        status=AccountStatus.ACTIVE,
        opened_on=persona.opened_on,
        balance=opening + running,
    )


def _transaction(draft: Draft, transaction_id: str, persona: Persona) -> Transaction:
    """Turn a draft into a validated transaction.

    Args:
        draft: Draft to convert.
        transaction_id: Identifier assigned in booking order.
        persona: Account and card holder.

    Returns:
        The transaction.
    """
    return Transaction(
        transaction_id=transaction_id,
        account_id=persona.account_id,
        card_id=persona.card.card_id if draft.uses_card else None,
        booked_at=draft.booked_at,
        amount=draft.amount,
        direction=draft.direction,
        channel=draft.channel,
        transaction_type=draft.transaction_type,
        description=draft.description,
    )
