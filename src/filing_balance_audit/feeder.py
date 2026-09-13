"""Pair a declaration with a capture, and feed the engine what survives.

WHY THE AGREEMENT IS DECLARED IN BOTH DIRECTIONS, which is the whole design and
was measured rather than reasoned.

A balance sheet gives two routes to one number: the total the filer tagged, and
the sum of the parts they tagged. When all three disagree, knowing WHICH is wrong
is the useful half of the answer, and the obvious model -- one indicator naming
both peers in `agrees_with` -- cannot give it. The engine names a finding
`redundant_disagreement:<indicator>`, so two peers on one indicator produce two
findings with one name, and the envelope carries one. Measured on a filing whose
three numbers all differ: one finding, naming the first peer, the second
disagreement invisible.

Declaring the relation on BOTH SIDES gives two distinct names, and the PATTERN of
which fired is the localisation:

    assets disagrees with the total, parts agrees with assets  -> the TOTAL is odd
    assets disagrees with the total, parts disagrees with assets -> ASSETS is odd

Both shapes are in the real corpus. One 10-Q files parts that sum to its assets
and a total one dollar below both; one 10-K files parts that sum to its total and
assets one dollar below. One arm cannot tell them apart.

Described and not named, here and below. The evidence is labelled with a keyed
hash under a salt that is not published, so a label in a docstring names a filing
only for whoever holds that one salt -- and reads like a durable reference to
everybody else.

THE SECOND ROUTE IS NOT ALWAYS A ROUTE, AND THAT WAS FOUND BY RUNNING IT. The
first version of this fed the parts sum whenever the tags were present. Against
the whole of 2025q1 it produced 667 findings over 663 filings, where the corpus
holds six. Every one of the extra had `assets` and the total agreeing exactly and
the parts disagreeing with both, because `Liabilities` plus `StockholdersEquity`
is not the whole of the credit side: temporary equity, redeemable preferred and
noncontrolling interest are tagged separately and sit in the total without
appearing in either part. Measured directly, that route holds on 68.5% of filings
and the noncontrolling variant on 81.1% -- both of which had already been measured
and written down before this fed them anyway.

So the parts are used as a second route ONLY when they reconcile to one side of
the identity. Parts that match neither are incomplete rather than wrong, and an
incomplete reading is declined and named, never scored. That is the engine's own
posture about short input, applied one layer out.

WHAT THE ENVELOPE DOES NOT CARRY. The engine's finding says two readings disagree
and does not say by how much -- `evidence` is absent from the envelope's findings,
measured. So the residual is computed here and reported by this package. A reader
told only *these disagree*, about money, has been told almost nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import Decimal
from typing import Any, Mapping, Sequence

from .declaration import ASSET_TAG, PART_GROUPS, TOTAL_TAGS

#: Above this magnitude a `Decimal` of whole reporting units stops surviving the
#: round trip through the engine's floating-point comparison, and a one-unit
#: discrepancy could be erased or invented by the conversion alone.
#:
#: The engine takes floats and this package's subject is money, so the boundary
#: is asserted rather than assumed. 2**53 is where consecutive integers stop
#: being distinguishable. The largest balance sheet in the measured quarter is
#: about four trillion, which is three orders of magnitude below it -- but a
#: reading that crosses it is refused rather than fed, because the failure it
#: would produce is a discrepancy that is not there.
EXACT_INTEGER_LIMIT = Decimal(2) ** 53


class FeedError(RuntimeError):
    """The engine could not be given this run, and why."""


@dataclass(frozen=True)
class Resolved:
    """One filing's identity, in one unit, as far as the capture supplies it."""

    name: str
    unit: str
    assets: Decimal | None = None
    total: Decimal | None = None
    total_tag: str | None = None
    parts: Decimal | None = None
    part_tags: tuple[str, ...] = ()

    @property
    def checkable(self) -> bool:
        """Both sides of the primary identity are present.

        The parts route is a bonus and not a requirement: it is computable on
        fewer filings than the total and, where computable, is not reliably the
        same number. Requiring it would discard most of the corpus to gain a
        second opinion that is wrong a third of the time.
        """
        return self.assets is not None and self.total is not None

    def reconciles(self, tolerance: Decimal) -> str | None:
        """Which side the parts sum agrees with: `total`, `assets`, or neither.

        `None` means no parts were tagged. `"neither"` means they were, and they
        are not a second reading of this balance sheet -- the credit side has
        members outside the two tags summed here. Distinguishing those two from
        each other, and both from a usable route, is what stopped this package
        reporting 663 filings as unbalanced when six are.
        """
        if self.parts is None:
            return None
        if self.total is not None and abs(self.parts - self.total) <= tolerance:
            return "total"
        if self.assets is not None and abs(self.parts - self.assets) <= tolerance:
            return "assets"
        return "neither"

    def residuals(self) -> dict[str, Decimal]:
        out: dict[str, Decimal] = {}
        if self.assets is not None and self.total is not None:
            out["assets_vs_total"] = self.assets - self.total
        if self.assets is not None and self.parts is not None:
            out["parts_vs_assets"] = self.parts - self.assets
        return out


@dataclass
class Fed:
    """What went to the engine, and what did not, with the reason."""

    resolved: list[Resolved] = field(default_factory=list)
    no_reading: list[str] = field(default_factory=list)
    incomplete: list[tuple[str, str]] = field(default_factory=list)
    excluded: list[str] = field(default_factory=list)
    over_limit: list[tuple[str, str]] = field(default_factory=list)
    #: Filings whose parts were tagged and reconcile to neither side, so the
    #: second route was declined. Counted and reported: it is a fact about the
    #: shape of the balance sheet, not about whether it balances.
    parts_incomplete: list[str] = field(default_factory=list)

    @property
    def unfed(self) -> tuple[str, ...]:
        return tuple(sorted({*self.no_reading,
                             *(n for n, _ in self.incomplete),
                             *(n for n, _ in self.over_limit)}))

    def disposition(self) -> dict[str, str]:
        """One outcome per DECLARED FILING, which is the audit's denominator.

        THE BUCKETS ABOVE ARE PER READING AND A FILING CAN HAVE SEVERAL. Six
        filings in one real quarter report in two currencies, and each currency
        is its own balance sheet with its own identity -- so a filing can be
        checked in one and incomplete in the other, and appear in two buckets.
        Adding the bucket lengths then over-counts the population, which is how
        an audit ends up right about every filing and wrong about how many there
        were. Caught by the test that asserts the denominator adds up.

        `checked` wins where any unit was checkable: the audit did reach that
        filing. The unit that could not be read is still in `incomplete` and is
        still printed.
        """
        out: dict[str, str] = {}
        for name in self.excluded:
            out[name] = "excluded"
        for name in self.no_reading:
            out.setdefault(name, "no_reading")
        for name, _ in self.over_limit:
            out.setdefault(name, "over_limit")
        for name, _ in self.incomplete:
            out.setdefault(name, "incomplete")
        for resolved in self.resolved:
            out[resolved.name] = "checked"          # wins over any other bucket
        return out


def resolve(reading: Any) -> Resolved:
    """Read one capture reading into the identity's three numbers."""
    values = reading.values
    total = total_tag = None
    for tag in TOTAL_TAGS:
        if tag in values:
            total, total_tag = values[tag], tag
            break
    parts = part_tags = None
    for group in PART_GROUPS:
        if all(tag in values for tag in group):
            parts, part_tags = sum(values[tag] for tag in group), group
            break
    return Resolved(name=reading.name, unit=reading.unit,
                    assets=values.get(ASSET_TAG), total=total, total_tag=total_tag,
                    parts=parts, part_tags=tuple(part_tags or ()))


def plan(period: Any, capture: Any) -> Fed:
    """Decide what the engine can be asked about, and record the rest.

    Every declared filing lands in exactly one bucket, and the buckets are
    reported. A filing that is declared and has no reading is a different fact
    from one whose reading is missing a side, and both are different from one
    counted out -- and none of the three is *balanced*.
    """
    fed, readings = Fed(), capture.by_name
    for point in period.points:
        if point.disabled:
            fed.excluded.append(point.name)
            continue
        found = readings.get(point.name)
        if not found:
            fed.no_reading.append(point.name)
            continue
        kept = False
        for reading in found:
            resolved = resolve(reading)
            if not resolved.checkable:
                missing = "assets" if resolved.assets is None else "a balance-sheet total"
                fed.incomplete.append((point.name, f"{reading.unit}: no {missing}"))
                continue
            too_big = [n for n, v in (("assets", resolved.assets),
                                      ("total", resolved.total),
                                      ("parts", resolved.parts))
                       if v is not None and abs(v) >= EXACT_INTEGER_LIMIT]
            if too_big:
                fed.over_limit.append(
                    (point.name, f"{reading.unit}: {', '.join(too_big)} exceeds the "
                                 f"magnitude at which whole units survive the engine's "
                                 f"comparison"))
                continue
            fed.resolved.append(resolved)
            kept = True
        if not kept and not any(n == point.name for n, _ in fed.incomplete) \
                and not any(n == point.name for n, _ in fed.over_limit):
            fed.no_reading.append(point.name)
    return fed


def model_text(period: Any) -> str:
    """The domain model, carrying the tolerance the declaration published.

    Generated rather than shipped as a file, because the tolerance is the one
    number in it that the period decides and a static model would have to hard
    code it -- which is exactly the guessed default the declaration refuses.
    """
    tolerance = period.tolerance_absolute
    return f"""domain:
  id: filing_balance
  name: "Balance-sheet identity, one entity per filing per reporting unit"
  entity_types: [Filing]
  indicators:
    Filing:
      - name: assets
        type: NUMERIC
        axioms: [CONSISTENCY]
        consistency:
          agrees_with: [balance_sheet_total]
          tolerance_absolute: {tolerance}
      - name: parts_sum
        type: NUMERIC
        axioms: [CONSISTENCY]
        consistency:
          agrees_with: [assets]
          tolerance_absolute: {tolerance}
      - name: balance_sheet_total
        type: NUMERIC
"""


@dataclass
class Run:
    envelope: Mapping[str, Any]
    fed: Fed
    residuals: Mapping[str, Mapping[str, Decimal]]


def entity_id(resolved: Resolved) -> str:
    """One entity per filing PER UNIT.

    A filing reporting in two currencies is two balance sheets and two identities.
    Collapsing them onto one entity is the cross-currency comparison this package
    exists to avoid, reintroduced at the last step.
    """
    return f"{resolved.name}::{resolved.unit}"


def run(period: Any, capture: Any) -> Run:
    """Feed the engine and return its envelope beside a record of what went in.

    The envelope's `not_checked` is as much of the answer as its `findings`: an
    arm that declined because a filing reported no total is a different fact from
    one that found nothing, and only the first is about the filing.
    """
    from arbiter_engine.api import EngineSession, check      # deferred

    fed = plan(period, capture)
    session = EngineSession()
    # Every way a model can fail to load arrives as `FeedError`, so the CLI's
    # exception table stays in one place. `load_domain` raises a bare `ValueError`
    # for a non-mapping and `yaml.YAMLError` does not subclass it, so an
    # unparseable model would otherwise escape as a traceback and exit 1 -- which
    # this package's contract reads as FINDINGS rather than as a document it
    # could not read.
    try:
        session.load_model(model_text(period))
    except Exception as problem:                             # noqa: BLE001
        raise FeedError(f"the engine would not load this model: {problem}") from problem

    residuals = {}
    for resolved in fed.resolved:
        properties: dict[str, float] = {
            "assets": float(resolved.assets),
            "balance_sheet_total": float(resolved.total),
        }
        # The second route is fed only where it IS a second reading of this
        # balance sheet. Where it reconciles to neither side it is not one, and
        # feeding it would score a finding against the tagging convention rather
        # than against the filing.
        where = resolved.reconciles(Decimal(str(period.tolerance_absolute)))
        if where == "neither":
            fed.parts_incomplete.append(entity_id(resolved))
        elif where is not None:
            properties["parts_sum"] = float(resolved.parts)
        session.add_entity(entity_id(resolved), "Filing", properties=properties)
        residuals[entity_id(resolved)] = resolved.residuals()

    envelope = check(session).to_dict()
    return Run(envelope=envelope, fed=fed, residuals=residuals)


#: What the pattern of fired findings says about which number is wrong.
#:
#: Derived from the engine's behaviour, measured: `assets` carries the agreement
#: with the total and `parts_sum` carries the agreement with assets, so which of
#: the two names appears is the signal. Each answer below was checked against a
#: real filing in 2025q1 rather than reasoned about.
ASSETS_ARM = "redundant_disagreement:assets"
PARTS_ARM = "redundant_disagreement:parts_sum"


def localise(kinds: Sequence[str], resolved: Resolved,
             tolerance: Decimal) -> str:
    """Say which number is the odd one out, or say that it cannot be said.

    The third answer is not a hedge. A filing whose three readings all differ
    has no majority and naming one would be a guess printed as a result --
    one 10-Q in the corpus files 35,126 / 35,128 / 35,129 and nothing in the
    filing says which was meant.
    """
    if ASSETS_ARM not in kinds:
        return "the identity holds"
    if PARTS_ARM in kinds:
        # Parts agree with the total and assets differs from both.
        return "the assets figure is the odd one out"
    where = resolved.reconciles(tolerance)
    if where == "assets":
        return "the balance-sheet total is the odd one out"
    if where == "neither":
        return ("all three readings differ, so which is wrong cannot be read "
                "off this filing")
    return ("no components were tagged, so which side is wrong cannot be read "
            "off this filing")
