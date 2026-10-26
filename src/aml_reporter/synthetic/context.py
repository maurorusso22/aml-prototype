"""Shared state for generating one case: seeded randomness and the look-back window."""

import calendar
import random
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import Self
from zoneinfo import ZoneInfo

TIME_ZONE = ZoneInfo("Europe/Rome")  # Time zone of every synthetic booking
PERIOD_START = date(2025, 10, 1)  # First day of every look-back window, fixed for reproducibility
PERIOD_END = date(2026, 9, 30)  # Last day of every look-back window
CENT = Decimal("0.01")  # Smallest amount unit


@dataclass(frozen=True)
class SynthContext:
    """Seeded randomness and calendar helpers for one case.

    Every case derives its own seed from the global seed and its index, so a case comes out
    identical whether it is generated alone or together with the others.
    """

    rng: random.Random
    period_start: date = PERIOD_START
    period_end: date = PERIOD_END

    @classmethod
    def create(cls, seed: int, case_index: int) -> Self:
        """Build the context of one case.

        Args:
            seed: Global seed of the generation run.
            case_index: Position of the scenario in the registry, starting at 1.

        Returns:
            A fresh context.
        """
        return cls(rng=random.Random(f"{seed}:{case_index}"))

    def money(self, low: float, high: float) -> Decimal:
        """Draw an amount in euros.

        Args:
            low: Minimum amount.
            high: Maximum amount.

        Returns:
            Amount rounded to the cent.
        """
        return Decimal(f"{self.rng.uniform(low, high):.2f}")

    def round_money(self, low: int, high: int, step: int) -> Decimal:
        """Draw a round amount in euros, such as a cash withdrawal or a house price.

        Args:
            low: Minimum amount.
            high: Upper bound, excluded.
            step: Granularity of the amount.

        Returns:
            Amount with two decimal places.
        """
        return Decimal(self.rng.randrange(low, high, step)).quantize(CENT)

    def at(self, day: date) -> datetime:
        """Draw a booking time during business hours.

        Args:
            day: Booking date.

        Returns:
            Timestamp in the Rome time zone.
        """
        hour, minute = self.rng.randint(8, 19), self.rng.randint(0, 59)
        return datetime(day.year, day.month, day.day, hour, minute, tzinfo=TIME_ZONE)

    def days_after(self, day: date, low: int, high: int) -> date:
        """Draw a date a few days after another.

        Args:
            day: Reference date.
            low: Minimum offset in days.
            high: Maximum offset in days.

        Returns:
            The shifted date.
        """
        return day + timedelta(days=self.rng.randint(low, high))

    def days_in_month(
        self, month: date, window: tuple[date, date], first: int = 1, last: int = 31, count: int = 1
    ) -> list[date]:
        """Draw dates in a month, keeping only those inside a window.

        Args:
            month: Any date in the month.
            window: First and last allowed dates.
            first: Earliest day of the month.
            last: Latest day of the month, capped at the month length.
            count: How many dates to draw.

        Returns:
            Dates inside the window, possibly fewer than `count`.
        """
        length = calendar.monthrange(month.year, month.month)[1]
        low, high = min(first, length), min(last, length)
        days = [month.replace(day=self.rng.randint(low, high)) for _ in range(count)]
        return [day for day in days if window[0] <= day <= window[1]]


def month_starts(start: date, end: date) -> list[date]:
    """List the first day of every month that overlaps a window.

    Args:
        start: First day of the window.
        end: Last day of the window.

    Returns:
        First days of the months, in order.
    """
    months, current = [], start.replace(day=1)
    while current <= end:
        months.append(current)
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)
    return months
