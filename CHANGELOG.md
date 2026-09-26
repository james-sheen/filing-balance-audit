# Changelog

## 0.1.0 -- unreleased

First build. Local and unpublished: no repository, not on PyPI.

- **Named `filing-balance-audit`.** It was renamed to `sec-balance-audit` and back,
  both times before any release, so no format id, import path or console script
  ever shipped under the interim name and nothing needs a migration.

  The round trip is recorded rather than tidied away, because the reason is the
  useful part. `sec-balance-audit` parses as *an audit by the SEC*, and it was the
  only name in this family to put an organisation where every sibling puts a
  setting -- `bmc-`, `factory-`, `engagement-`. `filing-` is the setting and
  carries no such reading.

  Format ids move with the distribution -- `filing-balance-audit/declaration/1` --
  because a reader refuses an unknown format BY NAME, and a document whose id names
  a different distribution would be refused for the right reason with a confusing
  message. `FilingVocabulary` and the `Filing` records never moved: they name the
  subject, which was a filing throughout.
- **The evidence ships pseudonymous.** Every figure is as filed and the six
  discrepancies are real; the filers are not named. `id` and `cik` carry stable
  positional pseudonyms and `battery/fetch_sec_quarter.py --named` emits the real
  form for local use. Pseudonymity and not anonymity, said plainly in `NOTICE`:
  the source is public and the scheme is positional, so the mapping is
  recoverable. What this repository does not publish is the mapping.

  `NOTICE` also carries the stronger half, which was measured rather than
  assumed: the figures are a join key on 93% of rows, so a reader with the same
  public quarter matches a row to a filer by its numbers alone. Replacing the
  pseudonyms with a salted digest was built and reverted -- it left that channel
  open, and the prior labelling remained in history where the figures join the
  two. See FINDINGS.md entry 16.
- **Four tests were named after the filers they were about**, beside those
  filers' exact figures, since the first commit. Handling identifiers never went
  near them: a function name does not look like one. Renamed, and the battery
  grew a `names` leg that reports any filer named in this tree beside a figure
  only that filer reported.
- **No hardcoded path to the engine.** `ARBITER_ENGINE` names a checkout; unset
  means not installed and not told where, and the legs that need it say so.
- **Affiliation disclaimer**, in `README.md` above the fold and in full in
  `NOTICE`: no connection to the SEC, and `audit` here is not a financial statement
  audit. Adding it surfaced that `NOTICE` had been copied from the consulting
  vertical with only its first line changed -- so it described that package and
  denied that anything named here is real, while the evidence names real
  registrants. Rewritten, and pinned by a test that cross-checks it against the
  evidence.

- Reads a period declaration and a capture, pairs them, and checks the
  balance-sheet identity through `arbiter-engine`.
- Both taxonomies: the total is `LiabilitiesAndStockholdersEquity` under US GAAP
  and `EquityAndLiabilities` under IFRS.
- The agreement is declared on both sides, so the pattern of findings says which
  number is the odd one out, or says that it cannot be said.
- Tolerance is declared per period and never defaulted.
- Evidence derived from SEC 2025q1: 6,231 filings, 6,045 checked, six that do not
  balance.
- The verification battery: thirteen legs, eleven green, `attest` and `tool`
  reported NOT BUILT rather than dropped.
- `battery/probe_pin.py` measures both floors. `arbiter-engine` is 0.1.12, one
  release below the number this was built against: on 0.1.11 an agreement block
  with no tolerance is answered from a 5% relative fallback instead of declined,
  which would report every fault in this corpus as agreement. `presence-audit` is
  `>=0.1.13,<0.3`: 0.1.13 is the first release whose findings take `point`, which
  this package writes, and 0.1.12 fails the suite; 0.2.0, which removes the old
  names, was run against before the ceiling admitted it. The floor was 0.1.7 until
  then, a release this suite could not demonstrate.
- Registered as a `presence-audit` vertical: all twelve required vocabulary
  members and all three optional ones, with the core's conformance kit as a
  battery leg. The `presence` verb is the core's three-valued answer, and its
  counts reconcile exactly with the feeder's own.
- `FINDINGS.md` records eleven things that did not survive building it. The first
  is the one the conformance kit says it cannot produce: the protocol has no room
  for a point that exists in more than one reporting unit. Filed upstream as
  `presence-audit` #13, with a reproduction showing the verdict changes with input
  order and a prototype that leaves that core's suite unchanged.
