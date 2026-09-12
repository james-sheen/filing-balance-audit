import json, os, pathlib, sys
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
#: Where to find the engine when it is not installed, for a development tree that
#: has a checkout beside it. NO DEFAULT PATH: the first version hardcoded one
#: author's directory layout, which is a leak of a private tree into a public
#: package and would have shipped. A developer who wants it sets the variable.
ENGINE_CLONE = pathlib.Path(os.environ["ARBITER_ENGINE"]) if os.environ.get(
    "ARBITER_ENGINE") else None


def _prefer_installed(module: str, fallback: pathlib.Path) -> bool:
    """Put `fallback` on the path ONLY where `module` cannot already be imported.

    This file used to insert both paths unconditionally. In a development tree
    that is right and convenient. In an environment where the package and the
    engine are already installed -- which is every environment
    `battery/probe_pin.py` builds -- it silently shadows them, so the suite
    exercises this working tree instead of the release under test.

    Not hypothetical: it invalidated two complete sweeps. One reported every
    release down to 0.1.0 passing, the other a floor at 0.1.8, and neither
    measured anything. What made it invisible is that
    `arbiter_engine.__version__` reads its own installed METADATA, so the
    shadowing code reported the number of the release it was standing in front
    of. Every version check anybody would write agreed with the intended release.

    Returns whether the fallback was needed, which is what
    `test_conftest_prefers_installed` asserts on.
    """
    try:
        __import__(module)
        return False
    except ImportError:
        if fallback.exists():
            sys.path.insert(0, str(fallback))
        return True


_prefer_installed("filing_balance_audit", ROOT / "src")
# The engine is an optional extra. Where it is neither installed nor beside this
# tree, the tests that need it ERROR on import rather than skipping: a skip is
# how a suite reports green about coverage it does not have, and the pin probe
# reads this suite as its oracle.
if ENGINE_CLONE is not None:
    _prefer_installed("arbiter_engine", ENGINE_CLONE)


@pytest.fixture(scope="session")
def evidence():
    return ROOT / "evidence"


@pytest.fixture(scope="session")
def real_period(evidence):
    from filing_balance_audit import declaration
    return declaration.load(json.loads((evidence / "2025q1-declaration.json").read_text()))


@pytest.fixture(scope="session")
def real_capture(evidence):
    from filing_balance_audit import capture
    return capture.load(json.loads((evidence / "2025q1-capture.json").read_text()))


@pytest.fixture(scope="session")
def real_run(real_period, real_capture):
    import logging
    from filing_balance_audit import feeder
    logging.disable(logging.CRITICAL)          # the engine warns on its own fire rate
    try:
        return feeder.run(real_period, real_capture)
    finally:
        logging.disable(logging.NOTSET)


def declaration_payload(**overrides):
    from filing_balance_audit import formats
    payload = {
        "format": formats.DECLARATION,
        "period": "testq",
        "tolerance_absolute": 0,
        "reviewed_by": "FIXTURE -- written for this test",
        "reviewed_on": "2026-09-12",
        "filings": [{"id": "F-1", "name": "Test Co", "form": "10-K",
                     "declared_type": "annual", "unit": "USD"}],
    }
    payload.update(overrides)
    return payload


def capture_payload(readings, unit="USD", filing_id="F-1"):
    from filing_balance_audit import formats
    return {"format": formats.CAPTURE, "period": "testq",
            "filings": [{"id": filing_id, "unit": unit, "readings": readings}]}
