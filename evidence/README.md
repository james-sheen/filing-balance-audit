# Evidence

`2025q1-declaration.json` and `2025q1-capture.json` are derived from the SEC's
Financial Statement Data Sets for 2025 Q1, by
[`../battery/fetch_sec_quarter.py`](../battery/fetch_sec_quarter.py).

**Source.** `sec.gov/files/dera/data/financial-statement-data-sets/2025q1.zip`,
127,765,057 bytes, retrieved 2026-09-12. US Government work; no copyright. SEC's
fair-access policy requires a declared User-Agent naming a contact on any request.

**The quarter is not committed and is not downloaded by the script.** It is about
128 MB. Fetch it once and pass the path. What ships is the derived pair and the
script, because evidence nobody can re-derive is an assertion with a file beside
it.

## What is derived and what is decided

The capture is the filers' numbers, carried as text so that money never passes
through binary floating point on its way in.

The declaration is the submission index plus two decisions, made in the fetch
script and repeated here because this is the file somebody reading the result will
open:

1. **Form families.** `10-K` and `20-F` are *annual*, `10-Q` and `6-K` are
   *interim*, `S-1` and its relatives are *registration*, everything else is
   *other*. Descriptive only.
2. **Nothing is counted out by type.** The sibling verticals in this family count
   some declared types out of the audit. Measured over this quarter there is no
   form family that reliably carries no balance sheet -- 10-K 97.7%, 10-Q 96.7%,
   S-1 96.6%, 40-F 100.0% once the IFRS total is read. So every type is audited,
   and a filing reporting no total is *declared but not readable*, which is the
   honest answer, rather than *counted out*, which would be a reader's opinion
   wearing a vocabulary's clothes.

## Real figures, anonymised filers

Every figure here is as filed and the six discrepancies are real. The filers are
not named: `id` and `cik` carry `HMAC-SHA256(salt, domain + identifier)` truncated
to twelve hex characters, and `name` follows the registrant. The declaration
records the construction, and the salt's fingerprint, in an `identifier_scheme`
key. The salt itself is not in this repository.

**The scheme was positional and is now keyed.** Labels used to be assigned by
sorted position, and this file used to say -- accurately -- that the result was
pseudonymity and not anonymity, because sorting the public quarter recovers that
mapping. It is now keyed on a secret, so nothing published here inverts it.

**A salt that shipped would not be a salt.** The quarter declares 6,231 filings
and 5,672 registrants. Both are small enough to enumerate completely, so a
committed salt lets anyone rebuild the whole mapping by hashing every candidate --
an artefact that looks irreversible and is not, which is worse than the positional
scheme, because that one said what it was.

**Row order is part of the scheme.** Rows are emitted in label order. Sorting them
by the real accession number and relabelling afterwards would leave row position
equal to sorted-identifier position, which is the positional mapping again, in the
one channel nobody inspects.

**What it does not buy.** The figures are unchanged and the figures are a join
key: 93% of the rows here carry a combination of values unique within the quarter,
so a reader holding the same public file can match a row to a filer by its numbers
alone. Closing the label channel does not close that one, and nothing that keeps
the figures exact can. They are exact because a one-dollar discrepancy reported to
a rounded number reports nothing.

**Re-deriving it.** `../battery/fetch_sec_quarter.py` needs a salt; there is no
default, because a default salt is a published salt. A stranger deriving this
quarter gets the same corpus under different labels, so the files will not compare
byte for byte and that is not a discrepancy. `--verify` is the comparison that
holds: it checks the figures, the forms, the units and which filings share a
registrant, and reports whether the two are the same corpus up to relabelling.
`--named` still emits the real identifiers, from the source, for local use.

Nothing here is an allegation. A balance sheet that does not balance by one dollar
is a balance sheet that does not balance by one dollar, and what that means is not
a question this package answers. The full statement is in [`../NOTICE`](../NOTICE).

## What this corpus cannot show you

**Both sides come from one filing.** The values and the structure are the filer's;
the taxonomy that gives the total its name and its natural balance is published by
someone else. That is more than a single-source corpus and less than two
instruments: the *equation* is in no file, and is brought by whoever writes the
model.

So this evidence can show a balance sheet that does not balance. It cannot show a
figure that was never filed, or one that two organisations disagree about. Those
are the failures a finance bridge would most want to catch, and no public dataset
supplies them.

**Amended filings are a thin restatement source, not a rich one.** 342 amendments
in the quarter, 79 whose original is in the same file at all, and 3 that restate
any balance-sheet value. A restatement corpus worth the name is a join across many
quarters.
