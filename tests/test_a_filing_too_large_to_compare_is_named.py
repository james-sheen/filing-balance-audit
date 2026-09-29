"""A filing whose figures are too large to compare exactly is named, not dropped.

At 2**53 and above the engine's float can no longer tell two whole units apart, so the
feeder sets such a filing aside rather than compare it -- and records why. The report
then printed every other bucket and not that one: a balanced filing beside a very large
one exited clean with `checked: 1`, and the large one appeared nowhere in the output.
"""
from __future__ import annotations

import json

from conftest import declaration_payload
from filing_balance_audit import cli, exit_contract, formats

LARGE = {"Assets": "9007199254740994", "LiabilitiesAndStockholdersEquity": "9007199254740995"}
BALANCED = {"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"}


def _files(tmp_path):
    declared = declaration_payload()
    declared["filings"].append({"id": "F-2", "name": "Large Co", "form": "10-K",
                                "declared_type": "annual", "unit": "USD"})
    captured = {"format": formats.CAPTURE, "period": "testq", "filings": [
        {"id": "F-1", "unit": "USD", "readings": BALANCED},
        {"id": "F-2", "unit": "USD", "readings": LARGE}]}
    paths = []
    for name, payload in (("d.json", declared), ("c.json", captured)):
        path = tmp_path / name
        path.write_text(json.dumps(payload))
        paths.append(str(path))
    return paths


def test_the_document_names_it_among_what_was_not_checked(tmp_path, capsys):
    declared, captured = _files(tmp_path)
    code = cli.main(["detect", declared, captured, "--json"])
    document = json.loads(capsys.readouterr().out)
    assert code == exit_contract.CLEAN and document["checked"] == 1
    [row] = document["not_checked"]["over_limit"]
    assert row.startswith("F-2: USD: ") and "exceeds the magnitude" in row


def test_the_text_report_counts_it(tmp_path, capsys):
    declared, captured = _files(tmp_path)
    cli.main(["detect", declared, captured])
    assert "1 too large to compare exactly" in capsys.readouterr().out


def test_an_ordinary_run_says_there_were_none(tmp_path, capsys):
    declared, captured = _files(tmp_path)
    doc = json.loads(open(captured).read())
    doc["filings"][1]["readings"] = BALANCED
    open(captured, "w").write(json.dumps(doc))
    cli.main(["detect", declared, captured, "--json"])
    assert json.loads(capsys.readouterr().out)["not_checked"]["over_limit"] == []
