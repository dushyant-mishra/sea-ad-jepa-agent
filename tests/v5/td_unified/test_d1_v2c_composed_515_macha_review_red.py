"""Macha independent review of PR #515 (D1 base-only producer -> standalone V2C) at fa06d486.

Tests only, fixture only, synthetic, no human data and no real expression.
Nothing here authenticates a source, a feature map, a rights issuer, a physical
unit, a donor, a depositor selection or a deployment.

Synthetic source worlds carry every molecule class the producer must exclude
(hidden query counts, withheld extension counts, collision mass, off-ledger
mass). The redactor and the expected D1 rows are written here independently
of the producer. GREEN tests are guards. Tests prefixed test_limit_ are
synthetic counterexamples of boundaries the composition expressly leaves to
an upstream issuer; they pass while the boundary is unresolved. No test here
is expected to fail at fa06d486; the two #514 entry-guard defects (PR #516)
live in the V2C file this head inherits and are reviewed there.
"""
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import tempfile

import pytest

from scripts.v5.td_unified import observation_d1_base_only_student_v2c_fixture_v1 as P
from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
WITHHELD = "WITHHELD_BY_EVIDENCE_RIGHTS"
STATUS = "STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY"
DOMAIN = b"JEPA-TD-UNIFIED-CANONICAL-V1\x00"
REPO = Path(__file__).resolve().parents[3]
CELL_KEYS = ("cell_id", "donor_id", "source_id", "operator_id")
LEGACY = ("scripts.v5.td_unified.observation_normalization_view_v2_bound_content_v1",
          "scripts.v5.td_unified.observation_v2b_public_student_gate_v1",
          "scripts.v5.td_unified.observation_normalization_view_v2_fixture",
          "scripts.v5.td_unified.observation_v2_private_pair_coherence_v1",
          "scripts.v5.td_unified.observation_d1_base_only_student_fixture_v1",
          "scripts.v5.td_unified.q_excluded_depth_v1")
_ARM = {"on": False, "ran": []}


@pytest.fixture(autouse=True)
def _reset():
    _ARM["on"], _ARM["ran"] = False, []
    yield
    _ARM["on"], _ARM["ran"] = False, []


def _digest(x):
    text = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(DOMAIN + text.encode("utf8")).hexdigest()


# ------------------------------------------------------------ synthetic source worlds

def _fixed_world():
    """Every observation state in one roster. C0 holds a measured zero for B; Z and
    E are structurally absent in O2; U is a collision; E is withheld (extension)."""
    return {
        "query": "ENSG_Q", "base_rights": ["RNA:BASE"],
        "rights": {"ENSG_A": "RNA:BASE", "ENSG_B": "RNA:BASE", "ENSG_Z": "RNA:BASE",
                   "ENSG_U": "RNA:BASE", "ENSG_Q": "RNA:QUERY", "ENSG_E": "RNA:EXT"},
        "states": {"M515_O1": {"ENSG_A": MS, "ENSG_B": MS, "ENSG_Z": MS, "ENSG_U": MCU, "ENSG_Q": MS, "ENSG_E": MS},
                   "M515_O2": {"ENSG_A": MS, "ENSG_B": MS, "ENSG_Z": SU, "ENSG_U": MCU, "ENSG_Q": MS, "ENSG_E": SU}},
        "roster": [dict(zip(CELL_KEYS, r)) for r in (("M515_C0", "M515_D0", "M515_S1", "M515_O1"),
                                                     ("M515_C1", "M515_D1", "M515_S1", "M515_O1"),
                                                     ("M515_C2", "M515_D2", "M515_S2", "M515_O2"))],
        "full": {"M515_C0": {"ENSG_A": 5, "ENSG_B": 0, "ENSG_Z": 2, "ENSG_Q": 7, "ENSG_E": 3},
                 "M515_C1": {"ENSG_A": 4, "ENSG_B": 3, "ENSG_Z": 1, "ENSG_Q": 5, "ENSG_E": 0},
                 "M515_C2": {"ENSG_A": 6, "ENSG_B": 2, "ENSG_Q": 11}},
        "collision": {"M515_C0": 4, "M515_C1": 4, "M515_C2": 0},
        "off_ledger": {"M515_C0": 0, "M515_C1": 12, "M515_C2": 5},
    }


def _random_world(rng):
    addresses = [f"ENSG_M515_{i:02d}" for i in range(rng.randint(4, 9))]
    query = rng.choice(addresses)
    base_rights = ["RNA:BASE"] if rng.random() < 0.6 else ["RNA:BASE", "RNA:BASE2"]
    rights = {a: ("RNA:QUERY" if a == query else
                  rng.choice(["RNA:BASE", "RNA:BASE", "RNA:BASE2", "RNA:EXT", "RNA:QUERY"]))
              for a in addresses}
    if not any(r in base_rights for r in rights.values()):
        rights[next(a for a in addresses if a != query)] = "RNA:BASE"
    ops = [f"M515_O{j}" for j in range(rng.randint(1, 3))]
    states = {op: {a: (MS if a == query else rng.choice([MS, MS, MS, SU, MCU])) for a in addresses}
              for op in ops}
    roster = [{"cell_id": f"M515_{op}_C{k}", "donor_id": f"M515_D{rng.randint(0, 5)}",
               "source_id": f"M515_S{j % 2}", "operator_id": op}
              for j, op in enumerate(ops) for k in range(rng.randint(1, 4))]
    rng.shuffle(roster)
    full = {c["cell_id"]: {a: rng.choice([0, rng.randint(1, 50), rng.randint(1, 50)])
                           for a in addresses if states[c["operator_id"]][a] == MS} for c in roster}
    return {"query": query, "base_rights": base_rights, "rights": rights, "states": states, "roster": roster,
            "full": full, "collision": {c["cell_id"]: rng.randint(0, 30) for c in roster},
            "off_ledger": {c["cell_id"]: rng.randint(0, 30) for c in roster}}


def _is_base(w, cell, address):
    return (w["rights"][address] in w["base_rights"]
            and w["states"][cell["operator_id"]][address] == MS)


def _redact(w, omit_zeros=True):
    """Independent redactor: base-right measured scalars only."""
    return [{"cell_id": c["cell_id"],
             "base_counts": {a: n for a, n in w["full"][c["cell_id"]].items()
                             if _is_base(w, c, a) and not (omit_zeros and n == 0)}}
            for c in w["roster"]]


def _policy(w):
    return {"query_address_id": w["query"], "base_evidence_rights": list(w["base_rights"]),
            "address_rights": dict(w["rights"]), "operator_states": deepcopy(w["states"]),
            "cell_roster": deepcopy(w["roster"])}


def _d1(w, cell):
    return sum(n for a, n in w["full"][cell["cell_id"]].items() if _is_base(w, cell, a))


def _physical_total(w, cell):
    cid = cell["cell_id"]
    return sum(w["full"][cid].values()) + w["collision"][cid] + w["off_ledger"][cid]


def _expected_rows(w):
    rows = []
    for cell in sorted(w["roster"], key=lambda c: c["cell_id"]):
        states, d1 = w["states"][cell["operator_id"]], _d1(w, cell)
        for a in sorted(w["rights"]):
            if _is_base(w, cell, a):
                state, n, d = MS, w["full"][cell["cell_id"]].get(a, 0), d1
            elif states[a] == MS:
                state, n, d = WITHHELD, None, None
            else:
                state, n, d = states[a], None, None
            rows.append({**cell, "address_id": a, "evidence_right": w["rights"][a], "state": state,
                         "count": n, "base_rights_normalization_depth": d})
    return rows


def _produce(observations, policy):
    return P.produce_d1_base_only_student_v2c_fixture(base_observations=observations, expected_policy=policy)


def _outcome(observations, policy):
    """Exact view bytes plus V2C receipt bytes, or the whole refusal, or an escape."""
    try:
        view = _produce(observations, policy)
        receipt = C.validate_student_v2c(student_view=view, expected_policy=policy)
    except C.StudentV2CRefusal as exc:
        return ("refused", type(exc).__name__, exc.args, repr(exc.__cause__), repr(exc.__context__),
                exc.__suppress_context__)
    except Exception as exc:  # noqa: BLE001 - an escape is a finding
        return ("ESCAPED", type(exc).__name__, str(exc))
    return ("view", json.dumps(view, sort_keys=True), json.dumps(receipt, sort_keys=True))


def _view_and_receipt(w, observations=None):
    policy = _policy(w)
    view = _produce(_redact(w) if observations is None else observations, policy)
    return view, C.validate_student_v2c(student_view=view, expected_policy=policy)


def _rename(x, old, new):
    if isinstance(x, dict):
        return {_rename(k, old, new): _rename(v, old, new) for k, v in x.items()}
    if isinstance(x, list):
        return [_rename(v, old, new) for v in x]
    return new if x == old else x


def _undigested(receipt):
    return {k: v for k, v in receipt.items() if not k.endswith("sha256")}


# ---------------------------------------------------------------- GREEN guards

def test_d1_is_the_measured_base_sum_over_300_random_worlds():
    """D1 = sum of permitted measured base-right counts, cell by cell, with every
    row reproduced by an independent construction; never the physical total."""
    refused = accepted = 0
    for i in range(300):
        w = _random_world(random.Random(515_000 + i))
        outcome = _outcome(_redact(w), _policy(w))
        if any(_d1(w, c) == 0 for c in w["roster"]):
            assert outcome[0] == "refused", i
            assert outcome[2] == ("no base-visible normalization depth remains for this cell",), i
            refused += 1
            continue
        assert outcome[0] == "view", (i, outcome)
        view = json.loads(outcome[1])
        assert view["rows"] == _expected_rows(w), i
        for cell in w["roster"]:
            hidden = _physical_total(w, cell) - _d1(w, cell)
            depth = {r["base_rights_normalization_depth"] for r in view["rows"]
                     if r["cell_id"] == cell["cell_id"] and r["state"] == MS}
            assert depth == {_d1(w, cell)}, i
            assert hidden >= 0 and (hidden == 0 or _physical_total(w, cell) not in depth), i
        accepted += 1
    assert accepted >= 100 and refused >= 20, (accepted, refused)


def _hidden_variants(w, rng):
    """Change only what the student must not see: query and withheld counts,
    collision mass and off-ledger mass. Base-right measured scalars are fixed."""
    for _ in range(6):
        v = deepcopy(w)
        for cell in v["roster"]:
            cid = cell["cell_id"]
            for a in v["full"][cid]:
                if not _is_base(v, cell, a):
                    v["full"][cid][a] = rng.randint(0, 10_000)
            v["collision"][cid] = rng.randint(0, 10_000)
            v["off_ledger"][cid] = rng.randint(0, 10_000)
        yield v


def test_hidden_mass_never_changes_the_view_the_receipt_or_the_refusal():
    for i in range(120):
        rng = random.Random(515_500 + i)
        w = _random_world(rng)
        reference = _outcome(_redact(w), _policy(w))
        for v in _hidden_variants(w, rng):
            assert any(_physical_total(v, c) != _physical_total(w, c) for c in w["roster"])
            assert _outcome(_redact(v), _policy(v)) == reference, i


_INJECTIONS = {"query": ("M515_C0", "ENSG_Q"), "withheld_extension": ("M515_C0", "ENSG_E"),
               "collision": ("M515_C0", "ENSG_U"), "structural_absence": ("M515_C2", "ENSG_Z"),
               "off_ledger_feature": ("M515_C0", "ENSG_OFF_LEDGER")}


def test_hidden_values_injected_into_the_base_input_get_one_value_independent_refusal():
    """If an upstream redactor leaks a query, withheld, collision, structural or
    off-ledger count into the base input, the refusal must not depend on the
    leaked value. Across 5 kinds x 1,027 values in the canonical integer domain
    there is exactly one refusal."""
    w = _fixed_world()
    responses = set()
    for kind, (cell, address) in _INJECTIONS.items():
        for value in list(range(1024)) + [2 ** 20, 2 ** 40, 2 ** 53 - 1]:
            observations = _redact(w)
            next(o for o in observations if o["cell_id"] == cell)["base_counts"][address] = value
            responses.add(_outcome(observations, _policy(w)))
    assert responses == {("refused", "StudentV2CRefusal",
                          ("D1 base input contains non-base or unmeasured count",), "None", "None", False)}


def test_the_injected_value_domain_edge_is_the_canonical_integer_limit():
    """Characterization of the declared domain, as in #504: at 2**53 the refusal
    changes to the canonical-domain message. Physically meaningless counts only."""
    w = _fixed_world()
    observations = _redact(w)
    observations[0]["base_counts"]["ENSG_Q"] = 2 ** 53
    assert _outcome(observations, _policy(w))[2] == ("V2C count outside exact integer domain",)


@pytest.mark.parametrize("field", ["library_total", "query_count", "physical_total", "residual"])
def test_no_extra_quantity_can_ride_along_with_a_base_observation(field):
    w = _fixed_world()
    observations = _redact(w)
    observations[0][field] = 42
    assert _outcome(observations, _policy(w))[0] == "refused"


_IMPORT_SCRIPT = r"""
import json, sys
sys.path.insert(0, sys.argv[1])
events, armed = [], [False]
sys.addaudithook(lambda event, args: events.append(event) if armed[0] else None)
import scripts.v5.td_unified.observation_d1_base_only_student_v2c_fixture_v1 as P
request = json.loads(sys.stdin.read())
armed[0] = True
view = P.produce_d1_base_only_student_v2c_fixture(base_observations=request["observations"],
                                                   expected_policy=request["policy"])
observed = sorted(set(events))
open(sys.argv[2], "rb").close()  # positive control: the armed hook must see this
control = sorted(set(events) - set(observed))
armed[0] = False
loaded = sorted(m for m in sys.modules if m == "scripts" or m.startswith("scripts."))
teacher_aware = sorted(m for m, mod in list(sys.modules.items()) if mod is not None and any(
    hasattr(mod, name) for name in ("_VIEW_BINDINGS", "validate_fixture_observation_view_v2_bound",
                                    "validate_public_student_v2b", "produce_fixture_teacher_view_v2_bound")))
print(json.dumps({"loaded": loaded, "teacher_aware": teacher_aware, "events": observed, "control": control,
                  "status": view["view_kind"]}))
"""


def test_the_composed_path_loads_no_legacy_or_teacher_aware_module():
    """Runtime import graph, not only the producer's own import statements: a
    fresh interpreter that imports and runs the producer holds exactly the two
    new modules (plus namespace packages), no module exposing a teacher
    registry, teacher producer or the #502/#510 validators, and the run raises
    no audit event (positive control: an open is seen)."""
    w = _fixed_world()
    payload = json.dumps({"observations": _redact(w), "policy": _policy(w)})
    with tempfile.TemporaryDirectory() as td:
        done = subprocess.run([sys.executable, "-I", "-B", "-c", _IMPORT_SCRIPT, str(REPO),
                               str(Path(P.__file__))], input=payload, text=True, capture_output=True,
                              cwd=td, check=True)
    result = json.loads(done.stdout)
    assert result["loaded"] == ["scripts", "scripts.v5", "scripts.v5.td_unified",
                                "scripts.v5.td_unified.observation_d1_base_only_student_v2c_fixture_v1",
                                "scripts.v5.td_unified.observation_v2c_standalone_student_gate_v1"]
    assert not set(result["loaded"]) & set(LEGACY)
    assert result["teacher_aware"] == []
    assert "open" in result["control"] and result["events"] == []
    assert result["status"] == "STUDENT_BASE_RIGHTS"


def test_the_four_observation_states_stay_distinct_through_the_composition():
    w = _fixed_world()
    view, _ = _view_and_receipt(w)
    rows = {(r["cell_id"], r["address_id"]): r for r in view["rows"]}
    triples = {k: (r["state"], r["count"], r["base_rights_normalization_depth"]) for k, r in rows.items()}
    assert triples["M515_C0", "ENSG_B"] == (MS, 0, 7)                 # measured zero
    assert triples["M515_C2", "ENSG_Z"] == (SU, None, None)           # structural absence
    assert triples["M515_C0", "ENSG_U"] == (MCU, None, None)          # unresolved collision
    assert triples["M515_C0", "ENSG_E"] == (WITHHELD, None, None)     # rights-withheld
    assert triples["M515_C0", "ENSG_Q"] == (WITHHELD, None, None)     # the query itself
    assert triples["M515_C2", "ENSG_E"] == (SU, None, None)           # withheld right, absent here
    assert _produce(_redact(w, omit_zeros=False), _policy(w)) == view  # explicit zero == omitted zero
    for cell, address in (("M515_C2", "ENSG_Z"), ("M515_C0", "ENSG_U"), ("M515_C0", "ENSG_E")):
        observations = _redact(w)
        next(o for o in observations if o["cell_id"] == cell)["base_counts"][address] = 0
        assert _outcome(observations, _policy(w))[0] == "refused", (cell, address)
    structural = deepcopy(w)
    structural["states"]["M515_O1"]["ENSG_B"] = SU
    del structural["full"]["M515_C0"]["ENSG_B"]
    structural["full"]["M515_C1"]["ENSG_B"] = 0
    other, _ = _view_and_receipt(structural, _redact(structural))
    assert next(r for r in other["rows"] if (r["cell_id"], r["address_id"]) == ("M515_C0", "ENSG_B"))["state"] == SU
    assert other["observable_sha256"] != view["observable_sha256"]


def _forgery(kind):
    w = _fixed_world()
    if kind == "count_conserving_swap":
        w["full"]["M515_C0"]["ENSG_A"], w["full"]["M515_C0"]["ENSG_Z"] = 2, 5
    elif kind == "fabricated_counts":
        w["full"]["M515_C1"]["ENSG_A"] = 400
    elif kind == "wrong_gene_identity":
        w["full"]["M515_C1"]["ENSG_A"], w["full"]["M515_C1"]["ENSG_B"] = 3, 4
    elif kind == "forged_roster":
        w["roster"][1]["donor_id"] = "M515_D0"
    elif kind == "forged_source":
        w["roster"][2]["source_id"] = "M515_S1"
    elif kind == "forged_query_rights":
        w["rights"]["ENSG_Q"], w["rights"]["ENSG_E"] = "RNA:EXT", "RNA:QUERY"
        w["states"]["M515_O2"]["ENSG_E"] = MS
        w["full"]["M515_C2"]["ENSG_E"] = 1
        w["query"] = "ENSG_E"
    elif kind == "self_issued_world":
        w = _rename(_rename(w, "M515_D1", "INVENTED_DONOR"), "M515_S2", "INVENTED_SOURCE")
        w["full"] = {c: {a: 99 for a in counts} for c, counts in w["full"].items()}
    return w


@pytest.mark.parametrize("kind", ["count_conserving_swap", "fabricated_counts", "wrong_gene_identity",
                                  "forged_roster", "forged_source", "forged_query_rights", "self_issued_world"])
def test_forgeries_move_the_commitment_but_never_gain_authentication_status(kind):
    _, honest = _view_and_receipt(_fixed_world())
    view, forged = _view_and_receipt(_forgery(kind))
    assert forged["receipt_sha256"] != honest["receipt_sha256"]
    assert _undigested(forged) == _undigested(honest)
    assert forged["status"] == STATUS and forged["authority_effect"] == view["authority_effect"] == "NONE"
    for obj in (view, forged):
        flags = {k: v for k, v in obj.items() if type(v) is bool}
        assert flags and set(flags.values()) == {False}, flags


class _RaisingKey:
    def __init__(self, twin):
        self.twin = twin

    def __hash__(self):
        return hash(self.twin)

    def __eq__(self, other):
        if not _ARM["on"]:
            return False
        _ARM["ran"].append("RaisingKey.__eq__")
        raise RuntimeError("attacker code ran")


@pytest.mark.parametrize("where", ["policy", "policy.address_rights", "policy.cell_roster[0]",
                                   "observations[0]", "observations[0].base_counts"])
def test_the_composed_entry_never_dispatches_caller_objects(where):
    """The #514 role-check defect is unreachable through the producer: it
    snapshots both inputs with no lookup, and hands V2C an exact-type view."""
    w = _fixed_world()
    policy, observations = _policy(w), _redact(w)
    target, twin = {"policy": (policy, "cell_roster"), "policy.address_rights": (policy["address_rights"], "ENSG_A"),
                    "policy.cell_roster[0]": (policy["cell_roster"][0], "cell_id"),
                    "observations[0]": (observations[0], "cell_id"),
                    "observations[0].base_counts": (observations[0]["base_counts"], "ENSG_A")}[where]
    target[_RaisingKey(twin)] = "m515"  # hash collides with an existing key
    _ARM["on"] = True
    outcome = _outcome(observations, policy)
    _ARM["on"] = False
    assert outcome[0] == "refused" and _ARM["ran"] == [], (outcome, _ARM["ran"])


# ---------------------------------------------------- unresolved boundaries (synthetic)

def test_known_query_alias_d1_leak_is_refused_before_receipt():
    """#518 historical witness demonstrated q molecules leaking through D1.
    The original frozen source/negative evidence remains unchanged. The adopted
    conservative rule now refuses the affected query, rather than claiming to
    separate two source features without a trusted issuer."""
    base = _rename(_rename(_fixed_world(), "ENSG_Q", "ENSG00000235481"),
                   "ENSG_A", "ENSG00000233776")
    for q in (0, 1, 31, 63):
        w = deepcopy(base)
        for cell in w["roster"]:
            w["full"][cell["cell_id"]]["ENSG00000235481"] = q
            w["full"][cell["cell_id"]]["ENSG00000233776"] += q
        assert _outcome(_redact(w), _policy(w))[0] == "refused"
    for blocked_id in ("ENSG00000257612", "ENSG00000257842", "ENSG00000258081"):
        w = _rename(_fixed_world(), "ENSG_Q", blocked_id)
        assert _outcome(_redact(w), _policy(w))[0] == "refused"


def _selection_world(q_floor_cell):
    """Upstream QC keeps a cell when its detected ledger genes (query included)
    reach a floor, like a depositor's genes-detected cut. Cell F sits one gene
    below the floor unless its own query count is positive."""
    w = _fixed_world()
    w["roster"].append(dict(zip(CELL_KEYS, ("M515_CF", "M515_D3", "M515_S1", "M515_O1"))))
    w["full"]["M515_CF"] = {"ENSG_A": 1, "ENSG_B": 1, "ENSG_Z": 1, "ENSG_E": 0, "ENSG_Q": q_floor_cell}
    w["collision"]["M515_CF"], w["off_ledger"]["M515_CF"] = 0, 0
    floor = 4
    kept = [c for c in w["roster"] if sum(1 for n in w["full"][c["cell_id"]].values() if n > 0) >= floor]
    w["roster"] = kept
    return w


def test_limit_query_dependent_roster_selection_leaks_through_the_roster():
    """Two worlds differ only in one cell's hidden query count. A query-dependent
    upstream selection changes the roster, so the student learns that cell's
    query was detected. Both receipts are ordinary; the composition names this
    only as depositor_qc_selection_authenticated=False, and nothing in the view,
    receipt or producer output claims a query-independent selection."""
    absent, present = _view_and_receipt(_selection_world(0)), _view_and_receipt(_selection_world(3))
    cells = [{r["cell_id"] for r in view["rows"]} for view, _ in (absent, present)]
    assert "M515_CF" not in cells[0] and "M515_CF" in cells[1]
    for view, receipt in (absent, present):
        assert receipt["status"] == STATUS and receipt["depositor_qc_selection_authenticated"] is False
        text = json.dumps([view, receipt]).lower()
        assert "independen" not in text and "selection_authenticated\": true" not in text


def test_limit_a_self_declared_pseudo_address_carries_off_ledger_mass_into_d1():
    """'Cannot enter the interface' holds only against an authenticated address
    universe: a policy that declares a base 'address' for residual mass makes D1
    equal the whole physical library, and the receipt is ordinary."""
    w = _fixed_world()
    w["rights"]["ENSG_RESIDUAL"] = "RNA:BASE"
    for states in w["states"].values():
        states["ENSG_RESIDUAL"] = MS
    for cell in w["roster"]:
        cid = cell["cell_id"]
        w["full"][cid]["ENSG_RESIDUAL"] = _physical_total(_fixed_world(), cell) - _d1(_fixed_world(), cell)
    view, receipt = _view_and_receipt(w)
    for cell in _fixed_world()["roster"]:
        depth = {r["base_rights_normalization_depth"] for r in view["rows"]
                 if r["cell_id"] == cell["cell_id"] and r["state"] == MS}
        assert depth == {_physical_total(_fixed_world(), cell)}
    assert receipt["status"] == STATUS


def test_limit_a_wrong_support_state_turns_structural_absence_into_a_measured_zero():
    """The deposit for O2 lacks ENSG_B (true state: structurally unmeasured). A
    policy that declares it measured makes the absent gene a measured zero,
    because omitted base counts mean zero. Only an authenticated support matrix
    can prevent this."""
    truth = _fixed_world()
    truth["states"]["M515_O2"]["ENSG_B"] = SU
    del truth["full"]["M515_C2"]["ENSG_B"]
    wrong = deepcopy(truth)
    wrong["states"]["M515_O2"]["ENSG_B"] = MS
    honest_view, _ = _view_and_receipt(truth)
    wrong_view, wrong_receipt = _view_and_receipt(wrong, _redact(truth))
    key = ("M515_C2", "ENSG_B")
    pick = lambda v: next((r["state"], r["count"]) for r in v["rows"] if (r["cell_id"], r["address_id"]) == key)
    assert pick(honest_view) == (SU, None) and pick(wrong_view) == (MS, 0)
    assert wrong_receipt["status"] == STATUS


def test_limit_the_producer_returns_a_view_only_and_receipts_are_mintable():
    w = _fixed_world()
    view = _produce(_redact(w), _policy(w))
    assert "receipt_sha256" not in view and "status" not in view
    tampered = deepcopy(view)
    next(r for r in tampered["rows"] if r["address_id"] == "ENSG_Q" and r["cell_id"] == "M515_C0").update(
        state=MS, count=7, base_rights_normalization_depth=7)
    tampered["observable_sha256"] = _digest({k: v for k, v in tampered.items() if k != "observable_sha256"})
    with pytest.raises(C.StudentV2CRefusal):
        C.validate_student_v2c(student_view=tampered, expected_policy=_policy(w))
    honest = C.validate_student_v2c(student_view=view, expected_policy=_policy(w))
    minted = {**{k: v for k, v in honest.items() if k != "receipt_sha256"},
              "validated_student_view_sha256": tampered["observable_sha256"]}
    minted["receipt_sha256"] = _digest(minted)
    assert set(minted) == set(honest) and minted["status"] == STATUS


_LAUNCH_SCRIPT = r"""
import importlib.util, json, sys, sysconfig
spec = importlib.util.spec_from_file_location("student_only_v2c", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
sys.path[:0] = [sys.argv[2], sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]]
import scripts.v5.td_unified.observation_d1_base_only_student_v2c_fixture_v1 as producer
import scripts.v5.td_unified.observation_normalization_view_v2_bound_content_v1 as teacher_module
with open(sys.argv[3], encoding="utf8") as handle:
    private = json.load(handle)
print(json.dumps({"producer_callable": callable(producer.produce_d1_base_only_student_v2c_fixture),
                  "teacher_validator_callable": callable(teacher_module.validate_fixture_observation_view_v2_bound),
                  "private_query_counts_read": {c: v["ENSG_Q"] for c, v in private["full"].items()}}))
"""


def test_limit_the_composed_path_has_no_student_process_boundary():
    """STUDENT_PROCESS_ISOLATION_NOT_YET_DEMONSTRATED. In the author's
    `python -I -S -B` verifier-only launch, student code still imports the
    producer and the #502 teacher-aware module from the readable tree, and
    reads the teacher's full-count file written by another process."""
    w = _fixed_world()
    with tempfile.TemporaryDirectory() as teacher_dir, tempfile.TemporaryDirectory() as student_dir:
        private = Path(teacher_dir) / "teacher_private_full_counts.json"
        private.write_text(json.dumps({"full": w["full"]}), encoding="utf8")
        copy = Path(student_dir) / "student_v2c.py"
        copy.write_bytes((REPO / "scripts" / "v5" / "td_unified" /
                          "observation_v2c_standalone_student_gate_v1.py").read_bytes())
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        done = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", _LAUNCH_SCRIPT, str(copy), str(REPO),
                               str(private)], text=True, capture_output=True, cwd=student_dir, env=env,
                              check=True)
    assert json.loads(done.stdout) == {"producer_callable": True, "teacher_validator_callable": True,
                                       "private_query_counts_read": {"M515_C0": 7, "M515_C1": 5, "M515_C2": 11}}
