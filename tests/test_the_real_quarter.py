"""The corpus is the fixture. Every assertion here is about 2025q1 as filed."""

from filing_balance_audit import exit_contract, feeder

#: The filings in 2025q1 whose balance sheet does not balance, and by how much.
#: Established by `docs/arbiter/tools/sec_identity_probe.py` reading the quarterly
#: file directly -- a second reader, not this package -- and reproduced here
#: through the whole pairing path.
UNBALANCED = {
    "F-04814": "1000.0000",     # a filing of registrant R-4708   S-1/A
    "F-04795": "1000.0000",     # a filing of registrant R-4708   S-1
    "F-01901": "500.0000",      # a filing of registrant R-1046     10-Q
    "F-05665": "-2.0000",       # 10-Q, all three readings differ
    "F-03283": "-1.0000",       # 10-K, the components match the total
    "F-03970": "1.0000",        # a filing of registrant R-4689       10-Q
}


def _fired(run):
    out = {}
    for finding in run.envelope.get("findings", []):
        out.setdefault(finding["entity_id"], []).append(finding["problem_type"])
    return out


def test_the_six_real_faults_are_found_and_no_others(real_run):
    fired = _fired(real_run)
    assert {e.split("::")[0] for e in fired} == set(UNBALANCED)


def test_each_residual_is_the_amount_the_second_reader_measured(real_run):
    by_filing = {r.name: r for r in real_run.fed.resolved}
    for adsh, expected in UNBALANCED.items():
        assert str(by_filing[adsh].residuals()["assets_vs_total"]) == expected


def test_the_whole_quarter_is_accounted_for(real_period, real_run):
    """Every declared filing has exactly one disposition, and they add up.

    The first version of this added the bucket lengths and came to 6,270 against
    a declared 6,231. The buckets are per READING and six filings in this quarter
    report in two currencies, so a filing checked in one and incomplete in the
    other was counted twice. An audit can be right about every filing and wrong
    about how many there were, and only the denominator says so.
    """
    disposition = real_run.fed.disposition()
    assert set(disposition) == {p.name for p in real_period.points}
    assert len(disposition) == len(real_period.points) == 6231
    assert sum(1 for v in disposition.values() if v == "checked") == 6045
    assert sum(1 for v in disposition.values() if v == "no_reading") == 33
    assert sum(1 for v in disposition.values() if v == "incomplete") == 153


def test_more_readings_than_filings_because_some_report_in_two_currencies(real_run):
    """6,083 readings across 6,045 filings: 38 file in more than one currency.

    The gap is the reason `disposition` exists, and the reason an entity is one
    filing PER UNIT. Each currency is its own balance sheet with its own
    identity, and comparing across them is the defect that made the first
    measurement of this corpus report a residual of 369 billion.
    """
    checked = [v for v in real_run.fed.disposition().values() if v == "checked"]
    assert len(real_run.fed.resolved) == 6083
    assert len(real_run.fed.resolved) - len(checked) == 38


def test_a_quarter_with_six_unbalanced_filings_exits_one(real_run):
    assert exit_contract.code_for(real_run) == exit_contract.FINDINGS


def test_the_components_route_is_declined_far_more_often_than_it_fires(real_run):
    """The gate this package needed, pinned by the number that forced it.

    Feeding the components whenever they were tagged produced 667 findings over
    663 filings against a corpus holding six. Every extra had assets and the
    total agreeing exactly, with components that reconcile to neither because
    temporary equity and noncontrolling interest are tagged outside both. The
    assertion is the SHAPE -- far more declined than fired -- rather than the
    number, which moves with the quarter.
    """
    assert len(real_run.fed.parts_incomplete) > 100
    fired = _fired(real_run)
    assert len(fired) < len(real_run.fed.parts_incomplete) / 10


def test_no_filing_whose_two_sides_agree_is_reported(real_run):
    fired = _fired(real_run)
    for resolved in real_run.fed.resolved:
        if resolved.assets == resolved.total:
            assert feeder.entity_id(resolved) not in fired


def test_the_core_and_the_feeder_agree_about_the_population(real_period, real_capture,
                                                            real_run):
    """Two independent paths over one quarter, and they have to reconcile.

    The core reaches its answer by pairing a declaration against a capture and
    asking whether each point is reading. The feeder reaches its answer by
    resolving each filing's identity and deciding whether it can be fed. Neither
    consults the other, and they are written from different questions -- so an
    agreement here is a cross-check and not a restatement.

    Exact equality rather than a tolerance. Two counts of one population differ
    for a reason, and *close enough* is how the reason stops being looked for.
    """
    from presence_audit import diff
    from filing_balance_audit.vertical import FilingVocabulary

    counts = diff.compare(real_period, real_capture,
                          vocabulary=FilingVocabulary()).counts()
    disposition = real_run.fed.disposition()
    tally = {state: sum(1 for v in disposition.values() if v == state)
             for state in ("checked", "incomplete", "no_reading")}

    assert counts["reading"] == tally["checked"] == 6045
    assert counts["present_not_reading"] == tally["incomplete"] == 153
    assert counts["declared_absent"] == tally["no_reading"] == 33
    assert counts["declared"] == len(real_period.points) == 6231


def test_the_core_classifies_every_declared_filing(real_period, real_capture):
    """`unrecognised_type` is expected to be zero, and zero is only meaningful
    if the count was taken over a non-empty population."""
    from presence_audit import diff
    from filing_balance_audit.vertical import FilingVocabulary

    counts = diff.compare(real_period, real_capture,
                          vocabulary=FilingVocabulary()).counts()
    assert counts["declared"] > 6000
    assert counts["unrecognised_type"] == 0
