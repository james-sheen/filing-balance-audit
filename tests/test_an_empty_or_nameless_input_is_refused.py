"""A document that holds nothing, or names nothing, is refused wherever it enters.

Measured before this: a capture of no filings made `presence` raise out of the
shared core -- its `complete` is `bool(readings)`, so it arrived as a walk that had
not finished and recorded no failure -- and made `detect` print *every filing that
could be checked, balanced* over none, exit 0. A declaration naming no filing ran
both verbs the same way. A declared entry with no id was a KeyError, and an entry
that is not a mapping an AttributeError, in either document; each exits 1, which
this package's contract reads as a filing that did not balance.

Every refusal here is 2: a document that could not be read has produced no
verdict. `declare` keeps counting an empty declaration, because a count of zero,
said, is what that verb is for.
"""

from __future__ import annotations

import json

import pytest

from conftest import capture_payload, declaration_payload
from filing_balance_audit import capture, declaration, feeder
from filing_balance_audit.cli import main
from filing_balance_audit.declaration import ASSET_TAG, TOTAL_TAGS

#: A balance sheet that balances, and one that does not.
BALANCED = {ASSET_TAG: "100", TOTAL_TAGS[0]: "100"}
UNBALANCED = {ASSET_TAG: "100", TOTAL_TAGS[0]: "101"}


def _outcomes(printed: str) -> list[str]:
    return [line for line in printed.splitlines() if line.startswith("OUTCOME")]


def _needs_engine() -> None:
    """Failed by name without the engine, never skipped: this suite is the pin
    probe's oracle, and a skip is a green run about coverage that did not happen."""
    try:
        import arbiter_engine  # noqa: F401
    except ImportError as problem:          # noqa: PERF203 - the point of the check
        pytest.fail(f"this asserts what `detect` does and the engine is not "
                    f"importable: {problem}. Install the extra, or set "
                    f"ARBITER_ENGINE to a checkout")


@pytest.fixture()
def documents(tmp_path):
    declared = declaration_payload()
    captured = capture_payload(BALANCED)
    bodies = {
        "decl": declared,
        "decl_empty": declaration_payload(filings=[]),
        "decl_nameless": declaration_payload(filings=[
            {k: v for k, v in declared["filings"][0].items() if k != "id"}]),
        "decl_shapeless": declaration_payload(filings=["F-1"]),
        "cap": captured,
        "cap_unbalanced": capture_payload(UNBALANCED),
        "cap_empty": dict(captured, filings=[]),
        "cap_nameless": capture_payload(BALANCED, filing_id=""),
        "cap_shapeless": dict(captured, filings=["F-1"]),
        "cap_elsewhere": capture_payload(BALANCED, filing_id="F-9"),
    }
    paths = {}
    for name, body in bodies.items():
        path = tmp_path / f"{name}.json"
        path.write_text(json.dumps(body))
        paths[name] = str(path)
    return paths


class TestTheCaptureReader:

    def test_a_capture_of_nothing_is_refused(self):
        with pytest.raises(capture.CaptureError) as refused:
            capture.load(dict(capture_payload(BALANCED), filings=[]))
        assert "holds no filings" in str(refused.value)

    def test_an_entry_that_is_not_a_filing_is_refused_by_its_position(self):
        payload = capture_payload(BALANCED)
        payload["filings"].append("F-2")
        with pytest.raises(capture.CaptureError) as refused:
            capture.load(payload)
        assert "filings[1] is str, not a captured filing" in str(refused.value)

    def test_a_filing_with_no_id_says_where_it_is(self):
        with pytest.raises(capture.CaptureError) as refused:
            capture.load(capture_payload(BALANCED, filing_id=""))
        assert "filings[0]: a captured filing carries no id" in str(refused.value)

    def test_filings_that_are_not_a_list_are_refused_as_that(self):
        """Iterated, a mapping yields its keys, and the first would be refused as
        an entry that is not a filing -- true, and about the wrong thing."""
        with pytest.raises(capture.CaptureError) as refused:
            capture.load(dict(capture_payload(BALANCED), filings={"F-1": {}}))
        assert "`filings` is dict" in str(refused.value)


class TestTheDeclarationReader:

    def test_a_filing_with_no_id_is_refused_by_its_position(self):
        payload = declaration_payload()
        payload["filings"].append({"name": "Second Co", "declared_type": "annual"})
        with pytest.raises(declaration.DeclarationError) as refused:
            declaration.load(payload)
        assert "filings[1] has no id" in str(refused.value)

    def test_a_blank_id_is_no_id(self):
        payload = declaration_payload()
        payload["filings"][0]["id"] = "  "
        with pytest.raises(declaration.DeclarationError) as refused:
            declaration.load(payload)
        assert "filings[0] has no id" in str(refused.value)

    def test_an_entry_that_is_not_a_filing_is_refused_by_its_position(self):
        with pytest.raises(declaration.DeclarationError) as refused:
            declaration.load(declaration_payload(filings=["F-1"]))
        assert "filings[0] is str, not a declared filing" in str(refused.value)

    def test_an_empty_declaration_still_loads(self):
        """`declare` counts it, and the verbs that judge refuse it themselves."""
        assert declaration.load(declaration_payload(filings=[])).points == ()


class TestTheFeeder:

    def test_a_run_with_nothing_checkable_is_refused(self):
        """The API's answer, which is the CLI's: nothing resolved, so the engine
        was given no entity and this package scored the silence clean."""
        _needs_engine()
        period = declaration.load(declaration_payload())
        elsewhere = capture.load(capture_payload(BALANCED, filing_id="F-9"))
        with pytest.raises(feeder.FeedError) as refused:
            feeder.run(period, elsewhere)
        assert "no declared filing could be checked" in str(refused.value)
        assert "1 with no reading" in str(refused.value)

    def test_the_same_run_over_its_own_filing_checks_it(self):
        _needs_engine()
        ran = feeder.run(declaration.load(declaration_payload()),
                         capture.load(capture_payload(BALANCED)))
        assert len(ran.fed.resolved) == 1


REFUSED = {
    "presence, a capture of nothing": ["presence", "decl", "cap_empty"],
    "presence, nothing and nothing": ["presence", "decl_empty", "cap_empty"],
    "presence, a declaration of nothing": ["presence", "decl_empty", "cap"],
    "presence, a capture entry that is not a filing": ["presence", "decl", "cap_shapeless"],
    "presence, a declared filing with no id": ["presence", "decl_nameless", "cap"],
    "detect, a capture of nothing": ["detect", "decl", "cap_empty"],
    "detect, a declaration of nothing": ["detect", "decl_empty", "cap"],
    "detect, nothing declared is in the capture": ["detect", "decl", "cap_elsewhere"],
    "detect, a captured filing with no id": ["detect", "decl", "cap_nameless"],
    "detect, a declared filing with no id": ["detect", "decl_nameless", "cap"],
    "declare, a declared filing with no id": ["declare", "decl_nameless"],
    "declare, an entry that is not a filing": ["declare", "decl_shapeless"],
}


@pytest.mark.parametrize("argv", REFUSED.values(), ids=list(REFUSED))
def test_the_verb_refuses_and_never_reports_a_finding(argv, documents, capsys):
    if argv[0] == "detect":
        _needs_engine()
    assert main([argv[0], *(documents[name] for name in argv[1:])]) == 2
    captured = capsys.readouterr()
    assert _outcomes(captured.out) == ["OUTCOME exit=2 verdict=could-not-complete"]
    assert "needs the" not in captured.err, captured.err


@pytest.mark.parametrize("verb", ["presence", "detect"])
def test_a_declaration_of_nothing_is_refused_as_that(verb, documents, capsys):
    """Before the engine is asked: `detect` would also find nothing to check, and
    say so in counts -- this says why."""
    if verb == "detect":
        _needs_engine()
    assert main([verb, documents["decl_empty"], documents["cap"]]) == 2
    assert "names no filing" in capsys.readouterr().err


UNCHANGED = {
    "declare, a declaration of nothing (a count of zero, said)": (["declare", "decl_empty"], 0),
    "detect, a filing that balances": (["detect", "decl", "cap"], 0),
    "detect, a filing that does not": (["detect", "decl", "cap_unbalanced"], 1),
    "presence, the declared filing reporting": (["presence", "decl", "cap"], 0),
}


@pytest.mark.parametrize("argv,code", UNCHANGED.values(), ids=list(UNCHANGED))
def test_a_document_that_holds_something_answers_as_before(argv, code, documents):
    if argv[0] == "detect":
        _needs_engine()
    assert main([argv[0], *(documents[name] for name in argv[1:])]) == code
