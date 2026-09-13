#!/usr/bin/env python3
"""BRIDGES's verification battery, for this package.

The twelve legs in that document's table are all named here. Ten run. Two --
`attest` and `tool` -- have no surface in this package to run against, and are
reported as NOT BUILT with the reason rather than dropped from the table. A
battery that quietly lists ten legs and calls itself complete is the defect the
table exists to prevent, and the summary line carries the count so a scanner sees
it and not just a reader.

    python3 battery/run_battery.py
    python3 battery/run_battery.py --only clean,fault
    python3 battery/run_battery.py --quarter /path/to/2025q1.zip   # enables `live`

Exit 0 every leg that ran passed, 1 a leg found something, 2 a leg could not run.
A leg that could not run is NAMED and never skipped: *not run* and *passed* are
different answers, and only one of them is about this package.

A leg that is NOT BUILT is a third thing and does not set the exit. It is a
declared absence rather than a failed measurement, and folding it into 2 meant
this battery could never be green -- which is how a check becomes one nobody
reads. The count is in the OUTCOME line instead, so `green` and `not_built=2`
arrive together and a scanner sees both.
"""

from __future__ import annotations

import argparse
import collections
import copy
import decimal
import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
SRC = ROOT / "src"
EVIDENCE = ROOT / "evidence"
DECLARATION = EVIDENCE / "2025q1-declaration.json"
CAPTURE = EVIDENCE / "2025q1-capture.json"
RESULT = HERE / "battery_result.json"
PIN_EVIDENCE = HERE / "pin_evidence.json"

CLEAN, FINDINGS, INCOMPLETE = 0, 1, 2

#: Where the engine is, when it is not installed. This package declares it as an
#: optional extra, so a source tree that has never installed the extra cannot
#: import it -- and a battery that quietly ran the engine-free legs and called
#: itself green would be reporting on half a package.
#:
#: NO DEFAULT PATH. The first version fell back to one author's directory layout,
#: which is a private tree leaking into a public package. Unset means *not
#: installed and not told where*, and the legs that need it report NOT RUN.
ENGINE_PATH = os.environ.get("ARBITER_ENGINE", "")

#: Every leg, by the name it reports under. `--only` is validated against this:
#: a mistyped name would otherwise select nothing, and a battery that ran nothing
#: exits 0.
SELECTABLE = ("engine", "conformance", "live", "names", "draft", "gate", "clean",
              "fault", "absent", "attest", "pipe", "tool", "suite", "pin", "ship")

#: How many filings in 2025q1 do not balance. The `clean` leg removes exactly
#: those, so a corpus that then produces a finding has produced it from
#: somewhere else.
#:
#: A COUNT, because the six used to be a list of labels. A hardcoded list stops
#: matching the moment the labelling changes -- and the leg that depends on it
#: then reports a corpus nobody described, which is a true sentence about the
#: wrong thing. The members are computed from the capture; this number is what
#: the battery still asserts up front, so the guard survives.
EXPECTED_UNBALANCED = 6

ASSET_TAG = "Assets"
TOTAL_TAGS = ("LiabilitiesAndStockholdersEquity", "EquityAndLiabilities")


def unbalanced_ids(capture) -> set[str]:
    """The filings in a capture whose two sides differ, by reading it.

    Deliberately NOT the package's own feeder. This is the battery, and a check
    whose expectation is produced by the code under test cannot falsify it.
    Assets against the total, in decimal, under either taxonomy -- which is the
    whole identity, short enough to restate independently here.
    """
    out = set()
    for f in capture["filings"]:
        total = next((f["readings"][t] for t in TOTAL_TAGS if t in f["readings"]), None)
        if total is None or "Assets" not in f["readings"]:
            continue
        try:
            assets, total = decimal.Decimal(f["readings"]["Assets"]), decimal.Decimal(total)
        except decimal.InvalidOperation:
            # 25 values in this corpus do not parse exactly, and the package
            # records them rather than dropping them. A filing whose figures
            # cannot be read is not a filing whose balance sheet disagrees.
            continue
        if assets != total:
            out.add(f["id"])
    return out

RESULTS: list[dict] = []


def leg(name: str, code: int, note: str, built: bool = True) -> int:
    """Record a leg. `built=False` is a DECLARED ABSENCE, not a failed measurement.

    The two were one state at first and the battery could never be green: a leg
    with no surface to test reported the same 2 as a leg whose engine was
    missing, so the worst code was permanently 2. A check that has never been
    green is a check nobody reads, and the gap it was protecting goes with it.

    So they are separated, and the count of unbuilt legs is carried in the
    OUTCOME line rather than only in the rows above it -- a scanner reads that
    line, and `green` beside `not_built=2` is a different claim from `green`.
    """
    RESULTS.append({"leg": name, "code": code, "note": note, "built": built})
    print(f"  {name:<8} {'-' if not built else code}  {note}")
    return code


def _pythonpath() -> str:
    parts = [str(SRC)]
    if ENGINE_PATH and pathlib.Path(ENGINE_PATH).exists():
        parts.append(ENGINE_PATH)
    if os.environ.get("PYTHONPATH"):
        parts.append(os.environ["PYTHONPATH"])
    return os.pathsep.join(parts)


def document_or_reason(proc) -> tuple[dict | None, str]:
    """The `--json` document, or why there is not one.

    Every leg that reads stdout goes through here. The first version parsed it
    directly and raised `JSONDecodeError` out of the battery the moment a verb
    exited 2 -- so a package whose engine was missing produced a traceback
    instead of a leg saying the engine was missing. A battery is the last place
    that should turn an honest exit into a crash.
    """
    try:
        return json.loads(proc.stdout), ""
    except json.JSONDecodeError:
        tail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return None, (tail[0][:150] if tail else f"exit {proc.returncode}, no output")


def cli(argv, cwd=None, env=None, stdout=subprocess.PIPE, timeout=600):
    environment = dict(os.environ, PYTHONPATH=_pythonpath())
    environment.update(env or {})
    return subprocess.run([sys.executable, "-m", "filing_balance_audit.cli", *argv],
                          stdout=stdout, stderr=subprocess.PIPE, text=True,
                          cwd=str(cwd or ROOT), env=environment, timeout=timeout)


def _load(path):
    return json.loads(pathlib.Path(path).read_text())


def _write(path, payload):
    pathlib.Path(path).write_text(json.dumps(payload))
    return str(path)


# ------------------------------------------------------------------- engine
def leg_engine() -> int:
    """C3's own probe: measure the engine you pin, do not read it.

    Four behaviours this package's design rests on, each asserted against the
    engine actually installed. The third is the one that would fail silently:
    an engine that guessed a relative tolerance instead of declining would let
    every one-dollar discrepancy on a million-dollar balance sheet pass, and
    every other leg here would still be green.
    """
    if ENGINE_PATH and pathlib.Path(ENGINE_PATH).exists():
        sys.path.insert(0, ENGINE_PATH)
    try:
        from arbiter_engine.api import EngineSession, check
    except ImportError as problem:
        return leg("engine", INCOMPLETE, f"could not import the engine: {problem}")

    def run(model, properties):
        session = EngineSession()
        session.load_model(model)
        session.add_entity("F", "Filing", properties=properties)
        envelope = check(session).to_dict()
        return ([f["problem_type"] for f in envelope.get("findings", [])],
                [d.get("reason") for d in envelope.get("not_checked", [])])

    sys.path.insert(0, str(SRC))
    from filing_balance_audit import feeder

    class Period:
        tolerance_absolute = 0.0
    model = feeder.model_text(Period())
    problems = []

    fired, _ = run(model, {"assets": 93840769, "balance_sheet_total": 93840770,
                           "parts_sum": 93840770})
    if feeder.ASSETS_ARM not in fired:
        problems.append("a one-unit difference on a 93-million balance sheet is "
                        "not reported at a zero tolerance")
    if feeder.PARTS_ARM not in fired:
        problems.append("the second direction does not fire, so no finding can "
                        "be localised")

    quiet, _ = run(model, {"assets": 1000, "balance_sheet_total": 1000,
                           "parts_sum": 1000})
    if quiet:
        problems.append(f"a balance sheet that balances reports {quiet}")

    _, declined = run(model, {"assets": 1000})
    if not any("missing_property" in str(d) for d in declined):
        problems.append("a filing with no total is not declined; it is being "
                        "answered from something")

    guessed = model.replace("          tolerance_absolute: 0.0\n", "")
    _, no_tolerance = run(guessed, {"assets": 100, "balance_sheet_total": 106})
    if not any("missing_config" in str(d).lower() for d in no_tolerance):
        problems.append("an agreement block with no tolerance is ANSWERED rather "
                        "than declined -- a guessed tolerance would silence every "
                        "real discrepancy in this corpus")

    if problems:
        return leg("engine", FINDINGS, f"{len(problems)} behaviour(s) differ: "
                                       f"{problems[0]}")
    return leg("engine", CLEAN, "4 behaviours this design rests on, measured on "
                                "the installed engine")


# -------------------------------------------------------------- conformance
def leg_conformance() -> int:
    """The core's own kit, RUN against this vertical's vocabulary.

    Two checks in one leg because they are two halves of one contract: that the
    core reaches for nothing the protocol does not declare, and that this
    vocabulary reaches for nothing the protocol does not declare on the objects
    it is handed.

    What it cannot prove is that the protocol is SUFFICIENT for this domain, and
    the kit says so itself. A stand-in written from the protocol can only find
    that something exceeded the document, never that the document is missing
    something a real domain needs.
    """
    try:
        from presence_audit.conformance import check_a_vocabulary, check_the_core
    except ImportError as problem:
        return leg("conformance", INCOMPLETE, f"could not import the core: {problem}")
    sys.path.insert(0, str(SRC))
    from filing_balance_audit.vertical import FilingVocabulary

    core = check_the_core()
    problems, notes = check_a_vocabulary(FilingVocabulary())
    if core or problems:
        return leg("conformance", FINDINGS,
                   f"{len(core)} core, {len(problems)} vocabulary: "
                   f"{(core + problems)[0][:110]}")
    return leg("conformance", CLEAN,
               f"nothing reached past the protocol, either way"
               + (f"; {len(notes)} observation(s)" if notes else ""))


# --------------------------------------------------------------------- live
def leg_live(quarter) -> int:
    """Can a live surface be read at all, and how many sources did it serve?"""
    if not quarter:
        return leg("live", INCOMPLETE, "NOT RUN: no --quarter given. The quarterly "
                                       "file is 128 MB and is not committed; "
                                       "everything below runs against what it "
                                       "produced, which is not the same claim")
    if not pathlib.Path(quarter).exists():
        return leg("live", INCOMPLETE, f"NOT RUN: no such quarterly file: {quarter}")
    with tempfile.TemporaryDirectory() as work:
        made = subprocess.run(
            [sys.executable, str(HERE / "fetch_sec_quarter.py"), str(quarter),
             "--out", work],
            capture_output=True, text=True, timeout=900)
        if made.returncode != 0:
            return leg("live", FINDINGS,
                       f"the live surface would not read: "
                       f"{(made.stderr or made.stdout).strip()[:120]}")
        produced = {p.name: p for p in pathlib.Path(work).glob("*.json")}
        # BY NAME, never by sort position. The first version took `produced[1]`
        # of a sorted list and compared the re-derived DECLARATION against the
        # committed CAPTURE, which differ for the obvious reason -- a red leg
        # reporting stale evidence about evidence that was current.
        if set(produced) != {CAPTURE.name, DECLARATION.name}:
            return leg("live", FINDINGS, f"expected {CAPTURE.name} and "
                                         f"{DECLARATION.name}, got {sorted(produced)}")
        fresh = _load(produced[CAPTURE.name])
        committed = _load(CAPTURE)
        if fresh["filings"] != committed["filings"]:
            return leg("live", FINDINGS, "the live surface no longer produces the "
                                         "committed evidence; the evidence is stale "
                                         "or the source moved")
    return leg("live", CLEAN, f"read the quarter and reproduced the committed "
                              f"evidence byte for byte, {len(committed['filings']):,} "
                              f"reading(s)")


# -------------------------------------------------------------------- names
#: Does this repository name a filer beside that filer's own figures?
#:
#: THE IDENTIFIERS WERE SCRUBBED AND THIS WAS NOT. Four tests in
#: `test_localisation.py` were named after the registrants they were about, beside
#: those registrants' exact reported figures. Nothing about a function name looks
#: like an identifier, so nothing that handled identifiers went near it -- and a
#: name written out is a stronger identification than the pseudonyms ever were,
#: because it needs no join and no source file at all.
#:
#: THE PREDICATE IS CO-OCCURRENCE, and the first version of this leg got it wrong.
#: Sweeping for filer names alone reported 67 hits over four real ones, because
#: thousands of registrants are named after ordinary words. Filtering to
#: non-dictionary words would have dropped three of the four, whose names are
#: ordinary English. What is not ordinary is a filer's name in the same file as a
#: figure only that filer reported, which is what makes it an identification
#: rather than a coincidence.
#:
#: THIS COMMENT WAS ITSELF A HIT. Its first draft named the three companies and
#: quoted one of their figures, to explain why the simpler predicate failed -- so
#: the leg went red on the paragraph documenting the leg. Prose about an
#: identification is an identification. It is described here and not quoted, and
#: that is the second time this repository has learned the same thing about
#: writing down what it just removed.
#:
#: Needs the quarter, so it cannot run in CI and says so rather than passing.
GENERIC_IN_A_FILER_NAME = {
    "GROUP", "HOLDINGS", "HOLDING", "TRUST", "CAPITAL", "PARTNERS", "INCOME",
    "GLOBAL", "AMERICA", "AMERICAN", "NATIONAL", "UNITED", "FIRST", "SECOND",
    "SERVICES", "SERVICE", "ENERGY", "FINANCIAL", "BANCORP", "BANCSHARES",
    "INTERNATIONAL", "RESOURCES", "PROPERTIES", "PROPERTY", "SOLUTIONS", "FUND",
    "SYSTEMS", "TECHNOLOGIES", "TECHNOLOGY", "PHARMACEUTICALS", "THERAPEUTICS",
    "ACQUISITION", "CORPORATION", "COMPANY", "LIMITED", "INDUSTRIES", "MEDICAL",
    "HEALTH", "ASSET", "ASSETS", "GENERAL", "STANDARD", "COMMUNITY", "SECURITY",
    "DIGITAL", "MEDIA", "GROWTH", "VALUE", "SELECT", "MASTER", "COMMON", "CORP",
    "PUBLIC", "PRIVATE", "INC", "PLC", "LTD", "THE", "AND", "FOR", "NEW",
}

#: Four digits, so a year or a small count is not a figure.
#:
#: And the figure must be one that exactly ONE filer reported, which is the
#: property that makes this an identification at all. Without that the leg
#: reported a company called Real beside the number 1000 -- both real, jointly
#: meaningless, because a figure thousands of filers report identifies nobody.
FIGURE = re.compile(r"(?<!\d)\d{4,}(?!\d)")


def _filers_and_their_figures(quarter):
    """Each filer's distinctive name words, and the values they reported."""
    import csv as _csv
    import io as _io
    import zipfile as _zipfile
    with _zipfile.ZipFile(quarter) as z:
        with z.open("sub.txt") as fh:
            of = {r["adsh"]: r["name"].upper() for r in _csv.DictReader(
                _io.TextIOWrapper(fh, "utf-8", errors="replace"), delimiter="\t")}
        figures = collections.defaultdict(set)
        with z.open("num.txt") as fh:
            for row in _csv.DictReader(
                    _io.TextIOWrapper(fh, "utf-8", errors="replace"), delimiter="\t"):
                if row["tag"] != ASSET_TAG and row["tag"] not in TOTAL_TAGS:
                    continue
                name = of.get(row["adsh"])
                if name:
                    figures[name].add(row["value"].split(".")[0].lstrip("-"))
    # Keep only the figures a single filer reported. A shared figure is not a
    # join key and a name beside one is a coincidence.
    reporters = collections.Counter(v for values in figures.values() for v in values)
    figures = {name: {v for v in values if reporters[v] == 1}
               for name, values in figures.items()}
    words = {name: {w for w in re.findall(r"[A-Z]{3,}", name)
                    if w not in GENERIC_IN_A_FILER_NAME}
             for name in figures}
    return words, figures


def leg_names(quarter) -> int:
    """Is any filer named in this repository beside a figure that filer reported?"""
    if not quarter or not pathlib.Path(quarter).exists():
        return leg("names", INCOMPLETE, "NOT RUN: needs --quarter, and the 128 MB "
                                        "source is not committed")
    words, figures = _filers_and_their_figures(quarter)
    shipped = {}
    for path in sorted(ROOT.rglob("*")):
        if (not path.is_file() or ".git" in path.parts
                or path.suffix not in {".py", ".md", ".toml", ".yml", ".cfg"}
                or path.name.startswith("2025q1")):
            continue
        text = path.read_text(errors="replace")
        shipped[path.relative_to(ROOT).as_posix()] = (
            set(re.findall(r"[A-Za-z]{3,}", text.upper())), set(FIGURE.findall(text)))
    found = []
    for name, mine in words.items():
        if not mine:
            continue
        for where, (said, numbers) in shipped.items():
            both = mine & said
            shared = figures[name] & numbers
            if both and shared:
                found.append((where, sorted(both)[0], sorted(shared)[0]))
    if not found:
        return leg("names", CLEAN, f"no filer of {len(figures):,} is named in this "
                                   f"repository beside a figure they reported")
    return leg("names", FINDINGS,
               f"{len(found)} place(s) name a filer beside that filer's own figure: "
               + "; ".join(f"{w} ({tok} with {num})" for w, tok, num in found[:5]))


# ------------------------------------------------------------- draft / gate
def leg_draft(work) -> tuple[int, str]:
    """Does draft tooling emit an unreviewed statement and exit clean?"""
    drafted = copy.deepcopy(_load(DECLARATION))
    drafted["reviewed_by"] = None
    drafted["reviewed_on"] = None
    path = _write(pathlib.Path(work) / "unsigned-declaration.json", drafted)
    proc = cli(["declare", path])
    if proc.returncode == 0:
        return leg("draft", FINDINGS, "an unsigned declaration was accepted by "
                                      "`declare`, so nothing downstream can be "
                                      "the first to refuse it"), path
    return leg("draft", CLEAN, "an unsigned declaration is produced, and `declare` "
                               "is already where it stops"), path


def leg_gate(drafted) -> int:
    """Does your own gate then refuse that exact file, by name?"""
    proc = cli(["detect", drafted, str(CAPTURE)])
    if proc.returncode != INCOMPLETE:
        return leg("gate", FINDINGS, f"the gate exited {proc.returncode} on an "
                                     f"unsigned declaration; 2 is the only honest "
                                     f"answer to a run that produced no verdict")
    if "not signed" not in (proc.stderr + proc.stdout):
        return leg("gate", FINDINGS, "the gate refused without saying it was the "
                                     "signature")
    return leg("gate", CLEAN, "the unsigned draft is refused by name and exits 2")



# -------------------------------------------------------------------- clean
def leg_clean(work) -> int:
    """Over an uncontaminated corpus, does the pipeline stay quiet?"""
    capture = copy.deepcopy(_load(CAPTURE))
    unbalanced = unbalanced_ids(capture)
    before = len(capture["filings"])
    capture["filings"] = [f for f in capture["filings"] if f["id"] not in unbalanced]
    removed = before - len(capture["filings"])
    if removed != EXPECTED_UNBALANCED:
        return leg("clean", INCOMPLETE, f"could not build a clean corpus: removed "
                                        f"{removed} where {EXPECTED_UNBALANCED} "
                                        f"unbalanced filings were expected, so this "
                                        f"leg would be testing a corpus nobody "
                                        f"described")
    path = _write(pathlib.Path(work) / "clean-capture.json", capture)
    proc = cli(["detect", str(DECLARATION), path, "--json"])
    document, why = document_or_reason(proc)
    if document is None:
        return leg("clean", INCOMPLETE, f"the run produced no verdict: {why}")
    if proc.returncode != CLEAN:
        return leg("clean", FINDINGS,
                   f"a corpus with every known fault removed still reports "
                   f"{len(document['findings'])}: "
                   f"{[f['filing'] for f in document['findings']][:3]}")
    return leg("clean", CLEAN, f"{removed} known faults removed and the "
                               f"remaining corpus is quiet")


# ------------------------------------------------------------ fault / absent
#: One fault per copy, and the expectation is written HERE, before the run.
#: `find` is what the leg asserts on -- the finding and not the exit code, so a
#: leg cannot pass because something else went wrong at the same time.
FAULTS = {
    "one_unit_off": {
        "why": "assets one unit below the total is the smallest real fault class "
               "in this corpus, and the one a relative tolerance would hide",
        "expect": "a finding naming this filing, localised to the assets figure",
    },
    "total_missing": {
        "why": "a filing with no total under either taxonomy",
        "expect": "not a finding: reported as declared-but-incomplete",
    },
    "parts_unreconciled": {
        "why": "components that reconcile to neither side, which is 658 real "
               "filings and none of them unbalanced",
        "expect": "not a finding: the second route is declined and counted",
    },
    "cross_currency": {
        "why": "the total moved to another reporting unit",
        "expect": "not a finding: the two are never compared, and both sides are "
                  "reported incomplete",
    },
    "reading_absent": {
        "why": "a declared filing with no reading at all",
        "expect": "not a finding: reported in no_reading",
    },
}


def _inject(name, capture):
    """Apply one fault to a copy, and return the filing it was applied to."""
    unbalanced = unbalanced_ids(capture)
    victim = next(f for f in capture["filings"]
                  if f["id"] not in unbalanced
                  and "Assets" in f["readings"]
                  and any(t in f["readings"] for t in TOTAL_TAGS))
    total = next(t for t in TOTAL_TAGS if t in victim["readings"])
    if name == "one_unit_off":
        victim["readings"]["Assets"] = str(int(float(victim["readings"][total])) - 1)
        victim["readings"].setdefault("Liabilities", "0")
        victim["readings"]["StockholdersEquity"] = str(
            int(float(victim["readings"][total])) - int(float(victim["readings"]["Liabilities"])))
    elif name == "total_missing":
        del victim["readings"][total]
    elif name == "parts_unreconciled":
        victim["readings"]["Liabilities"] = "1"
        victim["readings"]["StockholdersEquity"] = "1"
        victim["readings"].pop(
            "StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", None)
    elif name == "cross_currency":
        moved = {"id": victim["id"], "unit": "XTS",
                 "readings": {total: victim["readings"].pop(total)}}
        capture["filings"].append(moved)
    elif name == "reading_absent":
        capture["filings"] = [f for f in capture["filings"] if f["id"] != victim["id"]]
    return victim["id"]


def _verdict(name, adsh, document):
    """`None` when the leg passed. Asserts on the finding, never the exit code."""
    named = [f for f in document["findings"] if f["filing"] == adsh]
    not_checked = document["not_checked"]
    if name == "one_unit_off":
        if not named:
            return "the injected discrepancy is not reported"
        if "assets figure is the odd one out" not in named[0]["reading"]:
            return f"found, but localised as {named[0]['reading']!r}"
        return None
    if named:
        return f"reported as a finding, and it is not one: {named[0]['reading']!r}"
    where = {"total_missing": "incomplete",
             "parts_unreconciled": "parts_reconcile_to_neither_side",
             "cross_currency": "incomplete",
             "reading_absent": "no_reading"}[name]
    if not any(adsh in str(entry) for entry in not_checked[where]):
        return f"not a finding, but also absent from not_checked[{where!r}]"
    return None


def leg_faults(work) -> int:
    baseline = _load(CAPTURE)
    failed, absent_ok = [], None
    for name, spec in FAULTS.items():
        capture = copy.deepcopy(baseline)
        adsh = _inject(name, capture)
        # Rule 3: assert the injection took. An injector that silently no-ops
        # turns a fault leg into a green that tested nothing.
        if capture["filings"] == baseline["filings"]:
            failed.append(f"{name}: the injection did not apply")
            continue
        path = _write(pathlib.Path(work) / f"fault-{name}.json", capture)
        proc = cli(["detect", str(DECLARATION), path, "--json"])
        document, why = document_or_reason(proc)
        if document is None:
            failed.append(f"{name}: the run produced no verdict: {why}")
            continue
        problem = _verdict(name, adsh, document)
        if name == "reading_absent":
            absent_ok = problem
        elif problem:
            failed.append(f"{name}: {problem}")
    fault_code = leg("fault", FINDINGS if failed else CLEAN,
                     f"{len(FAULTS) - 1 - len(failed)}/{len(FAULTS) - 1} classes "
                     f"behaved as declared before the run"
                     + (f"; {failed[0]}" if failed else ""))
    leg("absent", FINDINGS if absent_ok else CLEAN,
        absent_ok or "a declared filing with no reading is reported, not dropped")
    return fault_code


# ------------------------------------------------------- attest / pipe / tool
def leg_attest() -> int:
    return leg("attest", INCOMPLETE,
               "NOT BUILT: this package has no attestation surface. The leg is "
               "named rather than dropped so the table keeps its full length and the "
               "gap is in the summary, not only in FINDINGS.md", built=False)


def leg_tool() -> int:
    return leg("tool", INCOMPLETE,
               "NOT BUILT: no tool or MCP surface. Same reason as attest",
               built=False)


def leg_pipe(work) -> int:
    """Does a reader walking away change the verdict, or print anything?"""
    capture = copy.deepcopy(_load(CAPTURE))
    path = _write(pathlib.Path(work) / "pipe-capture.json", capture)
    environment = dict(os.environ, PYTHONPATH=f"{SRC}:{os.environ.get('PYTHONPATH','')}")
    with subprocess.Popen(
            [sys.executable, "-m", "filing_balance_audit.cli", "detect",
             str(DECLARATION), path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            env=environment, cwd=str(ROOT)) as proc:
        proc.stdout.close()                      # the reader walks away
        _, err = proc.communicate(timeout=600)
    if proc.returncode not in (FINDINGS, 120, -13):
        return leg("pipe", FINDINGS, f"a closed reader changed the verdict to "
                                     f"{proc.returncode}; it was 1 with a reader")
    if "Traceback" in err:
        return leg("pipe", FINDINGS, "a closed reader produced a traceback")
    return leg("pipe", CLEAN, f"a closed reader neither changed the verdict "
                              f"({proc.returncode}) nor printed a traceback")


# -------------------------------------------------------------- suite / pin
def leg_suite() -> int:
    """Does the suite pass from a directory that is not the repository?"""
    with tempfile.TemporaryDirectory() as elsewhere:
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-q",
             "-p", "no:cacheprovider"],
            capture_output=True, text=True, cwd=elsewhere, timeout=900)
    tail = [ln for ln in proc.stdout.strip().splitlines() if ln.strip()]
    if proc.returncode != 0:
        return leg("suite", FINDINGS, f"the suite does not pass from elsewhere: "
                                      f"{tail[-1] if tail else '?'}")
    return leg("suite", CLEAN, f"from a directory that is not the repository: "
                               f"{tail[-1] if tail else 'passed'}")


def leg_pin() -> int:
    """Does every release inside the declared range actually run?

    Read from the probe's evidence rather than re-run here: the probe builds one
    environment per release and takes minutes. A missing or stale evidence file
    is NOT RUN, never a pass -- the failure this leg exists to catch is a range
    nobody exercised, and reading a green from an absent file would be that
    failure with a tick beside it.
    """
    if not PIN_EVIDENCE.exists():
        return leg("pin", INCOMPLETE,
                   "NOT RUN: no pin evidence. `python3 battery/probe_pin.py "
                   "--sweep` writes it; a declared range nobody exercised is the "
                   "leg's whole subject")
    evidence = _load(PIN_EVIDENCE)
    code = evidence.get("exit")
    notes = []
    for pin in evidence.get("pins", []):
        notes.append(f"{pin['dist']}{pin['specifier']}: "
                     f"{len(pin['in_range'])} in range, {pin['verdict']}")
    if code == 2:
        return leg("pin", INCOMPLETE, "; ".join(notes) or "the probe could not run")
    if code == 1:
        return leg("pin", FINDINGS, "; ".join(notes))
    return leg("pin", CLEAN, "; ".join(notes))


# --------------------------------------------------------------------- ship
def leg_ship(work) -> int:
    """Does the built artifact, installed clean, still do all of that?

    The leg to protect. Every other one above runs against a source tree no
    consumer will ever have.
    """
    dist = pathlib.Path(work) / "dist"
    built = subprocess.run([sys.executable, "-m", "build", "--wheel", "-o", str(dist)],
                           capture_output=True, text=True, cwd=str(ROOT), timeout=900)
    if built.returncode != 0:
        return leg("ship", INCOMPLETE, f"could not build a wheel: "
                                       f"{built.stderr.strip()[-120:]}")
    wheels = list(dist.glob("*.whl"))
    home = pathlib.Path(work) / "shipenv"
    made = subprocess.run([sys.executable, "-m", "virtualenv", "-q", str(home)],
                          capture_output=True, text=True)
    if made.returncode != 0:
        return leg("ship", INCOMPLETE, "could not create an environment")
    pip = home / "bin" / "pip"
    console = home / "bin" / "filing-balance-audit"
    installed = subprocess.run(
        [str(pip), "install", "-q", "--no-cache-dir", f"{wheels[0]}[engine]"],
        capture_output=True, text=True, timeout=900)
    if installed.returncode != 0:
        return leg("ship", INCOMPLETE, f"the wheel would not install: "
                                       f"{installed.stderr.strip()[-120:]}")
    # Run from somewhere that is not the repository, so `src/` cannot be reached.
    proc = subprocess.run([str(console), "detect", str(DECLARATION), str(CAPTURE),
                           "--json"], capture_output=True, text=True,
                          cwd=str(home), timeout=900)
    document, why = document_or_reason(proc)
    if document is None:
        return leg("ship", FINDINGS, f"the installed console script printed no "
                                     f"document: {why}")
    if proc.returncode != FINDINGS or len(document["findings"]) != EXPECTED_UNBALANCED:
        return leg("ship", FINDINGS,
                   f"the installed artifact exited {proc.returncode} with "
                   f"{len(document['findings'])} finding(s); the source tree "
                   f"reports {EXPECTED_UNBALANCED} at exit 1")
    return leg("ship", CLEAN, f"the built wheel, installed clean, reports the same "
                              f"{EXPECTED_UNBALANCED} filings at exit 1")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--only", help=f"comma-separated: {', '.join(SELECTABLE)}")
    ap.add_argument("--quarter", help="path to a quarterly zip, which enables `live`")
    ap.add_argument("--no-ship", action="store_true")
    args = ap.parse_args(argv)

    selected = None
    if args.only:
        selected = {name.strip() for name in args.only.split(",") if name.strip()}
        unknown = selected - set(SELECTABLE)
        if unknown:
            print(f"could-not-run: no such leg(s): {sorted(unknown)}. A mistyped "
                  f"name selects nothing, and a battery that ran nothing exits 0",
                  file=sys.stderr)
            return INCOMPLETE

    def wanted(name):
        return selected is None or name in selected

    print(f"battery: {ROOT.name}")
    work = tempfile.mkdtemp(prefix="fba-battery-")
    drafted = None
    try:
        if wanted("engine"):
            leg_engine()
        if wanted("conformance"):
            leg_conformance()
        if wanted("live"):
            leg_live(args.quarter)
        if wanted("names"):
            leg_names(args.quarter)
        if wanted("draft"):
            _, drafted = leg_draft(work)
        if wanted("gate"):
            if drafted is None:
                leg("gate", INCOMPLETE, "NOT RUN: needs the file `draft` produces")
            else:
                leg_gate(drafted)
        if wanted("clean"):
            leg_clean(work)
        if wanted("fault") or wanted("absent"):
            leg_faults(work)
        if wanted("attest"):
            leg_attest()
        if wanted("pipe"):
            leg_pipe(work)
        if wanted("tool"):
            leg_tool()
        if wanted("suite"):
            leg_suite()
        if wanted("pin"):
            leg_pin()
        if wanted("ship"):
            if args.no_ship:
                leg("ship", INCOMPLETE, "NOT RUN: --no-ship. Every other leg ran "
                                        "against a source tree no consumer has")
            else:
                leg_ship(work)
    finally:
        shutil.rmtree(work, ignore_errors=True)

    ran = [row for row in RESULTS if row["built"]]
    unbuilt = [row["leg"] for row in RESULTS if not row["built"]]
    unrun = [row["leg"] for row in ran if row["code"] == INCOMPLETE]
    worst = max((row["code"] for row in ran), default=INCOMPLETE)
    print(f"\n  {'-' * 70}")
    print(f"  OUTCOME battery_exit={worst} legs={len(RESULTS)} "
          f"green={sum(1 for r in ran if r['code'] == CLEAN)} "
          f"findings={sum(1 for r in ran if r['code'] == FINDINGS)} "
          f"could_not_run={len(unrun)} not_built={len(unbuilt)}"
          + (f" could_not_run->{unrun}" if unrun else "")
          + (f" not_built->{unbuilt}" if unbuilt else ""))
    RESULT.write_text(json.dumps(
        {"legs": RESULTS, "exit": worst,
         # Recorded even when null: a partial run whose result file looked like a
         # full one would be a green nobody could question.
         "only": sorted(selected) if selected else None,
         "quarter_supplied": bool(args.quarter)}, indent=1) + "\n")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
