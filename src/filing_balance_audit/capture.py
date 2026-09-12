"""What a period's filings actually reported, read as numbers.

VALUES ARE CARRIED AS TEXT AND PARSED AS `Decimal`. Every discrepancy in the
measured corpus is between one dollar and one thousand, against balance sheets up
to ninety-four million, and a reader that parses money as binary floating point
can manufacture a difference of exactly that size out of nothing. The capture
format therefore stores the digits, and this module is the only place they become
numbers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Sequence

from . import formats
from .declaration import ASSET_TAG, TOTAL_TAGS


class CaptureError(ValueError):
    """A capture this package will not read, and why."""


@dataclass(frozen=True)
class Reading:
    """One filing's balance-sheet lines, in one reporting unit.

    `unit` is part of the identity of a reading and not decoration. The corpus
    carries the same tag at the same instant in twenty-two currencies, and a
    reader keyed on the tag alone compares a total in one against an asset figure
    in another. Measured, that produced a residual of 369 billion against a
    balance sheet that balances.
    """

    name: str
    unit: str
    values: Mapping[str, Decimal]
    unreadable: Sequence[tuple[str, str]] = field(default_factory=tuple)


class FilingPoint:
    """One filing as the core sees it. A `CapturedPoint`.

    ONE POINT PER FILING, NOT PER READING, and the difference is the domain
    decision this class exists to make. The identity is checked per reporting
    unit -- a filing reporting in two currencies has two balance sheets and two
    identities, and comparing across them is the defect that made the first
    measurement of this corpus report a residual of 369 billion. But the
    question the core asks is *is this filing reporting at all*, and that is a
    question about the filing.

    So the core is answered per filing and the per-unit detail is this domain's
    to report, through `capture_findings`. Splitting it the other way would have
    given the core two points at one address, which it indexes by name, and one
    of them would have won silently.
    """

    def __init__(self, name: str, readings: Sequence[Reading]) -> None:
        self._name, self._readings = name, tuple(readings)

    name = property(lambda self: self._name)
    path = property(lambda self: self._name)
    is_enabled = property(lambda self: True)
    #: Nothing here is judged against a limit. A balance sheet balances or it
    #: does not, and an empty mapping says that rather than implying a limit
    #: nobody wrote.
    thresholds = property(lambda self: {})
    #: The reporting unit, or all of them where a filing reports in several.
    #: This member fits this domain exactly, which is worth saying because most
    #: of the mapping above is a decision and this one is not.
    units = property(lambda self: "/".join(sorted({r.unit for r in self._readings})) or None)

    @property
    def readings(self) -> tuple[Reading, ...]:
        return self._readings

    @property
    def is_reading(self) -> bool:
        """Both sides of the identity, in at least one unit."""
        return any(ASSET_TAG in r.values and any(t in r.values for t in TOTAL_TAGS)
                   for r in self._readings)

    @property
    def reading(self) -> object:
        """The assets figure, from the first unit that carries one.

        The headline number, as text. `None` means the filing reported no assets
        at all, which is the core's *present and not reading* -- a different fact
        from a filing nobody filed.
        """
        for r in self._readings:
            if ASSET_TAG in r.values:
                return str(r.values[ASSET_TAG])
        return None

    @property
    def state(self) -> object:
        """No status word exists in this domain, and one is not invented.

        The sibling verticals carry a word the source published -- a sensor
        health string, an issue status. A financial statement data set publishes
        no such thing about a filing, and returning `"ok"` would be this package
        asserting something nobody filed.
        """
        return None


@dataclass(frozen=True)
class Capture:
    period: str
    captured_at: str | None
    readings: Sequence[Reading]
    source: str = ""

    @property
    def by_name(self) -> Mapping[str, Sequence[Reading]]:
        out: dict[str, list[Reading]] = {}
        for reading in self.readings:
            out.setdefault(reading.name, []).append(reading)
        return out

    # ---- the core's `Capture` ----
    @property
    def points(self) -> Sequence[FilingPoint]:
        return tuple(FilingPoint(name, found) for name, found in self.by_name.items())

    @property
    def complete(self) -> bool:
        return bool(self.readings)

    @property
    def errors(self) -> Sequence[tuple[str, str, str]]:
        """Every value that would not parse, kept with the filing that filed it.

        Twenty-five of these are in one real quarter. The core reads this member;
        a reader that dropped them would report those filings as carrying no
        total, when what they carry is a total nobody can read.
        """
        return tuple((r.name, tag, raw)
                     for r in self.readings for tag, raw in r.unreadable)


def load(payload: Mapping[str, Any]) -> Capture:
    """Read a `filing-balance-audit/capture/1` document.

    A value that will not parse is RECORDED rather than dropped. Twenty-five of
    them are in one real quarter, and a reader that silently skipped them would
    report a filing as carrying no total when what it carries is a total nobody
    can read. Those are different facts and only one of them is about the filer.
    """
    formats.require(payload, formats.CAPTURE)
    readings = []
    for entry in payload.get("filings") or ():
        name = str(entry.get("id") or "")
        if not name:
            raise CaptureError("a captured filing carries no id; a reading that "
                               "names nothing cannot be paired with a declaration")
        unit = str(entry.get("unit") or "")
        if not unit:
            raise CaptureError(
                f"{name} reports no unit. A reading without one cannot be "
                f"compared with another reading, and comparing across units is "
                f"the defect this field exists to make impossible")
        values, unreadable = {}, []
        for tag, raw in (entry.get("readings") or {}).items():
            try:
                values[str(tag)] = Decimal(str(raw))
            except (InvalidOperation, ValueError):
                unreadable.append((str(tag), str(raw)))
        readings.append(Reading(name=name, unit=unit, values=values,
                                unreadable=tuple(unreadable)))
    return Capture(
        period=str(payload.get("period") or ""),
        captured_at=payload.get("captured_at"),
        readings=tuple(readings),
        source=str(payload.get("source") or ""),
    )
