"""What this package's exit code means, and what it deliberately does not.

    0  every filing that could be checked, balanced
    1  at least one filing did not balance
    2  the run could not be completed

TWO IS NOT A WORSE ONE. A run that could not read its declaration, could not
import the engine, or was handed a capture in a format it does not read has
produced no verdict at all, and reporting that as *no findings* is the failure
this contract exists to prevent. A reader who sees 0 is entitled to believe
somebody checked.

A FILING THAT COULD NOT BE CHECKED DOES NOT MOVE THE CODE, AND IS NOT SILENT.
Of one real quarter, 148 filings of 6,231 report no total this package can read,
and 658 more tag components that reconcile to neither side. None of that is a
finding about a filing and all of it is printed. An audit that folded them into
exit 1 would be crying wolf; one that dropped them would be claiming a
denominator it does not have.
"""

from __future__ import annotations

from typing import Any

CLEAN = 0
FINDINGS = 1
COULD_NOT_COMPLETE = 2


def code_for(run: Any) -> int:
    """The exit code for a completed run. `2` is raised by callers, not decided here."""
    return FINDINGS if run.envelope.get("findings") else CLEAN


def verdict(code: int) -> str:
    return {CLEAN: "clean",
            FINDINGS: "findings",
            COULD_NOT_COMPLETE: "could-not-complete"}.get(code, "unknown")
