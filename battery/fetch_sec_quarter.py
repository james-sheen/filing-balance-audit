#!/usr/bin/env python3
"""Re-derive the real-data evidence in `evidence/` from a published quarter.

    python3 battery/fetch_sec_quarter.py 2025q1.zip --out evidence

THE SOURCE IS NOT COMMITTED AND NOT DOWNLOADED HERE. A quarterly file is about
128 MB, from
`sec.gov/files/dera/data/financial-statement-data-sets/<quarter>.zip`. Fetch it
once and pass the path; a script that pulls a tenth of a gigabyte every time it
runs is a script people stop running. What ships is the derived pair plus this
file, because evidence nobody can re-derive is an assertion with a file beside it.

THE LABELS ARE KEYED ON A SALT THAT IS NOT COMMITTED, so a stranger re-deriving
this quarter gets the same corpus under different labels. `--verify` is how they
check that, and it compares up to relabelling rather than byte for byte.

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
import hashlib
import hmac
import io
import json
import os
import pathlib
import secrets
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


#: The evidence ships ANONYMISED, and `--named` opts out.
#:
#: WHAT THE PROBLEM IS. Every figure in this corpus is as filed and six balance
#: sheets in one quarter do not balance. Committing the named form publishes a
#: list of identified companies beside an arithmetic error. The arithmetic is the
#: subject here; which company filed it contributes nothing to any test.
#:
#: THE SCHEME WAS POSITIONAL AND IS NOW KEYED. Labels used to be assigned by
#: sorted position, which is deterministic and therefore reversible by anyone
#: holding the same quarter: sort it and read off the order. That was written
#: down as pseudonymity-not-anonymity rather than fixed. A label is now
#: `HMAC-SHA256(salt, domain + identifier)` truncated, under a salt that is NOT
#: published, so no holder of the source can invert it.
#:
#: A SALT THAT SHIPS IS NOT A SALT. This quarter declares 6,231 filings and 5,672
#: registrants. Both domains are small enough to enumerate completely in seconds,
#: so a committed salt would let anyone rebuild the whole mapping by hashing every
#: candidate -- an artefact that looks irreversible and is not, which is worse
#: than the positional scheme it replaced, because that one said what it was.
#:
#: WHAT IT COSTS. The committed evidence can no longer be reproduced byte for
#: byte by a stranger, because they do not have the salt and will derive
#: different labels. `--verify` exists for that: it compares a fresh derivation
#: against committed evidence UP TO RELABELLING, which is the strongest statement
#: that can still be made and is the one the reproducibility claim now rests on.
#:
#: WHAT IT DOES NOT BUY. The figures are unchanged, and the figures are a join
#: key: `Assets` and `StockholdersEquity` as filed identify one registrant to
#: anyone holding the same public quarter. Labelling is not the re-identification
#: channel and closing it does not close that one. Said here, and in `NOTICE`,
#: because an artefact that claims more privacy than it has is the failure this
#: change exists to avoid repeating.
LABEL_HEX = 12

#: 128 bits. Enough that the salt cannot be guessed, and a floor rather than a
#: default: a short salt on a 6,231-member domain is a rounding error away from
#: no salt at all.
MIN_SALT_BYTES = 16


def label_maker(salt: bytes):
    """Build the two label functions, domain-separated.

    The domains keep the namespaces apart. Without them an accession number and a
    registrant id that happened to share a string would take the same label, and
    the two are different populations that the declaration relates to each other.
    """
    def make(domain: bytes, value: str) -> str:
        digest = hmac.new(salt, domain + value.encode(), hashlib.sha256).hexdigest()
        return digest[:LABEL_HEX]
    return make


def labels(adshs, ciks, salt: bytes) -> tuple[dict[str, str], dict[str, str]]:
    """Irreversible labels for the two identifiers.

    `cik` is mapped separately and consistently, because `peer_groups` pairs an
    amendment with its original by REGISTRANT. Mapping it per filing would break
    the one relationship in the declaration that is not per-row.

    Collisions are checked rather than assumed. Twelve hex characters over six
    thousand members makes one vanishingly unlikely, and vanishingly unlikely is
    the condition under which nobody notices that two filings merged into one.
    """
    make = label_maker(salt)
    filing_of = {adsh: f"F-{make(b'filing:', adsh)}" for adsh in sorted(adshs)}
    registrant_of = {cik: f"R-{make(b'registrant:', cik)}" for cik in sorted(ciks)}
    for what, mapping in (("filing", filing_of), ("registrant", registrant_of)):
        if len(set(mapping.values())) != len(mapping):
            raise ValueError(f"{what} labels collided at {LABEL_HEX} hex characters")
    return filing_of, registrant_of


def salt_fingerprint(salt: bytes) -> str:
    """A public name for a private salt.

    Two evidence files derived under one salt share this; two derived under
    different salts do not. It tells a reader which derivation they are holding
    without telling them anything that helps invert one -- recovering the salt
    from it means brute-forcing the salt itself.
    """
    return hmac.new(salt, b"salt-fingerprint", hashlib.sha256).hexdigest()[:16]


def read_salt(path: pathlib.Path | None, create: bool) -> bytes:
    """The salt, from a file or `FBA_SALT`, and never from a default.

    There is deliberately no fallback. A default salt is a published salt, and a
    published salt on this domain size is no salt -- so the absence of one is an
    error the caller has to answer rather than something this script decides for
    them quietly.
    """
    if create:
        if path is None:
            raise ValueError("--new-salt needs --salt-file to say where to write it")
        if path.exists():
            raise ValueError(f"{path} exists; refusing to overwrite a salt in use "
                             f"-- evidence derived under it becomes unreproducible")
        path.write_bytes(secrets.token_bytes(32))
        path.chmod(0o600)
    if path is not None:
        salt = path.read_bytes().strip()
    elif os.environ.get("FBA_SALT"):
        salt = os.environb[b"FBA_SALT"].strip()
    else:
        raise ValueError("no salt: pass --salt-file, set FBA_SALT, or --new-salt "
                         "to make one. There is no default, because a default "
                         "salt is a published salt")
    if len(salt) < MIN_SALT_BYTES:
        raise ValueError(f"salt is {len(salt)} bytes; {MIN_SALT_BYTES} is the floor")
    return salt


def family(form: str) -> str:
    for prefixes, name in FORM_FAMILIES:
        if any(form.startswith(p) for p in prefixes):
            return name
    return "other"


def _rows(z: zipfile.ZipFile, name: str):
    with z.open(name) as fh:
        yield from csv.DictReader(
            io.TextIOWrapper(fh, "utf-8", errors="replace"), delimiter="\t")


def derive(path: str, salt: bytes | None, named: bool = False) -> tuple[dict, dict]:
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
    if named:
        filing_of = {a: a for a in subs}
        registrant_of = {s["cik"]: s["cik"] for s in subs.values()}
    else:
        filing_of, registrant_of = labels(
            subs, {s["cik"] for s in subs.values()}, salt)

    declaration = {
        "format": formats.DECLARATION,
        "period": quarter,
        "identifiers": "real" if named else "hashed",
        # What was done to the identifiers, recorded beside them. A reader
        # holding this file can tell what the labels are without being able to
        # invert them, and can tell whether two files share a derivation.
        "identifier_scheme": None if named else {
            "construction": f"HMAC-SHA256(salt, domain + identifier), first "
                            f"{LABEL_HEX} hex characters",
            "domains": {"id": "filing:", "cik": "registrant:"},
            "salt": "NOT PUBLISHED -- held by whoever derived this file",
            "salt_fingerprint": salt_fingerprint(salt),
            "row_order": "by label, not by identifier",
        },
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
            # SORTED BY LABEL, and that is not cosmetic. Sorting by `adsh` would
            # emit the rows in order of the real accession number, so the row
            # number of a filing IS its sorted position -- which is the exact
            # mapping the positional scheme published and this one withholds.
            # Hashing the labels while leaving this alone would have changed how
            # the identifiers look and nothing about what can be recovered.
            for adsh, s in sorted(subs.items(), key=lambda kv: filing_of[kv[0]])
        ],
    }
    capture = {
        "format": formats.CAPTURE,
        "period": quarter,
        "captured_at": None,
        "source": f"{quarter}.zip num.txt",
        "filings": [
            {"id": filing_of[adsh], "unit": uom, "readings": values}
            # By label, for the reason given in the declaration above.
            for (adsh, uom), values in sorted(
                readings.items(), key=lambda kv: (filing_of[kv[0][0]], kv[0][1]))
        ],
    }
    return declaration, capture


#: What a derivation of one quarter says, with every label removed.
#:
#: THIS IS WHAT REPRODUCIBILITY MEANS NOW. Two people deriving 2025q1 under
#: different salts produce different labels and identical corpora, so comparing
#: the files byte for byte reports a difference that is not one. These are the
#: invariants a relabelling cannot touch: the figures, the forms, the units, and
#: which filings share a registrant. Agreement on all of them is the statement
#: *this is the same corpus, relabelled* -- weaker than a byte comparison, and
#: the strongest thing left once the labels stop being derivable by a stranger.
def invariants(declaration: dict, capture: dict) -> dict:
    readings_of: dict[str, list] = collections.defaultdict(list)
    for f in capture["filings"]:
        readings_of[f["id"]].append((f["unit"], tuple(sorted(f["readings"].items()))))
    # Each filing carried as one joined tuple, so a capture row moving to a
    # different filing is a difference. Comparing the two files separately would
    # not see that: both multisets would be unchanged.
    joined = sorted(
        (f["form"], f["declared_type"], f["unit"], tuple(sorted(readings_of[f["id"]])))
        for f in declaration["filings"])
    # Group SIZES, not members: how many filings each registrant made is
    # invariant, which registrant it was is exactly what is being withheld.
    per_registrant = collections.Counter(f["cik"] for f in declaration["filings"])
    return {
        "period": declaration["period"],
        "tolerance_absolute": declaration["tolerance_absolute"],
        "filings": joined,
        "registrant_group_sizes": sorted(collections.Counter(per_registrant.values()).items()),
        "capture_rows": len(capture["filings"]),
    }


def verify(out: pathlib.Path, declaration: dict, capture: dict) -> int:
    """Compare a fresh derivation against committed evidence, up to relabelling."""
    q = declaration["period"]
    try:
        committed = (json.loads((out / f"{q}-declaration.json").read_text()),
                     json.loads((out / f"{q}-capture.json").read_text()))
    except FileNotFoundError as exc:
        print(f"could-not-run: {exc}", file=sys.stderr)
        return 2
    mine, theirs = invariants(declaration, capture), invariants(*committed)
    differing = [k for k in mine if mine[k] != theirs[k]]
    same_salt = (committed[0].get("identifier_scheme") or {}).get("salt_fingerprint") \
        == (declaration.get("identifier_scheme") or {}).get("salt_fingerprint")
    if differing:
        for k in differing:
            detail = ""
            if k == "filings":
                only_mine = len(set(mine[k]) - set(theirs[k]))
                only_theirs = len(set(theirs[k]) - set(mine[k]))
                detail = f" ({only_mine} only in the derivation, {only_theirs} only committed)"
            print(f"  differs: {k}{detail}")
        print(f"NOT THE SAME CORPUS -- {len(differing)} invariant(s) differ")
        return 1
    print(f"same corpus up to relabelling: {len(mine['filings']):,} filing(s), "
          f"{mine['capture_rows']:,} reading(s)")
    print("salt: " + ("the same one -- labels should match too" if same_salt else
                      "a different one, so the labels differ and that is expected"))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("quarterly_zip")
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--salt-file", type=pathlib.Path,
                    help="file holding the salt the labels are keyed on. Not "
                         "committed, and there is no default: a published salt "
                         "over six thousand identifiers is no salt")
    ap.add_argument("--new-salt", action="store_true",
                    help="generate a salt into --salt-file first. Refuses to "
                         "overwrite: evidence derived under a lost salt cannot "
                         "be re-derived under it again")
    ap.add_argument("--named", action="store_true",
                    help="emit real accession numbers and registrant names. For "
                         "local use: the committed evidence is anonymised")
    ap.add_argument("--verify", action="store_true",
                    help="do not write. Derive, and compare against the evidence "
                         "already in --out up to relabelling")
    args = ap.parse_args(argv)
    try:
        salt = None if args.named else read_salt(args.salt_file, args.new_salt)
        declaration, capture = derive(args.quarterly_zip, salt, named=args.named)
    except (FileNotFoundError, KeyError, ValueError, zipfile.BadZipFile) as exc:
        print(f"could-not-run: {exc}", file=sys.stderr)
        return 2
    if not capture["filings"]:
        print("could-not-run: no readings survived the filters, which reads "
              "identically to a quarter nobody filed in", file=sys.stderr)
        return 2
    if args.verify:
        return verify(args.out, declaration, capture)
    args.out.mkdir(parents=True, exist_ok=True)
    q = declaration["period"]
    for name, payload in ((f"{q}-declaration.json", declaration),
                          (f"{q}-capture.json", capture)):
        (args.out / name).write_text(json.dumps(payload, indent=1, sort_keys=True) + "\n")
        print(f"wrote {args.out / name}")
    print(f"{len(declaration['filings']):,} filing(s) declared, "
          f"{len(capture['filings']):,} reading(s) captured")
    if not args.named:
        # The salt is never printed. Its fingerprint is, because that is what a
        # caller needs to tell one derivation from another later.
        print(f"labels keyed on a salt with fingerprint "
              f"{declaration['identifier_scheme']['salt_fingerprint']} -- keep the "
              f"salt file, it is the only way to derive these same labels again")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
