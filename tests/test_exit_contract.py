"""The exit code is the contract, and 2 is not a worse 1."""

import json
import subprocess
import sys
import pathlib

import pytest

from conftest import declaration_payload, capture_payload
from filing_balance_audit import cli, exit_contract

ROOT = pathlib.Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "evidence"


def _write(tmp_path, name, payload):
    path = tmp_path / name
    path.write_text(json.dumps(payload))
    return path


def test_a_document_that_cannot_be_read_exits_two_and_says_so(tmp_path, capsys):
    code = cli.main(["detect", str(tmp_path / "absent.json"), str(tmp_path / "also.json")])
    assert code == exit_contract.COULD_NOT_COMPLETE
    assert "verdict=could-not-complete" in capsys.readouterr().out


def test_an_unsigned_declaration_is_refused_rather_than_reported_clean(tmp_path, capsys):
    declared = _write(tmp_path, "d.json", declaration_payload(reviewed_by=None))
    captured = _write(tmp_path, "c.json", capture_payload({"Assets": "1"}))
    assert cli.main(["detect", str(declared), str(captured)]) == \
        exit_contract.COULD_NOT_COMPLETE
    assert "verdict=could-not-complete" in capsys.readouterr().out


def test_a_declaration_with_no_tolerance_exits_two_not_clean(tmp_path, capsys):
    payload = declaration_payload()
    del payload["tolerance_absolute"]
    declared = _write(tmp_path, "d.json", payload)
    assert cli.main(["declare", str(declared)]) == exit_contract.COULD_NOT_COMPLETE
    assert "verdict=could-not-complete" in capsys.readouterr().out


def test_a_balanced_filing_exits_clean(tmp_path, capsys):
    declared = _write(tmp_path, "d.json", declaration_payload())
    captured = _write(tmp_path, "c.json", capture_payload(
        {"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"}))
    assert cli.main(["detect", str(declared), str(captured)]) == exit_contract.CLEAN
    assert "verdict=clean" in capsys.readouterr().out


def test_an_unbalanced_filing_exits_one(tmp_path, capsys):
    declared = _write(tmp_path, "d.json", declaration_payload())
    captured = _write(tmp_path, "c.json", capture_payload(
        {"Assets": "10", "LiabilitiesAndStockholdersEquity": "11"}))
    assert cli.main(["detect", str(declared), str(captured)]) == exit_contract.FINDINGS
    assert "verdict=findings" in capsys.readouterr().out


def test_the_real_quarter_through_the_command_line_is_a_document(capsys):
    """`--json` stdout is parsed WHOLE, not searched.

    A test that greps stdout passes on a document with a traceback printed above
    it, which is exactly the shape a broken run takes.
    """
    code = cli.main(["detect", str(EVIDENCE / "2025q1-declaration.json"),
                     str(EVIDENCE / "2025q1-capture.json"), "--json"])
    document = json.loads(capsys.readouterr().out)
    assert code == exit_contract.FINDINGS
    assert document["outcome"] == {"exit": 1, "verdict": "findings"}
    assert len(document["findings"]) == 6
    assert document["checked"] == 6083
    assert len(document["not_checked"]["parts_reconcile_to_neither_side"]) == 658
