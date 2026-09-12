"""The named artifacts this package reads and writes.

Every format carries its major version in its own name, and a reader refuses an
unknown major BY NAME rather than guessing. A reader that accepts an unknown
major and then finds a key missing reports a defect in the data; a reader that
refuses reports a defect in the pairing, which is the true one.
"""

from __future__ import annotations

from typing import Any, Mapping

DECLARATION = "filing-balance-audit/declaration/1"
CAPTURE = "filing-balance-audit/capture/1"
PRESENCE = "filing-balance-audit/presence/1"
DETECT = "filing-balance-audit/detect/1"

#: Every declared type a filing may carry, naming the family of form it is.
#:
#: NOTHING IS COUNTED OUT BY TYPE HERE, AND THAT IS A MEASURED DECISION.
#: The sibling verticals count some declared types out of the audit -- a ceremony
#: is not a deliverable -- and the obvious move was to do the same with forms
#: that do not carry a balance sheet. Measured over 2025q1, there is no such
#: form. Every family has filings that report one: 10-K at 97.7%, 10-Q at 96.7%,
#: S-1 at 96.6%, and 40-F at 100.0% once the second taxonomy is read. So
#: `is_expected_live` is true for all four, and the type is descriptive rather
#: than a filter. A filing that reports no total is `declared_absent`, which is
#: the honest answer, and not *counted out*, which would have been a reader's
#: opinion wearing a vocabulary's clothes.
DECLARED_TYPES = ("annual", "interim", "registration", "other")


class FormatError(ValueError):
    """A document whose format this package will not read, said with both names."""


def require(payload: Mapping[str, Any], expected: str) -> Mapping[str, Any]:
    """Return `payload` if it declares `expected`, else refuse naming both.

    The comparison is on the whole string including the major. A reader that
    compared only the prefix would accept a future major silently, which is the
    one outcome a versioned format exists to prevent.
    """
    if not isinstance(payload, Mapping):
        raise FormatError(
            f"expected a mapping declaring {expected}, got {type(payload).__name__}")
    got = payload.get("format")
    if got is None:
        raise FormatError(
            f"this document declares no format; {expected} was expected. A "
            f"document with no format is not an earlier version of one, it is "
            f"something nobody versioned")
    if got != expected:
        raise FormatError(f"this reader reads {expected} and the document "
                          f"declares {got}")
    return payload
