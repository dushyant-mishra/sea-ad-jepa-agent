"""Macha first-pass hostile RED probes for PR #433 (G7 E3 content enforcement).

Synthetic, outcome-blind fixture values only; no real, protected or human data.

Each test is written to FAIL against exact head
21c3fb3bd389f9a513ca9ed33b31acad56b0015f and to PASS once the defect is
repaired.  A repair keeps API freedom: a test passes if the module refuses the
hostile input with its domain error (``G7ContentError``) or returns a result
whose status does not claim the input was verified/bound.  Silently accepting
the hostile input with a VERIFIED/BOUND status is the failure being recorded.
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


def _atom(atom_id, right, state="MEASURED_SCALAR", count=None, library_size=None,
          source="SEA_AD", donor="D1"):
    return {"atom_id": atom_id, "source": source, "donor_id": donor, "right": right,
            "state": state, "count": count, "library_size": library_size}


def _honest_package(full, manifest=None):
    """Honest producer: withholds hidden measured scalars, pins every level."""
    m = _manifest() if manifest is None else manifest
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


def _assert_refused(call, why):
    try:
        result = call()
    except E.G7ContentError:
        return
    assert result.get("status") not in _ACCEPTED, (
        f"hostile input accepted as {result.get('status')!r}: {why}")


# --------------------------------------------------------------------------
# F1  Count/depth thinning re-expressed as a rights partition of ONE physical
#     measurement is accepted, and the binder counts the extra depth as added
#     biological support (V3.1 §6.5 / E3: count-thinning ladder must be refused
#     even when it carries the BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION label).
# --------------------------------------------------------------------------

def _split_measurement_world():
    # One physical measurement (cell X, gene G: 8 UMIs out of a 40-UMI library)
    # binomially split into three disjoint read batches, one per "right".
    # Rights names are the ordinary ones, so no label screen can catch it.
    full = [
        _atom("cell:X|gene:G|read_batch:1", "RNA:CORE", count=2, library_size=10),
        _atom("cell:X|gene:G|read_batch:2", "RNA:EXTENDED", count=3, library_size=15),
        _atom("cell:X|gene:G|read_batch:3", "CONTEXT:LAWFUL", count=3, library_size=15),
    ]
    return _honest_package(full)


def test_f1_depth_split_of_one_measurement_is_not_verified_as_rights_restriction():
    m, full, levels, pins = _split_measurement_world()
    _assert_refused(
        lambda: E.validate_g7_e3_content(manifest=m, full_atoms=full, levels=levels,
                                         expected_pins=pins),
        "a read-depth ladder over one cell x gene measurement was verified as a "
        "biological evidence-rights restriction")


def test_f1_depth_split_is_not_bound_as_added_supported_evidence():
    m, full, levels, pins = _split_measurement_world()
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    # penultimate sees batches 1+2, full sees 1+2+3 of the SAME molecules
    _assert_refused(
        lambda: _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b),
        "added read depth of an already-visible measurement was bound as "
        "added_supported_evidence=1 (depth substitution)")


def test_f1_duplicated_measurement_is_not_counted_twice_as_support():
    # The same physical measurement emitted twice: once under a penultimate
    # right and once under the terminal-only right.  Nothing physically new is
    # revealed at the terminal level, yet the binder demands added support = 1.
    full = [
        _atom("cell:A|gene:G", "RNA:CORE", count=0, library_size=31),
        _atom("cell:B|gene:G", "RNA:EXTENDED", count=5, library_size=31),
        _atom("cell:B|gene:G#copy", "CONTEXT:LAWFUL", count=5, library_size=31),
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    _assert_refused(
        lambda: _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b),
        "a duplicated measurement was bound as physically added supported evidence")


# --------------------------------------------------------------------------
# F2  The binder receipt does not identify the rows it verified, so it cannot
#     bind the later V3 decision call to the verified rows (TOCTOU).
# --------------------------------------------------------------------------

def test_f2_receipt_distinguishes_rows_that_differ_in_decision_bearing_values():
    full = [
        _atom("cell:A", "RNA:CORE", count=0, library_size=31),
        _atom("cell:B", "RNA:EXTENDED", count=5, library_size=31),
        _atom("cell:C", "CONTEXT:LAWFUL", count=3, library_size=31),
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    converged = _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3, displacement=0.0)], b)
    diverged = _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3, displacement=9.0)], b)
    assert converged != diverged, (
        "receipts for rows with terminal_displacement 0.0 and 9.0 are identical: "
        "the receipt does not bind the deciding rows it verified")


# --------------------------------------------------------------------------
# F3  A MEASURED_SCALAR with zero library depth is accepted as a measured zero
#     and counted as supported evidence.  With no molecules sampled there was
#     no measurement; measured zero is evidence only when depth is positive.
# --------------------------------------------------------------------------

def test_f3_zero_depth_measured_scalar_is_not_bound_as_support():
    full = [
        _atom("cell:A", "RNA:CORE", count=0, library_size=31),
        _atom("cell:B", "RNA:EXTENDED", count=5, library_size=31),
        _atom("cell:Z", "CONTEXT:LAWFUL", count=0, library_size=0),
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    _assert_refused(
        lambda: _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b),
        "a zero-depth observation was bound as added measured-zero support")


# --------------------------------------------------------------------------
# F4  Hidden-total poison invariance (V3.1 §6.3/§21): a depth field that
#     encodes withheld mass is required to stay byte-identical at every level,
#     so L0-visible bytes change when only an L0-withheld value changes.
# --------------------------------------------------------------------------

def _hidden_total_world(hidden_count):
    counts = {"cell:A": 0, "cell:B": hidden_count, "cell:C": 3}
    total = sum(counts.values())  # full-bundle library size incl. withheld mass
    rights = {"cell:A": "RNA:CORE", "cell:B": "RNA:EXTENDED", "cell:C": "CONTEXT:LAWFUL"}
    return [_atom(k, rights[k], count=v, library_size=total) for k, v in counts.items()]


def test_f4_hidden_mass_cannot_alter_level0_visible_bytes():
    outcomes = []
    for hidden in (5, 500):
        m, full, levels, pins = _honest_package(_hidden_total_world(hidden))
        try:
            E.validate_g7_e3_content(manifest=m, full_atoms=full, levels=levels,
                                     expected_pins=pins)
            outcomes.append(("ACCEPTED", E.canonical_sha256(levels[0]["atoms"])))
        except E.G7ContentError:
            outcomes.append(("REFUSED", None))
    both_accepted = all(o[0] == "ACCEPTED" for o in outcomes)
    assert not (both_accepted and outcomes[0][1] != outcomes[1][1]), (
        "two worlds differing only in an L0-withheld count were both verified while "
        "their L0-visible bytes differ: the visible depth field carries hidden mass")


# --------------------------------------------------------------------------
# F5  Non-domain exception leak: a huge-int displacement raises OverflowError.
# --------------------------------------------------------------------------

def test_f5_huge_int_displacement_raises_domain_error_not_overflow():
    full = [
        _atom("cell:A", "RNA:CORE", count=0, library_size=31),
        _atom("cell:B", "RNA:EXTENDED", count=5, library_size=31),
        _atom("cell:C", "CONTEXT:LAWFUL", count=3, library_size=31),
    ]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    try:
        _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3, displacement=10 ** 400)], b)
    except E.G7ContentError:
        return
    except Exception as exc:  # noqa: BLE001 - the leak is the defect under test
        pytest.fail(f"non-domain {type(exc).__name__} leaked: {exc}")
    pytest.fail("a 10**400 terminal displacement was accepted")


# --------------------------------------------------------------------------
# F6  The binder accepts two distinct source/donor units that the inherited V3
#     decision law conflates under its `source::donor` margin key.
# --------------------------------------------------------------------------

def test_f6_bound_units_remain_distinct_under_v3_unit_key():
    full = [
        _atom("a1", "RNA:CORE", count=1, library_size=9, source="A::B", donor="C"),
        _atom("a2", "CONTEXT:LAWFUL", count=2, library_size=9, source="A::B", donor="C"),
        _atom("b1", "RNA:CORE", count=4, library_size=9, source="A", donor="B::C"),
    ]
    m, full, levels, pins = _honest_package(full)
    roster = ["A", "A::B"]
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=roster)
    rows = [_row(b, 1, 2, source="A::B", donor="C"), _row(b, 1, 1, source="A", donor="B::C")]
    try:
        _bind(m, full, levels, pins, roster, rows, b)
    except E.G7ContentError:
        return
    keys = [V3._unit_key(r["source"], r["donor_id"]) for r in rows]
    assert len(set(keys)) == len(keys), (
        f"binder bound two units that V3 merges into one margin key {keys[0]!r}")


# --------------------------------------------------------------------------
# F7  The public binding helper mixes a manifest with a manifest digest that
#     does not belong to it (digest not bound to bytes).
# --------------------------------------------------------------------------

def test_f7_binding_helper_refuses_manifest_not_matching_its_pinned_digest():
    full = [
        _atom("cell:A", "RNA:CORE", count=0, library_size=31),
        _atom("cell:B", "RNA:EXTENDED", count=5, library_size=31),
        _atom("cell:C", "CONTEXT:LAWFUL", count=3, library_size=31),
    ]
    m, full, levels, pins = _honest_package(full)
    other = deepcopy(m)
    other["candidate_id"] = "SOME_OTHER_CANDIDATE"
    with pytest.raises(E.G7ContentError):
        E.derive_fixture_g7_e3_input_binding(other, pins, required_sources=["SEA_AD"])
