"""A4 repair laws: a refusal must not depend on withheld mass (Macha; fixture scope).

Macha's #481 review of #479 found A4 in this producer (PR #474 @ e7635e79): a cell
with no base-visible mass was refused as malformed (``QExcludedObservationError``)
when its physical total was 0, but as NOT_ESTIMABLE when only withheld molecules
were present, because the ``library_total < 1`` clause ran before the depth check.
The refusal class therefore revealed whether withheld molecules existed.
Noninterference covers refusals as well as emitted bytes.

Every outcome here is compared whole: the exact bytes a holder of one level's
rights may receive (the envelope and every level up to and including theirs), or
the exact refusal class and message. Counterfactuals change only counts the level
may not see, and the physical total moves with them, as it does physically.

Synthetic fixtures only. Nothing here authenticates a source, a feature map, a
query-rights issuer, a physical unit or a donor.
"""
from __future__ import annotations

import json
import random
from copy import deepcopy

import pytest

from scripts.v5.td_unified import q_excluded_depth_v1 as Q

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
WITHHELD = "WITHHELD_BY_EVIDENCE_RIGHTS"
_NOT_ESTIMABLE = ("refused", "QExcludedDepthNotEstimable", "no query-excluded depth remains for this cell")
_COVERING = ("refused", "QExcludedObservationError",
             "library_total must be an exact integer covering every stored count")
_Q_VALUES = (0, 1, 5, 100)
_LADDER = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
    {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
]
_BASE_VARIANTS = ("omitted_measured_zero", "explicit_measured_zero", "structurally_unmeasured",
                  "collision_inside_base")


def _visible_outcome(world, level_id):
    """Everything a holder of ``level_id`` rights may receive, as exact bytes, or the refusal."""
    try:
        result = Q.produce_rights_ladder_observations(**deepcopy(world))
    except Q.QExcludedObservationError as exc:
        return ("refused", type(exc).__name__, str(exc))
    ids = [lv["level_id"] for lv in result["levels"]]
    visible = {**result, "levels": result["levels"][: ids.index(level_id) + 1]}
    return ("view", json.dumps(visible, sort_keys=True, ensure_ascii=False))


def _zero_base_world(variant, q, *, e=0, residual=0):
    """One cell whose base-right addresses hold no molecules. ``residual`` is mass
    inside the physical total that no outside-base address carries (off-ledger or
    base collision mass); ``e`` and ``q`` are the EXT and QUERY counts."""
    states = {"B1": MS, "B2": MS, "E1": MS, "Q1": MS}
    counts = {}
    if variant == "explicit_measured_zero":
        counts.update(B1=0, B2=0)
    elif variant == "structurally_unmeasured":
        states.update(B1=SU, B2=SU)
    elif variant == "collision_inside_base":
        states.update(B2=MCU)
    if e:
        counts["E1"] = e
    if q:
        counts["Q1"] = q
    return {"cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
                       "library_total": residual + e + q, "counts": counts}],
            "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
            "operator_states": {"OP": states}, "ladder": deepcopy(_LADDER)}


# ---------------------------------------------------------------------------
# The A4 boundary itself: zero-base cells, hidden query counts 0, 1, 5 and 100
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("variant", _BASE_VARIANTS)
def test_a4_zero_base_cell_is_refused_identically_for_every_hidden_query_count(variant):
    outcomes = {q: _visible_outcome(_zero_base_world(variant, q), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {_NOT_ESTIMABLE}, outcomes


@pytest.mark.parametrize("variant", _BASE_VARIANTS)
def test_a4_refusal_is_identical_at_every_rights_level_over_every_withheld_right(variant):
    """L0 may see neither EXT nor QUERY counts; L1 may see EXT but not QUERY. With no
    base mass and no residual the depth is 0 at every level, whatever is withheld."""
    for level_id in ("L0", "L1"):
        outcomes = {(e, q): _visible_outcome(_zero_base_world(variant, q, e=e), level_id)
                    for e in _Q_VALUES for q in _Q_VALUES}
        assert set(outcomes.values()) == {_NOT_ESTIMABLE}, (level_id, outcomes)


def _two_operator_world(q, empty_first):
    """OP_A measures the query; OP_B leaves it structurally unmeasured (partial
    support). The healthy cell is validated before or after the empty one."""
    healthy = {"cell_id": "C_OK", "donor_id": "D1", "source_id": "S1", "operator_id": "OP_B",
               "library_total": 4 + 3 + 6 + 2, "counts": {"B1": 4, "B2": 3, "E1": 6}}
    empty = {"cell_id": "C_EMPTY", "donor_id": "D2", "source_id": "S2", "operator_id": "OP_A",
             "library_total": q, "counts": {"Q1": q} if q else {}}
    return {"cells": [empty, healthy] if empty_first else [healthy, empty],
            "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
            "operator_states": {"OP_A": {"B1": MS, "B2": MS, "E1": MS, "Q1": MS},
                                "OP_B": {"B1": MS, "B2": MS, "E1": MS, "Q1": SU}},
            "ladder": deepcopy(_LADDER)}


@pytest.mark.parametrize("empty_first", (True, False))
def test_a4_refusal_is_identical_across_operators_and_cell_order(empty_first):
    for level_id in ("L0", "L1"):
        outcomes = {q: _visible_outcome(_two_operator_world(q, empty_first), level_id) for q in _Q_VALUES}
        assert set(outcomes.values()) == {_NOT_ESTIMABLE}, (level_id, outcomes)


def test_an_empty_droplet_is_not_estimable_and_still_a_domain_refusal():
    """A physical total of 0 with no counts is well formed but has no depth. The
    refusal class is a subclass of the domain error, so a caller that catches
    QExcludedObservationError still catches it."""
    assert _visible_outcome(_zero_base_world("omitted_measured_zero", 0), "L0") == _NOT_ESTIMABLE
    assert issubclass(Q.QExcludedDepthNotEstimable, Q.QExcludedObservationError)


# ---------------------------------------------------------------------------
# Measured zero versus structural absence when a depth exists
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("residual", (1, 7))
def test_measured_zero_and_structural_absence_stay_distinct_and_invariant_to_the_query(residual):
    student = {}
    for variant in ("omitted_measured_zero", "explicit_measured_zero", "structurally_unmeasured"):
        l0 = {q: _visible_outcome(_zero_base_world(variant, q, residual=residual), "L0") for q in _Q_VALUES}
        l1 = {q: _visible_outcome(_zero_base_world(variant, q, e=3, residual=residual), "L1") for q in _Q_VALUES}
        top = {q: _visible_outcome(_zero_base_world(variant, q, residual=residual), "L2") for q in _Q_VALUES}
        assert len(set(l0.values())) == 1 and len(set(l1.values())) == 1, variant
        assert l0[0][0] == "view" and l1[0][0] == "view"
        assert len(set(top.values())) == len(_Q_VALUES)  # positive control: the richest level sees q
        student[variant] = l0[0]
    # Omitting a measured zero and storing it are the same measurement and the same bytes.
    assert student["omitted_measured_zero"] == student["explicit_measured_zero"]
    # Structural absence is a different physical state and must not collapse into zero.
    assert student["structurally_unmeasured"] != student["omitted_measured_zero"]
    zero = {r["address_id"]: r for r in json.loads(student["omitted_measured_zero"][1])["levels"][0]["rows"]}
    absent = {r["address_id"]: r for r in json.loads(student["structurally_unmeasured"][1])["levels"][0]["rows"]}
    assert (zero["B1"]["state"], zero["B1"]["count"], zero["B1"]["library_size"]) == (MS, 0, residual)
    assert (absent["B1"]["state"], absent["B1"]["count"], absent["B1"]["library_size"]) == (SU, None, None)
    for rows in (zero, absent):
        assert (rows["Q1"]["state"], rows["Q1"]["count"], rows["Q1"]["library_size"]) == (WITHHELD, None, None)


# ---------------------------------------------------------------------------
# Seeded whole-outcome noninterference at every level, crossing the zero boundary
# ---------------------------------------------------------------------------

_LADDER4 = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
    {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:RESERVED"]},
    {"level_id": "L3", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:RESERVED", "RNA:QUERY"]},
]
_RANK = {"RNA:BASE": 0, "RNA:EXT": 1, "RNA:RESERVED": 2, "RNA:QUERY": 3}


def _seeded_world(rng):
    rights = {f"B{i}": "RNA:BASE" for i in range(rng.randint(1, 3))}
    rights.update({f"E{i}": "RNA:EXT" for i in range(rng.randint(0, 2))})
    rights.update({"R0": "RNA:RESERVED", "Q": "RNA:QUERY"})
    states = {}
    for op in ("OP1", "OP2"):
        m = {}
        for a, right in rights.items():
            r = rng.random()
            if right == "RNA:BASE" and r < 0.15:
                m[a] = MCU
            elif r < 0.25 and a != "Q":
                m[a] = SU
            else:
                m[a] = MS
        if op == "OP2" and rng.random() < 0.3:
            m["Q"] = SU  # partial operator support for the query
        states[op] = m
    if rng.random() < 0.1:  # a structural NOT_ESTIMABLE route, also required to be invariant
        states[rng.choice(["OP1", "OP2"])][rng.choice(["R0", "Q"])] = MCU
    cells = []
    for i in range(rng.randint(1, 5)):
        op = rng.choice(["OP1", "OP2"])
        empty_base = rng.random() < 0.35
        counts = {}
        for a, s in states[op].items():
            if s != MS:
                continue
            if rights[a] == "RNA:BASE":
                k = 0 if empty_base else rng.randint(0, 20)
            else:
                k = rng.choice((0, 0, 1, 5, 100, rng.randint(0, 30)))
            if k or rng.random() < 0.5:  # a measured zero may be stored or omitted
                counts[a] = k
        residual = 0 if rng.random() < 0.5 else rng.randint(1, 9)
        cells.append({"cell_id": f"C{i}", "donor_id": f"D{i % 3}", "source_id": f"S{i % 2}",
                      "operator_id": op, "library_total": sum(counts.values()) + residual, "counts": counts})
    return {"cells": cells, "address_rights": rights, "operator_states": states, "ladder": deepcopy(_LADDER4)}


def _withheld_sum(world, cell, rank):
    op = world["operator_states"][cell["operator_id"]]
    return sum(c for a, c in cell["counts"].items() if _RANK[world["address_rights"][a]] > rank and op[a] == MS)


def _reassign_withheld(world, rank, rng):
    """Same cells and visible molecules; every count above ``rank`` is redrawn (all
    to zero, all positive, or freely), and the physical total moves by the same amount."""
    alt = deepcopy(world)
    for cell in alt["cells"]:
        op = alt["operator_states"][cell["operator_id"]]
        mode = rng.choice(("all_zero", "all_positive", "free"))
        for a, right in alt["address_rights"].items():
            if _RANK[right] <= rank or op[a] != MS:
                continue
            old = cell["counts"].get(a, 0)
            new = {"all_zero": 0, "all_positive": rng.choice((1, 5, 100, rng.randint(1, 40))),
                   "free": rng.choice((0, 1, 5, 100, rng.randint(0, 40)))}[mode]
            if new or rng.random() < 0.5:
                cell["counts"][a] = new
            else:
                cell["counts"].pop(a, None)
            cell["library_total"] += new - old
    return alt


def test_whole_outcome_noninterference_at_every_level_over_seeded_worlds():
    """Positive-control floors were fixed before the first run: produced >= 80,
    refused >= 60, zero-boundary crossings >= 30, richest level moved >= 60."""
    produced = refused = boundary = top_moved = 0
    for seed in range(240):
        rng = random.Random(474_400 + seed)
        world = _seeded_world(rng)
        for rank, level in enumerate(_LADDER4[:-1]):
            alt = _reassign_withheld(world, rank, rng)
            a = _visible_outcome(world, level["level_id"])
            b = _visible_outcome(alt, level["level_id"])
            assert a == b, (seed, level["level_id"], a[:2], b[:2])
            if rank == 0:
                produced += a[0] == "view"
                refused += a[0] == "refused"
                for before, after in zip(world["cells"], alt["cells"]):
                    no_depth = before["library_total"] - _withheld_sum(world, before, 0) == 0
                    if no_depth and (_withheld_sum(world, before, 0) == 0) != (_withheld_sum(alt, after, 0) == 0):
                        boundary += 1
                        break
                if a[0] == "view" and _visible_outcome(world, "L3") != _visible_outcome(alt, "L3"):
                    top_moved += 1
    assert produced >= 80 and refused >= 60 and boundary >= 30 and top_moved >= 60, (
        produced, refused, boundary, top_moved)


# ---------------------------------------------------------------------------
# Other refusal routes stay invariant; legitimate validation is preserved
# ---------------------------------------------------------------------------

def _one_cell(counts, total, states=None):
    return {"cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
                       "library_total": total, "counts": counts}],
            "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
            "operator_states": {"OP": states or {"B1": MS, "B2": MS, "E1": MS, "Q1": MS}},
            "ladder": deepcopy(_LADDER)}


def _with_q(counts, q):
    return {**counts, "Q1": q} if q else dict(counts)


def test_a_total_below_the_stored_counts_is_refused_identically_for_every_hidden_count():
    outcomes = {q: _visible_outcome(_one_cell(_with_q({"B1": 4}, q), 4 + q - 1), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {_COVERING}, outcomes


def test_a_negative_total_is_refused_identically_for_every_hidden_count():
    outcomes = {q: _visible_outcome(_one_cell(_with_q({}, q), q - 1), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {_COVERING}, outcomes


def test_collision_outside_the_base_rights_is_refused_identically_for_every_hidden_count():
    states = {"B1": MS, "B2": MS, "E1": MCU, "Q1": MS}
    outcomes = {q: _visible_outcome(_one_cell(_with_q({"B1": 4}, q), 4 + q + 2, states), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {("refused", "QExcludedDepthNotEstimable",
                                       "collision-unresolved mass outside the base rights cannot be removed "
                                       "from the depth")}, outcomes


def test_a_count_on_a_structurally_unmeasured_query_is_refused_whatever_its_value():
    states = {"B1": MS, "B2": MS, "E1": MS, "Q1": SU}
    outcomes = {q: _visible_outcome(_one_cell({"B1": 4, "Q1": q}, 4 + q + 1, states), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {("refused", "QExcludedObservationError",
                                       "count supplied for an address the operator did not measure as a scalar")}


@pytest.mark.parametrize("total", [True, 7.0, -1, 3, None, "9"])
def test_malformed_or_uncovering_totals_are_still_refused_with_the_domain_error(total):
    with pytest.raises(Q.QExcludedObservationError) as info:
        Q.produce_rights_ladder_observations(**_one_cell({"B1": 4, "Q1": 2}, total))
    assert type(info.value) is Q.QExcludedObservationError


def test_query_counts_never_reach_l0_or_l1_and_the_depth_excludes_them():
    for q in _Q_VALUES:
        result = Q.produce_rights_ladder_observations(**_one_cell(_with_q({"B1": 4, "E1": 2}, q), 4 + 2 + 3 + q))
        rows = {(lv["level_id"], r["address_id"]): r for lv in result["levels"] for r in lv["rows"]}
        for level_id in ("L0", "L1"):
            assert (rows[(level_id, "Q1")]["state"], rows[(level_id, "Q1")]["count"]) == (WITHHELD, None)
            assert rows[(level_id, "B1")]["library_size"] == 4 + 3  # base mass plus residual, never q or e
        assert rows[("L2", "Q1")]["count"] == q and rows[("L2", "Q1")]["library_size"] == 7


# ---------------------------------------------------------------------------
# Self-audit round 2: the whole refusal object, not only class and message
# ---------------------------------------------------------------------------

def test_round2_the_whole_refusal_object_is_identical_for_every_hidden_query_count():
    """Probe added after the fix; it fails at e7635e79 through the A4 class
    difference. Cause, context, notes and instance attributes never differed."""
    for variant in _BASE_VARIANTS:
        refusals = set()
        for q in _Q_VALUES:
            with pytest.raises(Q.QExcludedObservationError) as info:
                Q.produce_rights_ladder_observations(**_zero_base_world(variant, q))
            exc = info.value
            refusals.add((type(exc), exc.args, exc.__cause__ is None, exc.__context__ is None,
                          exc.__suppress_context__, tuple(getattr(exc, "__notes__", ())), tuple(sorted(vars(exc)))))
        assert len(refusals) == 1, (variant, refusals)


# ---------------------------------------------------------------------------
# Self-audit round 3: a second A4 route found by an exhaustive old/new differential
# ---------------------------------------------------------------------------

def test_round3_zero_total_with_an_outside_base_collision_is_refused_by_the_collision_rule():
    """Over 10,368 one-cell worlds the repair changed no accepted bytes and no
    accept decision; 256 refusals changed, all with total 0 and nothing stored.
    112 of them were this route: with a collision-unresolved address outside the
    base rights, ``total < 1`` refused an empty cell as malformed while the same
    cell holding withheld molecules was refused by the collision rule."""
    states = {"B1": MS, "B2": MS, "E1": MCU, "Q1": MS}
    outcomes = {q: _visible_outcome(_one_cell(_with_q({}, q), q, states), "L0") for q in _Q_VALUES}
    assert set(outcomes.values()) == {("refused", "QExcludedDepthNotEstimable",
                                       "collision-unresolved mass outside the base rights cannot be removed "
                                       "from the depth")}, outcomes


# ---------------------------------------------------------------------------
# Declared limit, characterized (a passing characterization means it is present)
# ---------------------------------------------------------------------------

def test_characterize_noninterference_is_claimed_only_inside_the_declared_integer_domain():
    """LIMITATION. Every integer, the physical total included, must lie below 2**53
    so it is exact in float64 and inside the canonical encoder's domain. A total
    that leaves the domain only because of withheld molecules is refused before any
    semantics, so at that edge the refusal depends on withheld mass. No nucleus
    approaches 2**53 molecules; the claim is noninterference over the declared domain."""
    base = 2 ** 53 - 10
    inside = _visible_outcome(_one_cell({"B1": base, "Q1": 5}, base + 5), "L0")
    outside = _visible_outcome(_one_cell({"B1": base, "Q1": 20}, base + 20), "L0")
    assert inside[0] == "view"
    assert outside == ("refused", "QExcludedObservationError", "integer outside the physical count domain")
