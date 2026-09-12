#!/usr/bin/env python3
"""Re-derive the real-data evidence in `evidence/` from a published quarter.

    python3 battery/fetch_sec_quarter.py 2025q1.zip --out evidence

THE SOURCE IS NOT COMMITTED AND NOT DOWNLOADED HERE. A quarterly file is about
128 MB, from
`sec.gov/files/dera/data/financial-statement-data-sets/<quarter>.zip`. Fetch it
once and pass the path; a script that pulls a tenth of a gigabyte every time it
runs is a script people stop running. What ships is the derived pair plus this
file, because evidence nobody can re-derive is an assertion with a file beside it.

SEC's fair-access policy requires a declared User-Agent naming a contact. This
script does not make requests, so it needs none -- which is the other reason the
download is the reader's step and not this one's.

WHAT IS DERIVED, AND WHAT IS A DECISION. The capture is the filer's numbers,
carried as text. The declaration is the submission index, plus two decisions this
file makes and names: which form families count as which declared type, and that
none of them is counted out. Both are recorded in `evidence/README.md` beside the
result rather than only here.
"""

from __future__ import annotations

import argparse
import collections
import csv
import io
import json
import pathlib
import sys
import zipfile

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from filing_balance_audit import formats                              # noqa: E402
from filing_balance_audit.declaration import (ASSET_TAG, PART_GROUPS,  # noqa: E402
                                              TOTAL_TAGS)

#: Which family a form belongs to, by prefix, first match winning.
#:
#: A DECISION, NOT A MEASUREMENT, and it is descriptive only. Measured over
#: 2025q1 there is no form family that reliably carries no balance sheet, so
#: nothing here is used to count a filing out -- the type is reported and the
#: audit covers all four. See `formats.DECLARED_TYPES`.
FORM_FAMILIES = (
    (("10-K", "20-F", "40-F", "11-K", "N-CSR"), "annual"),
    (("10-Q", "6-K"), "interim"),
    (("S-1", "S-3", "S-4", "S-11", "F-1", "F-3", "F-4", "POS AM", "424B"), "registration"),
)

TAGS = (ASSET_TAG, *TOTAL_TAGS, *{t for group in PART_GROUPS for t in group})


#: The evidence ships PSEUDONYMOUS, and `--named` opts out.
#:
#: WHAT THE PROBLEM IS. Every figure in this corpus is as filed and six balance
#: sheets in one quarter do not balance. Committing the named form publishes a
#: list of identified companies beside an arithmetic error, in a repository whose
#: sibling verticals all ship synthetic examples. The arithmetic is the subject
#: here; which company filed it contributes nothing to any test in this package.
#:
#: WHAT THIS IS AND IS NOT. It is NOT anonymisation and must not be described as
#: any. The source is public, the scheme below is positional, and anyone holding
#: the same quarterly file can recover the mapping by sorting it. What is not
#: published is the mapping -- so this repository is not a searchable list of
#: named companies with broken balance sheets, and a reader who wants the named
#: form derives it from the SEC with `--named`, which is where naming belongs.
#:
#: The scheme is POSITIONAL so that it is deterministic: the same quarter yields
#: the same pseudonyms on every run, which is what lets the committed evidence be
#: re-derived and compared byte for byte. A salted digest would be genuinely
#: irreversible and would also make that impossible, which is a worse trade for a
#: package whose evidence has to be reproducible by a stranger.
def pseudonyms(adshs, ciks) -> tuple[dict[str, str], dict[str, str]]:
    """Stable pseudonyms for the two identifiers, by sorted position.

    `cik` is mapped separately and consistently, because `peer_groups` pairs an
    amendment with its original by REGISTRANT. Mapping it per filing would break
    the one relationship in the declaration that is not per-row.
    """
    return ({adsh: f"F-{n:05d}" for n, adsh in enumerate(sorted(adshs), 1)},
            {cik: f"R-{n:04d}" for n, cik in enumerate(sorted(ciks), 1)})


def family(form: str) -> str:
    for prefixes, name in FORM_FAMILIES:
        if any(form.startswith(p) for p in prefixes):
            return name
    return "other"


def _rows(z: zipfile.ZipFile, name: str):
    with z.open(name) as fh:
        yield from csv.DictReader(
            io.TextIOWrapper(fh, "utf-8", errors="replace"), delimiter="\t")


def derive(path: str, named: bool = False) -> tuple[dict, dict]:
    z = zipfile.ZipFile(path)
    subs = {r["adsh"]: r for r in _rows(z, "sub.txt")}
    readings: dict[tuple[str, str], dict[str, str]] = collections.defaultdict(dict)
    for r in _rows(z, "num.txt"):
        # Point-in-time, consolidated, parent-only, at the filing's own period.
        # A non-empty `segments` is a dimensional breakdown and a non-empty
        # `coreg` is a co-registrant; either summed into the total is a
        # discrepancy the filer never filed.
        if r["tag"] not in TAGS or r["qtrs"] != "0" or r["coreg"] or r.get("segments"):
            continue
        period = subs.get(r["adsh"], {}).get("period")
        if not period or r["ddate"] != period:
            continue
        readings[(r["adsh"], r["uom"])][r["tag"]] = r["value"]

    quarter = pathlib.Path(path).stem
    filing_of, registrant_of = pseudonyms(
        subs, {s["cik"] for s in subs.values()})
    if named:
        filing_of = {a: a for a in subs}
        registrant_of = {s["cik"]: s["cik"] for s in subs.values()}

    declaration = {
        "format": formats.DECLARATION,
        "period": quarter,
        "identifiers": "real" if named else "pseudonymous",
        # Zero, and written down. A balance sheet balances exactly in the unit it
        # is reported in, and every real discrepancy in this quarter is between
        # one and one thousand units.
        "tolerance_absolute": 0,
        "reviewed_by": "DERIVED FROM A PUBLIC DATASET -- not signed by a person",
        "reviewed_on": "2026-09-12",
        "sources": [{
            "path": f"{quarter}.zip",
            "derived_from": "SEC Financial Statement Data Sets, US Government work",
            "supplied": ["sub.txt", "num.txt"],
        }],
        "filings": [
            # `cik` is the REGISTRANT, and it is here for `peer_groups`: an
            # amendment and its original are two filings of one balance sheet,
            # and without the registrant there is nothing to pair them by.
            {"id": filing_of[adsh], "cik": registrant_of[s["cik"]],
             "name": s["name"] if named else f"Registrant {registrant_of[s['cik']]}",
             "form": s["form"], "declared_type": family(s["form"]),
             "unit": next((u for (a, u) in readings if a == adsh), "")}
            for adsh, s in sorted(subs.items())
        ],
    }
    capture = {
        "format": formats.CAPTURE,
        "period": quarter,
        "captured_at": None,
        "source": f"{quarter}.zip num.txt",
        "filings": [
            {"id": filing_of[adsh], "unit": uom, "readings": values}
            for (adsh, uom), values in sorted(readings.items())
        ],
    }
    return declaration, capture


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("quarterly_zip")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--named", action="store_true",
                    help="emit real accession numbers and registrant names. For "
                         "local use: the committed evidence is pseudonymous")
    args = ap.parse_args(argv)
    try:
        declaration, capture = derive(args.quarterly_zip, named=args.named)
    except (FileNotFoundError, KeyError, zipfile.BadZipFile) as exc:
        print(f"could-not-run: {exc}", file=sys.stderr)
        return 2
    if not capture["filings"]:
        print("could-not-run: no readings survived the filters, which reads "
              "identically to a quarter nobody filed in", file=sys.stderr)
        return 2
    args.out.mkdir(parents=True, exist_ok=True)
    q = declaration["period"]
    for name, payload in ((f"{q}-declaration.json", declaration),
                          (f"{q}-capture.json", capture)):
        (args.out / name).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
        print(f"wrote {args.out / name}")
    print(f"{len(declaration['filings']):,} filing(s) declared, "
          f"{len(capture['filings']):,} reading(s) captured")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
