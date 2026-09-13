"""Which number is wrong, and when that cannot be said.

Every case below is a real filing from 2025q1. The numbers are as filed.

THESE TESTS USED TO BE NAMED AFTER THE FILERS. Four of them carried a real
registrant's name in the function name, beside that registrant's exact reported
figures, in a test about their balance sheet not balancing. The evidence files
were anonymised and this was not, because nothing about it looks like an
identifier -- it is a function name. It named the company outright, which is a
stronger identification than anything the evidence ever carried.

So a case is described by its shape. The figures stay: they are the specification,
and they are as filed.
"""

from decimal import Decimal

from filing_balance_audit import feeder

ZERO = Decimal(0)
BOTH = [feeder.ASSETS_ARM, feeder.PARTS_ARM]
ASSETS_ONLY = [feeder.ASSETS_ARM]


def _filing(assets, total, parts=None):
    return feeder.Resolved(name="F", unit="USD", assets=Decimal(assets),
                           total=Decimal(total),
                           parts=None if parts is None else Decimal(parts))


def test_the_components_match_the_total_so_assets_is_odd():
    """A 10-K in the corpus: 93,840,769 against a total of 93,840,770."""
    item = _filing("93840769", "93840770", "93840770")
    assert feeder.localise(BOTH, item, ZERO) == "the assets figure is the odd one out"


def test_the_components_match_assets_so_the_total_is_odd():
    """A 10-Q: components sum to its assets; the total is one below.

    The same defect class as the case above, pointing the other way. A single arm
    detects both and can tell neither apart, which is why the agreement is
    declared on both sides.
    """
    item = _filing("39843", "39842", "39843")
    assert feeder.localise(ASSETS_ONLY, item, ZERO) == \
        "the balance-sheet total is the odd one out"


def test_all_three_differ_so_nothing_is_claimed():
    """35,126 / 35,128 / 35,129. There is no majority and naming one is a guess."""
    item = _filing("35126", "35128", "35129")
    assert "cannot be read off this filing" in feeder.localise(ASSETS_ONLY, item, ZERO)


def test_a_filing_that_tagged_no_components_claims_nothing():
    """A 10-Q: 500 out, and no second route exists for it."""
    item = _filing("218873", "218373")
    assert feeder.localise(ASSETS_ONLY, item, ZERO) == \
        ("no components were tagged, so which side is wrong cannot be read "
         "off this filing")


def test_a_filing_that_balances_is_said_to_balance():
    assert feeder.localise([], _filing("10", "10", "10"), ZERO) == "the identity holds"


def test_the_two_unlocalisable_answers_are_not_the_same_sentence():
    """A filing that tagged no components and one whose components disagree are
    different facts, and a reader deciding whether to go and look needs which."""
    assert (feeder.localise(ASSETS_ONLY, _filing("1", "2"), ZERO)
            != feeder.localise(ASSETS_ONLY, _filing("1", "2", "9"), ZERO))
