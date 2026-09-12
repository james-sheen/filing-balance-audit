"""Pairing, the two taxonomies, the units, and the magnitude the engine imposes."""

from decimal import Decimal

import pytest

from conftest import capture_payload, declaration_payload
from filing_balance_audit import capture, declaration, feeder

ZERO = Decimal(0)


def _resolve(readings, unit="USD"):
    read = capture.load(capture_payload(readings, unit=unit))
    return feeder.resolve(read.readings[0])


def test_the_ifrs_total_is_read_as_the_same_line_as_the_us_gaap_one():
    """A reader knowing one name finds the identity on 17.4% of 40-F filings.

    They carry one, under IFRS, where the total is `EquityAndLiabilities`. With
    both names 40-F is 100.0%. The gap looked like a property of the form and was
    a property of the reader.
    """
    us = _resolve({"Assets": "10", "LiabilitiesAndStockholdersEquity": "10"})
    ifrs = _resolve({"Assets": "10", "EquityAndLiabilities": "10"})
    assert us.checkable and ifrs.checkable
    assert ifrs.total_tag == "EquityAndLiabilities"
    assert us.total_tag == "LiabilitiesAndStockholdersEquity"


def test_a_filing_with_no_total_under_either_taxonomy_is_not_checkable():
    assert not _resolve({"Assets": "10", "Liabilities": "4"}).checkable


def test_the_components_prefer_the_equity_that_includes_noncontrolling_interest():
    resolved = _resolve({
        "Assets": "10", "LiabilitiesAndStockholdersEquity": "10",
        "Liabilities": "4", "StockholdersEquity": "5",
        "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest": "6"})
    assert resolved.parts == Decimal("10")
    assert "IncludingPortion" in resolved.part_tags[1]


@pytest.mark.parametrize("parts,expected", [("10", "total"), ("11", "assets"), ("99", "neither")])
def test_components_are_a_second_route_only_when_they_reconcile(parts, expected):
    """The gate that took this package from 667 findings to 6.

    Components reconciling to neither side are not a second reading of this
    balance sheet -- temporary equity and noncontrolling interest are tagged
    outside both -- so they are declined rather than scored.
    """
    resolved = feeder.Resolved(name="F", unit="USD", assets=Decimal("11"),
                               total=Decimal("10"), parts=Decimal(parts))
    assert resolved.reconciles(ZERO) == expected


def test_components_that_were_never_tagged_reconcile_to_nothing_at_all():
    """`None` and `"neither"` are different answers and are kept apart."""
    assert feeder.Resolved(name="F", unit="USD", assets=Decimal(1),
                           total=Decimal(1)).reconciles(ZERO) is None


def test_a_filing_reporting_in_two_currencies_is_two_entities():
    payload = capture_payload({"Assets": "1", "LiabilitiesAndStockholdersEquity": "1"})
    payload["filings"].append({"id": "F-1", "unit": "CNY",
                               "readings": {"Assets": "7",
                                            "LiabilitiesAndStockholdersEquity": "7"}})
    fed = feeder.plan(declaration.load(declaration_payload()), capture.load(payload))
    assert {feeder.entity_id(r) for r in fed.resolved} == {"F-1::USD", "F-1::CNY"}


def test_a_total_in_one_currency_is_never_compared_with_assets_in_another():
    """The defect that produced a residual of 369 billion when first measured."""
    payload = capture_payload({"Assets": "100"})
    payload["filings"].append({"id": "F-1", "unit": "CNY",
                               "readings": {"LiabilitiesAndStockholdersEquity": "700"}})
    fed = feeder.plan(declaration.load(declaration_payload()), capture.load(payload))
    assert fed.resolved == []
    assert len(fed.incomplete) == 2


def test_a_magnitude_the_engine_cannot_compare_exactly_is_refused_not_fed():
    """Above 2**53 a one-unit difference can be erased or invented by the cast.

    The engine compares floats and this package's subject is money, so the
    boundary is refused rather than crossed: the failure it would produce is a
    discrepancy that is not there.
    """
    huge = str(int(feeder.EXACT_INTEGER_LIMIT) + 2)
    fed = feeder.plan(declaration.load(declaration_payload()),
                      capture.load(capture_payload(
                          {"Assets": huge, "LiabilitiesAndStockholdersEquity": huge})))
    assert fed.resolved == []
    assert fed.over_limit and "exceeds the magnitude" in fed.over_limit[0][1]


def test_a_balance_sheet_just_below_the_limit_is_still_fed():
    """The control. A guard that refused everything would pass the test above."""
    ok = str(int(feeder.EXACT_INTEGER_LIMIT) - 2)
    fed = feeder.plan(declaration.load(declaration_payload()),
                      capture.load(capture_payload(
                          {"Assets": ok, "LiabilitiesAndStockholdersEquity": ok})))
    assert len(fed.resolved) == 1 and fed.over_limit == []


def test_an_excluded_filing_is_counted_out_by_name_and_not_by_omission():
    payload = declaration_payload()
    payload["filings"][0]["excluded"] = True
    fed = feeder.plan(declaration.load(payload),
                      capture.load(capture_payload({"Assets": "1"})))
    assert fed.excluded == ["F-1"] and fed.resolved == []


def test_the_model_carries_the_declared_tolerance_and_not_a_default():
    for tolerance in (0, 1, 50.5):
        text = feeder.model_text(declaration.load(
            declaration_payload(tolerance_absolute=tolerance)))
        assert f"tolerance_absolute: {float(tolerance)}" in text
    # Both directions, which is what makes a disagreement localisable.
    assert text.count("agrees_with") == 2
