"""Charts for the report, rendered as PNG images sized for the text width of an A4 page.

Series colours come from a palette validated for colour-vision deficiencies. Text never wears
a series colour, and every chart has a legend, so no information relies on colour alone.
"""

import io
from collections import defaultdict
from datetime import date
from decimal import Decimal

from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter

from ..models import Direction, PaymentPurpose
from .base import AnalysisContext, month_starts

INFLOW_COLOUR = "#2a78d6"  # Palette slot 1 (blue)
OUTFLOW_COLOUR = "#eb6834"  # Palette slot 2 (orange), validated next to slot 1
SURFACE = "#fcfcfb"  # Chart background
TEXT = "#52514e"  # Secondary text: legends and tick labels
GRID = "#e1e0d9"  # Hairline gridlines
BASELINE = "#c3c2b7"  # Axis line
FIGURE_SIZE = (6.3, 2.8)  # Inches: the text width of an A4 page with standard margins
DPI = 200  # Sharp in print without bloating the document
BAR_WIDTH = 0.38  # Share of a month slot taken by each of its two bars
LABEL_SIZE = 7  # Points, for tick labels and legends alike


def monthly_flows_chart(context: AnalysisContext) -> bytes:
    """Draw inflows and outflows per month as paired columns.

    Args:
        context: Case under analysis.

    Returns:
        PNG image.
    """
    bundle = context.bundle
    months = month_starts(bundle.period_start, bundle.period_end)
    sums: dict[tuple[Direction, date], Decimal] = defaultdict(Decimal)
    for tx in bundle.transactions:
        sums[(tx.direction, tx.booked_at.date().replace(day=1))] += tx.amount
    figure, axes = _canvas()
    positions = range(len(months))
    for shift, direction, colour, label in (
        (-BAR_WIDTH / 2, Direction.INBOUND, INFLOW_COLOUR, "Inflows"),
        (BAR_WIDTH / 2, Direction.OUTBOUND, OUTFLOW_COLOUR, "Outflows"),
    ):
        heights = [float(sums[(direction, month)]) for month in months]
        lefts = [position + shift for position in positions]
        axes.bar(lefts, heights, BAR_WIDTH, color=colour, label=label)
    axes.set_xticks(list(positions), [month.strftime("%b %y") for month in months])
    axes.yaxis.set_major_formatter(FuncFormatter(_compact))
    axes.grid(axis="y", color=GRID, linewidth=0.6)
    _legend(axes)
    return _png(figure)


def purpose_mix_chart(context: AnalysisContext) -> bytes:
    """Draw enriched inflows and outflows per payment purpose as paired horizontal bars.

    Args:
        context: Case under analysis.

    Returns:
        PNG image.
    """
    sums: dict[tuple[Direction, PaymentPurpose], Decimal] = defaultdict(Decimal)
    for tx in context.bundle.transactions:
        enrichment = context.enrichments.get(tx.transaction_id)
        if enrichment is not None:
            sums[(tx.direction, enrichment.payment_purpose)] += tx.amount
    purposes = list(PaymentPurpose)[::-1]
    figure, axes = _canvas()
    positions = range(len(purposes))
    for shift, direction, colour, label in (
        (BAR_WIDTH / 2, Direction.INBOUND, INFLOW_COLOUR, "Inflows"),
        (-BAR_WIDTH / 2, Direction.OUTBOUND, OUTFLOW_COLOUR, "Outflows"),
    ):
        widths = [float(sums[(direction, purpose)]) for purpose in purposes]
        axes.barh([p + shift for p in positions], widths, BAR_WIDTH, color=colour, label=label)
    names = [purpose.replace("_", " ").capitalize() for purpose in purposes]
    axes.set_yticks(list(positions), names)
    axes.xaxis.set_major_formatter(FuncFormatter(_compact))
    axes.grid(axis="x", color=GRID, linewidth=0.6)
    _legend(axes)
    return _png(figure)


def _canvas() -> tuple[Figure, Axes]:
    """Create a figure with recessive axes on the chart surface.

    Returns:
        The figure and its single axes.
    """
    figure = Figure(figsize=FIGURE_SIZE, dpi=DPI, facecolor=SURFACE)
    axes = figure.add_subplot(facecolor=SURFACE)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(BASELINE)
    axes.tick_params(colors=TEXT, labelsize=LABEL_SIZE, length=0)
    axes.set_axisbelow(True)
    return figure, axes


def _legend(axes: Axes) -> None:
    """Place the legend in one row above the plot, where it can never cover a bar.

    Args:
        axes: Axes holding labelled series.
    """
    style = {"fontsize": LABEL_SIZE, "labelcolor": TEXT, "frameon": False, "borderaxespad": 0.2}
    axes.legend(loc="lower left", bbox_to_anchor=(0, 1.0), ncols=2, **style)


def _compact(value: float, _position: int) -> str:
    """Format an axis tick in euros, compact from one thousand up.

    Args:
        value: Tick value.
        _position: Tick index, unused.

    Returns:
        Text such as `0`, `500`, `12K`, or `1.2M`.
    """
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}K"
    return f"{value:.0f}"


def _png(figure: Figure) -> bytes:
    """Render a figure to PNG.

    Args:
        figure: Figure to render.

    Returns:
        PNG bytes.
    """
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", facecolor=SURFACE, bbox_inches="tight")
    return buffer.getvalue()
