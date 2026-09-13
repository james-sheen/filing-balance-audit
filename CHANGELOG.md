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
- **The evidence ships anonymised.** Every figure is as filed and the six
  discrepancies are real; the filers are not named. `id` and `cik` carry
  `HMAC-SHA256(salt, domain + identifier)` under a salt that is not committed and
  has no default, so the mapping cannot be recovered from anything published here.
  `battery/fetch_sec_quarter.py --named` still emits the real form, from the
  source, for local use.

  The labels were briefly positional. That was disclosed as pseudonymity and not
  anonymity, which was accurate, and replacing it turned up two things worth the
  entry. Rows were emitted in order of the real accession number, so relabelling
  alone would have republished the positional mapping in the row order; they are
  now emitted by label. And the figures are themselves a join key on 93% of rows,
  which no labelling scheme touches -- stated in `NOTICE`, because an artefact
  claiming more privacy than it has is worse than one claiming less.

  The cost is byte-for-byte reproducibility: a stranger derives the same corpus
  under different labels. `--verify` replaces the byte comparison with an
  up-to-relabelling one over the figures, forms, units and registrant groupings,
  and the battery's `live` leg now runs it under a salt it invents -- proving a
  reader without the key can reproduce the corpus, which the old byte comparison
  never claimed.
- **Four tests were named after the filers they were about**, beside those
  filers' exact figures, since the first commit. Anonymising the evidence did not
  touch them: a function name does not look like an identifier. Renamed, and the
  battery grew a `names` leg that reports any filer named in this tree beside a
  figure only that filer reported.
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
  which would report every fault in this corpus as agreement. `presence-audit`
  stays at 0.1.7, which this suite cannot demonstrate and a sibling's can -- 0.1.6
  fails the consulting vertical on behaviour this package does not exercise.
- Registered as a `presence-audit` vertical: all twelve required vocabulary
  members and all three optional ones, with the core's conformance kit as a
  battery leg. The `presence` verb is the core's three-valued answer, and its
  counts reconcile exactly with the feeder's own.
- `FINDINGS.md` records eleven things that did not survive building it. The first
  is the one the conformance kit says it cannot produce: the protocol has no room
  for a point that exists in more than one reporting unit. Filed upstream as
  `presence-audit` #13, with a reproduction showing the verdict changes with input
  order and a prototype that leaves that core's suite unchanged.
