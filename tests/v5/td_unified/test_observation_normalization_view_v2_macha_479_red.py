"""Macha independent review of PR #479 (V2 normalization view) at ae762d70.

Fixture-only, synthetic, no human data. Nothing here authenticates a source,
a feature map, a query-rights issuer, a physical unit or a donor.

GREEN tests are guards or measured characterizations of a limitation; a
characterization passing means the limitation is present, not that it is
acceptable. RED tests (prefix test_red_) state required behavior that the
reviewed head does not have; they are expected to fail at ae762d70.
"""
from copy import deepcopy
import json
import random

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_fixture as V2
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.q_excluded_depth_v1 import (
    QExcludedDepthNotEstimable, QExcludedObservationError,
)

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
_LADDER = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
    {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:RESERVED", "RNA:QUERY"]},
]


def _outcome(fn, world):
    """Complete observable outcome: exact bytes of the view, or the refusal."""
    try:
        view = fn(**deepcopy(world))
    except QExcludedObservationError as exc:
        return ("refused", type(exc).__name__, str(exc))
    return ("view", json.dumps(view, sort_keys=True, ensure_ascii=False))


def _random_world(rng):
    n_base, n_ext = rng.randint(1, 4), rng.randint(0, 2)
    rights = {f"B{i}": "RNA:BASE" for i in range(n_base)}
    rights.update({f"E{i}": "RNA:EXT" for i in range(n_ext)})
    rights.update({"R0": "RNA:RESERVED", "Q": "RNA:QUERY"})
    states = {}
    for op in ("OP1", "OP2"):
        m = {}
        for a in rights:
            r = rng.random()
            if a.startswith("B") and r < 0.15:
                m[a] = MCU          # inside base only; outside base is refused upstream
            elif r < 0.30 and a != "Q":
                m[a] = SU
            else:
                m[a] = MS
        if op == "OP2" and rng.random() < 0.3:
            m["Q"] = SU             # partial operator support for the query
        states[op] = m
    cells = []
    for i in range(rng.randint(1, 6)):
        op = rng.choice(["OP1", "OP2"])
        counts = {}
        for a, s in states[op].items():
            if s == MS and rng.random() < 0.8:  # omitted MS entry = measured zero
                counts[a] = rng.randint(0, 20) if rng.random() > 0.1 else 0
        if sum(counts.values()) == 0:
            # Keep every physical total >= 1: the zero-total boundary is its own RED case.
            hidden = [a for a, s in states[op].items() if s == MS and rights[a] != "RNA:BASE"]
            if hidden:
                counts[hidden[0]] = 1
        cells.append({"cell_id": f"C{i}", "donor_id": f"D{i % 3}", "source_id": f"S{i % 2}",
                      "operator_id": op, "library_total": max(1, sum(counts.values())),
                      "counts": counts})
    return {"cells": cells, "address_rights": rights, "operator_states": states,
            "ladder": deepcopy(_LADDER), "query_address_id": "Q"}


def _withheld_counterfactual(world, rng):
    """Move only mass the student may not see; the physical total moves with it."""
    alt, moved = deepcopy(world), 0
    for cell in alt["cells"]:
        op = alt["operator_states"][cell["operator_id"]]
        for a, right in alt["address_rights"].items():
            if right != "RNA:BASE" and op[a] == MS and rng.random() < 0.7:
                delta = rng.randint(1, 50)
                cell["counts"][a] = cell["counts"].get(a, 0) + delta
                cell["library_total"] += delta
                moved += delta
    return alt, moved


# ---------------------------------------------------------------- GREEN guards

def test_complete_student_outcome_is_invariant_to_all_withheld_mass_over_seeded_worlds():
    """Strongest form of requirement B: the whole student outcome (bytes or the
    refusal and its message), not one scalar, is unchanged when every withheld
    count moves with the physical total. Positive control: the teacher moves."""
    produced = refused = teacher_moved = 0
    for seed in range(240):
        rng = random.Random(479_000 + seed)
        world = _random_world(rng)
        alt, moved = _withheld_counterfactual(world, rng)
        a = _outcome(V2.produce_fixture_student_view_v2, world)
        b = _outcome(V2.produce_fixture_student_view_v2, alt)
        assert a == b, seed
        if a[0] == "view":
            produced += 1
            V2.validate_fixture_observation_view_v2(json.loads(a[1]))
            if moved and _outcome(V2.produce_fixture_teacher_view_v2, world) != \
                    _outcome(V2.produce_fixture_teacher_view_v2, alt):
                teacher_moved += 1
        else:
            refused += 1
    assert produced >= 100 and refused >= 40 and teacher_moved >= 90, (produced, refused, teacher_moved)


def test_characterize_v2_depth_is_a_function_of_the_student_view_alone():
    """Under V2's conservation rule (total == sum of mapped scalar counts) the
    depth equals the sum of student-visible scalar counts. The private physical
    total therefore adds no information inside V2's domain."""
    checked = 0
    for seed in range(60):
        world = _random_world(random.Random(4790 + seed))
        outcome = _outcome(V2.produce_fixture_student_view_v2, world)
        if outcome[0] != "view":
            continue
        view = json.loads(outcome[1])
        visible, depth = {}, {}
        for row in view["rows"]:
            if row["state"] == MS:
                visible[row["cell_id"]] = visible.get(row["cell_id"], 0) + row["count"]
                depth[row["cell_id"]] = row["base_rights_normalization_depth"]
        assert depth == visible
        checked += 1
    assert checked >= 20


def test_characterize_conservation_cannot_see_an_in_ledger_alias_of_the_query():
    """LIMITATION (requirement C). QA is a ledger address with base rights that
    carries some of the query gene's molecules (duplicated mapping / alias).
    Totals still balance, V2 issues the view, and the student view moves with q."""
    def w(q_molecules):
        q, qa = q_molecules * 3 // 5, q_molecules - q_molecules * 3 // 5
        return {"cells": [{"cell_id": "C", "donor_id": "D", "source_id": "S", "operator_id": "O",
                           "library_total": 5 + q + qa, "counts": {"B": 5, "QA": qa, "Q": q}}],
                "address_rights": {"B": "RNA:BASE", "QA": "RNA:BASE", "Q": "RNA:QUERY"},
                "operator_states": {"O": {"B": MS, "QA": MS, "Q": MS}},
                "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                           {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:QUERY"]}],
                "query_address_id": "Q"}
    low = V2.produce_fixture_student_view_v2(**w(10))
    high = V2.produce_fixture_student_view_v2(**w(40))
    assert low["observable_sha256"] != high["observable_sha256"]
    assert {r["address_id"]: r["count"] for r in high["rows"]}["QA"] == 16


def test_characterize_teacher_digest_is_an_unkeyed_commitment_openable_from_the_student_view():
    """LIMITATION (requirement D). Every teacher-view byte except the withheld
    counts is determined by the student view (states of withheld rows are MS;
    SU/MCU are already shown). So the teacher's observable_sha256 is a
    commitment whose hiding strength is only the joint entropy of the withheld
    values; a small view is opened by enumeration. Teacher digests must be
    custodied like the teacher values."""
    world = {"cells": [{"cell_id": f"C{i}", "donor_id": "D", "source_id": "S", "operator_id": "O",
                        "library_total": 9 + q, "counts": {"B": 9, "Q": q}}
                       for i, q in enumerate((7, 23))],
             "address_rights": {"B": "RNA:BASE", "Q": "RNA:QUERY"},
             "operator_states": {"O": {"B": MS, "Q": MS}},
             "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                        {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:QUERY"]}],
             "query_address_id": "Q"}
    student = V2.produce_fixture_student_view_v2(**deepcopy(world))
    target = V2.produce_fixture_teacher_view_v2(**deepcopy(world))["observable_sha256"]
    template = {k: v for k, v in student.items() if k != "observable_sha256"}
    template["view_kind"] = "TEACHER_RICHER_RIGHTS"
    depth = {r["cell_id"]: r["base_rights_normalization_depth"]
             for r in student["rows"] if r["state"] == MS}
    recovered = None
    for q0 in range(64):
        for q1 in range(64):
            guess = deepcopy(template)
            for r in guess["rows"]:
                if r["state"] == "WITHHELD_BY_EVIDENCE_RIGHTS":
                    r["state"] = MS
                    r["count"] = q0 if r["cell_id"] == "C0" else q1
                    r["base_rights_normalization_depth"] = depth[r["cell_id"]]
            if canonical_sha256(guess) == target:
                recovered = (q0, q1)
                break
        if recovered:
            break
    assert recovered == (7, 23)


def test_characterize_barcode_reuse_across_sources_fails_closed_rather_than_merging():
    """Production note: real 10x barcodes repeat across libraries; the fixture
    keys cells globally and refuses, which is safe but needs a source-scoped key."""
    world = {"cells": [{"cell_id": "AAAC-1", "donor_id": d, "source_id": s, "operator_id": "O",
                        "library_total": 3, "counts": {"B": 3}}
                       for d, s in (("D1", "S1"), ("D2", "S2"))],
             "address_rights": {"B": "RNA:BASE", "Q": "RNA:QUERY"},
             "operator_states": {"O": {"B": MS, "Q": MS}},
             "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                        {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:QUERY"]}],
             "query_address_id": "Q"}
    with pytest.raises(QExcludedObservationError, match="duplicate cell_id"):
        V2.produce_fixture_student_view_v2(**world)


# ------------------------------------------------------------------ RED cases

def _world():
    return {
        "cells": [
            {"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
             "library_total": 20, "counts": {"B1": 2, "B2": 1, "E1": 7, "Q1": 10}},
            {"cell_id": "C2", "donor_id": "D2", "source_id": "SRC", "operator_id": "OP",
             "library_total": 9, "counts": {"B1": 4, "E1": 1, "Q1": 4}},
        ],
        "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "B3": "RNA:BASE",
                           "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
        "operator_states": {"OP": {"B1": MS, "B2": MS, "B3": SU, "E1": MS, "Q1": MS}},
        "ladder": [
            {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
            {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
            {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
        ],
        "query_address_id": "Q1",
    }


def test_red_refusal_of_an_empty_base_cell_does_not_depend_on_withheld_mass():
    """Noninterference covers refusals too. A cell with no base mass is refused
    as malformed when its physical total is 0 but as NOT_ESTIMABLE when only
    withheld mass is present, so the refusal class reveals whether withheld
    mass exists. Inherited from PR #474 (Macha-authored): the `total < 1`
    clause precedes the depth check. Both worlds have depth 0 and should be
    refused identically."""
    def w(q):
        return {"cells": [{"cell_id": "C", "donor_id": "D", "source_id": "S", "operator_id": "O",
                           "library_total": q, "counts": {"Q": q} if q else {}}],
                "address_rights": {"B": "RNA:BASE", "Q": "RNA:QUERY"},
                "operator_states": {"O": {"B": MS, "Q": MS}},
                "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                           {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:QUERY"]}],
                "query_address_id": "Q"}
    empty = _outcome(V2.produce_fixture_student_view_v2, w(0))
    hidden = _outcome(V2.produce_fixture_student_view_v2, w(5))
    assert empty[0] == hidden[0] == "refused"
    assert empty == hidden


def _resign(view):
    body = {k: v for k, v in view.items() if k != "observable_sha256"}
    return {**body, "observable_sha256": canonical_sha256(body)}


def _physical_total(cell_id):
    return next(c["library_total"] for c in _world()["cells"] if c["cell_id"] == cell_id)


def _q_count(cell_id):
    return next(c["counts"]["Q1"] for c in _world()["cells"] if c["cell_id"] == cell_id)


_LEAKS = {
    "physical_total": lambda d, cell: _physical_total(cell),
    "depth_plus_query": lambda d, cell: d + _q_count(cell),
    "offset": lambda d, cell: d + 1,
    "scaled": lambda d, cell: 2 * d,
}


@pytest.mark.parametrize("kind", ["student", "teacher"])
@pytest.mark.parametrize("leak", sorted(_LEAKS))
def test_red_v2_consumer_refuses_a_depth_field_carrying_withheld_or_physical_mass(kind, leak):
    """R2 re-entry at the V2 consumer. Under V2's own conservation rule the
    lawful depth of every cell is exactly the sum of its base-right scalar
    counts, which the view itself carries, so the consumer can check it. At
    ae762d70 a view whose depth is the physical total (contains q) validates."""
    make = V2.produce_fixture_student_view_v2 if kind == "student" else V2.produce_fixture_teacher_view_v2
    honest = make(**_world())
    V2.validate_fixture_observation_view_v2(honest)
    forged = deepcopy(honest)
    for row in forged["rows"]:
        if row["state"] == MS:
            row["base_rights_normalization_depth"] = _LEAKS[leak](
                row["base_rights_normalization_depth"], row["cell_id"])
    with pytest.raises(QExcludedObservationError):
        V2.validate_fixture_observation_view_v2(_resign(forged))


@pytest.mark.parametrize("variant", ["expose_other_withheld_right", "relabel_query_then_expose_it"])
def test_red_v2_consumer_cannot_certify_a_student_view_that_exposes_non_base_rights(variant):
    """The consumer checks only the row whose address equals query_address_id,
    and the view does not carry the base rights, so 'STUDENT_BASE_RIGHTS' is a
    self-declared label: E1 (RNA:EXT) or Q1 itself can be exposed."""
    forged = V2.produce_fixture_student_view_v2(**_world())
    depth = {r["cell_id"]: r["base_rights_normalization_depth"]
             for r in forged["rows"] if r["state"] == MS}
    target = "E1" if variant == "expose_other_withheld_right" else "Q1"
    if variant == "relabel_query_then_expose_it":
        forged["query_address_id"] = "B3"
    for row in forged["rows"]:
        if row["address_id"] == target:
            row["state"] = MS
            row["count"] = next(c["counts"][target] for c in _world()["cells"]
                                if c["cell_id"] == row["cell_id"])
            row["base_rights_normalization_depth"] = depth[row["cell_id"]]
    with pytest.raises(QExcludedObservationError):
        V2.validate_fixture_observation_view_v2(_resign(forged))


class _Meta(type):
    calls = []

    def __eq__(cls, other):
        _Meta.calls.append("eq")
        if cls.__dict__.get("mode") == "lie":
            return True
        raise RuntimeError("payload-chosen exception")

    __hash__ = type.__hash__


class _Raises(metaclass=_Meta):
    mode = "raise"


class _Lies(metaclass=_Meta):
    mode = "lie"


def _place(where, obj):
    view = V2.produce_fixture_student_view_v2(**_world())
    if where == "whole_view":
        return obj
    if where == "schema":
        view["schema"] = obj
    elif where == "row_count":
        next(r for r in view["rows"] if r["state"] == MS)["count"] = obj
    elif where == "digest":
        view["observable_sha256"] = obj
    return view


@pytest.mark.parametrize("cls", [_Raises, _Lies], ids=["raises", "lies"])
@pytest.mark.parametrize("where", ["whole_view", "schema", "row_count", "digest"])
def test_red_v2_consumer_type_dispatch_runs_no_payload_code(where, cls):
    """R5X class in the V2 consumer: `kind in (str, int, bool)` compares the
    payload's type, so a payload metaclass __eq__ runs inside the validator and
    may choose the exception that leaves it. Exact dispatch is `kind is str`."""
    _Meta.calls.clear()
    escaped = None
    try:
        V2.validate_fixture_observation_view_v2(_place(where, cls()))
        escaped = "validated"
    except QExcludedObservationError:
        pass
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    ran = len(_Meta.calls)
    if escaped or ran:
        pytest.fail(f"escape={escaped!s} payload_calls={ran}", pytrace=False)
