"""How outflows leave the account: branch, ATM, online, card terminal, or another bank."""

from ..models import Channel, Direction, Fact, FactCategory
from .base import AnalysisContext
from .facts import Facts, ratio, total
from .registry import analyser

CHANNEL_NAMES = {  # How each channel reads in a fact label
    Channel.BRANCH: "branches",
    Channel.ATM: "ATMs",
    Channel.ONLINE: "online banking",
    Channel.POS: "card terminals",
    Channel.INTERBANK: "collections by other banks",
}


@analyser
def channel_mix(context: AnalysisContext) -> list[Fact]:
    """Share of outflow value by channel; every channel always gets a fact, possibly zero.

    Args:
        context: Case under analysis.

    Returns:
        Facts F-CHAN-001 to F-CHAN-005, in the order of the `Channel` enum.
    """
    facts = Facts("CHAN", FactCategory.TRANSACTION_BEHAVIOUR)
    outflows = context.flows(Direction.OUTBOUND)
    whole = total(outflows)
    for number, channel in enumerate(Channel, start=1):
        used = [tx for tx in outflows if tx.channel is channel]
        label = f"Share of outflows through {CHANNEL_NAMES[channel]}"
        facts.add(number, label, ratio(total(used), whole), "ratio", used)
    return facts.items
