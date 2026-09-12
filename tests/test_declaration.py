"""The declaration refuses what cannot be repaired downstream."""

import pytest

from conftest import declaration_payload
from filing_balance_audit import declaration, formats


def test_a_declaration_with_no_tolerance_is_refused_not_defaulted():
    payload = declaration_payload()
    del payload["tolerance_absolute"]
    with pytest.raises(declaration.DeclarationError) as refused:
        declaration.load(payload)
    # The reason matters as much as the refusal: a reader who is told only
    # *invalid* will add a default, which is the outcome this prevents.
    assert "no default" in str(refused.value)


def test_zero_is_a_legitimate_tolerance_and_is_not_read_as_absent():
    """The falsy-zero trap, and the whole package turns on it.

    For money the answer is almost always exactly zero, so a guard written as
    `if not payload.get("tolerance_absolute")` would refuse every correct
    declaration this package expects to see.
    """
    assert declaration.load(declaration_payload(tolerance_absolute=0)).tolerance_absolute == 0.0


def test_a_boolean_is_not_a_number_of_reporting_units():
    """`True` is an `int` in Python and would otherwise pass as a tolerance of 1."""
    with pytest.raises(declaration.DeclarationError):
        declaration.load(declaration_payload(tolerance_absolute=True))


@pytest.mark.parametrize("bad", ["0", -1, None, [0]])
def test_a_tolerance_that_is_not_a_distance_is_refused(bad):
    with pytest.raises(declaration.DeclarationError):
        declaration.load(declaration_payload(tolerance_absolute=bad))


def test_an_unrecognised_declared_type_is_refused_rather_than_counted_out():
    payload = declaration_payload()
    payload["filings"][0]["declared_type"] = "prospectus"
    with pytest.raises(declaration.DeclarationError) as refused:
        declaration.load(payload)
    assert "denominator" in str(refused.value)


def test_every_declared_type_the_format_names_is_accepted():
    """The enumeration and the reader cannot drift apart.

    Asserted over `formats.DECLARED_TYPES` rather than a list written here: a
    copy of the vocabulary in the test is a second record of one fact, and two
    records of one fact drift.
    """
    for kind in formats.DECLARED_TYPES:
        payload = declaration_payload()
        payload["filings"][0]["declared_type"] = kind
        assert declaration.load(payload).points[0].type == kind


def test_a_disclosure_marker_is_upper_case_as_written():
    """A firm actually named `Derived Analytics LLP` files a real signature.

    A case-insensitive comparison reports it as a disclosure, which prints a
    real signature as unsigned -- the inversion nobody would think to check.
    """
    for written, expected in [
            ("FIXTURE -- written for this test", "FIXTURE"),
            ("DERIVED FROM A PUBLIC DATASET -- not signed", "DERIVED"),
            ("NOT SIGNED yet", "NOT SIGNED"),
            ("Derived Analytics LLP", None),
            ("Fixture Consulting Ltd", None),
            ("Jane Smith", None)]:
        period = declaration.load(declaration_payload(reviewed_by=written))
        assert period.disclosure == expected, written


def test_a_declaration_with_no_signature_is_not_reviewed():
    assert not declaration.load(declaration_payload(reviewed_by=None)).reviewed
    assert not declaration.load(declaration_payload(reviewed_on=None)).reviewed


def test_a_document_of_another_format_is_refused_by_both_names():
    with pytest.raises(formats.FormatError) as refused:
        declaration.load(declaration_payload(format="filing-balance-audit/capture/1"))
    assert "declaration/1" in str(refused.value)
    assert "capture/1" in str(refused.value)
