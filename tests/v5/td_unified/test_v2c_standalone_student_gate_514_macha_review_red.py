"""Macha independent review of PR #514 (standalone V2C student verifier) at 63099f6b.

Tests only, fixture only, synthetic, no human data. Nothing here authenticates a
source, a feature map, a rights issuer, a physical unit, a donor or a deployment.

RED tests (prefix test_red_) state required behavior the reviewed head does not
have; they are expected to fail at 63099f6b. GREEN tests are guards. Tests
prefixed test_limit_ are characterizations of limitations V2C expressly
disclaims; they pass while the limitation is present.

Student views are built here independently of the #502 teacher-aware producer
and signed with an independent canonical-JSON encoder. The unchanged Macha #507
(blob d5981430) and #512 (blob 1a915431) files are carried beside this one so
their original RED results can be read at this head.
"""
from collections import OrderedDict, defaultdict
from copy import deepcopy
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unicodedata

import pytest

from scripts.v5.td_unified import observation_v2c_standalone_student_gate_v1 as C

try:
    import numpy as np
except ImportError:  # pragma: no cover - CI installs numpy
    np = None

MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
WITHHELD = "WITHHELD_BY_EVIDENCE_RIGHTS"
STUDENT, TEACHER = "STUDENT_BASE_RIGHTS", "TEACHER_RICHER_RIGHTS"
SCHEMA = "TD_OBSERVATION_NORMALIZATION_VIEW_V2_BOUND_CONTENT_V1_FIXTURE"
DEPTH = "BASE_RIGHTS_INVARIANT_NORMALIZATION_DEPTH_NOT_PHYSICAL_TOTAL"
DOMAIN = b"JEPA-TD-UNIFIED-CANONICAL-V1\x00"
FLAGS = ("source_authenticated", "donor_identity_authenticated",
         "physical_measurement_identity_authenticated", "q_rights_issuer_authenticated",
         "source_feature_mapping_authenticated", "external_truth_access_authorized",
         "same_code_path_authorized", "real_training_authorized")
STATUS = "STUDENT_ONLY_CONTENT_POLICY_CONSISTENT_NO_AUTHORITY"
REPO = Path(__file__).resolve().parents[3]
V2C_FILE = REPO / "scripts" / "v5" / "td_unified" / "observation_v2c_standalone_student_gate_v1.py"
CELL_KEYS = ("cell_id", "donor_id", "source_id", "operator_id")

# Two operators so every observation state occurs: A/B/Z/U carry the base
# right, Q is the query, E an extension right. In O1, U is a collision; in O2,
# Z and E are structurally absent. C0 holds a measured zero for B.
_RIGHTS = {"A": "RNA:BASE", "B": "RNA:BASE", "Z": "RNA:BASE", "U": "RNA:BASE",
           "Q": "RNA:QUERY", "E": "RNA:EXT"}
_STATES = {"M514_O1": {"A": MS, "B": MS, "Z": MS, "U": MCU, "Q": MS, "E": MS},
           "M514_O2": {"A": MS, "B": MS, "Z": SU, "U": MCU, "Q": MS, "E": SU}}
_BASE = {"M514_C0": {"A": 5, "B": 0, "Z": 2}, "M514_C1": {"A": 4, "B": 3, "Z": 1},
         "M514_C2": {"A": 6, "B": 2}}
_ROSTER = (("M514_C0", "M514_D0", "M514_S1", "M514_O1"),
           ("M514_C1", "M514_D1", "M514_S1", "M514_O1"),
           ("M514_C2", "M514_D2", "M514_S2", "M514_O2"))
_ARM = {"on": False, "ran": []}


@pytest.fixture(autouse=True)
def _disarm():
    _ARM["on"], _ARM["ran"] = False, []
    yield
    _ARM["on"], _ARM["ran"] = False, []


def _digest(x):
    """Independent canonical encoder: sorted compact JSON under the declared domain."""
    text = json.dumps(x, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(DOMAIN + text.encode("utf8")).hexdigest()


def _world(hidden=(7, 5, 11)):
    """`hidden` is the per-cell query count. It never reaches the student view or
    policy; it only defines the teacher's full view of the same cells."""
    return {"query": "Q", "base_rights": ["RNA:BASE"], "rights": dict(_RIGHTS),
            "states": deepcopy(_STATES), "base_counts": deepcopy(_BASE),
            "roster": [dict(zip(CELL_KEYS, r)) for r in _ROSTER],
            "hidden_q": dict(zip(sorted(_BASE), hidden))}


def _sign(view, signer=_digest):
    body = {k: v for k, v in view.items() if k != "observable_sha256"}
    return {**body, "observable_sha256": signer(body)}


def _view(w, kind=STUDENT, reveal=None):
    """Student view from base counts only. `reveal` maps cell -> {address: count}
    for withheld addresses a teacher-like candidate exposes."""
    base = set(w["base_rights"])
    rows = []
    for cell in sorted(w["roster"], key=lambda c: c["cell_id"]):
        states, counts = w["states"][cell["operator_id"]], w["base_counts"][cell["cell_id"]]
        d1 = sum(n for a, n in counts.items() if states[a] == MS and w["rights"][a] in base)
        for a in sorted(w["rights"]):
            exposed = (reveal or {}).get(cell["cell_id"], {})
            if states[a] == MS and w["rights"][a] in base:
                state, n, d = MS, counts.get(a, 0), d1
            elif states[a] == MS and a in exposed:
                state, n, d = MS, exposed[a], d1
            elif states[a] == MS:
                state, n, d = WITHHELD, None, None
            else:
                state, n, d = states[a], None, None
            rows.append({**cell, "address_id": a, "evidence_right": w["rights"][a], "state": state,
                         "count": n, "base_rights_normalization_depth": d})
    body = {"schema": SCHEMA, "view_kind": kind, "authority_scope": "FIXTURE_ONLY",
            "query_address_id": w["query"], "reader_partition": "reader_fit",
            "depth_semantics": DEPTH, "rows": rows, **{f: False for f in FLAGS},
            "authority_effect": "NONE"}
    return _sign(body)


def _policy(w):
    return {"query_address_id": w["query"], "base_evidence_rights": list(w["base_rights"]),
            "address_rights": dict(w["rights"]), "operator_states": deepcopy(w["states"]),
            "cell_roster": deepcopy(w["roster"])}


def _rename(x, old, new):
    """Replace every string equal to `old`, keys included, in a JSON-like object."""
    if isinstance(x, dict):
        return {_rename(k, old, new): _rename(v, old, new) for k, v in x.items()}
    if isinstance(x, list):
        return [_rename(v, old, new) for v in x]
    return new if x == old else x


def _outcome(view, policy):
    """Complete observable response: exact receipt bytes, the whole refusal, or an escape."""
    try:
        receipt = C.validate_student_v2c(student_view=view, expected_policy=policy)
    except C.StudentV2CRefusal as exc:
        return ("refused", type(exc).__name__, exc.args, repr(exc.__cause__), repr(exc.__context__),
                exc.__suppress_context__)
    except Exception as exc:  # noqa: BLE001 - an escape is the finding
        return ("ESCAPED", type(exc).__name__, str(exc))
    return ("receipt", json.dumps(receipt, sort_keys=True))


def _receipt(view, policy):
    return C.validate_student_v2c(student_view=view, expected_policy=policy)


def _row(view, cell, address):
    return next(r for r in view["rows"] if r["cell_id"] == cell and r["address_id"] == address)


# ---------------------------------------------------------------- RED cases

class _RaisingKey:
    def __hash__(self):
        return hash("view_kind")

    def __eq__(self, other):
        if _ARM["on"]:
            _ARM["ran"].append("RaisingKey.__eq__")
            raise RuntimeError("attacker code ran inside the V2C role check")
        return False


class _StrSubclassKey(str):
    def __hash__(self):
        return str.__hash__("view_kind")

    def __eq__(self, other):
        if _ARM["on"]:
            _ARM["ran"].append("StrSubclassKey.__eq__")
            raise LookupError("attacker code ran inside the V2C role check")
        return str.__eq__(self, other)


class _PoisonTruth:
    def __bool__(self):
        raise ZeroDivisionError("attacker truth value")


class _PoisonEqKey:
    def __hash__(self):
        return hash("view_kind")

    def __eq__(self, other):
        if _ARM["on"]:
            _ARM["ran"].append("PoisonEqKey.__eq__")
            return _PoisonTruth()
        return False


_HOSTILE_KEYS = {"raising_eq": lambda: _RaisingKey(), "str_subclass": lambda: _StrSubclassKey("m514"),
                 "poisoned_truth": lambda: _PoisonEqKey()}


@pytest.mark.parametrize("key_kind", sorted(_HOSTILE_KEYS))
def test_red_role_check_runs_attacker_equality_before_the_snapshot(key_kind):
    """Hostile input. The role is read with dict.get on the caller's live dict
    before the strict snapshot. A top-level key whose hash equals hash('view_kind')
    makes that lookup call the key's own __eq__, so attacker code runs and its
    exception escapes as a raw RuntimeError/LookupError/ZeroDivisionError instead
    of StudentV2CRefusal. The module promises a 'strict snapshot before any
    potentially attacker-controlled dispatch' and that StudentV2CRefusal covers
    'all unqualified input ... including hostile types'; the author's own test
    asserts the same invariant for a hostile view_kind *value*. Nested positions
    are safe (see test_hostile_keys_below_the_top_level_never_dispatch)."""
    w = _world()
    view = {_HOSTILE_KEYS[key_kind](): "m514"}
    view.update(_view(w))
    _ARM["on"] = True
    outcome = _outcome(view, _policy(w))
    _ARM["on"] = False
    assert outcome[0] == "refused" and _ARM["ran"] == [], (outcome, _ARM["ran"])


def test_red_receipt_is_issued_for_a_snapshot_whose_role_was_never_checked():
    """Time of check != time of use. The role is read twice from the caller's
    live dict (one read type-checked, the other compared) and never from the
    snapshot that is digested and receipted. A key whose __eq__ runs during the
    second read swaps in an object whose __ne__ runs after the comparison,
    restores TEACHER_RICHER_RIGHTS and deletes the key. V2C then snapshots a
    teacher-labelled view and returns a STUDENT_ONLY receipt committing to it.
    No withheld value is exposed (rows still obey the student rules), but the
    'accepts STUDENT_BASE_RIGHTS only' contract is false for the receipted bytes."""
    w = _world()
    labelled = _view(w, kind=TEACHER)
    assert _outcome(labelled, _policy(w))[0] == "refused"  # the label is enforced when read honestly
    calls = []

    class Restore:
        def __init__(self, live, key):
            self.live, self.key = live, key

        def __ne__(self, other):
            self.live["view_kind"] = TEACHER
            del self.live[self.key]
            return False

        __hash__ = None

    class Swap:
        live = None

        def __hash__(self):
            return hash("view_kind")

        def __eq__(self, other):
            if _ARM["on"]:
                calls.append(1)
                if len(calls) == 2:
                    self.live["view_kind"] = Restore(self.live, self)
            return False

    live, key = {}, Swap()
    key.live = live
    live[key] = None
    live.update(labelled)
    live["view_kind"] = STUDENT
    _ARM["on"] = True
    outcome = _outcome(live, _policy(w))
    _ARM["on"] = False
    receipted_label = live.get("view_kind")
    assert outcome[0] == "refused", (
        f"V2C receipted a snapshot labelled {receipted_label!r}; receipt digest names the "
        f"teacher-labelled bytes: {outcome[0] == 'receipt' and labelled['observable_sha256'] in outcome[1]}")


# ---------------------------------------------------------------- GREEN guards

def test_v2c_digests_agree_with_an_independent_canonical_json_encoder():
    w = _world()
    view, policy = _view(w), _policy(w)
    r = _receipt(view, policy)
    assert C._sha({k: x for k, x in view.items() if k != "observable_sha256"}) == view["observable_sha256"]
    assert r["status"] == STATUS
    assert r["validated_student_view_sha256"] == view["observable_sha256"]
    assert r["complete_policy_sha256"] == _digest(policy)
    assert r["receipt_sha256"] == _digest({k: x for k, x in r.items() if k != "receipt_sha256"})
    assert all(r[k] is False for k in r if k.endswith(("_authenticated", "_authorized")))


def _guesses():
    for g in range(1024):
        yield {"M514_C0": {"Q": g % 8, "E": g % 3}, "M514_C1": {"Q": (g // 8) % 8, "E": 0},
               "M514_C2": {"Q": g // 64}}


def test_teacher_candidates_get_one_world_independent_response():
    """Hidden-query noninterference and the #502 membership oracle. Four worlds
    differ only in hidden query counts (each world's truth is among the guesses).
    For 1,024 teacher-labelled guesses, the same 1,024 relabelled as student, and
    each world's true teacher view (2,049 per world), every response must be
    identical across worlds, and each family must get one constant refusal."""
    worlds = [_world(h) for h in ((7, 5, 11), (0, 0, 0), (3, 7, 15), (1, 2, 3))]
    guesses = list(_guesses())
    teacher_family = [_view(worlds[0], TEACHER, g) for g in guesses]
    exposed_family = [_view(worlds[0], STUDENT, g) for g in guesses]
    per_world = []
    for w in worlds:
        assert _view(w) == _view(worlds[0]) and _policy(w) == _policy(worlds[0])
        q0, q1, q2 = (w["hidden_q"][c] for c in sorted(w["hidden_q"]))
        truth = guesses[q0 + 8 * q1 + 64 * q2]
        assert [truth[c]["Q"] for c in sorted(truth)] == [q0, q1, q2]
        policy = _policy(w)
        responses = [_outcome(v, policy) for v in teacher_family + exposed_family]
        responses.append(_outcome(_view(w, TEACHER, truth), policy))
        per_world.append(responses)
    assert all(r == per_world[0] for r in per_world[1:])
    teacher_responses = set(per_world[0][:1024]) | {per_world[0][-1]}
    exposed_responses = set(per_world[0][1024:2048])
    assert len(teacher_responses) == 1 and next(iter(teacher_responses))[0] == "refused"
    assert len(exposed_responses) == 1 and next(iter(exposed_responses))[0] == "refused"


_PURITY_SCRIPT = r"""
import importlib.util, json, sys
spec = importlib.util.spec_from_file_location("v2c_copy", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
cases = json.loads(sys.stdin.read())
events = []
armed = [False]
sys.addaudithook(lambda event, args: events.append(event) if armed[0] else None)
outcomes = []
armed[0] = True
for view, policy in cases:
    try:
        outcomes.append(module.validate_student_v2c(student_view=view, expected_policy=policy)["status"])
    except module.StudentV2CRefusal as exc:
        outcomes.append("refused:" + exc.args[0])
observed = sorted(set(events))
open(sys.argv[1], "rb").close()  # positive control: the armed hook must see this
control = sorted(set(events) - set(observed))
armed[0] = False
print(json.dumps({"events": observed, "control": control, "outcomes": outcomes}))
"""


def test_validation_performs_no_io_import_or_process_event():
    """Runtime purity, not only import-graph purity: with a CPython audit hook
    installed after loading, accepted, refused and teacher-labelled validations
    raise no audit event at all (no open, import, socket, subprocess or os call)."""
    w = _world()
    guess = next(_guesses())
    cases = [(_view(w), _policy(w)), (_view(w, TEACHER, guess), _policy(w)),
             (_view(w, STUDENT, guess), _policy(w)), (_view(w), {**_policy(w), "cell_roster": []})]
    with tempfile.TemporaryDirectory() as td:
        done = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", _PURITY_SCRIPT, str(V2C_FILE)],
                              input=json.dumps(cases), text=True, capture_output=True, cwd=td, check=True)
    result = json.loads(done.stdout)
    assert "open" in result["control"]
    assert result["events"] == []
    assert result["outcomes"][0] == STATUS and all(o.startswith("refused:") for o in result["outcomes"][1:])


def test_module_holds_no_mutable_state_and_returns_no_caller_object():
    mutable = {k: type(v).__name__ for k, v in vars(C).items()
               if not k.startswith("__") and isinstance(v, (dict, list, set, bytearray))}
    assert mutable == {}
    w = _world()
    view, policy = _view(w), _policy(w)
    first = _receipt(view, policy)
    assert all(type(v) in (str, bool) for v in first.values())
    _row(view, "M514_C0", "A")["count"] = 99
    policy["cell_roster"].pop()
    assert _receipt(_view(w), _policy(w)) == first


def _variant(kind):
    w = _world()
    if kind == "drop_cell":
        w["roster"] = [c for c in w["roster"] if c["cell_id"] != "M514_C1"]
        del w["base_counts"]["M514_C1"]
    elif kind == "add_cell":
        w["roster"].append(dict(zip(CELL_KEYS, ("M514_C3", "M514_D3", "M514_S2", "M514_O2"))))
        w["base_counts"]["M514_C3"] = {"A": 1}
    elif kind == "relabel_donor":
        w["roster"][1]["donor_id"] = "M514_D9"
    elif kind == "relabel_source":
        w["roster"][2]["source_id"] = "M514_S9"
    elif kind == "move_cell_operator":
        w["roster"][1]["operator_id"] = "M514_O2"
        del w["base_counts"]["M514_C1"]["Z"]
    elif kind == "operator_state_substitution":
        w["states"]["M514_O1"]["B"] = SU
        for c in ("M514_C0", "M514_C1"):
            del w["base_counts"][c]["B"]
    elif kind == "query_readdressed":
        w["rights"]["Q2"] = "RNA:QUERY"
        for s in w["states"].values():
            s["Q2"] = MS
        w["query"] = "Q2"
    elif kind == "base_promotion":
        w["rights"]["E"] = "RNA:BASE"
        w["base_counts"]["M514_C0"]["E"] = 3
    elif kind == "rights_class_renamed":
        w["rights"] = {a: r.replace("RNA:BASE", "RNA:BASE_V2") for a, r in w["rights"].items()}
        w["base_rights"] = ["RNA:BASE_V2"]
    elif kind == "base_ladder_extended":
        w["base_rights"] = ["RNA:BASE", "RNA:UNUSED"]
    elif kind == "alias_address_declared":
        w["rights"]["Q_ALIAS"] = "RNA:QUERY"
        for s in w["states"].values():
            s["Q_ALIAS"] = MS
    return w


_POLICY_VARIANTS = ("drop_cell", "add_cell", "relabel_donor", "relabel_source", "move_cell_operator",
                    "operator_state_substitution", "query_readdressed", "base_promotion",
                    "rights_class_renamed", "base_ladder_extended", "alias_address_declared")


@pytest.mark.parametrize("kind", _POLICY_VARIANTS)
def test_receipt_names_exactly_the_policy_it_enforced(kind):
    """Policy and roster integrity: donor, source, operator, roster, query
    address, rights classes, ladder and structural states all move the
    commitment, and no receipt ever names a policy other than the one enforced."""
    honest_view, honest_policy = _view(_world()), _policy(_world())
    honest = _receipt(honest_view, honest_policy)
    w = _variant(kind)
    changed = _receipt(_view(w), _policy(w))
    assert changed["complete_policy_sha256"] == _digest(_policy(w)) != honest["complete_policy_sha256"]
    assert changed["receipt_sha256"] != honest["receipt_sha256"]
    crossed = _outcome(honest_view, _policy(w))
    assert crossed[0] == "refused" or json.loads(crossed[1])["complete_policy_sha256"] == _digest(_policy(w))


def _content_variant(kind):
    w = _world()
    view = _view(w)
    resign = True
    if kind == "count_conserving_swap":
        _row(view, "M514_C0", "A")["count"], _row(view, "M514_C0", "Z")["count"] = 2, 5
    elif kind == "fabricated_counts":
        _row(view, "M514_C1", "A")["count"] = 40
        for a in ("A", "B", "Z"):
            _row(view, "M514_C1", a)["base_rights_normalization_depth"] = 44
    elif kind == "measured_zero_raised":
        _row(view, "M514_C0", "B")["count"] = 1
        for a in ("A", "B", "Z"):
            _row(view, "M514_C0", a)["base_rights_normalization_depth"] = 8
    elif kind == "inconsistent_view_digest":
        _row(view, "M514_C0", "A")["count"] = 6
        resign = False
    elif kind == "stale_d1":
        _row(view, "M514_C0", "A")["count"] = 6
    elif kind == "measured_zero_relabelled_structural":
        _row(view, "M514_C0", "B").update(state=SU, count=None, base_rights_normalization_depth=None)
    elif kind == "withheld_query_revealed":
        _row(view, "M514_C0", "Q").update(state=MS, count=7, base_rights_normalization_depth=7)
    elif kind == "collision_resolved":
        _row(view, "M514_C0", "U").update(state=MS, count=4, base_rights_normalization_depth=7)
    elif kind == "structural_absence_filled":
        _row(view, "M514_C2", "Z").update(state=MS, count=0, base_rights_normalization_depth=8)
    elif kind == "operator_altered_in_view":
        for r in view["rows"]:
            if r["cell_id"] == "M514_C2":
                r["operator_id"] = "M514_O1"
    elif kind == "donor_altered_in_view":
        for r in view["rows"]:
            if r["cell_id"] == "M514_C1":
                r["donor_id"] = "M514_D0"
    elif kind == "row_dropped":
        view["rows"].pop()
    elif kind == "row_duplicated":
        view["rows"].append(deepcopy(view["rows"][0]))
    elif kind == "evidence_right_relabelled":
        _row(view, "M514_C0", "Q")["evidence_right"] = "RNA:BASE"
    return (_sign(view) if resign else view), _policy(w)


_ACCEPTED_CONTENT = ("count_conserving_swap", "fabricated_counts", "measured_zero_raised")
_REFUSED_CONTENT = ("inconsistent_view_digest", "stale_d1", "measured_zero_relabelled_structural",
                    "withheld_query_revealed", "collision_resolved", "structural_absence_filled",
                    "operator_altered_in_view", "donor_altered_in_view", "row_dropped", "row_duplicated",
                    "evidence_right_relabelled")


@pytest.mark.parametrize("kind", _ACCEPTED_CONTENT + _REFUSED_CONTENT)
def test_view_content_changes_move_the_receipt_or_are_refused(kind):
    honest = _receipt(_view(_world()), _policy(_world()))
    view, policy = _content_variant(kind)
    outcome = _outcome(view, policy)
    if kind in _REFUSED_CONTENT:
        assert outcome[0] == "refused", outcome
        return
    r = json.loads(outcome[1])
    assert r["complete_policy_sha256"] == honest["complete_policy_sha256"]
    assert r["validated_student_view_sha256"] == view["observable_sha256"] != honest["validated_student_view_sha256"]
    assert r["receipt_sha256"] != honest["receipt_sha256"]


@pytest.mark.parametrize("extra", [("query", 7), ("collision", 4), ("off_ledger", 12), ("physical_total", 30)])
def test_d1_must_be_the_measured_base_sum_not_a_physical_or_d2_depth(extra):
    """A self-consistent view whose depth includes query, collision, off-ledger
    or whole-library mass is refused: V2C enforces D1 = sum of measured
    base-right counts, so a D2 or physical-total depth cannot be receipted."""
    w = _world()
    view = _view(w)
    for r in view["rows"]:
        if r["cell_id"] == "M514_C0" and r["state"] == MS:
            r["base_rights_normalization_depth"] = 7 + extra[1]
    assert _outcome(_sign(view), _policy(w))[0] == "refused"


class _HookedMeta(type):
    def __eq__(cls, other):
        _ARM["ran"].append("HookedMeta.__eq__")
        return True

    def __hash__(cls):
        _ARM["ran"].append("HookedMeta.__hash__")
        return 0

    def __repr__(cls):
        _ARM["ran"].append("HookedMeta.__repr__")
        return "A"


class _HookedClass(metaclass=_HookedMeta):
    pass


class _HookedStr(str):
    def __eq__(self, other):
        _ARM["ran"].append("HookedStr.__eq__")
        return True

    def __hash__(self):
        _ARM["ran"].append("HookedStr.__hash__")
        return str.__hash__(self)

    def __str__(self):
        _ARM["ran"].append("HookedStr.__str__")
        return "A"


class _HookedInt(int):
    def __eq__(self, other):
        _ARM["ran"].append("HookedInt.__eq__")
        return True

    def __index__(self):
        _ARM["ran"].append("HookedInt.__index__")
        return 1

    __hash__ = int.__hash__


class _Indexable:
    def __index__(self):
        _ARM["ran"].append("Indexable.__index__")
        return 1


class _DictSub(dict):
    pass


class _ListSub(list):
    pass


def _hostile_values():
    deep = "A"
    for _ in range(40):
        deep = [deep]
    selfref = []
    selfref.append(selfref)
    values = {"float": 1.0, "nan": float("nan"), "bool": True, "bytes": b"A", "tuple": ("A",),
              "set": {"A"}, "frozenset": frozenset({"A"}), "decimal": Decimal(1), "fraction": Fraction(1),
              "complex": 1j, "str_subclass": _HookedStr("A"), "int_subclass": _HookedInt(1),
              "dict_subclass": _DictSub(), "list_subclass": _ListSub(), "ordered_dict": OrderedDict(),
              "defaultdict": defaultdict(list), "int_2_53": 2 ** 53, "neg_2_53": -(2 ** 53),
              "indexable": _Indexable(), "hooked_class": _HookedClass, "deep_nesting": deep,
              "self_reference": selfref, "lone_surrogate": "\ud800", "nul_in_token": "A\x00",
              "padded_token": " A", "empty_token": ""}
    if np is not None:
        values.update({"np_int64": np.int64(1), "np_str": np.str_("A"), "np_array": np.array([1])})
    return values


def _set_policy(path):
    def put(view, policy, x):
        target = policy
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = x
    return put


def _set_view(path):
    def put(view, policy, x):
        target = view
        for step in path[:-1]:
            target = target[step]
        target[path[-1]] = x
    return put


_POSITIONS = {
    "policy.query_address_id": _set_policy(("query_address_id",)),
    "policy.base_evidence_rights[0]": _set_policy(("base_evidence_rights", 0)),
    "policy.address_rights[A]": _set_policy(("address_rights", "A")),
    "policy.operator_states[O1][A]": _set_policy(("operator_states", "M514_O1", "A")),
    "policy.cell_roster[0].donor_id": _set_policy(("cell_roster", 0, "donor_id")),
    "view.query_address_id": _set_view(("query_address_id",)),
    "view.authority_effect": _set_view(("authority_effect",)),
    "view.rows[0].cell_id": _set_view(("rows", 0, "cell_id")),
    "view.rows[0].count": _set_view(("rows", 0, "count")),
    "view.rows[0].base_rights_normalization_depth": _set_view(("rows", 0, "base_rights_normalization_depth")),
}


@pytest.mark.parametrize("position", sorted(_POSITIONS))
def test_unsupported_python_objects_are_refused_without_dispatch(position):
    assert _HookedStr("A") == "B" and _HookedClass == 0 and _ARM["ran"]  # the recorders do fire
    _ARM["ran"] = []
    escapes = {}
    for name, value in _hostile_values().items():
        w = _world()
        view, policy = _view(w), _policy(w)
        _POSITIONS[position](view, policy, value)
        _ARM["ran"] = []
        outcome = _outcome(view, policy)
        if outcome[0] != "refused" or _ARM["ran"]:
            escapes[name] = (outcome[:2], list(_ARM["ran"]))
    assert escapes == {}


@pytest.mark.parametrize("where", ["view.rows[0]", "policy", "policy.address_rights",
                                   "policy.operator_states", "policy.cell_roster[0]"])
def test_hostile_keys_below_the_top_level_never_dispatch(where):
    w = _world()
    view, policy = _view(w), _policy(w)
    target = {"view.rows[0]": lambda: view["rows"][0], "policy": lambda: policy,
              "policy.address_rights": lambda: policy["address_rights"],
              "policy.operator_states": lambda: policy["operator_states"],
              "policy.cell_roster[0]": lambda: policy["cell_roster"][0]}[where]()
    target[_RaisingKey()] = "m514"
    _ARM["on"] = True
    outcome = _outcome(view, policy)
    _ARM["on"] = False
    assert outcome[0] == "refused" and _ARM["ran"] == [], (outcome, _ARM["ran"])


def test_canonical_carriage_return_collision_is_unreachable_by_accepted_input():
    """The encoder folds CR and CRLF into LF, so it is not injective on strings
    holding CR. That collision must be unreachable: every string a receipt can
    commit to is a control-free token or a fixed constant, so any CR/LF variant
    of an identity is refused, here re-signed with V2C's own encoder so that the
    token check, not the digest check, is what refuses."""
    assert C._enc("M514\rC0") == C._enc("M514\nC0") == C._enc("M514\r\nC0")
    for old, new in (("M514_C0", "M514\rC0"), ("M514_C0", "M514\nC0"), ("M514_D1", "M514\r\nD1"),
                     ("M514_S2", "M514\tS2"), ("M514_O1", "M514\x0bO1"), ("RNA:BASE", "RNA:\rBASE")):
        view = _sign(_rename(_view(_world()), old, new), signer=C._sha)
        assert _outcome(view, _policy(_rename(_world(), old, new)))[0] == "refused", (old, new)
    w = _world()
    policy = _policy(w)
    policy["address_rights"]["K\rX"], policy["address_rights"]["K\nX"] = "RNA:EXT", "RNA:EXT"
    assert _outcome(_view(w), policy)[0] == "refused"


# ---------------------------------------------------------------- limitations V2C disclaims

def test_limit_a_coherent_self_supplied_forgery_gets_an_ordinary_receipt():
    """Authentication. A fabricated world (invented donors, sources, roster and a
    different query) checked against its own fabricated policy is as 'consistent'
    as the honest one; the receipt cannot say which policy an issuer released."""
    honest = _receipt(_view(_world()), _policy(_world()))
    w = _world()
    w["roster"] = [dict(zip(CELL_KEYS, (f"FAKE_C{i}", "FAKE_DONOR", "FAKE_SOURCE", "M514_O1")))
                   for i in range(3)]
    w["base_counts"] = {f"FAKE_C{i}": {"A": 50, "B": 50, "Z": 50} for i in range(3)}
    w["rights"]["Q"], w["rights"]["E"], w["query"] = "RNA:EXT", "RNA:QUERY", "E"
    forged = _receipt(_view(w), _policy(w))
    assert forged["status"] == honest["status"] == STATUS
    assert {k: v for k, v in forged.items() if not k.endswith("sha256")} == \
           {k: v for k, v in honest.items() if not k.endswith("sha256")}


def test_limit_a_receipt_can_be_minted_without_running_v2c():
    """The receipt is an unkeyed digest. Anyone can produce one, with the honest
    status, for a view V2C itself refuses (here one exposing the query count). A
    receipt is evidence only for a consumer that re-runs V2C on the bytes."""
    w = _world()
    exposing = _view(w, STUDENT, next(_guesses()))
    assert _outcome(exposing, _policy(w))[0] == "refused"
    template = _receipt(_view(w), _policy(w))
    minted = {k: v for k, v in template.items() if k != "receipt_sha256"}
    minted["validated_student_view_sha256"] = exposing["observable_sha256"]
    minted["receipt_sha256"] = _digest(minted)
    assert set(minted) == set(template) and minted["status"] == STATUS


def test_known_unresolved_query_address_aliases_are_conservatively_refused():
    """The historical #514/#516 source still records the pre-2026-11-04
    positive alias-leak witness. This main-branch regression requires refusal
    after the adopted #513 rights restriction, without inventing an issuer."""
    w = _world()
    policy = _policy(w)
    policy["alias_classes"] = [["Q", "A"]]
    assert _outcome(_view(w), policy)[0] == "refused"
    for query, holder in (
        ("ENSG00000257612", "A"),        # MIR4307HG
        ("ENSG00000257842", "A"),        # LINC02588
        ("ENSG00000258081", "A"),        # ambiguous legacy chr14
        ("ENSG00000235481", "ENSG00000233776"),  # UBE2R2-AS1/legacy
        ("ENSG00000233776", "ENSG00000235481"),  # reciprocal alias query
    ):
        w = _rename(_rename(_world(), "Q", query), "A", holder)
        assert _outcome(_view(w), _policy(w))[0] == "refused"


def test_limit_unicode_lookalike_identities_are_distinct_but_unauthenticated():
    """NFC/NFD and zero-width variants of one cell identity are different tokens:
    the commitment keeps them apart, but nothing says which is the depositor's."""
    digests = set()
    for variant in ("M514_Cé", unicodedata.normalize("NFD", "M514_Cé"), "M514_Cé​"):
        w = _rename(_world(), "M514_C0", variant)
        digests.add(_receipt(_view(w), _policy(w))["validated_student_view_sha256"])
    assert len(digests) == 3


_LAUNCH_SCRIPT = r"""
import importlib.util, json, sys, sysconfig
spec = importlib.util.spec_from_file_location("student_only_v2c", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
legacy = "scripts.v5.td_unified.observation_normalization_view_v2_bound_content_v1"
before = legacy in sys.modules
# No capability the launch withheld is used: the source tree and the
# teacher's file are simply readable by the same operating-system user.
sys.path[:0] = [sys.argv[2], sysconfig.get_paths()["purelib"], sysconfig.get_paths()["platlib"]]
import scripts.v5.td_unified.observation_normalization_view_v2_bound_content_v1 as teacher_module
with open(sys.argv[3], encoding="utf8") as handle:
    private = json.load(handle)
print(json.dumps({"legacy_loaded_by_launch": before,
                  "teacher_validator_callable": callable(teacher_module.validate_fixture_observation_view_v2_bound),
                  "teacher_producer_callable": callable(teacher_module.produce_fixture_teacher_view_v2_bound),
                  "private_query_counts_read": private["hidden_q"]}))
"""


def test_limit_the_standalone_launch_is_not_a_student_process_boundary():
    """STUDENT_PROCESS_ISOLATION_NOT_YET_DEMONSTRATED. Under the author's own
    `python -I -S -B` launch of a copied verifier file, student code can import
    the #502 teacher-aware validator and producer from the readable source tree
    and read a teacher-private file written by another process. No deployment
    artifact (container, sandbox, OS identity or ACL) exists at this head."""
    w = _world()
    with tempfile.TemporaryDirectory() as teacher_dir, tempfile.TemporaryDirectory() as student_dir:
        private = Path(teacher_dir) / "teacher_private_hidden_q.json"
        private.write_text(json.dumps({"hidden_q": w["hidden_q"]}), encoding="utf8")
        copy = Path(student_dir) / "student_only_v2c.py"
        copy.write_bytes(V2C_FILE.read_bytes())
        env = {k: v for k, v in os.environ.items() if not k.startswith("PYTHON")}
        done = subprocess.run([sys.executable, "-I", "-S", "-B", "-c", _LAUNCH_SCRIPT, str(copy), str(REPO),
                               str(private)], text=True, capture_output=True, cwd=student_dir, env=env,
                              check=True)
    result = json.loads(done.stdout)
    assert result == {"legacy_loaded_by_launch": False, "teacher_validator_callable": True,
                      "teacher_producer_callable": True, "private_query_counts_read": w["hidden_q"]}
