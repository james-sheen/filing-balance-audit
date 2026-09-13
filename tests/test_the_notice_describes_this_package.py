"""`NOTICE` is the file a reader opens to find out what is true about provenance.

It was wrong. This package's `NOTICE` was copied from the consulting vertical and
only its first line was changed, so it went on describing *deliverables a
statement of work says should exist* and asserting that **nothing named anywhere
here is real**. The evidence in this repository reports real discrepancies in
real published balance sheets, and named real registrants when that was written.
The legal notice said the opposite of the truth about the one thing it exists to
be believed on.

No test could have caught it, because nothing imports `NOTICE`. These assertions
are the cheapest thing that can.
"""

import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
NOTICE = (ROOT / "NOTICE").read_text()
README = (ROOT / "README.md").read_text()

#: Line breaks are not meaning. Matching a phrase against wrapped prose fails on
#: where the author happened to wrap it -- `licensed auditors` is split across two
#: lines in `NOTICE` and the first version of this file reported it absent. Every
#: phrase assertion below goes through here.
FLAT = " ".join(NOTICE.split()).lower()


def test_the_notice_names_this_distribution():
    assert NOTICE.splitlines()[0].strip() == "filing-balance-audit"


def test_the_notice_does_not_describe_a_sibling_vertical():
    """The words that were in it, and whose presence meant it was somebody else's.

    Matched as a SET rather than one sentence: the failure was a wholesale copy,
    so any of the sibling's subject nouns surviving is the same defect.
    """
    # Unambiguous markers only. `engagement` and `deliverable` are NOT here: the
    # first version listed them and failed on *a regulated engagement performed
    # by licensed auditors*, which is this package's own sentence. A forbidden
    # word that can occur innocently makes the check fire against the right file
    # for the wrong reason.
    somebody_elses = ("statement of work", "consultant", "opc ua",
                      "entity-manager", "redfish")
    assert [word for word in somebody_elses if word in FLAT] == []
    # And the subject line, which is where the copy actually showed.
    subject = next(line for line in NOTICE.splitlines()
                   if line.startswith("This project"))
    assert "balance" in subject


def test_the_notice_denies_affiliation_with_the_regulator():
    assert "not affiliated" in FLAT
    assert "securities and exchange commission" in FLAT


def test_the_notice_separates_this_from_a_regulated_audit():
    """The name carries the word `audit`, which means something specific here."""
    assert "financial statement audit" in FLAT
    assert "licensed auditors" in FLAT


def test_the_readme_carries_the_same_denial_and_points_at_the_notice():
    """Above the fold, because the name makes its impression before any prose."""
    head = README[:README.index("```")]
    assert "Not affiliated with the SEC" in head
    assert "NOTICE" in head


def test_the_notice_matches_what_the_evidence_actually_is():
    """A cross-check between two artefacts, not a grep for a sentence.

    IT HAS ALREADY CAUGHT ONE. The notice said *the companies named in that
    evidence are real*, which was true when written. The evidence was then
    re-derived without names and the sentence became false -- and this test went
    red on the same commit, which is the entire reason it exists.

    So it reads the evidence, decides what the evidence IS, and holds the notice
    to that rather than to a remembered state. It has now been re-pointed a
    second time, for the same reason in the other direction: the labels were
    positional, the notice correctly called that pseudonymity and NOT anonymity,
    and the labels are now a keyed hash under an unpublished salt. The old
    assertions would hold a truthful notice to a retired description.
    """
    declaration = json.loads(
        (ROOT / "evidence" / "2025q1-declaration.json").read_text())
    assert declaration["identifiers"] == "hashed"
    scheme = declaration["identifier_scheme"]
    assert scheme["salt"].startswith("NOT PUBLISHED")
    assert all(re.fullmatch(r"F-[0-9a-f]{12}", f["id"])
               for f in declaration["filings"])
    assert not re.search(r'"cik": "\d+"', json.dumps(declaration))

    assert "salt" in FLAT
    assert "not published" in FLAT
    # The residual channel, disclosed. Closing the label channel does not close
    # this one and the notice has to say so -- an artefact claiming more privacy
    # than it has is the failure this whole change exists to avoid.
    assert "join key" in FLAT
    # and it must not claim the figures are invented, which they are not
    for denial in ("every example is synthetic", "nothing here is real"):
        assert denial not in FLAT, denial
    assert "as filed" in FLAT


def test_the_notice_does_not_still_describe_the_retired_scheme():
    """The sentences most at risk are the ones that were ABOUT the old scheme.

    `positional` and `pseudonym` were load-bearing words here while the labels
    were assigned by sorted position. They are now false of the evidence, and
    false in the most convincing way: they read as careful disclosure. Allowed
    only where the notice is explicitly narrating what changed.
    """
    # BY SENTENCE, not by line. The first version of this walked `splitlines()`
    # and failed on a sentence whose past-tense marker had wrapped onto the line
    # above -- the same defect `FLAT` exists for, reintroduced two screens below
    # the comment that names it.
    for sentence in re.split(r"(?<=[.!?])\s+", " ".join(NOTICE.split())):
        low = sentence.lower()
        if "pseudonym" in low or "positional" in low:
            assert any(marker in low for marker in
                       ("was", "were", "used to", "briefly", "then")), sentence
