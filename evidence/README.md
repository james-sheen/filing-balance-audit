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

## Real figures, pseudonymous filers

Every figure here is as filed and the six discrepancies are real. The filers are
not named: `id` and `cik` carry stable pseudonyms (`F-00001`, `R-0001`) assigned by
sorted position, and `name` follows the registrant. The declaration records which
form it is in an `identifiers` key.

**Pseudonymity, not anonymity.** The scheme is positional and the source is public,
so anyone with the same quarterly file can recover the mapping by sorting it, and
`../battery/fetch_sec_quarter.py --named` emits it directly. What is not published
here is the mapping -- so this repository is not a searchable list of identified
companies beside an arithmetic error, which is the only thing the pseudonyms buy
and all they are claimed to buy.

Positional rather than a salted digest ON PURPOSE: a digest would be genuinely
irreversible and would also make the committed evidence impossible for a stranger
to re-derive and compare byte for byte, which is a worse trade for evidence whose
whole value is that somebody else can reproduce it.

**The digest was tried, and reverted, and the measurements are why.** Keying the
labels under an unpublished salt closed the label channel and closed nothing else.
The figures are a join key on 93% of rows, so a reader with the public quarter
matched rows to filers without consulting a label either way. Worse, the previous
labelling stayed in the repository's history, and with both labellings published
the figures join them: 5,774 of 6,198 filing labels, 93%, mapped back to their
positional ones using nothing but a clone. A published repository cannot be anonymised at its tip.
What the digest did cost was reproducibility -- a stranger's derivation no longer
matched byte for byte, which is the one property this file leads with.

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
