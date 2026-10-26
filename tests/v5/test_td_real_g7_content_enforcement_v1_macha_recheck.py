"""Macha recheck RED probes for PR #446 (G7 E3 negative-screen repair).

Synthetic, outcome-blind fixture values only; no real, protected or human data.

Each test is written to FAIL against exact head
f088f40625020253d4378812511e3c473063bb10 and to PASS once the module either
refuses the hostile input with its domain error (``G7ContentError``) or returns
a status that does not claim the input was verified/bound.  As in the #441
hostile file, API freedom is kept: a successor that adds a physical
measurement-identity field (so these fixtures become schema-invalid) passes
here, and must then ship its own identity-bearing variants of these attacks.

R1/R2 attack classes are DECLARED in the PR #446 body as unproven; they are
recorded here because the code still returns VERIFIED/BOUND for them, i.e. the
limitation is documented but not fail-closed.  R3-R5 are not declared.
"""
from __future__ import annotations

from copy import deepcopy

import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3

RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]
_ACCEPTED = {
    "E3_CONTENT_MECHANICS_VERIFIED_FIXTURE_ONLY",
    "E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY",
}


def _manifest(rights=RIGHTS):
    return {
        "schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
        "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(rights),
        "levels": [
            {"level_id": f"L{i}",
             "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
             "evidence_rights": list(rights[: i + 1])}
            for i in range(len(rights))
        ],
    }


def _atom(atom_id, right, count, library_size, *, source="SEA_AD", donor="D1"):
    return {"atom_id": atom_id, "source": source, "donor_id": donor, "right": right,
            "state": "MEASURED_SCALAR", "count": count, "library_size": library_size}


def _honest_package(full):
    """Honest producer: withholds hidden measured scalars, pins every level."""
    m = _manifest()
    mh, fh = E.canonical_sha256(m), E.canonical_sha256(full)
    levels, tok, atm = [], {}, {}
    for lv in m["levels"]:
        atoms = deepcopy(full)
        for a in atoms:
            if a["state"] == "MEASURED_SCALAR" and a["right"] not in lv["evidence_rights"]:
                a.update(state="WITHHELD_BY_EVIDENCE_RIGHTS", count=None, library_size=None)
        token = {"schema": E.RIGHTS_TOKEN_SCHEMA, "candidate_id": m["candidate_id"],
                 "level_id": lv["level_id"], "evidence_rights": list(lv["evidence_rights"]),
                 "manifest_sha256": mh, "full_atoms_sha256": fh}
        levels.append({"level_id": lv["level_id"], "rights_token": token, "atoms": atoms})
        tok[lv["level_id"]] = E.canonical_sha256(token)
        atm[lv["level_id"]] = E.canonical_sha256(atoms)
    pins = dict(manifest_sha256=mh, full_atoms_sha256=fh,
                token_sha256_by_level=tok, atoms_sha256_by_level=atm)
    return m, full, levels, pins


def _row(binding, pen, fin, *, source="SEA_AD", donor="D1", displacement=0.02):
    return {"source": source, "donor_id": donor, "terminal_displacement": displacement,
            "penultimate_supported_evidence": pen, "full_supported_evidence": fin,
            "added_supported_evidence": fin - pen, "input_binding_sha256": binding}


def _bind(m, full, levels, pins, roster, rows, binding):
    return E.bind_g7_terminal_inputs_e3(
        manifest=m, full_atoms=full, levels=levels, expected_pins=pins,
        required_sources=roster, rows=rows, reference_input_binding_sha256=binding)


def _validate(m, full, levels, pins):
    return E.validate_g7_e3_content(manifest=m, full_atoms=full, levels=levels,
                                    expected_pins=pins)


def _assert_refused(call, why):
    try:
        result = call()
    except E.G7ContentError:
        return
    assert result.get("status") not in _ACCEPTED, (
        f"hostile input accepted as {result.get('status')!r}: {why}")


# --------------------------------------------------------------------------
# R1  F1 repaired only for the exact hostile-fixture spellings.  The atom
#     schema has no physical measurement identity, and the repair is a
#     substring denylist on atom_id ("|read_batch:", "#copy", ...).  The SAME
#     depth split / duplicate with ordinary IDs is still VERIFIED and BOUND.
#     (Declared in the PR body; not fail-closed.)
# --------------------------------------------------------------------------

def _opaque_split_world():
    # Identical numbers to #441 F1: one cell x gene measurement (8 of 40 UMIs)
    # split into three read batches, now with opaque hex atom IDs.
    full = [
        _atom("e7f3a1", "RNA:CORE", 2, 10),
        _atom("0b9c42", "RNA:EXTENDED", 3, 15),
        _atom("5d2e88", "CONTEXT:LAWFUL", 3, 15),
    ]
    return _honest_package(full)


def test_r1_opaque_id_depth_split_is_not_verified_as_rights_restriction():
    m, full, levels, pins = _opaque_split_world()
    _assert_refused(lambda: _validate(m, full, levels, pins),
                    "read-depth split of one measurement verified once atom IDs are opaque")


def test_r1_opaque_id_depth_split_is_not_bound_as_added_supported_evidence():
    m, full, levels, pins = _opaque_split_world()
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    _assert_refused(
        lambda: _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b),
        "added read depth of an already-visible measurement bound as added support=1")


def test_r1_opaque_id_duplicated_measurement_is_not_counted_twice():
    full = [
        _atom("9a01", "RNA:CORE", 0, 31),
        _atom("c4d2", "RNA:EXTENDED", 5, 31),
        _atom("77fe", "CONTEXT:LAWFUL", 5, 31),  # byte copy of c4d2's measurement
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    _assert_refused(
        lambda: _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b),
        "a duplicated measurement with an opaque ID was bound as added support")


@pytest.mark.parametrize("alias", [
    "cell:X|gene:G|readbatch:1",
    "cell:X|gene:G|read-batch:1",
    "cell:X|gene:G/read_batch:1",
    "cell:X|gene:G｜read_batch:1",  # FULLWIDTH VERTICAL LINE
])
def test_r1_trivial_spelling_variants_of_the_denylisted_alias_are_not_verified(alias):
    full = [
        _atom("cell:X|gene:G", "RNA:CORE", 2, 10),
        _atom("cell:Y|gene:H", "RNA:EXTENDED", 1, 9),
        _atom(alias, "CONTEXT:LAWFUL", 3, 15),
    ]
    m, full, levels, pins = _honest_package(full)
    _assert_refused(lambda: _validate(m, full, levels, pins),
                    f"read-batch alias {alias!r} evaded the substring screen")


# --------------------------------------------------------------------------
# R2  F4 repaired only for library_size == exact (source, donor) pooled count.
#     Offset, scaled, or per-observation-unit (per-cell) denominators that
#     contain withheld mass still let L0-visible bytes depend on an
#     L0-withheld count while both worlds verify.  (Declared; not fail-closed.)
# --------------------------------------------------------------------------

def _two_world_poison(build):
    outcomes = []
    for hidden in (5, 500):
        m, full, levels, pins = _honest_package(build(hidden))
        try:
            _validate(m, full, levels, pins)
            outcomes.append(("ACCEPTED", E.canonical_sha256(levels[0]["atoms"])))
        except E.G7ContentError:
            outcomes.append(("REFUSED", None))
    both = all(o[0] == "ACCEPTED" for o in outcomes)
    return both and outcomes[0][1] != outcomes[1][1]


def _pooled_world(transform):
    def build(hidden):
        counts = {"a": 0, "b": hidden, "c": 3}
        rights = {"a": "RNA:CORE", "b": "RNA:EXTENDED", "c": "CONTEXT:LAWFUL"}
        lib = transform(sum(counts.values()))
        return [_atom(k, rights[k], v, lib) for k, v in counts.items()]
    return build


def test_r2_offset_pooled_library_does_not_leak_withheld_mass():
    assert not _two_world_poison(_pooled_world(lambda t: t + 1)), (
        "library_size = pooled total + 1 carries the L0-withheld count into L0 bytes")


def test_r2_scaled_pooled_library_does_not_leak_withheld_mass():
    assert not _two_world_poison(_pooled_world(lambda t: 2 * t)), (
        "library_size = 2 x pooled total carries the L0-withheld count into L0 bytes")


def test_r2_per_observation_unit_library_does_not_leak_withheld_mass():
    # Physically standard per-cell depth: each cell's library is its own UMI
    # total, which includes the withheld gene of that cell.  The donor-level
    # equality screen never matches a per-cell total when a donor has >1 cell.
    def build(hidden):
        cell_x = 4 + hidden   # x1 visible at L0, x2 withheld at L0
        cell_y = 6 + 2        # y1 visible at L0, y2 withheld at L0
        return [
            _atom("x1", "RNA:CORE", 4, cell_x),
            _atom("x2", "RNA:EXTENDED", hidden, cell_x),
            _atom("y1", "RNA:CORE", 6, cell_y),
            _atom("y2", "CONTEXT:LAWFUL", 2, cell_y),
        ]
    assert not _two_world_poison(build), (
        "per-cell library_size containing an L0-withheld count was verified in two "
        "worlds whose L0-visible bytes differ")


# --------------------------------------------------------------------------
# R3  F6 repaired by a '::' substring ban, which is not injectivity: a single
#     trailing/leading ':' still makes two distinct bound units collide under
#     V3's f"{source}::{donor}" margin key.  (Not declared.)
# --------------------------------------------------------------------------

def test_r3_single_colon_boundary_units_remain_distinct_under_v3_unit_key():
    full = [
        _atom("a1", "RNA:CORE", 1, 9, source="A:", donor="B"),
        _atom("a2", "CONTEXT:LAWFUL", 2, 9, source="A:", donor="B"),
        _atom("b1", "RNA:CORE", 4, 9, source="A", donor=":B"),
    ]
    m, full, levels, pins = _honest_package(full)
    roster = ["A", "A:"]
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=roster)
    rows = [_row(b, 1, 2, source="A:", donor="B"), _row(b, 1, 1, source="A", donor=":B")]
    try:
        _bind(m, full, levels, pins, roster, rows, b)
    except E.G7ContentError:
        return
    keys = [V3._unit_key(r["source"], r["donor_id"]) for r in rows]
    assert len(set(keys)) == len(keys), (
        f"binder bound two units that V3 merges into one margin key {keys[0]!r}")


# --------------------------------------------------------------------------
# R4  The consumer-facing binder receipt drops the two limitation flags the
#     repair added to the validation receipt, although the support counts it
#     certifies depend on exactly those unauthenticated semantics. (Not declared.)
# --------------------------------------------------------------------------

def test_r4_binder_receipt_carries_physical_identity_and_depth_limitations():
    full = [
        _atom("cell:A", "RNA:CORE", 0, 31),
        _atom("cell:B", "RNA:EXTENDED", 5, 31),
        _atom("cell:C", "CONTEXT:LAWFUL", 3, 31),
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    receipt = _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b)
    if receipt.get("status") not in _ACCEPTED:
        return
    missing = [k for k in ("physical_atom_identity_authenticated",
                           "q_excluded_library_provenance_authenticated")
               if receipt.get(k) is not False]
    assert not missing, (
        f"BOUND receipt certifies support counts but omits limitation flags {missing}")


# --------------------------------------------------------------------------
# R5  Non-domain exception leak (same class as #441 F5): deeply nested
#     evidence raises RecursionError instead of G7ContentError. (Not declared.)
# --------------------------------------------------------------------------

def test_r5_deeply_nested_evidence_raises_domain_error_not_recursion_error():
    full = [
        _atom("cell:A", "RNA:CORE", 0, 31),
        _atom("cell:B", "RNA:EXTENDED", 5, 31),
        _atom("cell:C", "CONTEXT:LAWFUL", 3, 31),
    ]
    m, full, levels, pins = _honest_package(full)
    deep = 0
    for _ in range(5000):
        deep = [deep]
    poisoned = deepcopy(full)
    poisoned[1]["count"] = deep
    try:
        _validate(m, poisoned, levels, pins)
    except E.G7ContentError:
        return
    except Exception as exc:  # noqa: BLE001 - the leak is the defect under test
        pytest.fail(f"non-domain {type(exc).__name__} leaked")
    pytest.fail("deeply nested evidence was accepted")
