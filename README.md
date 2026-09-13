# filing-balance-audit

Of the filings a period says should balance, which do, which cannot be checked,
and which do not.

A bridge from the SEC's Financial Statement Data Sets to
[`arbiter-engine`](https://github.com/james-sheen/arbiter), built to the method in
that repository's `BRIDGES.md`.

> **Not affiliated with the SEC, and not an audit in the regulated sense.** This
> reads a dataset the Securities and Exchange Commission publishes and is a
> consumer of it and nothing else: no connection, no endorsement, no affiliation.
> A *financial statement audit* is a regulated engagement performed by licensed
> auditors; this is not one. It reads published figures and reports whether one arithmetic
> identity holds in them. It forms no opinion, and a discrepancy it reports is an
> arithmetic fact about what was filed rather than an allegation about anyone.
> Full text in [`NOTICE`](NOTICE).
>
> Every figure in `evidence/` is as filed and six balance sheets in it do not
> balance, but the filers are **not named** -- accession numbers and registrants
> carry keyed hashes under a salt that is not published and is not in this
> repository, so the mapping cannot be recovered from anything here.
>
> The figures themselves are a different matter and `NOTICE` says so: 93% of rows
> carry a combination of values unique within the quarter, so a reader holding the
> same public file can match one to a filer by its numbers alone. Anonymising the
> labels does not close that, and keeping the figures exact is the point of the
> package.

```
$ filing-balance-audit detect evidence/2025q1-declaration.json evidence/2025q1-capture.json
period 2025q1: 6,083 filing(s) checked against a tolerance of 0
  F-ad464bc48688 Registrant R-bd643c517b18            USD
      the assets figure is the odd one out
      assets_vs_total: -1.0000
      parts_vs_assets: 1.0000
  ...
  not checked -- 33 with no reading, 154 missing a side, 658 whose components
  reconcile to neither side
OUTCOME exit=1 verdict=findings
```

Six filings in that quarter publish a balance sheet that does not balance, by one
dollar to one thousand. The figures are real; the labels are not, and they are not
stable across readers -- re-derive the evidence under your own salt and the same
six filings come back under six different names.

## The corpus was measured before this was designed

Every number here comes from running
[`sec_identity_probe.py`](../docs/arbiter/tools/sec_identity_probe.py) over
`2025q1` as published. The measurement is the reason the package looks the way it
does, and two of its results contradict what the design started from.

| Identity | Comparable | Exact |
|---|---:|---:|
| `Assets` = the balance-sheet total, either taxonomy | 6,083 | **99.90%** |
| `Assets` = `Liabilities` + `StockholdersEquity` | 4,818 | 68.47% |

**The identity everybody names is the second one, and it is not a ground truth.**
Temporary equity, redeemable preferred and noncontrolling interest are tagged
outside `StockholdersEquity` and inside the total, so a third of real filings fail
it for reasons that are structural rather than mistaken. The largest residuals are
large asset managers and utilities carrying substantial noncontrolling interests.
Nothing about those filings is wrong.

**The balance-sheet total has two standard names.** US GAAP calls it
`LiabilitiesAndStockholdersEquity`; foreign private issuers filing 20-F, 40-F and
6-K report under IFRS, where it is `EquityAndLiabilities`. A reader knowing only
the first finds the identity on 17.4% of 40-F filings and reports the other 90 as
carrying no balance sheet. They carry one. Knowing both takes 40-F to 100.0%.

## What it does that a single check cannot

A balance sheet gives two routes to one number: the total the filer tagged, and
the sum of the components they tagged. Which of those is wrong is the useful half
of the answer, and the agreement is therefore declared in both directions so the
pattern of findings localises it.

- Components agree with the total, assets differs -> **the assets figure is odd**
  (a 10-K in the corpus, one dollar out on ninety-four million)
- Components agree with assets, the total differs -> **the total is odd**
  (a 10-Q, the same defect pointing the other way)
- All three differ -> **nothing is claimed.** One 10-Q files 35,126 / 35,128 /
  35,129 and no reading of that filing says which was meant.

Described rather than named, because the labels move with whoever derived the
evidence. The figures do not.

The components are used as a second route **only where they reconcile to one side**.
Where they reconcile to neither, the credit side has members outside the two tags
and the route is declined, counted and printed -- never scored. Without that gate
this package reported 667 findings over a corpus holding six.

## The tolerance is declared, never defaulted

Two readings of one balance sheet agree when they are within a stated distance,
and the declaration must name it. That is not house style: the engine's agreement
arm declines outright without one and says why. For money the answer is almost
always exactly `0`, and it still has to be written down -- a `0` nobody wrote is
indistinguishable from a question nobody asked.

A relative tolerance is the wrong instrument here and dangerously so. One percent
of a ninety-four-million-dollar balance sheet is nine hundred thousand dollars,
and every real discrepancy in the measured quarter is between one and one
thousand.

## Exit codes

```
0  every filing that could be checked, balanced
1  at least one filing did not balance
2  the run could not be completed
```

`2` is not a worse `1`. A run that could not read its declaration or reach the
engine has produced no verdict, and reporting that as *no findings* is the failure
the contract exists to prevent.

## Install

```bash
pip install filing-balance-audit          # Stage 1: read, pair, report
pip install 'filing-balance-audit[engine]' # + the engine, for `detect`
```

```
filing-balance-audit declare   <declaration.json>
filing-balance-audit presence  <declaration.json> <capture.json>   # the core
filing-balance-audit detect    <declaration.json> <capture.json>   # the engine
```

`presence` is the shared core's three-valued answer -- of the filings a period
declares, which are reporting, which are present and not reporting, and which are
absent -- and this package does not re-implement it. Over 2025q1 that is 6,045
reading, 153 present and not reporting, 33 absent.

**The two paths reconcile exactly, and that is a cross-check rather than a
restatement.** The core reaches its answer by pairing a declaration against a
capture; the feeder reaches its own by resolving each identity and deciding what
can be fed. Neither consults the other and they are written from different
questions, so `tests/test_the_real_quarter.py` asserts the three numbers agree
with no tolerance at all.

## The vocabulary

Registered with [`presence-audit`](https://github.com/james-sheen/presence-audit).
All twelve required members are answered and so are the three optional ones: a
report printing `point` about a filing is in somebody else's noun.

**Nothing is counted out by type, and that is this vertical's one real departure
from its siblings.** Every other vertical in the family uses `is_expected_live`
to remove declared types the audit was never about. Measured here, there is no
form family that reliably carries no balance sheet, so every type is audited. It
is an answer arrived at by measurement, not an unimplemented stub, and it is said
out loud because a reviewer who knows the siblings will read a permissive
predicate as one.

The core's conformance kit runs as a battery leg and reports nothing reaching
past the protocol in either direction. What it explicitly cannot prove is that
the protocol is *sufficient* for a new domain -- and this one found something it
is not, filed upstream as `presence-audit` #13 with a prototyped remedy. Measured
rather than asserted: two captured points at one declared address produce a
different verdict depending which order the capture lists them in. See
`FINDINGS.md`.

Stage 1 declares no dependency on the engine. That is a claim this package
asserts rather than describes:
`tests/test_stage_one_is_dependency_free.py` makes `arbiter_engine` unimportable
and runs the whole pairing path, with a control proving the block is real.

## The battery

`BRIDGES.md`'s verification battery. Twelve legs are named; ten run.

```bash
python3 battery/run_battery.py                      # ten legs
python3 battery/run_battery.py --quarter 2025q1.zip # + `live`, against the source
python3 battery/probe_pin.py --sweep                # the pin leg's evidence
```

`attest` and `tool` are reported **NOT BUILT** rather than dropped: this package
has no attestation and no tool surface, and a battery that quietly lists ten legs
and calls itself complete is the defect the table exists to prevent. They do not
set the exit code -- a declared absence is not a failed measurement, and folding
the two together meant the battery could never be green, which is how a check
becomes one nobody reads. The count travels in the `OUTCOME` line, so `green` and
`not_built=2` arrive together.

`pin` is the leg with nothing to show when it passes, and the one a prose
description of a battery drops. It reads `battery/pin_evidence.json`; a missing
or stale file is **NOT RUN**, never a pass, because a range nobody exercised is
the leg's whole subject.

## Status

**Local and unpublished.** Not on PyPI and no repository created.

Both floors are probed. `arbiter-engine>=0.1.12` is measured: the suite fails on
0.1.11, where an agreement block with no tolerance is still answered from a 5%
relative fallback rather than declined. The declared floor before the probe
existed was 0.1.13, a design note rather than a measurement.

`presence-audit>=0.1.7` is a floor this suite cannot reach -- 0.1.6 passes here --
and it stays, because the consulting vertical in this family measured 0.1.6
failing on exit-contract behaviour this package does not exercise. A floor from
somebody else's measurement is still a floor; a floor from this one would have been
lower and wrong.

`FINDINGS.md` records what did not survive building this. The worst of them
invalidated three complete measurements before anything noticed, and took three
attempts to close.
