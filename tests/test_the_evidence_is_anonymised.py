"""What can be recovered from the committed evidence, and what cannot.

The evidence carries real figures from real balance sheets. The filers are not
named, and this file is the check on that -- not on the prose describing it,
which lives in `test_the_notice_describes_this_package.py`, but on the bytes.

THE SCHEME THIS REPLACED FAILED HONESTLY. Labels used to be assigned by sorted
position, which the notice correctly called pseudonymity and not anonymity: sort
the public quarter and read the mapping off it. The labels are now
`HMAC-SHA256(salt, domain + identifier)` under a salt that is not committed.

AND THE ORDERING CHANNEL IS THE ONE WORTH A TEST. Hashing the labels while still
emitting rows in order of the real accession number would have changed how the
identifiers look and nothing about what is recoverable: row 1 is still the first
filing in sorted order. `test_rows_are_ordered_by_label` is the guard on that,
and it is the assertion here most likely to be undone by accident.
"""

import json
import pathlib
import re
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "battery"))
import fetch_sec_quarter as fetch                                   # noqa: E402

LABEL = re.compile(r"(F|R)-[0-9a-f]{12}")
DECLARATION = json.loads((ROOT / "evidence" / "2025q1-declaration.json").read_text())
CAPTURE = json.loads((ROOT / "evidence" / "2025q1-capture.json").read_text())


def test_the_declaration_says_what_was_done_to_the_identifiers():
    assert DECLARATION["identifiers"] == "hashed"
    scheme = DECLARATION["identifier_scheme"]
    assert "HMAC-SHA256" in scheme["construction"]
    assert scheme["salt"] == "NOT PUBLISHED -- held by whoever derived this file"
    assert re.fullmatch(r"[0-9a-f]{16}", scheme["salt_fingerprint"])


def test_every_label_is_a_digest_and_not_a_position():
    """A positional label passes a *looks like a label* test and fails this one."""
    for filing in DECLARATION["filings"]:
        assert LABEL.fullmatch(filing["id"]), filing["id"]
        assert LABEL.fullmatch(filing["cik"]), filing["cik"]
        assert filing["name"] == f"Registrant {filing['cik']}"
    for row in CAPTURE["filings"]:
        assert LABEL.fullmatch(row["id"]), row["id"]


def test_no_real_identifier_survives_in_either_file():
    """An accession number is digits and dashes; a CIK is digits."""
    for payload in (DECLARATION, CAPTURE):
        flat = json.dumps(payload)
        assert not re.search(r'"(id|cik)": "\d[\d-]*"', flat)


def test_rows_are_ordered_by_label():
    """Position must carry nothing the label does not already carry.

    This is the assertion that distinguishes anonymising the evidence from
    renaming it. Sorting by the real accession number and then relabelling leaves
    row order equal to sorted-identifier order, which IS the retired positional
    mapping -- published in the one channel nobody looks at.
    """
    ids = [f["id"] for f in DECLARATION["filings"]]
    assert ids == sorted(ids)
    rows = [(f["id"], f["unit"]) for f in CAPTURE["filings"]]
    assert rows == sorted(rows)


def test_the_labels_do_not_cluster_the_way_a_counter_would():
    """A sequence has dense low-order structure; a digest does not.

    Cheap and independent of the regex above: positional labels zero-pad, so
    their first hex characters are almost all `0`. A hash spreads over all 16.
    """
    first = {f["id"][2] for f in DECLARATION["filings"]}
    assert len(first) == 16


def test_a_different_salt_gives_different_labels_for_the_same_filing():
    """The salt is doing the work, not the construction around it."""
    one, _ = fetch.labels(["0001-25-000001"], ["1750"], b"x" * 32)
    two, _ = fetch.labels(["0001-25-000001"], ["1750"], b"y" * 32)
    assert one != two
    again, _ = fetch.labels(["0001-25-000001"], ["1750"], b"x" * 32)
    assert one == again, "the same salt has to reproduce the same evidence"


def test_the_two_namespaces_are_separated():
    """One string in both populations must not take one label.

    Without domain separation a CIK equal to an accession number collapses the
    two, and the declaration is the file that relates them.
    """
    filings, registrants = fetch.labels(["1750"], ["1750"], b"z" * 32)
    assert filings["1750"][2:] != registrants["1750"][2:]


def test_a_salt_shorter_than_the_floor_is_refused(tmp_path):
    """No salt, and a token salt, are the same failure and both are loud."""
    short = tmp_path / "s"
    short.write_bytes(b"tooshort")
    with pytest.raises(ValueError, match="floor"):
        fetch.read_salt(short, create=False)
    with pytest.raises(ValueError, match="no default"):
        fetch.read_salt(None, create=False)


def test_a_salt_in_use_is_never_overwritten(tmp_path):
    """Overwriting it makes every evidence file derived under it unreproducible."""
    salt = tmp_path / "s"
    fetch.read_salt(salt, create=True)
    with pytest.raises(ValueError, match="refusing to overwrite"):
        fetch.read_salt(salt, create=True)


def test_the_salt_is_not_committed_anywhere_in_the_tree():
    """The one file that would undo all of this if it shipped."""
    tracked = [p for p in ROOT.rglob("*")
               if p.is_file() and ".git" not in p.parts and "salt" in p.name.lower()]
    assert tracked == []
