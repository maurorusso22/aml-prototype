"""Report sections, in reading order; each one writes itself into the document."""

from collections.abc import Callable

from docx.document import Document

from ..data import ReportData
from ..i18n import Catalog
from .activity import behaviour, counterparties, geography, profile
from .case import alert_context, customer_profile, relationship
from .closing import analyst_assessment, appendix
from .flags import red_flags
from .front import cover, findings

type Section = Callable[[Document, ReportData, Catalog], None]

SECTIONS: tuple[Section, ...] = (  # Order of the sections in the report
    cover,
    findings,
    alert_context,
    customer_profile,
    relationship,
    behaviour,
    counterparties,
    geography,
    red_flags,
    profile,
    analyst_assessment,
    appendix,
)
