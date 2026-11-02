"""Macha independent review of PR #510 (V2B student-only gate) at ef51325d.

Tests only, fixture only, synthetic, no human data. Nothing here authenticates a
source, a feature map, a rights issuer, a physical unit or a donor.

RED tests (prefix test_red_) state required behavior the reviewed head does not
have; they are expected to fail at ef51325d. GREEN tests are guards or
characterizations; a passing characterization means the limitation is present.
The unchanged Macha #507 file (blob d5981430) is carried beside this one so its
original RED results can be read at this head.
"""
from copy import deepcopy
import json

import pytest

from scripts.v5.td_unified import observation_v2b_public_student_gate_v1 as S
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError

B = S.B  # reachable from the V2B module itself; no private name is used to reach it
MS, SU, MCU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"
WITHHELD = "WITHHELD_BY_EVIDENCE_RIGHTS"
STUDENT, TEACHER = "STUDENT_BASE_RIGHTS", "TEACHER_RICHER_RIGHTS"
_LADDER = [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
           {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]}]


@pytest.fixture(autouse=True)
def _fresh_registry():
    registry, lock = getattr(B, "_VIEW_BINDINGS", None), getattr(B, "_VIEW_BINDINGS_LOCK", None)
    if registry is None or lock is None:
        yield
        return
    with lock:
        saved = dict(registry)
        registry.clear()
    try:
        yield
    finally:
        with lock:
            registry.clear()
            registry.update(saved)


def _world(qs=(7, 23)):
    return {"cells": [{"cell_id": f"M510_C{i}", "donor_id": f"M510_D{i}", "source_id": "M510_S",
                       "operator_id": "M510_O", "library_total": 5 + 4 + q, "counts": {"B1": 5, "B2": 4, "Q": q}}
                      for i, q in enumerate(qs)],
            "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "Q": "RNA:QUERY"},
            "operator_states": {"M510_O": {"B1": MS, "B2": MS, "Q": MS}},
            "ladder": deepcopy(_LADDER), "query_address_id": "Q"}


def _policy(w):
    return {"query_address_id": w["query_address_id"],
            "base_evidence_rights": deepcopy(w["ladder"][0]["evidence_rights"]),
            "address_rights": deepcopy(w["address_rights"]),
            "operator_states": deepcopy(w["operator_states"]),
            "cell_roster": [{k: c[k] for k in ("cell_id", "donor_id", "source_id", "operator_id")} for c in w["cells"]]}


def _sign(view):
    body = {k: v for k, v in view.items() if k != "observable_sha256"}
    return {**body, "observable_sha256": B.canonical_sha256(body)}


def _outcome(validate, *args, **kwargs):
    """Complete observable response: exact receipt bytes, or the whole refusal."""
    try:
        receipt = validate(*args, **kwargs)
    except QExcludedObservationError as exc:
        return ("refused", type(exc).__name__, exc.args, repr(exc.__cause__), repr(exc.__context__),
                tuple(getattr(exc, "__notes__", ())))
    return ("receipt", json.dumps(receipt, sort_keys=True))


def _v2b(view, policy):
    return _outcome(S.validate_public_student_v2b, student_view=view, expected_policy=policy)


def _teacher_candidate(student, guess):
    view = deepcopy(student)
    view["view_kind"] = TEACHER
    depth = {r["cell_id"]: r["base_rights_normalization_depth"] for r in view["rows"] if r["state"] == MS}
    for r in view["rows"]:
        if r["state"] == WITHHELD:
            r.update(state=MS, count=guess[r["cell_id"]], base_rights_normalization_depth=depth[r["cell_id"]])
    return _sign(view)


# ---------------------------------------------------------------- RED cases

def test_red_teacher_membership_oracle_is_still_reachable_from_the_v2b_module():
    """Boundary bypass. V2B itself never reads the registry, but the #502 public
    validator stays importable (here as S.B, an attribute of the V2B module) and
    still answers teacher membership. A student holding only its own view and
    the public functions recovers the hidden counts; documentation that it
    'must not be imported at a student boundary' is not a code boundary."""
    student = B.produce_fixture_student_view_v2_bound(**_world())
    B.produce_fixture_teacher_view_v2_bound(**_world())  # the teacher actor's lawful issuance
    recovered = [(q0, q1) for q0 in range(32) for q1 in range(32)
                 if _outcome(S.B.validate_fixture_observation_view_v2_bound,
                             _teacher_candidate(student, {"M510_C0": q0, "M510_C1": q1}))[0] == "receipt"]
    assert recovered == [], f"hidden query counts recovered through a public validator: {recovered}"


def _roster_world(kind):
    w = _world()
    if kind == "drop_cell":
        w["cells"] = w["cells"][:1]
    elif kind == "relabel_donor":
        w["cells"][1]["donor_id"] = "M510_D_OTHER"
    elif kind == "relabel_source":
        w["cells"][1]["source_id"] = "M510_S_OTHER"
    elif kind == "substitute_operator_state":  # a measured base gene declared structurally unmeasured
        w["operator_states"]["M510_O"]["B2"] = SU
        for c in w["cells"]:
            c["library_total"] -= c["counts"].pop("B2")
    return w


@pytest.mark.parametrize("kind", ["drop_cell", "relabel_donor", "relabel_source", "substitute_operator_state"])
def test_red_receipt_commits_to_the_enforced_roster_and_operator_states(kind):
    """Source-roster spoofing and operator-state substitution. V2B enforces the
    roster and operator states, but its receipt commits only to (query, base
    rights, address rights). A view and policy that drop a cell, relabel a
    donor or source, or turn a measured base gene into structural absence
    validate with a receipt byte-identical to the honest one, so a consumer
    holding the honest commitment cannot see the substitution."""
    honest = _v2b(B.produce_fixture_student_view_v2_bound(**_world()), _policy(_world()))
    spoof_world = _roster_world(kind)
    spoof = _v2b(B.produce_fixture_student_view_v2_bound(**spoof_world), _policy(spoof_world))
    assert honest[0] == spoof[0] == "receipt"
    assert spoof != honest, "receipt is identical to the honest receipt"


def _forged_view(kind):
    view = deepcopy(B.produce_fixture_student_view_v2_bound(**_world()))
    for r in view["rows"]:
        if r["cell_id"] != "M510_C0" or r["state"] != MS:
            continue
        if kind == "count_preserving_swap":
            r["count"] = {"B1": 4, "B2": 5}[r["address_id"]]
        elif kind == "query_mass_laundered_into_base":  # q = 7 added to B1 and to D1
            r["base_rights_normalization_depth"] += 7
            r["count"] += 7 if r["address_id"] == "B1" else 0
        elif kind == "fabricated_counts":
            r["count"] = {"B1": 50, "B2": 1}[r["address_id"]]
            r["base_rights_normalization_depth"] = 51
    return _sign(view)


@pytest.mark.parametrize("kind", ["count_preserving_swap", "query_mass_laundered_into_base", "fabricated_counts"])
def test_red_receipt_identifies_the_view_it_validated(kind):
    """D1 integrity and receipt binding. Against the honest frozen policy, a
    count-preserving swap, query molecules laundered into a base count (with D1
    raised to match), or wholly invented counts validate, and the receipt is
    byte-identical to the honest one: it carries no digest of the view it
    certified, so it can be replayed for any view."""
    honest = _v2b(B.produce_fixture_student_view_v2_bound(**_world()), _policy(_world()))
    forged = _v2b(_forged_view(kind), _policy(_world()))
    assert honest[0] == forged[0] == "receipt"
    assert forged != honest, "receipt is identical to the honest receipt"


@pytest.mark.parametrize("element", [["RNA:BASE"], {"right": "RNA:BASE"}], ids=["list", "dict"])
def test_red_malformed_policy_is_refused_with_the_domain_error(element):
    """Noncanonical policy value. set(base) runs before the element type check,
    so an unhashable element escapes as TypeError instead of the domain error."""
    policy = _policy(_world())
    policy["base_evidence_rights"] = [element]
    student = B.produce_fixture_student_view_v2_bound(**_world())
    try:
        S.validate_public_student_v2b(student_view=student, expected_policy=policy)
        escaped = "validated"
    except QExcludedObservationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    assert escaped is None, escaped


# ---------------------------------------------------------------- GREEN guards

def test_v2b_gives_one_complete_response_to_every_teacher_candidate_in_every_hidden_world():
    """2,049 inputs per world (1,024 teacher-role guesses, 1,024 student-role
    guesses that expose a guessed query count, and the actually issued teacher
    view), in four worlds that differ only in hidden counts. Every complete
    response (class, args, cause, context, notes) is identical everywhere."""
    per_world = []
    for qs in ((7, 23), (8, 24), (0, 0), (100, 1)):
        registry = getattr(B, "_VIEW_BINDINGS", None)
        if registry is not None:
            with B._VIEW_BINDINGS_LOCK:
                registry.clear()
        w = _world(qs)
        student = B.produce_fixture_student_view_v2_bound(**w)
        issued_teacher = B.produce_fixture_teacher_view_v2_bound(**w)
        responses = {_v2b(issued_teacher, _policy(w))}
        for q0 in range(32):
            for q1 in range(32):
                guess = {"M510_C0": q0, "M510_C1": q1}
                teacher = _teacher_candidate(student, guess)
                responses.add(_v2b(teacher, _policy(w)))
                responses.add(_v2b(_sign({**teacher, "view_kind": STUDENT}), _policy(w)))
        per_world.append((json.dumps(student, sort_keys=True), _v2b(student, _policy(w)), frozenset(responses)))
    assert all(x == per_world[0] for x in per_world)
    assert len(per_world[0][2]) == 2  # one role refusal, one state refusal; no receipt among them
    assert all(r[0] == "refused" for r in per_world[0][2])


def _committed_substitution(kind):
    w = {"cells": [{"cell_id": "M510_C0", "donor_id": "M510_D0", "source_id": "M510_S", "operator_id": "M510_O",
                    "library_total": 9 + 4 + 11 + 2, "counts": {"B": 9, "E": 4, "Q": 11, "Z": 2}}],
         "address_rights": {"B": "RNA:BASE", "E": "RNA:EXT", "Q": "RNA:QUERY", "Z": "RNA:EXT"},
         "operator_states": {"M510_O": dict.fromkeys(("B", "E", "Q", "Z"), MS)},
         "ladder": deepcopy(_LADDER), "query_address_id": "Q"}
    if kind == "base_promotion":
        w["ladder"][0]["evidence_rights"] = ["RNA:BASE", "RNA:EXT"]
    elif kind == "decoy_query":
        w["address_rights"].update(Q="RNA:BASE", Z="RNA:QUERY")
        w["query_address_id"] = "Z"
    elif kind == "query_relabel_same_rights":
        w["address_rights"].update(Q="RNA:EXT", E="RNA:QUERY")
        w["query_address_id"] = "E"
    elif kind == "drop_address":
        w["cells"][0]["library_total"] -= w["cells"][0]["counts"].pop("Z")
        del w["address_rights"]["Z"], w["operator_states"]["M510_O"]["Z"]
    return w


@pytest.mark.parametrize("kind", ["base_promotion", "decoy_query", "query_relabel_same_rights", "drop_address"])
def test_policy_substitutions_in_committed_fields_change_the_commitment(kind):
    honest_world, spoof_world = _committed_substitution("honest"), _committed_substitution(kind)
    honest = S.validate_public_student_v2b(student_view=B.produce_fixture_student_view_v2_bound(**honest_world),
                                           expected_policy=_policy(honest_world))
    spoof = S.validate_public_student_v2b(student_view=B.produce_fixture_student_view_v2_bound(**spoof_world),
                                          expected_policy=_policy(spoof_world))
    assert spoof["policy_commitment_sha256"] != honest["policy_commitment_sha256"]
    with pytest.raises(QExcludedObservationError):  # and the spoofed view fails the honest policy
        S.validate_public_student_v2b(student_view=B.produce_fixture_student_view_v2_bound(**spoof_world),
                                      expected_policy=_policy(honest_world))


def test_a_phantom_base_right_changes_the_commitment_of_an_unchanged_view():
    """A base right that no address carries leaves the view bytes unchanged
    (issuing both worlds trips #502's first-issuer binding, characterized in
    #507), so only the policy differs; the commitment must still differ."""
    w = _committed_substitution("honest")
    view, honest_policy = B.produce_fixture_student_view_v2_bound(**w), _policy(w)
    phantom_policy = {**honest_policy, "base_evidence_rights": ["RNA:BASE", "RNA:PHANTOM"]}
    honest = S.validate_public_student_v2b(student_view=view, expected_policy=honest_policy)
    phantom = S.validate_public_student_v2b(student_view=view, expected_policy=phantom_policy)
    assert phantom["policy_commitment_sha256"] != honest["policy_commitment_sha256"]


def test_measured_zero_and_structural_absence_are_enforced_against_a_fixed_policy():
    w = _world()
    w["operator_states"]["M510_O"]["B2"] = SU
    for c in w["cells"]:
        c["library_total"] -= c["counts"].pop("B2")
    absent_view, absent_policy = B.produce_fixture_student_view_v2_bound(**w), _policy(w)
    zero_world = _world()
    for c in zero_world["cells"]:
        c["library_total"] -= c["counts"]["B2"]
        c["counts"]["B2"] = 0
    zero_view, zero_policy = B.produce_fixture_student_view_v2_bound(**zero_world), _policy(zero_world)
    assert _v2b(absent_view, absent_policy)[0] == _v2b(zero_view, zero_policy)[0] == "receipt"
    assert _v2b(absent_view, zero_policy)[0] == "refused"  # absence presented as a measured zero policy
    assert _v2b(zero_view, absent_policy)[0] == "refused"  # measured zero presented as absence


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


class _ClassProperty:
    @property
    def __class__(self):
        _Meta.calls.append("__class__")
        return str


class _KeyStr(str):
    def __eq__(self, other):
        _Meta.calls.append("key-eq")
        return str.__eq__(self, other)

    def __hash__(self):
        _Meta.calls.append("key-hash")
        return str.__hash__(self)


class _DictSub(dict):
    pass


def _hostile(where):
    view, policy = B.produce_fixture_student_view_v2_bound(**_world()), _policy(_world())
    return {
        "view_lies": lambda: (_Lies(), policy),
        "policy_raises": lambda: (view, _Raises()),
        "policy_query_lies": lambda: (view, {**policy, "query_address_id": _Lies()}),
        "policy_base_class_property": lambda: (view, {**policy, "base_evidence_rights": [_ClassProperty()]}),
        "policy_right_raises": lambda: (view, {**policy, "address_rights": {**policy["address_rights"], "Q": _Raises()}}),
        "policy_state_key_str_subclass": lambda: (view, {**policy, "operator_states": {
            "M510_O": {_KeyStr(k) if k == "Q" else k: v for k, v in policy["operator_states"]["M510_O"].items()}}}),
        "policy_roster_dict_subclass": lambda: (view, {**policy, "cell_roster": [_DictSub(c) for c in policy["cell_roster"]]}),
        "policy_dict_subclass": lambda: (view, _DictSub(policy)),
        "policy_bool_right": lambda: (view, {**policy, "address_rights": {**policy["address_rights"], "B1": True}}),
        "policy_deep_nesting": lambda: (view, {**policy, "cell_roster": [[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[[0]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]]}),
    }[where]()


_WHERE = ["view_lies", "policy_raises", "policy_query_lies", "policy_base_class_property", "policy_right_raises",
          "policy_state_key_str_subclass", "policy_roster_dict_subclass", "policy_dict_subclass",
          "policy_bool_right", "policy_deep_nesting"]


@pytest.mark.parametrize("where", _WHERE)
def test_hostile_values_are_refused_with_the_domain_error_and_run_no_payload_code(where):
    view, policy = _hostile(where)
    _Meta.calls.clear()
    try:
        S.validate_public_student_v2b(student_view=view, expected_policy=policy)
        escaped = "validated"
    except QExcludedObservationError as exc:
        escaped = None if exc.__cause__ is None else f"cause={type(exc.__cause__).__name__}"
    except BaseException as exc:  # noqa: BLE001
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    assert (escaped, _Meta.calls) == (None, [])


def test_receipt_and_later_validation_are_independent_of_caller_objects_after_return():
    view, policy = B.produce_fixture_student_view_v2_bound(**_world()), _policy(_world())
    first = S.validate_public_student_v2b(student_view=view, expected_policy=policy)
    frozen = json.dumps(first, sort_keys=True)
    policy["base_evidence_rights"].append("RNA:QUERY")
    policy["cell_roster"].pop()
    view["rows"][0]["count"] = 999
    assert json.dumps(first, sort_keys=True) == frozen
    assert _v2b(view, policy)[0] == "refused"


# ------------------------------------------- GREEN characterizations (limitations)

def test_characterize_the_shared_registry_is_readable_and_holds_teacher_digests():
    """LIMITATION (same process). After a lawful teacher issuance the registry
    reachable as S.B._VIEW_BINDINGS holds the teacher digest, which #481 showed
    is an unkeyed commitment openable by enumeration from the student view."""
    B.produce_fixture_student_view_v2_bound(**_world())
    teacher = B.produce_fixture_teacher_view_v2_bound(**_world())
    assert teacher["observable_sha256"] in S.B._VIEW_BINDINGS


def test_characterize_the_policy_cannot_express_alias_classes():
    """LIMITATION (cross-rights alias). The policy schema has no alias-class
    field, so it is refused if one is supplied, and a base-right address that
    carries the query gene's molecules (an in-ledger alias; Macha #509 found 11
    candidate addresses) validates with D1 that contains those molecules."""
    policy = _policy(_world())
    with pytest.raises(QExcludedObservationError, match="separately frozen expected policy"):
        S.validate_public_student_v2b(student_view=B.produce_fixture_student_view_v2_bound(**_world()),
                                      expected_policy={**policy, "alias_classes": [["Q", "B2"]]})
    alias = _world()  # B2 is a base-right alias that also carries Q's molecules
    for c, q in zip(alias["cells"], (7, 23)):
        c["counts"]["B2"] += q
        c["library_total"] += q
    receipt = S.validate_public_student_v2b(student_view=B.produce_fixture_student_view_v2_bound(**alias),
                                            expected_policy=_policy(alias))
    assert receipt["status"] == S.RESULT_STATUS


def test_characterize_a_self_issued_view_and_policy_validate_without_any_issuance():
    """LIMITATION. With an empty registry, a hand-built student view (never
    produced) and a matching self-written policy validate; V2B checks
    consistency, not custody."""
    view = _forged_view("fabricated_counts")
    registry = getattr(B, "_VIEW_BINDINGS", None)
    if registry is not None:
        with B._VIEW_BINDINGS_LOCK:
            registry.clear()
    assert S.validate_public_student_v2b(student_view=view, expected_policy=_policy(_world()))["status"] == S.RESULT_STATUS
