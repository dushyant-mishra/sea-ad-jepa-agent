"""Laws for the query-excluded depth producer (synthetic fixtures only; no authority).

G7 R2 at the shared source -> CaseBundle / G7 edge: a library total that contains a
withheld gene's counts lets withheld evidence reach visible bytes. These tests fix the
lawful denominator semantics; they do not authenticate any source (R1/R2 issuer half).
"""
from __future__ import annotations

import random
from copy import deepcopy

import pytest

from scripts.v5.td_unified import q_excluded_depth_v1 as Q
from scripts.v5.td_unified.canonical_v1 import canonical_sha256
from scripts.v5.td_unified.casebundle_v1 import validate_casebundle

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
RIGHTS = ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]
LADDER = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
    {"level_id": "L2", "evidence_rights": list(RIGHTS)},
]


def _world(seed, n_addresses=12, n_cells=6):
    rng = random.Random(seed)
    addresses = [f"A{i:02d}" for i in range(n_addresses)]
    rights = {a: rng.choice(RIGHTS) for a in addresses}
    for i, r in enumerate(RIGHTS):  # every right is populated
        rights[addresses[i]] = r
    states = {}
    for op in ("OP0", "OP1"):
        states[op] = {a: rng.choice([MS, MS, MS, SU, MCU] if rights[a] == "RNA:BASE" else [MS, MS, SU])
                      for a in addresses}
    cells = []
    for c in range(n_cells):
        op = rng.choice(["OP0", "OP1"])
        counts = {}
        for a in addresses:
            if states[op][a] == MS:
                k = rng.randint(0, 20)
                if k or rng.random() < 0.5:  # sometimes store a measured zero explicitly
                    counts[a] = k
        hidden = rng.randint(0, 30) + sum(rng.randint(0, 9) for a in addresses if states[op][a] == MCU)
        cells.append({"cell_id": f"C{c:02d}", "donor_id": f"D{c % 3}", "source_id": "SRC",
                      "operator_id": op, "library_total": sum(counts.values()) + hidden + 1,
                      "counts": counts})
    return {"cells": cells, "address_rights": rights, "operator_states": states, "ladder": deepcopy(LADDER)}


def _produce(world):
    return Q.produce_rights_ladder_observations(**deepcopy(world))


def _level(result, level_id):
    return next(lv for lv in result["levels"] if lv["level_id"] == level_id)


# ---------------------------------------------------------------------------
# Noninterference (same-cell counterfactuals) and depth invariance
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("seed", range(60))
def test_withheld_counts_never_reach_the_visible_level_bytes(seed):
    world = _world(seed)
    base = _produce(world)
    moved = 0
    for k, level in enumerate(LADDER):
        visible = set(level["evidence_rights"])
        twin = deepcopy(world)
        delta_total = 0
        for cell in twin["cells"]:
            for a, right in twin["address_rights"].items():
                if right not in visible and twin["operator_states"][cell["operator_id"]][a] == MS:
                    delta = 1 + (seed + k + len(a)) % 7
                    cell["counts"][a] = cell["counts"].get(a, 0) + delta
                    cell["library_total"] += delta  # a physical total moves with its molecules
                    delta_total += delta
        moved += delta_total > 0
        out = _produce(twin)
        assert _level(out, level["level_id"])["rows_sha256"] == _level(base, level["level_id"])["rows_sha256"], (
            f"withheld counts changed visible bytes at {level['level_id']}")
        for earlier in LADDER[:k]:
            assert (_level(out, earlier["level_id"])["rows_sha256"]
                    == _level(base, earlier["level_id"])["rows_sha256"])
    assert moved >= 1  # positive control: the counterfactual really moved withheld mass


def test_depth_is_invariant_across_the_ladder_and_previously_visible_rows_keep_their_bytes():
    result = _produce(_world(7))
    by_level = {lv["level_id"]: {(r["cell_id"], r["address_id"]): r for r in lv["rows"]} for lv in result["levels"]}
    for lower, upper in (("L0", "L1"), ("L1", "L2")):
        for key, row in by_level[lower].items():
            if row["state"] == MS:
                assert by_level[upper][key] == row
    depths = {}
    for lv in result["levels"]:
        for r in lv["rows"]:
            if r["state"] == MS:
                assert depths.setdefault(r["cell_id"], r["library_size"]) == r["library_size"]


def test_depth_is_the_whole_row_total_minus_every_measured_count_outside_the_base_rights():
    world = {
        "cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
                   "library_total": 100, "counts": {"B1": 10, "B2": 0, "E1": 25, "Q1": 40}}],
        "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "B3": "RNA:BASE", "E1": "RNA:EXT",
                           "Q1": "RNA:QUERY", "Q2": "RNA:QUERY"},
        "operator_states": {"OP": {"B1": MS, "B2": MS, "B3": MCU, "E1": MS, "Q1": MS, "Q2": SU}},
        "ladder": deepcopy(LADDER),
    }
    result = _produce(world)
    rows = {(lv["level_id"], r["address_id"]): r for lv in result["levels"] for r in lv["rows"]}
    assert rows[("L0", "B1")]["library_size"] == 100 - 25 - 40
    assert rows[("L2", "Q1")] ["library_size"] == 35  # level-invariant
    assert rows[("L2", "Q1")]["count"] == 40


# ---------------------------------------------------------------------------
# Four measurement states, measured zero, refusals
# ---------------------------------------------------------------------------

def _small(**override):
    world = {
        "cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
                   "library_total": 50, "counts": {"B1": 4, "Q1": 6}}],
        "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "B3": "RNA:BASE", "E1": "RNA:EXT",
                           "Q1": "RNA:QUERY"},
        "operator_states": {"OP": {"B1": MS, "B2": MS, "B3": SU, "E1": MS, "Q1": MS}},
        "ladder": deepcopy(LADDER),
    }
    world.update(override)
    return world


def test_four_states_stay_distinct_and_measured_zero_stays_measured():
    world = _small()
    world["operator_states"]["OP"]["E1"] = MCU
    world["address_rights"]["E1"] = "RNA:BASE"
    rows = {(lv["level_id"], r["address_id"]): r for lv in _produce(world)["levels"] for r in lv["rows"]}
    assert rows[("L0", "B2")]["state"] == MS and rows[("L0", "B2")]["count"] == 0
    assert rows[("L0", "B3")]["state"] == SU and rows[("L0", "B3")]["count"] is None
    assert rows[("L0", "E1")]["state"] == MCU and rows[("L0", "E1")]["library_size"] is None
    assert rows[("L0", "Q1")]["state"] == "WITHHELD_BY_EVIDENCE_RIGHTS"
    assert rows[("L0", "Q1")]["count"] is None and rows[("L0", "Q1")]["library_size"] is None
    assert rows[("L2", "Q1")]["state"] == MS and rows[("L2", "Q1")]["count"] == 6


def test_collision_outside_the_base_rights_is_not_estimable():
    world = _small()
    world["operator_states"]["OP"]["E1"] = MCU  # its unknown mass would stay in the depth
    with pytest.raises(Q.QExcludedDepthNotEstimable):
        _produce(world)


def test_no_remaining_depth_is_not_estimable():
    world = _small()
    world["cells"][0].update(library_total=6, counts={"Q1": 6})
    with pytest.raises(Q.QExcludedDepthNotEstimable):
        _produce(world)


# ---------------------------------------------------------------------------
# Consumer conformance and identity
# ---------------------------------------------------------------------------

def test_base_level_student_view_passes_the_existing_casebundle_validator():
    result = _produce(_world(3))
    base = _level(result, "L0")
    receipt = validate_casebundle({
        "schema": "KNOWN_TRUTH_CASEBUNDLE_V1", "case_id": "Q_EXCLUDED_FIXTURE", "authority_scope": "FIXTURE_ONLY",
        "manifest_sha256": "a" * 64, "population_access_policy_sha256": "b" * 64,
        "address_universe_sha256": "c" * 64, "reader_partition": "reader_fit",
        "observations": base["casebundle_observations"],
    })
    assert receipt["status"] == "CASEBUNDLE_FIXTURE_VALIDATED_NO_AUTHORITY"


def test_atom_identity_is_recomputable_from_coordinates_and_unique():
    result = _produce(_world(11))
    for lv in result["levels"]:
        ids = [r["atom_id"] for r in lv["rows"]]
        assert len(ids) == len(set(ids))
        for r in lv["rows"]:
            assert r["atom_id"] == canonical_sha256(
                ["JEPA_Q_EXCLUDED_ATOM_V1", r["source_id"], r["operator_id"], r["cell_id"], r["address_id"]])
        for atom, row in zip(lv["g7_atoms"], lv["rows"]):
            assert atom == {"atom_id": row["atom_id"], "source": row["source_id"], "donor_id": row["donor_id"],
                            "right": row["right"], "state": row["state"], "count": row["count"],
                            "library_size": row["library_size"]}


def test_result_declares_fixture_scope_and_no_physical_or_source_authority():
    result = _produce(_world(5))
    assert result["authority_scope"] == "FIXTURE_ONLY"
    for flag in ("source_authenticated", "physical_measurement_identity_authenticated",
                 "donor_identity_authenticated"):
        assert result[flag] is False
    assert result["depth_rule"] == "WHOLE_ROW_RAW_TOTAL_MINUS_MEASURED_COUNTS_OUTSIDE_BASE_RIGHTS"


def test_caller_mutation_after_the_call_cannot_change_the_result():
    world = _world(9)
    result = Q.produce_rights_ladder_observations(**world)
    before = canonical_sha256(result)
    world["cells"][0]["counts"]["A00"] = 999
    world["ladder"][0]["evidence_rights"].append("RNA:QUERY")
    assert canonical_sha256(result) == before


# ---------------------------------------------------------------------------
# Normalise first: hostile or ambiguous inputs are refused with the domain error
# ---------------------------------------------------------------------------

class _PayloadStr(str):
    __hash__ = str.__hash__

    def __eq__(self, other):
        raise RuntimeError("payload code ran")

    __ne__ = __eq__


class _ListSub(list):
    pass


def _hostile(name):
    w = _small()
    c = w["cells"][0]
    if name == "payload_key_in_cell":
        c[_PayloadStr("donor_id")] = c.pop("donor_id")
    elif name == "payload_key_in_counts":
        c["counts"][_PayloadStr("B1")] = c["counts"].pop("B1")
    elif name == "payload_value_cell_id":
        c["cell_id"] = _PayloadStr("C1")
    elif name == "payload_key_in_states":
        w["operator_states"]["OP"][_PayloadStr("B1")] = w["operator_states"]["OP"].pop("B1")
    elif name == "list_subclass_cells":
        w["cells"] = _ListSub(w["cells"])
    elif name == "bool_count":
        c["counts"]["B1"] = True
    elif name == "negative_count":
        c["counts"]["B1"] = -1
    elif name == "float_library":
        c["library_total"] = 50.0
    elif name == "library_below_counts":
        c["library_total"] = 9
    elif name == "count_on_unmeasured":
        c["counts"]["B3"] = 1
    elif name == "count_on_unknown_address":
        c["counts"]["Z9"] = 1
    elif name == "duplicate_cell_id":
        w["cells"].append(deepcopy(c))
    elif name == "missing_operator":
        c["operator_id"] = "NOPE"
    elif name == "state_map_missing_address":
        del w["operator_states"]["OP"]["E1"]
    elif name == "unknown_state":
        w["operator_states"]["OP"]["E1"] = "MEASURED"
    elif name == "right_outside_ladder":
        w["address_rights"]["E1"] = "RNA:OTHER"
    elif name == "ladder_not_nested":
        w["ladder"][1]["evidence_rights"] = ["RNA:EXT"]
    elif name == "ladder_not_increasing":
        w["ladder"][1]["evidence_rights"] = ["RNA:BASE"]
    elif name == "duplicate_level_id":
        w["ladder"][2]["level_id"] = "L1"
    elif name == "empty_ladder":
        w["ladder"] = []
    elif name == "untrimmed_identity":
        c["donor_id"] = "D1 "
    elif name == "deep_nesting":
        deep = 0
        for _ in range(5000):
            deep = [deep]
        c["counts"]["B1"] = deep
    elif name == "extra_cell_field":
        c["library_size"] = 50
    return w


_HOSTILE = ["payload_key_in_cell", "payload_key_in_counts", "payload_value_cell_id", "payload_key_in_states",
            "list_subclass_cells", "bool_count", "negative_count", "float_library", "library_below_counts",
            "count_on_unmeasured", "count_on_unknown_address", "duplicate_cell_id", "missing_operator",
            "state_map_missing_address", "unknown_state", "right_outside_ladder", "ladder_not_nested",
            "ladder_not_increasing", "duplicate_level_id", "empty_ladder", "untrimmed_identity",
            "deep_nesting", "extra_cell_field"]


@pytest.mark.parametrize("name", _HOSTILE)
def test_hostile_or_ambiguous_input_is_refused_with_the_domain_error(name):
    world = _hostile(name)
    try:
        Q.produce_rights_ladder_observations(**world)
    except Q.QExcludedObservationError:
        return
    except BaseException as exc:  # noqa: BLE001 - an escape is the defect under test
        pytest.fail(f"{name}: {type(exc).__name__} escaped instead of QExcludedObservationError", pytrace=False)
    pytest.fail(f"{name}: accepted", pytrace=False)


def test_the_honest_small_world_is_accepted():
    assert _produce(_small())["levels"][0]["level_id"] == "L0"


# ---------------------------------------------------------------------------
# Self-audit round 1 (Macha, RED first): values the encoder below cannot hold
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["huge_count", "huge_library", "lone_surrogate_cell_id",
                                  "lone_surrogate_right", "control_char_donor", "lone_surrogate_address"])
def test_round1_values_outside_the_physical_or_text_domain_are_refused(name):
    w = _small()
    c = w["cells"][0]
    if name == "huge_count":
        c["counts"]["B1"] = 10 ** 5000
        c["library_total"] = 10 ** 5000 + 100
    elif name == "huge_library":
        c["library_total"] = 2 ** 53
    elif name == "lone_surrogate_cell_id":
        c["cell_id"] = "C\ud8001"
    elif name == "lone_surrogate_right":
        for lv in w["ladder"]:
            lv["evidence_rights"] = [r if r != "RNA:EXT" else "RNA:\udc00" for r in lv["evidence_rights"]]
        w["address_rights"]["E1"] = "RNA:\udc00"
    elif name == "control_char_donor":
        c["donor_id"] = "D\r1"
    elif name == "lone_surrogate_address":
        w["address_rights"]["\ud800X"] = "RNA:BASE"
        w["operator_states"]["OP"]["\ud800X"] = MS
    try:
        Q.produce_rights_ladder_observations(**w)
    except Q.QExcludedObservationError:
        return
    except BaseException as exc:  # noqa: BLE001
        pytest.fail(f"{name}: {type(exc).__name__} escaped", pytrace=False)
    pytest.fail(f"{name}: accepted", pytrace=False)


# ---------------------------------------------------------------------------
# Self-audit round 3 (Macha, RED first): frozen order and storage-layout invariance
# ---------------------------------------------------------------------------

def test_round3_levels_keep_the_frozen_rights_order_consumers_pin():
    world = _small()
    world["ladder"] = [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                       {"level_id": "L1", "evidence_rights": ["RNA:EXT", "RNA:BASE"]},
                       {"level_id": "L2", "evidence_rights": ["RNA:QUERY", "RNA:EXT", "RNA:BASE"]}]
    result = _produce(world)
    assert [lv["evidence_rights"] for lv in result["levels"]] == [lv["evidence_rights"] for lv in world["ladder"]]


def test_round3_identity_does_not_depend_on_input_storage_order():
    world = _world(21)
    shuffled = deepcopy(world)
    random.Random(1).shuffle(shuffled["cells"])
    shuffled["address_rights"] = dict(reversed(list(shuffled["address_rights"].items())))
    for op in shuffled["operator_states"]:
        shuffled["operator_states"][op] = dict(reversed(list(shuffled["operator_states"][op].items())))
    for cell in shuffled["cells"]:
        cell["counts"] = dict(reversed(list(cell["counts"].items())))
    assert canonical_sha256(_produce(world)) == canonical_sha256(_produce(shuffled))
