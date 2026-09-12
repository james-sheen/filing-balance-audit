"""`NOTICE` is the file a reader opens to find out what is true about provenance.

It was wrong. This package's `NOTICE` was copied from the consulting vertical and
only its first line was changed, so it went on describing *deliverables a
statement of work says should exist* and asserting that **nothing named anywhere
here is real**. The evidence in this repository names real registrants and reports
real discrepancies in real published balance sheets. The legal notice said the
opposite of the truth about the one thing it exists to be believed on.

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
    re-derived pseudonymously and the sentence became false -- and this test went
    red on the same commit, which is the entire reason it exists.

    So it reads the evidence, decides what the evidence IS, and holds the notice
    to that rather than to a remembered state.
    """
    declaration = json.loads(
        (ROOT / "evidence" / "2025q1-declaration.json").read_text())
    pseudonymous = declaration["identifiers"] == "pseudonymous"
    assert pseudonymous, "the committed evidence should ship pseudonymous"
    assert all(f["id"].startswith("F-") for f in declaration["filings"])
    assert not re.search(r'"cik": "\d+"', json.dumps(declaration))

    assert "pseudonym" in FLAT
    assert "not anonymity" in FLAT
    # and it must not claim the figures are invented, which they are not
    for denial in ("every example is synthetic", "nothing here is real"):
        assert denial not in FLAT, denial
    assert "as filed" in FLAT
