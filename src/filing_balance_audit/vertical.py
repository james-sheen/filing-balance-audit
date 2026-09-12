"""This domain, offered to the shared core as a registered vertical.

All twelve required members of the core's `Vocabulary` are answered, and so are
the three optional ones: a report printing `point` about a filing is a report in
somebody else's noun.

**NOTHING IS COUNTED OUT BY TYPE, AND THAT IS THIS VERTICAL'S ONE REAL DEPARTURE
FROM ITS SIBLINGS.** Every other vertical in this family uses `is_expected_live`
to remove declared types the audit was never about -- a ceremony is not a
deliverable. The obvious move here was to do the same with form families that do
not carry a balance sheet. Measured over 2025q1 there is no such family: 10-K
97.7%, 10-Q 96.7%, S-1 96.6%, and 40-F 100.0% once the second taxonomy is read.
So `is_expected_live` is true for every type this domain declares. It is a real
answer arrived at by measurement, not an unimplemented stub, and it is said here
because a reviewer who knows the siblings will read a permissive predicate as one.

**WHAT THIS VERTICAL DELIBERATELY DOES NOT REPORT.** `capture_findings` can see
the identity failing -- assets against a balance-sheet total is derivable from
the capture alone, without any declaration. It does not report it. The engine
already does, through CONSISTENCY, and a second path to the same answer is a
finding no test can fail on: remove either and the verdict is unchanged, so
neither is load-bearing and neither can go red alone. What arrives here instead
is what the engine cannot see -- values it never received because they would not
parse, and a filing whose second currency is incomplete.
"""

from __future__ import annotations

from typing import Any, Mapping, Sequence

from .declaration import ASSET_TAG as _ASSETS, TOTAL_TAGS as _TOTALS

#: Every class a declared filing can fall into. `unrecognised` is last and is not
#: a type anything declares: `declaration.load` refuses an unknown type outright.
#: It exists because `classify` is handed whatever the core has, including
#: `None`, and a classifier that can answer outside its own vocabulary is not one.
KINDS = ("annual", "interim", "registration", "other", "unrecognised")

#: The kinds the audit is about: all of them. See the module docstring.
AUDITED = ("annual", "interim", "registration", "other")


class FilingVocabulary:
    """The core's vocabulary, for balance sheets on a period of filings.

    `Filing`, not `Sec`, and the distribution rename to `filing-balance-audit` did
    not change it. The prefix names the SOURCE; this class names the SUBJECT, and
    the subject is a filing. `noun` is `("filing", "filings")` for the same
    reason -- the report is about filings, and a reader of it does not need to be
    told which regulator the data came from in every sentence.
    """

    kinds = KINDS
    noun = ("filing", "filings")

    #: Only the kind that should never appear is counted separately. A count of
    #: filings this domain could not classify is a fact about the declaration
    #: reaching it, and zero is the expected reading.
    count_keys = {"unrecognised": "unrecognised_type"}

    def count_labels(self) -> Mapping[str, tuple[str, str]]:
        return {
            "unrecognised_type": (
                "filings of a type this vocabulary does not know",
                "expected to be zero: the reader refuses an unknown type, so a "
                "non-zero count here means something reached the core without "
                "passing through it"),
        }

    def classify(self, declared_type: str | None) -> str:
        return declared_type if declared_type in AUDITED else "unrecognised"

    def is_auditable(self, kind: str) -> bool:
        return kind in AUDITED

    def is_expected_live(self, declared_type: str | None) -> bool:
        """Every recognised type. Measured, not permissive by default."""
        return self.classify(declared_type) in AUDITED

    def template_pattern(self, declared_name: str) -> object:
        """Never a template.

        An accession number is an identifier: there is nothing in it to
        substitute. Returning `None` is the protocol's *this name is not a
        template*, and it is the honest answer rather than an unimplemented one.
        A domain that guessed here would wildcard an identifier into a
        match-anything pattern, which is how one filing comes to stand for a
        thousand.
        """
        return None

    def same_point(self, old: Any, new: Any) -> bool:
        """Two captures at one accession number, and whether they are one filing.

        A domain with no evidence to the contrary says yes. This domain has
        some: a filing reporting only in USD and the same accession number
        reporting only in CNY are not two readings of one balance sheet, they are
        two balance sheets. Where the reporting units overlap at all, or either
        side reports none, the answer is yes.
        """
        before = {r.unit for r in getattr(old, "readings", ())}
        after = {r.unit for r in getattr(new, "readings", ())}
        if not before or not after:
            return True
        return bool(before & after)

    def captures_comparable(self, before: Any, after: Any) -> bool:
        """Whether per-filing comparison between these two captures means anything.

        Two different quarters have disjoint filings by construction -- an
        accession number is issued once -- so pairing them point by point
        compares nothing against nothing and reports every filing as vanished.
        False here means those comparisons are SKIPPED and said to be skipped,
        which is a different answer from *they ran and found nothing*.

        **A CAPTURE THAT NAMES NO PERIOD IS NOT COMPARABLE TO ANOTHER ONE.** The
        first version of this compared the two periods directly, and two captures
        that both carry none compare `None == None` and come back TRUE -- a
        sentinel equal to itself, read as agreement. The conformance kit drove it
        with a foreign capture carrying no period at all and this member said
        *yes, comparable*, which is the one answer it must not give about two
        objects it cannot identify.
        """
        was, now = getattr(before, "period", None), getattr(after, "period", None)
        if not was or not now:
            return False
        return was == now

    def point_changes(self, old: Any, new: Any, *,
                      comparable: bool = False) -> Sequence[object]:
        """What changed about one filing, in terms only this domain has."""
        if not comparable:
            return ()
        changes = []
        before = {r.unit for r in getattr(old, "readings", ())}
        after = {r.unit for r in getattr(new, "readings", ())}
        for unit in sorted(before - after):
            changes.append(f"stopped reporting in {unit}")
        for unit in sorted(after - before):
            changes.append(f"began reporting in {unit}")
        was, now = getattr(old, "reading", None), getattr(new, "reading", None)
        if was is not None and now is not None and was != now:
            changes.append(f"restated total assets: {was} -> {now}")
        return tuple(changes)

    def capture_changes(self, before: Any, after: Any) -> Sequence[object]:
        """What changed about the period as a whole."""
        changes = []
        was, now = getattr(before, "period", None), getattr(after, "period", None)
        if was != now:
            changes.append(f"a different period: {was} -> {now}")
        counts = (len(getattr(before, "readings", ())), len(getattr(after, "readings", ())))
        if counts[0] != counts[1]:
            changes.append(f"readings {counts[0]:,} -> {counts[1]:,}")
        errors = (len(getattr(before, "errors", ())), len(getattr(after, "errors", ())))
        if errors[0] != errors[1]:
            changes.append(f"unreadable values {errors[0]} -> {errors[1]}")
        return tuple(changes)

    def capture_findings(self, capture: Any) -> Sequence[object]:
        """Findings only this domain can produce from its own capture.

        Neither is the identity failing. See the module docstring: the engine
        reports that, and two paths to one answer is a finding nothing can
        falsify.
        """
        from presence_audit.diff import Finding          # deferred: optional extra

        out = []
        for name, tag, raw in getattr(capture, "errors", ()):
            out.append(Finding(
                kind="unreadable_value", sensor=name,
                detail=f"{tag} was filed as {raw!r}, which is not a number. The "
                       f"engine never receives it, so no axiom can decline it "
                       f"either -- it is absent from both answers unless this "
                       f"says so"))
        for point in getattr(capture, "points", ()):
            readings = getattr(point, "readings", ())
            if len(readings) < 2:
                continue
            partial = [r.unit for r in readings
                       if not (_ASSETS in r.values
                               and any(t in r.values for t in _TOTALS))]
            if partial and len(partial) < len(readings):
                out.append(Finding(
                    kind="partial_second_currency", sensor=point.name,
                    detail=f"reports in {point.units} and only some of those "
                           f"carry both sides: {', '.join(sorted(partial))} is "
                           f"incomplete. The filing is checked on the currency "
                           f"that is complete, so it is neither absent nor "
                           f"fully checked"))
        return tuple(out)

    def peer_groups(self, declaration: Any) -> Sequence[Mapping[str, object]]:
        """Filings this domain considers redundant readings of one thing.

        An amendment and its original. One registrant filing an S-1 and then an
        S-1/A for the same period has filed the same balance sheet twice, and
        the two should agree -- `a filing of registrant R-4708` filed both in 2025q1 and both
        carry the same thousand-dollar discrepancy, which is how you can tell the
        fault is in the statement rather than in one transcription of it.

        Grouped by registrant and form family rather than by form: `S-1` and
        `S-1/A` are the pair, and grouping by the literal form would put them in
        different groups and find nothing.
        """
        groups: dict[tuple[str, str], list[str]] = {}
        for point in getattr(declaration, "points", ()):
            registrant = getattr(point, "cik", "") or ""
            form = (getattr(point, "form", "") or "").removesuffix("/A")
            if not registrant or not form:
                continue
            groups.setdefault((registrant, form), []).append(point.name)
        return tuple({"key": f"{registrant}:{form}", "members": tuple(sorted(members))}
                     for (registrant, form), members in sorted(groups.items())
                     if len(members) > 1)

    def report_sections(self) -> Mapping[str, object]:
        """One extra key: how much of the period could be read at all.

        A vertical with nothing to add returns an empty mapping and the report
        has no such key -- rather than a key holding an empty object, which reads
        as *checked and found nothing*.
        """
        return {"reporting_units": _reporting_units}


def _reporting_units(capture: Any) -> Mapping[str, object]:
    units: dict[str, int] = {}
    for reading in getattr(capture, "readings", ()):
        units[reading.unit] = units.get(reading.unit, 0) + 1
    return {"count": len(units),
            "readings_by_unit": dict(sorted(units.items(), key=lambda kv: -kv[1]))}


def register(period: Any = None) -> None:
    """Offer this vocabulary to the core for the current process.

    `period` is accepted and unused, and that is deliberate rather than an
    oversight. A sibling vertical needs the declaration here because its
    `capture_findings` has to know each point's declared type, and the protocol
    hands that hook the capture alone. This domain's capture findings are
    derivable from the capture, so nothing has to be smuggled in -- and the
    parameter is kept so a caller written against the family's shape does not
    have to know which of the two it is talking to.
    """
    from presence_audit.vocabulary import register as _register   # deferred
    _register(FilingVocabulary())
