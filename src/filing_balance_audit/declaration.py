"""A period of filings, read as the declaration of what should balance.

THE TOLERANCE IS A SPECIFICATION AND IT IS REQUIRED. Two readings of one balance
sheet agree when they are within a stated distance of each other, and how close
that is, is a fact about the system rather than about this package. It is
declared per period and this module refuses a declaration that omits it.

That refusal is not a house style borrowed from a sibling -- it is forced, and
the force was measured. The engine's CONSISTENCY arm declines outright when a
redundancy block carries no tolerance, and says why: *how close two readings must
be is a fact about the system*. A default here would be a number nobody decided,
silently supplied to an engine that had deliberately refused to supply one.

FOR MONEY THE NUMBER IS ALMOST ALWAYS ZERO, AND IT STILL HAS TO BE WRITTEN DOWN.
A balance sheet balances exactly, in the unit it is reported in. A relative
tolerance is the wrong instrument here and dangerously so: one percent of a
ninety-four-million-dollar balance sheet is nine hundred thousand dollars, and
every real discrepancy in the measured corpus is between one dollar and one
thousand. So `tolerance_absolute` is what this format takes, and a declaration
that means zero says zero.

ONE SIGNATURE, RECORDED AS A CHOICE. A period declaration is prepared and read by
one person, and the gate asks that a person signs at all rather than asking for a
second name nobody is accountable for. An unreviewed declaration is refused by
every verb that would act on it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from . import formats

#: The balance-sheet total, under each taxonomy this package reads.
#:
#: TWO NAMES FOR ONE LINE, and knowing only the first is a reader defect that
#: reads as a corpus property. Measured over 2025q1: a reader holding only the
#: US-GAAP name finds the identity on 17.4% of 40-F filings and 49.6% of 20-F,
#: and reports the rest as filings carrying no balance sheet. They carry one,
#: under IFRS. With both names 40-F is 100.0%, 20-F is 94.1%, and the comparable
#: corpus goes from 5,769 filings to 6,083. The IFRS identity is exact on every
#: one of the 314 filings where it can be computed.
TOTAL_TAGS = ("LiabilitiesAndStockholdersEquity", "EquityAndLiabilities")

#: The asset side. One name in both taxonomies, which is why the gap above sat
#: on the other side of the equation and was easy to miss.
ASSET_TAG = "Assets"

#: The components that sum to the total, tried in order. The first complete pair
#: wins. This is the SECOND route to the same number, and having two is what
#: makes a disagreement localisable rather than merely detectable.
PART_GROUPS = (
    ("Liabilities", "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest"),
    ("Liabilities", "StockholdersEquity"),
)

#: Words that mark a `reviewed_by` as a disclosure rather than a person's
#: signature, upper case as written. A closed, short set: a marker nobody
#: recognises is not a disclosure, it is prose.
DISCLOSURE_MARKERS = frozenset({"FIXTURE", "DERIVED", "SYNTHETIC", "UNSIGNED"})


@dataclass(frozen=True)
class Filing:
    """One filing a period says should balance. A `DeclaredPoint`.

    The last three members are the core's, answered rather than left off.
    `expects_reading` is TRUE for every type this domain declares, which is the
    measured decision recorded in `formats.DECLARED_TYPES`: no form family
    reliably carries no balance sheet. `is_templated` is False because an
    accession number is an identifier and not a pattern -- there is nothing in
    it to substitute -- and `thresholds` is empty because nothing here is judged
    against a limit. A balance sheet balances or it does not.
    """

    name: str
    type: str | None
    display_name: str
    source: str
    disabled: bool = False
    form: str = ""
    unit: str = ""
    cik: str = ""

    expects_reading: bool = True
    is_templated: bool = False
    thresholds: Sequence[Any] = ()


@dataclass(frozen=True)
class Period:
    """A `DeclarationSource`, plus the tolerance only this document can publish."""

    points: Sequence[Filing]
    sources: Sequence[Any]
    tolerance_absolute: float
    period: str = ""
    #: The core reads both. Empty here and said so: a period index records no
    #: anomalies of its own, and a source it could not read would have stopped
    #: `load` rather than arriving as a note.
    anomalies: Sequence[Any] = ()
    unreadable: Sequence[tuple[str, str]] = ()
    reviewed_by: str | None = None
    reviewed_on: str | None = None

    @property
    def reviewed(self) -> bool:
        return bool(self.reviewed_by) and bool(self.reviewed_on)

    @property
    def disclosure(self) -> str | None:
        """The marker word if this signature discloses itself, else `None`.

        A gate asking only whether the field is filled cannot tell a signature
        from an attribution, and a corpus derived from public filings has to fill
        it to be usable at all. The marker must be UPPER CASE as written: a firm
        actually named `Derived Analytics LLP` is a real signature, and a
        case-insensitive comparison reports it as a disclosure -- a real
        signature printed as unsigned, which is the failure nobody would think
        to check.
        """
        written = (self.reviewed_by or "").strip()
        first = written.split(maxsplit=1)
        head = first[0].rstrip(":,-") if first else ""
        if head.isupper() and head in DISCLOSURE_MARKERS:
            return head
        if written.startswith("NOT SIGNED"):
            return "NOT SIGNED"
        return None


class DeclarationError(ValueError):
    """A declaration this package will not act on, and why."""


def load(payload: Mapping[str, Any]) -> Period:
    """Read a `filing-balance-audit/declaration/1` document.

    Refuses rather than records, for the two things that cannot be repaired
    downstream: a missing tolerance, because the engine's agreement arm declines
    without one and a guessed number would be worse than the decline; and a
    declared type outside the enumeration, because a type nobody recognises would
    be counted out silently and leave the denominator wrong.
    """
    formats.require(payload, formats.DECLARATION)

    if "tolerance_absolute" not in payload:
        raise DeclarationError(
            "this declaration names no tolerance_absolute. Two readings of one "
            "balance sheet agree when they are within a stated distance, and "
            "the engine declines to judge agreement without that distance "
            "rather than choosing one. There is no default here either: for "
            "money the answer is almost always 0, and a 0 nobody wrote down is "
            "indistinguishable from a question nobody asked")
    tolerance = payload["tolerance_absolute"]
    if not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or tolerance < 0:
        raise DeclarationError(
            f"tolerance_absolute is {tolerance!r}; it has to be a number of "
            f"reporting units, and 0 is the usual and legitimate answer")

    period = str(payload.get("period") or "(unnamed period)")
    points = []
    for entry in payload.get("filings") or ():
        declared_type = entry.get("declared_type")
        if declared_type not in formats.DECLARED_TYPES:
            raise DeclarationError(
                f"{entry.get('id')!r} declares type {declared_type!r}, which is "
                f"not one of {', '.join(formats.DECLARED_TYPES)}. An "
                f"unrecognised type would be counted out rather than audited, "
                f"so it is refused here instead of quietly narrowing the "
                f"denominator")
        name = str(entry["id"])
        label = str(entry.get("name") or "")
        points.append(Filing(
            name=name,
            type=declared_type,
            display_name=f"{name} {label[:48]}".strip(),
            source=period,
            disabled=bool(entry.get("excluded")),
            form=str(entry.get("form") or ""),
            unit=str(entry.get("unit") or ""),
            cik=str(entry.get("cik") or ""),
        ))

    return Period(
        points=tuple(points),
        sources=tuple(payload.get("sources") or ()),
        tolerance_absolute=float(tolerance),
        period=period,
        reviewed_by=payload.get("reviewed_by"),
        reviewed_on=payload.get("reviewed_on"),
    )
