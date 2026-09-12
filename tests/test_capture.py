"""The capture keeps what it cannot read, and refuses what it cannot pair."""

import pytest

from conftest import capture_payload
from filing_balance_audit import capture


def test_a_value_that_will_not_parse_is_recorded_not_dropped():
    """Twenty-five of these are in one real quarter.

    A reader that skipped them would report the filing as carrying no total.
    What it carries is a total nobody can read, and only one of those two facts
    is about the filer.
    """
    read = capture.load(capture_payload({"Assets": "100", "Liabilities": "n/a"}))
    assert dict(read.readings[0].values) == {"Assets": capture.Decimal("100")}
    assert read.readings[0].unreadable == (("Liabilities", "n/a"),)


def test_a_reading_with_no_unit_is_refused():
    payload = capture_payload({"Assets": "1"})
    del payload["filings"][0]["unit"]
    with pytest.raises(capture.CaptureError) as refused:
        capture.load(payload)
    assert "comparing across units" in str(refused.value)


def test_a_reading_with_no_id_is_refused():
    payload = capture_payload({"Assets": "1"})
    del payload["filings"][0]["id"]
    with pytest.raises(capture.CaptureError):
        capture.load(payload)


def test_money_survives_as_decimal_and_not_as_binary_floating_point():
    """A one-unit discrepancy is the subject here, so the reader cannot round.

    `0.1 + 0.2` is the canonical demonstration; a balance sheet in cents is the
    same failure with a filing attached.
    """
    read = capture.load(capture_payload({"Assets": "0.1", "Liabilities": "0.2"}))
    total = read.readings[0].values["Assets"] + read.readings[0].values["Liabilities"]
    assert str(total) == "0.3"
    assert float(0.1) + float(0.2) != 0.3


def test_one_filing_in_two_currencies_is_two_readings():
    payload = capture_payload({"Assets": "1"})
    payload["filings"].append({"id": "F-1", "unit": "CNY", "readings": {"Assets": "7"}})
    read = capture.load(payload)
    assert len(read.by_name["F-1"]) == 2
    assert {r.unit for r in read.by_name["F-1"]} == {"USD", "CNY"}
