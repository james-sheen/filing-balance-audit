"""The command line. Two verbs, and the exit code is the contract.

    filing-balance-audit declare   <declaration.json>
    filing-balance-audit presence  <declaration.json> <capture.json> [--json]
    filing-balance-audit detect    <declaration.json> <capture.json> [--json]
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
from decimal import Decimal
from typing import Any, Sequence

from . import capture as capture_mod
from . import declaration as declaration_mod
from . import exit_contract, feeder, formats
from .vertical import FilingVocabulary


class Unreadable(Exception):
    """A document this run could not open or parse.

    Its own type, and not `SystemExit`. The first version raised `SystemExit`
    here while every other refusal in this module RETURNED an exit code, so
    `main()` exited the process on one path and returned on the others -- and a
    caller embedding this, including the suite, saw two different contracts from
    one function. Caught by the test that calls `main` for a missing file.
    """


def _read(path: pathlib.Path) -> Any:
    """Read a document, or raise. Every failure here is *this run produced no
    verdict*, never *nothing was found*."""
    try:
        return json.loads(path.read_text())
    except FileNotFoundError:
        raise Unreadable(f"no such document: {path}") from None
    except OSError as problem:
        raise Unreadable(f"{path} could not be opened: {problem}") from None
    except json.JSONDecodeError as problem:
        raise Unreadable(f"{path} is not readable JSON: {problem}") from None


def _refuse(message: str) -> int:
    print(f"{message}", file=sys.stderr)
    print(f"OUTCOME exit={exit_contract.COULD_NOT_COMPLETE} "
          f"verdict={exit_contract.verdict(exit_contract.COULD_NOT_COMPLETE)}")
    return exit_contract.COULD_NOT_COMPLETE


def cmd_declare(args: argparse.Namespace) -> int:
    try:
        period = declaration_mod.load(_read(args.declaration))
    except (Unreadable, formats.FormatError,
            declaration_mod.DeclarationError) as problem:
        return _refuse(str(problem))
    if not period.reviewed:
        return _refuse("this declaration is not signed. A period nobody reviewed "
                       "is not a statement of what should balance, it is a list")
    disclosure = period.disclosure
    signed = (f"disclosed as {disclosure}" if disclosure
              else f"reviewed by {period.reviewed_by}")
    kinds: dict[str, int] = {}
    for point in period.points:
        kinds[point.type or "?"] = kinds.get(point.type or "?", 0) + 1
    print(f"period {period.period}: {len(period.points):,} filing(s), {signed} "
          f"on {period.reviewed_on}")
    print(f"  tolerance: {period.tolerance_absolute:g} reporting unit(s) "
          f"-- declared, not defaulted")
    for kind in formats.DECLARED_TYPES:
        print(f"  {kind:<13} {kinds.get(kind, 0):>6,}")
    print("  none of these types is counted out; see formats.DECLARED_TYPES")
    print(f"OUTCOME exit={exit_contract.CLEAN} "
          f"verdict={exit_contract.verdict(exit_contract.CLEAN)}")
    return exit_contract.CLEAN


def cmd_presence(args: argparse.Namespace) -> int:
    """The three-valued answer, from the shared core rather than from here.

    Of the filings this period declares: which are reporting, which are present
    and not reporting, and which are absent. The distinction is the core's whole
    subject and this package does not re-implement it.

    The vocabulary is passed EXPLICITLY rather than registered into the process.
    `vocabulary=` is scoped to the call; registration is ambient and lasts for
    the process, so a caller embedding this package would inherit a domain it
    never asked for. `vertical.register()` exists for callers that want the
    ambient form, and this verb does not use it.
    """
    try:
        period = declaration_mod.load(_read(args.declaration))
        captured = capture_mod.load(_read(args.capture))
    except (Unreadable, formats.FormatError, declaration_mod.DeclarationError,
            capture_mod.CaptureError) as problem:
        return _refuse(str(problem))
    if not period.reviewed:
        return _refuse("this declaration is not signed, so nothing acts on it")
    try:
        from presence_audit import diff
    except ImportError:
        return _refuse("presence needs the shared core: pip install presence-audit")

    report = diff.compare(period, captured, vocabulary=FilingVocabulary())
    counts = report.counts()
    findings = list(report.findings)
    if args.json:
        print(json.dumps({
            "format": formats.PRESENCE,
            "period": period.period,
            "counts": dict(counts),
            "findings": [{"kind": f.kind, "filing": f.point, "detail": f.detail}
                         for f in findings],
            # The text path prints an OUTCOME line and the first version of this
            # document did not carry one, so one verb reported its verdict in
            # two shapes and a consumer reading the JSON had to infer it from the
            # process exit.
            "outcome": {"exit": exit_contract.FINDINGS if findings else exit_contract.CLEAN,
                        "verdict": exit_contract.verdict(
                            exit_contract.FINDINGS if findings else exit_contract.CLEAN)},
        }, indent=1, sort_keys=True))
        return exit_contract.FINDINGS if findings else exit_contract.CLEAN

    noun = FilingVocabulary.noun[1]
    print(f"period {period.period}: {len(period.points):,} {noun} declared")
    for key, value in counts.items():
        print(f"  {key:<26} {value:>7,}")
    for finding in findings[:20]:
        print(f"  [{finding.kind}] {finding.point} -- {finding.detail}")
    if len(findings) > 20:
        print(f"  ... and {len(findings) - 20:,} more")
    code = exit_contract.FINDINGS if findings else exit_contract.CLEAN
    print(f"OUTCOME exit={code} verdict={exit_contract.verdict(code)}")
    return code


def cmd_detect(args: argparse.Namespace) -> int:
    try:
        period = declaration_mod.load(_read(args.declaration))
        captured = capture_mod.load(_read(args.capture))
    except (Unreadable, formats.FormatError, declaration_mod.DeclarationError,
            capture_mod.CaptureError) as problem:
        return _refuse(str(problem))
    if not period.reviewed:
        return _refuse("this declaration is not signed, so nothing acts on it")
    try:
        run = feeder.run(period, captured)
    except ImportError:
        return _refuse("detect needs the engine: pip install 'filing-balance-audit[engine]'")
    except feeder.FeedError as problem:
        return _refuse(str(problem))

    tolerance = Decimal(str(period.tolerance_absolute))
    resolved = {feeder.entity_id(r): r for r in run.fed.resolved}
    labels = {p.name: p.display_name for p in period.points}
    fired: dict[str, list[str]] = {}
    for finding in run.envelope.get("findings", []):
        fired.setdefault(finding["entity_id"], []).append(finding["problem_type"])

    report = []
    for entity, kinds in sorted(fired.items()):
        item = resolved[entity]
        report.append({
            "filing": item.name,
            "name": labels.get(item.name, item.name),
            "unit": item.unit,
            "residuals": {k: str(v) for k, v in item.residuals().items()},
            "reading": feeder.localise(kinds, item, tolerance),
        })

    code = exit_contract.code_for(run)
    fed = run.fed
    if args.json:
        print(json.dumps({
            "format": formats.DETECT,
            "period": period.period,
            "checked": len(fed.resolved),
            "findings": report,
            "not_checked": {
                "no_reading": sorted(fed.no_reading),
                "incomplete": [f"{n}: {why}" for n, why in sorted(fed.incomplete)],
                "parts_reconcile_to_neither_side": sorted(fed.parts_incomplete),
                "excluded": sorted(fed.excluded),
            },
            "outcome": {"exit": code, "verdict": exit_contract.verdict(code)},
        }, indent=1, sort_keys=True))
        return code

    print(f"period {period.period}: {len(fed.resolved):,} filing(s) checked "
          f"against a tolerance of {period.tolerance_absolute:g}")
    for item in report:
        print(f"  {item['name'][:52]:<52} {item['unit']}")
        print(f"      {item['reading']}")
        for key, value in item["residuals"].items():
            print(f"      {key}: {value}")
    if not report:
        print("  every filing that could be checked, balanced")
    # Said out loud rather than folded into the count above: a filing nobody
    # could check is not a filing that balanced.
    print(f"  not checked -- {len(fed.no_reading):,} with no reading, "
          f"{len(fed.incomplete):,} missing a side, "
          f"{len(fed.parts_incomplete):,} whose components reconcile to neither side")
    print(f"OUTCOME exit={code} verdict={exit_contract.verdict(code)}")
    return code


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="filing-balance-audit", description=__doc__)
    verbs = parser.add_subparsers(dest="verb", required=True)
    d = verbs.add_parser("declare", help="read a declaration and say what it declares")
    d.add_argument("declaration", type=pathlib.Path)
    d.set_defaults(run=cmd_declare)
    pr = verbs.add_parser("presence", help="the three-valued answer, from the core")
    pr.add_argument("declaration", type=pathlib.Path)
    pr.add_argument("capture", type=pathlib.Path)
    pr.add_argument("--json", action="store_true")
    pr.set_defaults(run=cmd_presence)
    t = verbs.add_parser("detect", help="check a capture against a declaration")
    t.add_argument("declaration", type=pathlib.Path)
    t.add_argument("capture", type=pathlib.Path)
    t.add_argument("--json", action="store_true")
    t.set_defaults(run=cmd_detect)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
