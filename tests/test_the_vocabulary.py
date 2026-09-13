"""The vocabulary this vertical offers the shared core.

The conformance kit is run here rather than described. It proves one thing and
says so itself: that nothing reached past the protocol. It cannot prove the
protocol is SUFFICIENT for this domain -- a fixture written from the protocol can
only ever find that something exceeded the document, never that the document is
missing something a real domain needs. What this vertical found that the kit
could not is recorded in `FINDINGS.md`.
"""

import json
import pathlib

import pytest

from presence_audit.conformance import (Capture as ForeignCapture, SAMPLE_CAPTURE,
                                        check_a_vocabulary, check_the_core)
from presence_audit.vocabulary import DEFAULT_NOUN

from filing_balance_audit import formats
from filing_balance_audit.vertical import AUDITED, KINDS, FilingVocabulary

VOCABULARY = FilingVocabulary()
ROOT = pathlib.Path(__file__).resolve().parents[1]


def test_the_conformance_kit_reports_no_problem_with_this_vocabulary():
    problems, _ = check_a_vocabulary(VOCABULARY)
    assert problems == []


def test_the_core_itself_still_reaches_for_nothing_it_does_not_declare():
    """Run against the installed core, not described. A vertical is where this
    is found: the core once called `.points` on a capture the protocol never
    declared it, and the one vertical in the tree happened to have it."""
    assert check_the_core() == []


def test_every_required_member_is_answered():
    required = ("kinds", "count_keys", "classify", "is_auditable",
                "is_expected_live", "template_pattern", "same_point",
                "captures_comparable", "point_changes", "capture_changes",
                "capture_findings", "peer_groups")
    missing = [name for name in required if not hasattr(VOCABULARY, name)]
    assert missing == []


def test_the_three_optional_members_are_answered_rather_than_defaulted():
    """A report printing `point` about a filing is in somebody else's noun."""
    assert VOCABULARY.noun == ("filing", "filings")
    assert tuple(VOCABULARY.noun) != tuple(DEFAULT_NOUN)
    assert VOCABULARY.count_labels()
    assert VOCABULARY.report_sections()


def test_classify_never_answers_outside_its_own_kinds():
    for declared in [*formats.DECLARED_TYPES, None, "", "prospectus", 7]:
        assert VOCABULARY.classify(declared) in KINDS


def test_nothing_is_counted_out_by_type_and_that_is_measured():
    """This vertical's one real departure from its siblings.

    Every declared type is audited, because no form family reliably carries no
    balance sheet. Asserted over `formats.DECLARED_TYPES` so the two cannot
    drift: a copy of the enumeration here would be a second record of one fact.
    """
    assert set(AUDITED) == set(formats.DECLARED_TYPES)
    for declared in formats.DECLARED_TYPES:
        assert VOCABULARY.is_expected_live(declared)
        assert VOCABULARY.is_auditable(VOCABULARY.classify(declared))
    assert not VOCABULARY.is_expected_live(None)
    assert not VOCABULARY.is_auditable("unrecognised")


def test_an_accession_number_is_never_read_as_a_template():
    """A guessed pattern wildcards an identifier into a match-anything."""
    for name in ("F-9a3c1f77b0d2", "{cik}-25-{seq}", ""):
        assert VOCABULARY.template_pattern(name) is None


def test_two_captures_that_name_no_period_are_not_comparable():
    """`None == None` is True, and that is the whole defect.

    The first version compared the two periods directly, so two captures both
    carrying none came back comparable -- a sentinel equal to itself, read as
    agreement about two objects this domain cannot identify.
    """
    foreign = ForeignCapture(SAMPLE_CAPTURE)
    assert not VOCABULARY.captures_comparable(foreign, foreign)


@pytest.mark.parametrize("before,after,expected", [
    ("2025q1", "2025q1", True),
    ("2025q1", "2024q4", False),
    ("2025q1", "", False),
    ("", "", False),
])
def test_only_two_captures_of_one_named_period_are_comparable(before, after, expected):
    class Stub:
        def __init__(self, period): self.period = period
    assert VOCABULARY.captures_comparable(Stub(before), Stub(after)) is expected


def test_a_filing_reporting_only_in_another_currency_is_not_the_same_point():
    class Reading:
        def __init__(self, unit): self.unit = unit
    class Point:
        def __init__(self, *units): self.readings = [Reading(u) for u in units]
    assert VOCABULARY.same_point(Point("USD"), Point("USD", "CNY"))
    assert not VOCABULARY.same_point(Point("USD"), Point("CNY"))
    # No evidence to the contrary is not evidence: the protocol's default is yes.
    assert VOCABULARY.same_point(Point(), Point("CNY"))


def test_peer_groups_pairs_an_amendment_with_its_original(real_period, real_run):
    """One registrant filed an S-1 and an S-1/A in 2025q1, both carrying the same
    thousand-dollar discrepancy -- which is how the fault is shown to be in the
    statement rather than in one transcription of it.

    The pair is found BY ITS RESIDUAL and not by name. It used to be named, with
    the two positional labels; the evidence is now keyed on a salt this suite
    does not hold, so the only durable way to say *those two* is the thing that
    makes them interesting -- they are the two filings a thousand out.
    """
    groups = VOCABULARY.peer_groups(real_period)
    assert groups, "no peer group was found in a real quarter"
    thousand = {r.name for r in real_run.fed.resolved
                if str(r.residuals().get("assets_vs_total")) == "1000.0000"}
    assert len(thousand) == 2, "the S-1 and its amendment"
    assert any(thousand <= set(g["members"]) for g in groups), \
        "the two are one registrant's, so a peer group has to contain both"
    assert all(len(g["members"]) > 1 for g in groups)


def test_the_identity_failure_is_deliberately_not_a_capture_finding(real_capture):
    """The engine reports it. A second path to one answer is a finding no test
    can fail on: remove either and the verdict is unchanged."""
    kinds = {f.kind for f in VOCABULARY.capture_findings(real_capture)}
    assert kinds <= {"unreadable_value", "partial_second_currency"}
    assert "unreadable_value" in kinds


def test_capture_findings_reports_what_the_engine_never_receives(real_capture):
    findings = [f for f in VOCABULARY.capture_findings(real_capture)
                if f.kind == "unreadable_value"]
    assert len(findings) == len(real_capture.errors) == 25


def test_a_partial_second_currency_is_reported_where_one_exists():
    """Constructed, because 2025q1 has none -- and that is the reason to write it.

    Of 39 multi-currency filings in that quarter, 38 carry both sides in every
    currency and one carries them in none. Zero are partial. A finding kind whose
    only evidence is a corpus that never produces it is a kind nothing can
    falsify: the code could be wrong in either direction and every run would look
    identical.

    So the case is built here while the real count is still zero, rather than
    waiting for the quarter that has one and discovering then whether this works.
    """
    from filing_balance_audit import capture
    from filing_balance_audit import formats

    read = capture.load({
        "format": formats.CAPTURE, "period": "testq",
        "filings": [
            {"id": "F-1", "unit": "USD",
             "readings": {"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"}},
            {"id": "F-1", "unit": "CNY", "readings": {"Assets": "70"}},
        ]})
    findings = [f for f in VOCABULARY.capture_findings(read)
                if f.kind == "partial_second_currency"]
    assert len(findings) == 1
    assert findings[0].sensor == "F-1"
    assert "CNY" in findings[0].detail


def test_a_filing_complete_in_every_currency_is_not_reported():
    """The control. Without it the test above passes on a predicate that fires
    for any multi-currency filing at all, which is 38 of the 39 in one quarter."""
    from filing_balance_audit import capture, formats

    both = {"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"}
    read = capture.load({
        "format": formats.CAPTURE, "period": "testq",
        "filings": [{"id": "F-1", "unit": "USD", "readings": both},
                    {"id": "F-1", "unit": "CNY", "readings": both}]})
    assert not [f for f in VOCABULARY.capture_findings(read)
                if f.kind == "partial_second_currency"]


def test_a_filing_incomplete_in_every_currency_is_left_to_the_pairing():
    """One real filing in 2025q1 is this. It is not a partial-currency finding:
    nothing about it is partial, and the core reports it as present and not
    reading, which is the right answer and not this vocabulary's to duplicate."""
    from filing_balance_audit import capture, formats

    read = capture.load({
        "format": formats.CAPTURE, "period": "testq",
        "filings": [{"id": "F-1", "unit": "USD", "readings": {"Assets": "10"}},
                    {"id": "F-1", "unit": "CNY", "readings": {"Assets": "70"}}]})
    assert not [f for f in VOCABULARY.capture_findings(read)
                if f.kind == "partial_second_currency"]


def test_this_capture_never_yields_two_points_at_one_address(real_capture):
    """The invariant that keeps this vertical clear of `presence-audit` #13.

    Upstream indexes captured points by name with `setdefault`, so a capture
    holding two at one address has one of them silently discarded and the verdict
    depends on which order they were listed in. That is filed there with a
    prototype, and it is not this package's to fix.

    What IS this package's is never handing it such a capture. `Capture.points`
    yields one `FilingPoint` per filing with the per-unit readings inside it, so
    the addresses are unique by construction. Asserted over a real quarter that
    contains 39 filings reporting in two currencies -- the exact shape that would
    trip it.

    Deliberately an assertion about THIS code and not about upstream's. A test
    pinning the upstream behaviour would go red the day it is fixed, which is the
    wrong signal from the wrong subject.
    """
    names = [p.name for p in real_capture.points]
    assert len(names) == len(set(names))
    multi = [p for p in real_capture.points if len(p.readings) > 1]
    assert len(multi) == 39, "the corpus that makes this test worth having"
