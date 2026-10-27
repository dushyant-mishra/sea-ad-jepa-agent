"""Macha independent review RED for #470 (G7 E3 scoped R3-R5 repair). Tests only.

Target: scripts/v5/td_real_g7_content_enforcement_v1.py at exact head
2e173fa48895 (#470, stacked on #449 062bfe36). Synthetic, outcome-blind fixture
values only; no real, protected or human data; nothing here grants authority.

GREEN guards (pass at 2e173fa4; the R3/R5-depth ones fail at 062bfe36):
  R3   exhaustive two-unit rosters never bind a V3 ``source::donor`` collision,
       a collider with no measured scalar is still refused, and non-colliding
       colon-bearing identities still bind.
  R5   deep nesting on every canonicalized surface is a G7ContentError.

RED (fail at 2e173fa4 and at 062bfe36; pre-existing, not introduced by #470):
  R5X  Payload code runs in containers the binder compares BEFORE it checks exact
       types (level_id value, level/token/pins/row dict keys), so a hostile input
       chooses the exception that leaves the G7 boundary.
  R6   Same root cause, worse effect: the binder validates caller-owned objects in
       place and digests or re-reads them afterwards. A hostile row key rewrites
       rows that were already checked (R6a), and a hostile level_id rewrites the
       penultimate level's atoms after their pin check (R6b). Either way the
       binder returns BOUND for support counts that contradict the pinned content,
       and V3 turns NOT_ESTIMABLE into PASS on the rows the receipt binds.
  R1D  R1 at the donor level: donor_id is as opaque as atom_id. One physical
       donor's eight specimen blocks bind as eight donors and V3 passes the
       donor sign test on a single donor. Like R1, only source-authenticated
       donor identity can close it; a confusable/suffix screen is not proof.
       (API freedom as in #449: a successor that adds an authenticated donor
       identity field, making this fixture schema-invalid, passes here.)
"""
from __future__ import annotations

import itertools
from copy import deepcopy

import pytest

from scripts.v5 import td_real_g7_content_enforcement_v1 as E
from scripts.v5 import td_real_g7_terminal_decision_v3 as V3

RIGHTS = ["RNA:CORE", "RNA:EXTENDED", "CONTEXT:LAWFUL"]
BOUND = "E3_TERMINAL_INPUTS_BOUND_FIXTURE_ONLY"


def _manifest():
    return {
        "schema": "JEPA_TD_REAL_EVIDENCE_LADDER_MANIFEST_V1", "frozen": True,
        "candidate_id": "DUMMY_CANDIDATE", "full_evidence_rights": list(RIGHTS),
        "levels": [
            {"level_id": f"L{i}", "operator_family": "BIOLOGICAL_EVIDENCE_RIGHTS_RESTRICTION",
             "evidence_rights": list(RIGHTS[: i + 1])}
            for i in range(len(RIGHTS))
        ],
    }


def _atom(atom_id, right, count, library_size, *, source="SEA_AD", donor="D1",
          state="MEASURED_SCALAR"):
    if state != "MEASURED_SCALAR":
        count = library_size = None
    return {"atom_id": atom_id, "source": source, "donor_id": donor, "right": right,
            "state": state, "count": count, "library_size": library_size}


def _honest_package(full):
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


def _v3(rows, binding):
    return V3.adjudicate_g7_terminal_v3(
        rows=rows, required_sources=["SEA_AD"], decision_qualification=V3._qual(),
        reference_artifact=V3._ref(rows, binding=binding))


def _rows_sha(rows):
    return E.canonical_sha256(sorted(rows, key=lambda r: (r["source"], r["donor_id"])))


# --------------------------------------------------------------------------
# R3 guards
# --------------------------------------------------------------------------

def test_r3_exhaustive_two_unit_rosters_never_bind_a_v3_key_collision():
    names = ["".join(p) for n in (1, 2, 3) for p in itertools.product("a:", repeat=n)]
    units = [(s, d) for s in names for d in names]
    collisions_seen = over_refused = 0
    for u1, u2 in itertools.combinations(units, 2):
        collide = V3._unit_key(*u1) == V3._unit_key(*u2)
        collisions_seen += collide
        full = [_atom("x1", "RNA:CORE", 1, 9, source=u1[0], donor=u1[1]),
                _atom("x2", "RNA:CORE", 1, 9, source=u2[0], donor=u2[1])]
        roster = sorted({u1[0], u2[0]})
        m, full, levels, pins = _honest_package(full)
        b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=roster)
        rows = [_row(b, 1, 1, source=u[0], donor=u[1]) for u in (u1, u2)]
        try:
            receipt = _bind(m, full, levels, pins, roster, rows, b)
        except E.G7ContentError:
            over_refused += not collide and not any("::" in x for x in u1 + u2)
            continue
        assert receipt["status"] == BOUND
        assert not collide, f"bound {u1} and {u2}, which V3 merges into {V3._unit_key(*u1)!r}"
    assert collisions_seen == 40  # the enumeration is not vacuous
    assert over_refused == 0, "a non-colliding identity without '::' was refused"


def test_r3_colliding_unit_without_measured_scalar_is_refused():
    full = [_atom("x1", "RNA:CORE", 1, 9, source="A:", donor="B"),
            _atom("x2", "RNA:CORE", None, None, source="A", donor=":B",
                  state="STRUCTURALLY_UNMEASURED")]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["A", "A:"])
    rows = [_row(b, 1, 1, source="A:", donor="B"), _row(b, 0, 0, source="A", donor=":B")]
    with pytest.raises(E.G7ContentError):
        _bind(m, full, levels, pins, ["A", "A:"], rows, b)


def test_r3_noncolliding_colon_identities_still_bind():
    full = [_atom("x1", "RNA:CORE", 1, 9, source="SEA-AD:MTG", donor="H20.33.001"),
            _atom("x2", "RNA:CORE", 1, 9, source="SEA-AD:MTG", donor="H21:7")]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA-AD:MTG"])
    rows = [_row(b, 1, 1, source="SEA-AD:MTG", donor=d) for d in ("H20.33.001", "H21:7")]
    assert _bind(m, full, levels, pins, ["SEA-AD:MTG"], rows, b)["status"] == BOUND


# --------------------------------------------------------------------------
# R5 guards and R5X
# --------------------------------------------------------------------------

def _honest3():
    full = [_atom("a", "RNA:CORE", 0, 31), _atom("b", "RNA:EXTENDED", 5, 31),
            _atom("c", "CONTEXT:LAWFUL", 3, 31)]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    return m, full, levels, pins, b


def _deep(kind, n=5000):
    out = 0
    for _ in range(n):
        out = [out] if kind == "list" else {"k": out}
    return out


@pytest.mark.parametrize("surface", ["atom_value_list", "atom_value_dict", "token_value", "manifest_value"])
def test_r5_deep_nesting_on_every_canonicalized_surface_is_a_domain_error(surface):
    m, full, levels, pins, b = _honest3()
    if surface == "atom_value_list":
        full = deepcopy(full)
        full[1]["count"] = _deep("list")
    elif surface == "atom_value_dict":
        full = deepcopy(full)
        full[1]["count"] = _deep("dict")
    elif surface == "token_value":
        levels[0]["rights_token"]["candidate_id"] = _deep("list")
    else:
        m = dict(m, extra=_deep("dict"))
    with pytest.raises(E.G7ContentError):
        _bind(m, full, levels, pins, ["SEA_AD"], [_row(b, 2, 3)], b)


class _PayloadStr(str):
    """An exact-looking key or level id whose comparison runs caller code."""

    __hash__ = str.__hash__

    def __eq__(self, other):
        raise RuntimeError("exception chosen by the payload")

    __ne__ = __eq__


def _rekey(mapping, key, cls=_PayloadStr):
    mapping[cls(key)] = mapping.pop(key)


@pytest.mark.parametrize("route", ["level_id_value", "level_key", "token_key", "pins_key",
                                   "pins_level_map_key", "row_key"])
def test_r5x_payload_code_cannot_choose_the_exception_that_leaves_the_binder(route):
    m, full, levels, pins, b = _honest3()
    rows = [_row(b, 2, 3)]
    assert _bind(m, full, levels, pins, ["SEA_AD"], deepcopy(rows), b)["status"] == BOUND
    if route == "level_id_value":
        levels[0]["level_id"] = _PayloadStr("L0")
    elif route == "level_key":
        _rekey(levels[0], "atoms")
    elif route == "token_key":
        _rekey(levels[0]["rights_token"], "schema")
    elif route == "pins_key":
        _rekey(pins, "manifest_sha256")
    elif route == "pins_level_map_key":
        _rekey(pins["token_sha256_by_level"], "L0")
    else:
        _rekey(rows[0], "source")
    try:
        _bind(m, full, levels, pins, ["SEA_AD"], rows, b)
    except E.G7ContentError:
        return
    except Exception as exc:  # noqa: BLE001 - the escape is the defect under test
        pytest.fail(f"payload-chosen {type(exc).__name__} left the G7 boundary via {route}")
    pytest.fail(f"hostile {route} was accepted")


# --------------------------------------------------------------------------
# R6  validate-in-place, read-or-digest-later
# --------------------------------------------------------------------------

def _no_support_world(n=9):
    """Nine donors whose only measured scalar is visible at every level: added support 0."""
    full = [_atom(f"x{i}", "RNA:CORE", 1, 9, donor=f"D{i:02d}") for i in range(n)]
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    return m, full, levels, pins, b, [_row(b, 1, 1, donor=f"D{i:02d}") for i in range(n)]


def test_r6a_hostile_row_key_cannot_mint_a_receipt_for_rows_that_contradict_content():
    m, full, levels, pins, b, honest = _no_support_world()
    honest_sha = _bind(m, full, levels, pins, ["SEA_AD"], deepcopy(honest), b)["deciding_rows_sha256"]
    assert _v3(honest, b)["status"] == "NOT_ESTIMABLE"
    rows = deepcopy(honest)
    checked, hostile = rows[:-1], rows[-1]
    fired = []

    class Forger(str):
        __hash__ = str.__hash__

        def __eq__(self, other):
            if not fired:
                fired.append(True)
                for r in checked:  # rows the binder has already validated
                    r.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                             added_supported_evidence=2, terminal_displacement=0.0)
                hostile["source"] = hostile.pop(self)  # leave only exact keys behind
            return str.__eq__(self, other)

        def __ne__(self, other):
            return not self.__eq__(other)

    _rekey(hostile, "source", Forger)
    with pytest.raises(E.G7ContentError):  # presented directly, the forged rows are refused
        forged_direct = deepcopy(honest)
        for r in forged_direct[:-1]:
            r.update(penultimate_supported_evidence=1, full_supported_evidence=3,
                     added_supported_evidence=2, terminal_displacement=0.0)
        _bind(m, full, levels, pins, ["SEA_AD"], forged_direct, b)
    try:
        receipt = _bind(m, full, levels, pins, ["SEA_AD"], rows, b)
    except E.G7ContentError:
        return
    assert receipt["deciding_rows_sha256"] == honest_sha, (
        f"BOUND receipt binds rows the binder never validated (V3 on them: {_v3(rows, b)['status']}; "
        f"on the content-true rows: NOT_ESTIMABLE)")


def test_r6b_hostile_level_id_cannot_rewrite_validated_atoms_before_support_counting():
    m, full, levels, pins, b, honest = _no_support_world()
    penultimate, terminal = levels[-2], levels[-1]

    class Forger(str):
        __hash__ = str.__hash__

        def __ne__(self, other):
            for a in penultimate["atoms"]:  # already pinned and validated
                a.update(state="WITHHELD_BY_EVIDENCE_RIGHTS", count=None, library_size=None)
            terminal["level_id"] = str.__str__(self)  # the type check re-reads an exact str
            return False

        __eq__ = str.__eq__

    terminal["level_id"] = Forger(terminal["level_id"])
    claimed = [_row(b, 0, 1, donor=r["donor_id"], displacement=0.0) for r in honest]
    try:
        receipt = _bind(m, full, levels, pins, ["SEA_AD"], claimed, b)
    except E.G7ContentError:
        return
    pytest.fail(f"{receipt['status']} for added support 1 per donor although the pinned content has 0 "
                f"(V3 on the bound rows: {_v3(claimed, b)['status']})")


# --------------------------------------------------------------------------
# R1D  donor identity is opaque (R1 at the replication unit)
# --------------------------------------------------------------------------

def test_r1d_specimen_identifiers_of_one_donor_are_not_bound_as_independent_donors():
    blocks = ["MTG", "DLPFC", "A9", "A1", "M1", "S1", "V1", "CB"]
    ids = [f"H20.33.001-{blk}" for blk in blocks]  # one physical donor, eight tissue blocks
    full = ([_atom(f"x{i}", "RNA:CORE", 1, 9, donor=d) for i, d in enumerate(ids)]
            + [_atom(f"y{i}", "CONTEXT:LAWFUL", 2, 9, donor=d) for i, d in enumerate(ids)])
    m, full, levels, pins = _honest_package(full)
    b = E.derive_fixture_g7_e3_input_binding(m, pins, required_sources=["SEA_AD"])
    rows = [_row(b, 1, 2, donor=d, displacement=0.0) for d in ids]
    try:
        receipt = _bind(m, full, levels, pins, ["SEA_AD"], rows, b)
    except E.G7ContentError:
        return
    if receipt.get("status") != BOUND:
        return
    decision = _v3(rows, b)
    pytest.fail(f"one donor bound as {receipt['bound_unit_count']} donors; V3 {decision['status']} "
                f"with donor_count={decision['source_details']['SEA_AD']['donor_count']}")
