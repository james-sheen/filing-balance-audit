# What did not survive building this

The family convention: the report of what contact with a real corpus and a real
engine refuted. Everything below was found by running something, and the order is
roughly worst first.

**The numbers are positions, not names.** They renumber when something is
inserted -- as they did, colliding, the first time two entries went in at the
top. Nothing cites them; cite an entry by what it says.

## 1. A private path shipped in a public package, and hid a worse defect behind it

`tests/conftest.py` and `battery/run_battery.py` both carried an absolute path to
the author's own checkout of the engine as its fallback location -- one machine's
directory layout, in a package meant to be installed by strangers. The path is
described rather than quoted here, because a document explaining that a leak was
removed is a place the leak is very easily re-introduced, and the shared hygiene
sweep caught exactly that on the first run against this tree. Found by
scanning for internal markers before answering a question about IP, not by any
check in the suite.

Removing it exposed the defect it had been masking. With no engine installed and
no path to one, `pytest` reported `Interrupted: 1 error during collection` and ran
**nothing** -- because `test_the_engine_this_package_pins.py` imported the engine
at module scope. So on a machine with no engine, the tests that exist to prove
Stage 1 needs no engine could not run. The hardcoded path had been supplying an
engine on the only machine anybody had tried it on, so the suite never reached
that state.

The module-level import was itself a deliberate choice over `importorskip`, for a
good reason -- a skip is a green run about coverage that did not happen, and the
pin probe reads this suite as its oracle. It was the right rule implemented at the
wrong scope. The import is now inside the tests: without an engine they FAIL by
name and the other 72 still run.

## 2. The legal notice described a different package, and denied what was true

`NOTICE` is the one file a reader opens to find out what is true about provenance.
This package's was copied from the consulting vertical and only its FIRST LINE was
changed, so it went on describing *the deliverables a statement of work says should
exist* -- and it asserted, in capitals, that **no statement of work, engagement,
client or consultant named anywhere here is real, and every example will say so on
its face.**

The evidence in this repository names real registrants and reports real
discrepancies in real published balance sheets. The legal notice said the opposite
of the truth about the one subject it exists to be believed on. Its
`NO REDISTRIBUTED THIRD-PARTY CONTENT` heading was false too: `evidence/` is
derived from SEC data.

Nothing could have caught it. No code imports `NOTICE`, the rename swept the
distribution name through every file and left the body untouched because the body
never mentioned the old name, and a reader checking that the notice *existed* would
have found it. It was found by being asked to add an affiliation disclaimer to a
file that turned out to need a rewrite.

**Closed** by rewriting it for this package -- the affiliation denial, the
separation from a regulated audit, the derived-not-redistributed provenance, and
the realness of the evidence stated rather than denied -- and by
`tests/test_the_notice_describes_this_package.py`, which cross-checks the notice
against the evidence rather than grepping for a sentence: the declaration carries
over a thousand real registrant numbers, so the notice is held to that.

Four of its six assertions fail against the notice as it actually shipped, which is
the control that matters. Two of them were wrong on the first attempt, both in the
same way: `engagement` was a forbidden word that occurs innocently in this
package's own *a regulated engagement performed by licensed auditors*, and
`licensed auditors` was reported absent because it is wrapped across two lines.
Phrase assertions now run against whitespace-normalised text and the forbidden list
holds only unambiguous markers.

**The siblings were checked and every one of their notices describes its own
package.** This was not a family pattern; it was one copy with one line changed.

## 3. The protocol has no room for a point that exists in more than one unit

The result the conformance kit says it cannot give you, so it is first.

That kit proves nothing reached past the contract, in either direction, and it
says plainly what it cannot prove: that the contract is SUFFICIENT. A stand-in
written from the protocol can only discover that something exceeded the
document, never that the document is missing something a real domain needs. It
asks a real vertical with real data to find that, and this is what one found.

**A filing reporting in two currencies is two balance sheets.** Each has its own
identity, and comparing across them is the defect that made the first
measurement of this corpus report a residual of 369 billion. Thirty-eight
filings in one quarter do it. But the core indexes `CapturedPoint` by name, and
the declaration has one point per filing, so a second point at the same address
is not a second reading -- it is a collision, and one of the two wins silently.

So this vertical answers the core per filing and pushes the per-unit detail into
`capture_findings`, which works and is honest but loses something real: the
core's three-valued answer cannot distinguish *reading in USD and incomplete in
CNY* from *reading*. That filing is counted as reading, and the gap is reported
in a finding beside the count rather than in it.

**What fit, which is most of it, and is worth saying.** `Capture.errors` takes
the values that would not parse exactly. `CapturedPoint.units` is the reporting
currency with nothing bent to fit. `peer_groups` pairs an amendment with its
original -- one registrant filed an S-1 and an S-1/A in one quarter, both
carrying the same thousand-dollar discrepancy, which is how the fault is shown to
be in the statement rather than in one transcription of it. The one member this
domain could not answer honestly is the one above.

**Filed upstream as `james-sheen/presence-audit` #13**, with the reproduction and
a prototyped remedy rather than a complaint.

What went with it is worth recording, because it is stronger than the finding as
first written. Stated as *the protocol has no room for this*, it is a modelling
limitation somebody can reasonably decline. Measured, it is a correctness defect:
the same two captured points in the other order produce a different verdict --
clean one way, a regression the other -- and nothing in either report says a point
was discarded. The order-dependence was there to be found the whole time and was
not looked for until the ask needed a reproduction.

The ask carries two proposals. The small one makes the discard visible with a
`duplicate_address` finding; prototyped against 0.1.7 it leaves that core's suite
at 290 passed and 1 skipped, identical to baseline, with a control showing a
single-point capture produces no such finding. The larger one -- a declared point
matching the SET at its address, with a third `partially_reading` state -- is
sketched and explicitly left as the maintainer's design decision, because it
changes `Match` and two other verticals are already on that contract.

## 4. A sentinel compared equal to itself, and was read as agreement

`captures_comparable` decides whether two captures support this domain's
per-point comparisons. The first version compared their periods directly, and
two captures that both carry NO period compare `None == None` and come back
TRUE.

The conformance kit drove it with a foreign capture that names no period at all,
and the member said *yes, comparable* about two objects this domain cannot
identify. It reported no problem, correctly -- nothing had reached past the
protocol, which is all that kit claims to check -- so the wrong answer was
arrived at entirely within the contract.

**Closed** by requiring both periods to be present before comparing them, with a
parametrised test over the four cases. The lesson is narrower than the usual one
about `None`: the defect was not a missing attribute, it was a default that
happened to satisfy the comparison it was fed to.

## 5. The pin probe installed release after release and tested the working tree

Worst of the session, because it produced two complete measurements that were
both meaningless and both looked fine.

`battery/probe_pin.py` builds one environment per release, installs that release
and this package into it, and runs the suite from a directory that is not the
repository -- precisely so the INSTALLED copies are what get exercised. Its own
docstring says so. Then `tests/conftest.py`, which prepends `src/` and the engine
clone to `sys.path` so a development tree works out of the box, defeated it from
the inside. Every environment imported the working tree.

**The version check anybody would write would have agreed.**
`arbiter_engine.__version__` reads its own installed metadata, so the clone's
code reported the number of the release it was standing in front of. Asked
directly, the environment said `0.1.7`. What it was running was HEAD.

Two sweeps were burned. The first, against a suite with no engine-behaviour
assertions, reported every release down to 0.1.0 passing -- a floor eleven
releases too high. The second, after those assertions were added, reported a
floor at 0.1.8. Neither number measured anything.

**It took two more attempts to close, and both are the same lesson again.**

The first fix did not apply. The edit was one statement in a script that failed
to compile, so nothing in it ran -- and the checks afterwards were all things
that pass whether or not the fix landed, in a development tree where nothing is
installed. A green that cannot distinguish the two states is not evidence about
either.

The second fix was a guard in the wrong process. The probe gained a preflight
resolving where `arbiter_engine` and `filing_balance_audit` actually import from,
failing the release if either is outside `site-packages`. It runs `python -c`,
which never loads `conftest.py`, so it reported a clean environment and pytest
then shadowed it anyway. A guard has to run where the thing it guards runs.

**Closed** three ways. The conftest prefers what is installed and falls back to
the tree only where the import fails. The probe keeps its preflight, which is now
a true statement because nothing defeats it from inside. And
`test_conftest_does_not_shadow_a_module_that_is_already_installed` asserts the
guard from inside pytest, with a control proving it can still insert a fallback
that is genuinely needed -- so the one thing no external check could see is
checked by the suite that was being fooled.

**And then a second pin broke both halves of it.** Registering the vocabulary
added `presence-audit` as a required dependency, so the probe had two ranges to
walk instead of one, and two things written for a single subject failed at once.

The preflight named both dependencies by hand, so probing the core failed on an
engine that environment had no reason to hold -- a guard written for one subject,
reporting confidently about another. It now resolves the DIST UNDER TEST plus
this package, derived from the pin being walked.

The below-floor leg was worse, because pip was right. Installing
`presence-audit==0.1.6` beside a package declaring `presence-audit>=0.1.7` is a
`ResolutionImpossible`, and the probe reported it as a failing release. It is not
a failing release; it is the probe asking the resolver to approve of a floor
violation, which is the one thing a below-floor leg exists to commit. Fixed by
installing the package and everything it needs first, then forcing the exact
release on top with `--no-deps`. The resolver is told to stand down rather than
consulted.

## 6. A floor this suite cannot reach, held by a sibling's measurement

Registering the vocabulary added a second pinned range, and the probe measured it:
`presence-audit` 0.1.7 and 0.1.6 both pass, 0.1.5 fails. So nothing in this
repository measured the declared floor of 0.1.7, and the obvious move was to drop
it to 0.1.6.

It stays at 0.1.7, and the reason is a measurement somebody else took. The
consulting vertical in this family probed the same range and **0.1.6 fails its
suite**, on exit-contract behaviour this package does not exercise. Lowering to
what this oracle reaches would claim support for a release a sibling has already
measured broken -- and the only thing standing between those two positions is
which suite happened to ask.

That is a floor from a specification rather than a guess, which is what the method
asks for. It is simply not a specification this repository produced, and the pin
says so in a comment rather than looking like a number somebody measured here.

**The probe was reporting it wrongly, and that is the defect.** Its verdict had
two outcomes where there are three. `floor-holds` is only true when the release
IMMEDIATELY below the floor fails; where something below it passes and a lower one
fails, the floor is higher than anything measured requires. The first version
printed *the floor is the first release above it that does not fail* about a floor
two releases up -- a precise sentence, confidently wrong, about the one claim this
probe exists to make. There is now a third verdict for it.

## 7. Adding tests moved the measured floor, which is what a probe's reach means

The first sweep found nothing failing below the floor, down to the earliest
release. That reads as *the floor is far too high*. It was also a suite that
never asked the engine any of the questions this package depends on -- whether a
zero absolute tolerance is honoured, whether an agreement block with no tolerance
declines rather than guessing, whether both declared directions fire.

Those assertions lived in the battery's `engine` leg, which runs once against
whichever engine is installed. The pin probe's oracle is the SUITE, so a
behaviour asserted only in the battery is invisible to every release it walks.

**Closed** by `tests/test_the_engine_this_package_pins.py`. A range is exercised
only as far as its oracle reaches, and moving five assertions across that line
changed the answer -- from *nothing below fails* to a boundary at a named
release, once the shadowing above was also fixed.

The boundary is real and it is the one that would have been silent. On 0.1.11 an
agreement block carrying no tolerance still ANSWERS, from a global 5% relative
fallback; from 0.1.12 it declines and says why. This package's subject is a
one-dollar discrepancy against a ninety-four-million-dollar balance sheet, six
decimal places inside any relative margin anybody would pick -- so on 0.1.11
every real fault in the corpus is reported as agreement, by an engine that looks
like it is working. **The declared floor was 0.1.13 and the measured one is
0.1.12**; the old number came from a design note naming the release this was
built against.

## 8. The design's own second route re-imported a gap the design had measured

The plan for this package said, in writing, that a balance sheet gives two routes
to one number and that comparing both is what localises an error. It also said, in
the same measurement, that `Liabilities` + `StockholdersEquity` agrees with
`Assets` on 68.47% of filings, because temporary equity, redeemable preferred and
noncontrolling interest are tagged outside both.

The first feeder fed the components whenever the tags were present. Over the whole
of 2025q1 it produced **667 findings across 663 filings**, against a corpus holding
six. Every extra one had assets and the total agreeing *exactly* and the
components disagreeing with both.

The two sentences were four paragraphs apart in one document and were written by
the same pass. Measuring a limit does not stop you building on the other side of
it; the measurement only helps if something reads it back.

**Closed** by using the components as a second route only where they reconcile to
one side of the identity, and declining -- counted, printed, never scored -- where
they reconcile to neither. 658 filings in the quarter land there.

## 9. The denominator did not add up, and every individual answer was right

The buckets recording what was and was not fed are per READING. A filing that
reports in two currencies is two balance sheets with two identities, so it can be
checked in one and incomplete in the other, and appear in two buckets. Summing the
bucket lengths gave 6,270 against a declared 6,231.

Nothing about any single filing was wrong. The audit was wrong about how many
filings there were, which is the one error that cannot be found by checking the
findings. Found by the test that asserts the denominator adds up, which existed
only because the test was written to assert exactly that.

**Closed** by `Fed.disposition()`, one outcome per declared filing, with `checked`
winning where any unit was checkable. 6,045 filings checked across 6,083 readings:
38 file in more than one currency.

## 10. The engine reports one disagreement where two were declared

`agrees_with` names peers on one indicator, and the engine names a finding
`redundant_disagreement:<indicator>`. Two peers on one indicator therefore produce
two findings with one name, and the envelope carries one. Measured on a filing
whose three readings all differ: one finding, naming the first peer, the second
disagreement invisible.

Not a defect in the engine so much as a consequence of the naming, but it silently
defeats the obvious model. **Worked around** by declaring the agreement on both
sides, which yields two distinct names -- and the pattern of which fired is the
localisation this package reports.

## 11. The envelope drops the evidence, so the finding cannot say how much

The engine's `Problem` carries `peer`, `value`, `peer_value` and the difference.
The envelope's findings carry `entity_id`, `problem_type`, `axiom`, `severity` and
`reason`, and no evidence at all. A reader told only *these two disagree*, about
money, has been told almost nothing: one dollar and one billion read identically.

**Worked around** by computing the residual in this package and printing it. Worth
sending upstream: every consumer of a CONSISTENCY finding has to do this.

## 12. The reader invented a 369-billion discrepancy three times before it worked

Recorded in `../docs/arbiter/tools/sec_identity_probe.py`, because it happened
during the measurement rather than during the build, and because the first run
reported 23 unbalanced filings where six is the answer.

The three: a tag read without its unit, and the corpus carries tags at one instant
in 22 currencies; a repeated `(filing, tag)` row resolved by file order; and
dimensional breakdowns summed into the total they break down. The tell was the
magnitude -- a balance sheet out by 369 billion is a unit bug, not a fraud.

The one worth keeping is the fourth, found later: **a per-form completion rate of
17.4% on 40-F filings looked like a fact about 40-F filings.** It was a fact about
a reader that knew one taxonomy. The honest form of *which forms carry a balance
sheet* is *which forms carry one this reader can see*.

## 13. The command line had two refusal contracts

One path raised `SystemExit`, every other returned an exit code, so `main()` ended
the process on one input and returned on the rest. A caller embedding it -- the
suite included -- saw two contracts from one function. Found by the first test that
called `main` with a missing file.

## 14. Six thousand entities in one session trips the engine's own rate warning

`FireFrequencyTracker` warns at 100 fires per hour for an (axiom, type) pair, and a
quarter's worth of filings declines CONSISTENCY far more often than that on the
components arm. It is a warning and not an error, and it floods stderr. Noted
rather than worked around: the engine is right that the rate is unusual, and a
bridge feeding a whole quarter is an unusual consumer.

## 15. Hashing the labels would have changed nothing, because the rows were sorted

The evidence shipped with positional labels: sort the quarter's accession numbers,
number them. That was disclosed as pseudonymity and not anonymity, which was
accurate, and then it was replaced with a keyed hash so the mapping could not be
recovered at all.

The replacement was very nearly cosmetic. Both files emitted their rows in order
of the REAL identifier -- `sorted(subs.items())` on the declaration, `sorted(readings.items())`
on the capture -- because that was the natural way to write it and nothing about
labelling had ever depended on it. Relabelling under a secret salt while leaving
that alone publishes the positional mapping anyway: row 1 is the first filing in
sorted order, row 2 the second, for all 6,231. The identifiers would have looked
irreversible and the file would have carried the same information in its shape.

Emitting by label fixes it, and the fix is one `key=` argument. What is worth
recording is that the defect lives in a line that has nothing to do with the
feature: a reviewer reading the hashing code sees a correct HMAC under a good
salt, and the leak is two functions away in an argument nobody would think to
question. **A privacy change is not confined to the code that does the privacy.**

Measured after the change: the correlation between a row's new position and its
old positional index is -0.015, and 992 of the first 2,000 adjacent pairs descend.
Before it, both numbers would have been the maximum. `test_rows_are_ordered_by_label`
is the guard, and it is the assertion in that file most likely to be undone by
somebody tidying a sort key.

## 16. The labels were never the way to identify these filings

93.07% of the rows in this evidence -- 5,805 of 6,237 -- carry a combination of
reported values that is unique within the quarter. The source is public. So a
reader who wants to know who filed a row joins on the figures and never looks at
the identifier at all, whatever it says.

This was measured by accident, checking something else: joining the pre-hash and
post-hash evidence to confirm the ordering fix had worked. The join was written on
the figures because that was the only key the two files still shared, and it
matched 5,805 rows across two independently-labelled derivations. The check
answered its own question and incidentally measured the thing the labels were
supposed to be protecting.

It does not make the hashing pointless. Not publishing a list of named companies
beside their arithmetic errors is a real difference from publishing one, and that
is the whole claim. But it bounds what the claim can be, and the bound belongs in
`NOTICE` rather than in a findings file, which is where it now is: **the filers
cannot be recovered from what is published here, and that is not the same as their
being unidentifiable.** The only way to close the second channel is to stop
reporting the figures exactly, and the figures reported exactly are the package.

## 17. The evidence was anonymised and the test names were not

Four tests in `test_localisation.py` were named after the registrants they were
about: the company name in the function name, that company's exact reported
figures three lines below, in a test asserting their balance sheet does not
balance. They had been there since the first commit.

Anonymising the evidence did not touch them and was never going to. Everything in
that change -- the hashing, the salt, the row ordering, the notice -- is about
`id` and `cik`, because those are the fields that look like identifiers. A
function name does not look like an identifier. It looks like a name the author
chose, which is exactly what it was.

It is also a stronger identification than anything the labels ever leaked. The
label channel required holding the 128 MB source and sorting it; this one required
reading the file. The repository spent a change closing the harder channel while
the easier one sat in a test suite, and the only reason it surfaced is that the
renamed functions were being read for an unrelated reason.

**The leg that now checks it got its predicate wrong twice.** Sweeping for filer
names alone reported 67 hits over the four, because thousands of registrants are
named after ordinary words; filtering to non-dictionary words would have dropped
three of the four, whose names are ordinary English. What identifies is a filer's
name in the same file as a figure only that filer reported -- and with that
predicate, over 5,667 filers, the tree is clean and a single reintroduced name is
found by name and file.

**And the comment explaining all this was itself a hit.** Its first draft named
three of the companies and quoted one of their figures, to say why the simpler
predicate failed, so the leg went red on the paragraph documenting the leg. The
same lesson as entry 2 in a different costume: prose about a thing is made of the
thing. Describe the retired name, never quote it.

## What is not claimed

**This section described four gaps and all four have since been closed**, which
is the reason it is being rewritten rather than appended to: prose describing an
absence reads as current long after the absence is gone, and the first version of
this paragraph said *no battery, no pin probe, no conformance kit, and no
registration with the shared core's vocabulary*. All four now exist.

What is genuinely open:

- The `attest` and `tool` legs have no surface here and are reported NOT BUILT.
- The multi-unit gap is filed upstream as `presence-audit` #13 and is open there.
  Nothing in this package waits on it: `Capture.points` yields one point per
  filing so the addresses are unique by construction, and a test asserts that
  over a real quarter carrying 39 filings that would otherwise trip it.
- The `presence-audit` floor is higher than this suite can demonstrate, and stays
  for a sibling's measurement. That is recorded in `pyproject.toml` beside the pin
  rather than only here.
- No repository, no release. This is a local tree.
