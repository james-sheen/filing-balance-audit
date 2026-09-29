"""A filing's reading is the number the core's protocol promises, and nothing is lost.

`FilingPoint.reading` returned the assets figure as text, where the shared core's
protocol says `Optional[float]`, and the core prints a live point's reading as a number.
So a declared filing marked excluded that was still reporting crashed `presence` with a
traceback -- exit 1, which this family reads as findings. The reading is a float now;
the exact figure a restatement is compared on stays text, because two totals past 2**53
that differ by one are the same float.
"""
from __future__ import annotations

import json

from conftest import declaration_payload
from filing_balance_audit import capture, cli, exit_contract, formats
from filing_balance_audit.vertical import FilingVocabulary


def _capture(assets, total):
    return capture.load({"format": formats.CAPTURE, "period": "testq", "filings": [
        {"id": "F-1", "unit": "USD",
         "readings": {"Assets": assets, "LiabilitiesAndStockholdersEquity": total}}]})


def test_the_reading_is_a_float_and_the_filed_figure_keeps_every_digit():
    [point] = _capture("9007199254740995", "9007199254740995").points
    assert isinstance(point.reading, float)
    assert point.assets_as_filed == "9007199254740995"


def test_an_excluded_filing_that_reports_is_a_finding_not_a_crash(tmp_path, capsys):
    declared = declaration_payload()
    declared["filings"].append({"id": "F-6", "name": "Left Co", "form": "10-K",
                                "declared_type": "annual", "unit": "USD",
                                "excluded": True})
    captured = {"format": formats.CAPTURE, "period": "testq", "filings": [
        {"id": "F-1", "unit": "USD",
         "readings": {"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"}},
        {"id": "F-6", "unit": "USD",
         "readings": {"Assets": "5", "LiabilitiesAndStockholdersEquity": "5"}}]}
    paths = []
    for name, payload in (("d.json", declared), ("c.json", captured)):
        (tmp_path / name).write_text(json.dumps(payload))
        paths.append(str(tmp_path / name))
    code = cli.main(["presence", *paths, "--json"])
    report = json.loads(capsys.readouterr().out)
    assert code == exit_contract.FINDINGS
    assert "disabled_in_config_but_live" in {f["kind"] for f in report["findings"]}


def test_a_restatement_below_float_precision_is_still_seen():
    # 2**53 + 1 and 2**53 are one float: a restatement of one unit is invisible to it.
    [old] = _capture("9007199254740993", "9007199254740993").points
    [new] = _capture("9007199254740992", "9007199254740992").points
    assert old.reading == new.reading
    changes = FilingVocabulary().point_changes(old, new, comparable=True)
    assert "restated total assets: 9007199254740993 -> 9007199254740992" in changes
