"""The engine behaviours this package's design rests on, asserted per release.

WHY THESE ARE IN THE SUITE AND NOT ONLY IN THE BATTERY. `battery/probe_pin.py`
installs each release the pin claims and runs THIS SUITE against it, so the suite
is the pin probe's oracle. Behaviours asserted only in the battery are invisible
to it: the battery runs once, against whichever engine happens to be installed.

The first sweep found every release down to 0.1.0 passing, which looked like a
floor eleven releases too high. It was also a suite that never asked the engine
the questions this package depends on. A range is only exercised as far as the
oracle reaches.

**NOT `pytest.importorskip`, AND NOT A MODULE-LEVEL IMPORT EITHER.** A skip would
turn a machine without the engine into a green run reporting coverage it does not
have, and the pin probe -- which reads this suite as its oracle -- would then pass
every release because none of these ever ran.

A module-level import was the first answer and it was worse in a way that took
removing a hardcoded path to notice: pytest reports `Interrupted: 1 error during
collection` and runs NOTHING. So on a machine with no engine the tests proving
Stage 1 needs no engine could not run -- the exact machine they are about.

The import is therefore inside the tests. Without the engine each one FAILS, by
name, with a non-zero exit, while the rest of the suite runs.
"""

import pytest

from filing_balance_audit import feeder


def _engine():
    try:
        from arbiter_engine.api import EngineSession, check
    except ImportError as problem:          # noqa: PERF203 - the point of the test
        pytest.fail(f"this file asserts engine behaviour and the engine is not "
                    f"importable: {problem}. Install the extra, or set "
                    f"ARBITER_ENGINE to a checkout. Not skipped: a skip here is a "
                    f"green run about coverage that did not happen")
    return EngineSession, check


class _Period:
    tolerance_absolute = 0.0


def _run(model, properties):
    EngineSession, check = _engine()
    session = EngineSession()
    session.load_model(model)
    session.add_entity("F", "Filing", properties=properties)
    envelope = check(session).to_dict()
    return ([f["problem_type"] for f in envelope.get("findings", [])],
            [str(d.get("reason")) for d in envelope.get("not_checked", [])])


MODEL = feeder.model_text(_Period())

#: A 10-K in 2025q1, as filed: one dollar on ninety-four million. The figures are
#: real; the filer is not named in the committed evidence, whose labels are keyed
#: on an unpublished salt. `fetch_sec_quarter.py --named` recovers the real
#: identifiers from the source for anyone who wants them.
ONE_DOLLAR_OUT = {"assets": 93840769, "balance_sheet_total": 93840770,
             "parts_sum": 93840770}


def test_a_zero_absolute_tolerance_catches_a_one_unit_difference():
    """The whole package. A relative tolerance of even 0.001% would miss this."""
    fired, _ = _run(MODEL, ONE_DOLLAR_OUT)
    assert feeder.ASSETS_ARM in fired


def test_both_declared_directions_fire_so_a_finding_can_be_localised():
    """Two peers on ONE indicator collapse to one finding; two indicators do not.

    Measured on the engine: `redundant_disagreement:<indicator>` is the name, so
    the second peer's disagreement has nowhere to go. This asserts the workaround
    still works, on whatever release is installed.
    """
    fired, _ = _run(MODEL, ONE_DOLLAR_OUT)
    assert feeder.PARTS_ARM in fired
    assert len(set(fired)) == 2


def test_a_balance_sheet_that_balances_reports_nothing():
    fired, _ = _run(MODEL, {"assets": 1000, "balance_sheet_total": 1000,
                            "parts_sum": 1000})
    assert fired == []


def test_a_filing_with_no_total_is_declined_and_not_answered():
    """Not a finding and not a pass. 154 real filings land here in one quarter."""
    fired, declined = _run(MODEL, {"assets": 1000})
    assert fired == []
    assert any("missing_property" in d for d in declined)


def test_an_agreement_block_with_no_tolerance_declines_rather_than_guessing():
    """The behaviour that would fail SILENTLY and take the package with it.

    An engine that fell back to a relative tolerance would answer *they agree*
    for every discrepancy in this corpus -- one dollar against ninety-four
    million is six decimal places inside any relative margin anybody would pick.
    Nothing else in this suite can tell that engine from a correct one.
    """
    without = MODEL.replace("          tolerance_absolute: 0.0\n", "")
    assert without != MODEL, "the tolerance was not removed, so this asserts nothing"
    fired, declined = _run(without, {"assets": 100, "balance_sheet_total": 106})
    assert fired == []
    assert any("missing_config" in d.lower() for d in declined)
