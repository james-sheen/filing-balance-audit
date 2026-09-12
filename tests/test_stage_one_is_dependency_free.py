"""Stage 1 declares no dependency on the engine, and this is what says so.

`pyproject.toml` puts the engine in an optional extra and the README repeats it.
Both are prose. The claim is only true if reading a declaration, reading a
capture and pairing them all work on a machine where the engine cannot be
imported at all -- so that machine is built here rather than described.
"""

import builtins
import importlib
import pathlib
import sys

import pytest

from conftest import capture_payload, declaration_payload

STAGE_ONE = ["filing_balance_audit",
             "filing_balance_audit.formats",
             "filing_balance_audit.declaration",
             "filing_balance_audit.capture",
             "filing_balance_audit.feeder",
             "filing_balance_audit.exit_contract",
             "filing_balance_audit.cli"]


@pytest.fixture
def without_the_engine(monkeypatch):
    """Make `arbiter_engine` unimportable, and drop anything that already has it."""
    real_import = builtins.__import__

    def refuse(name, *args, **kwargs):
        if name == "arbiter_engine" or name.startswith("arbiter_engine."):
            raise ImportError("no module named 'arbiter_engine' (blocked by this test)")
        return real_import(name, *args, **kwargs)

    for name in [n for n in sys.modules if n.startswith(("arbiter_engine",
                                                         "filing_balance_audit"))]:
        monkeypatch.delitem(sys.modules, name, raising=False)
    monkeypatch.setattr(builtins, "__import__", refuse)
    yield


def test_the_engine_really_is_unreachable_in_this_fixture(without_the_engine):
    """The control. Without it, every assertion below passes on a machine that
    simply has the engine installed, and the fixture proves nothing."""
    with pytest.raises(ImportError):
        importlib.import_module("arbiter_engine")


def test_every_stage_one_module_imports_with_the_engine_unreachable(without_the_engine):
    for name in STAGE_ONE:
        importlib.import_module(name)


def test_a_declaration_and_a_capture_pair_with_the_engine_unreachable(without_the_engine):
    declaration = importlib.import_module("filing_balance_audit.declaration")
    capture = importlib.import_module("filing_balance_audit.capture")
    feeder = importlib.import_module("filing_balance_audit.feeder")
    fed = feeder.plan(
        declaration.load(declaration_payload()),
        capture.load(capture_payload({"Assets": "10",
                                      "LiabilitiesAndStockholdersEquity": "10"})))
    assert len(fed.resolved) == 1
    assert fed.disposition() == {"F-1": "checked"}


def test_the_verb_that_needs_the_engine_refuses_by_name_and_exits_two(
        without_the_engine, tmp_path, capsys):
    """Not a crash and not a clean exit. A run that could not reach the engine
    has produced no verdict, and it says which package to install."""
    import json
    cli = importlib.import_module("filing_balance_audit.cli")
    exit_contract = importlib.import_module("filing_balance_audit.exit_contract")
    declared = tmp_path / "d.json"
    declared.write_text(json.dumps(declaration_payload()))
    captured = tmp_path / "c.json"
    captured.write_text(json.dumps(capture_payload({"Assets": "1"})))
    code = cli.main(["detect", str(declared), str(captured)])
    assert code == exit_contract.COULD_NOT_COMPLETE
    printed = capsys.readouterr()
    assert "needs the engine" in printed.err
    assert "verdict=could-not-complete" in printed.out


def test_conftest_does_not_shadow_a_module_that_is_already_installed():
    """The guard that stopped the pin probe measuring this working tree.

    Asserted here rather than trusted, because the version number could not
    catch it: `arbiter_engine.__version__` reads installed METADATA, so a
    shadowing source clone reports whichever release is installed in front of
    it. Two complete sweeps were invalidated by this and both looked fine.

    The probe also checks the environment from a SEPARATE process, which never
    loads `conftest.py` at all -- so that check could not have seen this either.
    A guard has to run where the thing it guards runs.
    """
    import conftest
    before = list(sys.modules)
    assert _prefer_installed_is_a_noop_for("sys"), (
        "conftest inserted a fallback path for a module that imports fine, "
        "which is how an installed release gets shadowed by a working tree")
    assert list(sys.modules)[:len(before)] == before


def _prefer_installed_is_a_noop_for(module):
    import conftest
    marker = pathlib.Path("/nonexistent-fallback-that-must-not-be-used")
    inserted = conftest._prefer_installed(module, marker)
    return not inserted and str(marker) not in sys.path


def test_the_fallback_is_used_when_the_module_really_is_missing():
    """The control. Without it the assertion above passes on a guard that
    never inserts anything at all, which would be a different defect."""
    import conftest
    fallback = pathlib.Path(__file__).resolve().parent
    try:
        assert conftest._prefer_installed("a_module_nobody_has_installed", fallback)
        assert str(fallback) in sys.path
    finally:
        while str(fallback) in sys.path:
            sys.path.remove(str(fallback))
