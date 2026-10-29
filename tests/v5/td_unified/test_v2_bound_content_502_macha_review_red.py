"""Macha independent review of PR #502 (V2 rights-bound content consumer) at 0789247c.

Tests only, fixture only, synthetic, no human data. Nothing here authenticates a
source, a feature map, a rights issuer, a physical unit or a donor.

RED tests (prefix test_red_) state required behavior that the reviewed head does
not have; they are expected to fail at 0789247c. GREEN tests are guards or
characterizations; a passing characterization means the limitation is present,
not that it is acceptable.

Every test here calls the NEW bound API directly. None of them is the unmodified
Macha #481 file, which stays byte-identical at blob 3dda6c2c on #481 and as
macha481_review_source_immutable.py on #502. Where a test rebuilds a #481 forgery
on the new API it says so.
"""
from copy import deepcopy

import pytest

from scripts.v5.td_unified import observation_normalization_view_v2_bound_content_v1 as B
from scripts.v5.td_unified import observation_normalization_view_v2_fixture as LEGACY
from scripts.v5.td_unified.q_excluded_depth_v1 import QExcludedObservationError

MS, SU = "MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED"
WITHHELD = "WITHHELD_BY_EVIDENCE_RIGHTS"
STUDENT, TEACHER = "STUDENT_BASE_RIGHTS", "TEACHER_RICHER_RIGHTS"
VALIDATED = "V2_BOUND_CONTENT_FIXTURE_VIEW_VALIDATED_NO_AUTHORITY"
_LADDER = [
    {"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
    {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]},
]


@pytest.fixture(autouse=True)
def _fresh_registry():
    """Isolate the process-local issuer map per test and restore it afterwards."""
    registry = getattr(B, "_VIEW_BINDINGS", None)
    lock = getattr(B, "_VIEW_BINDINGS_LOCK", None)
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


def _outcome(view):
    try:
        return B.validate_fixture_observation_view_v2_bound(view)["status"]
    except QExcludedObservationError as exc:
        return f"refused: {exc}"


def _sign(body):
    body = {k: v for k, v in body.items() if k != "observable_sha256"}
    return {**body, "observable_sha256": B.canonical_sha256(body)}


def _query_world(qs=(7, 23)):
    """Base B and the queried gene Q only, so Q is the sole withheld value."""
    return {"cells": [{"cell_id": f"C{i}", "donor_id": "D", "source_id": "S", "operator_id": "O",
                       "library_total": 9 + q, "counts": {"B": 9, "Q": q}} for i, q in enumerate(qs)],
            "address_rights": {"B": "RNA:BASE", "Q": "RNA:QUERY"},
            "operator_states": {"O": {"B": MS, "Q": MS}},
            "ladder": deepcopy(_LADDER), "query_address_id": "Q"}


def _teacher_candidate(student, guess):
    """Built from the student view alone: every teacher byte except the withheld
    counts is fixed by it (#481 characterization), so only the counts are guessed."""
    body = deepcopy({k: v for k, v in student.items() if k != "observable_sha256"})
    body["view_kind"] = TEACHER
    depth = {r["cell_id"]: r["base_rights_normalization_depth"] for r in body["rows"] if r["state"] == MS}
    for r in body["rows"]:
        if r["state"] == WITHHELD:
            r["state"], r["count"] = MS, guess[r["cell_id"]]
            r["base_rights_normalization_depth"] = depth[r["cell_id"]]
    return _sign(body)


# ---------------------------------------------------------------- RED cases

def test_red_public_validator_is_not_a_membership_oracle_for_teacher_views():
    """Student/teacher leakage. The producer registers the teacher digest in the
    same process map that the single public validator consults, so a holder of
    the student view alone can ask the validator which candidate teacher view was
    issued. At 0789247c exactly one of 1,024 candidates validates: the true
    withheld counts. No teacher digest is needed (the #481 enumeration needed it)."""
    student = B.produce_fixture_student_view_v2_bound(**_query_world())
    B.produce_fixture_teacher_view_v2_bound(**_query_world())  # the teacher actor's lawful issuance
    recovered = [(q0, q1) for q0 in range(32) for q1 in range(32)
                 if _outcome(_teacher_candidate(student, {"C0": q0, "C1": q1})) == VALIDATED]
    assert recovered == [], f"withheld query counts recovered through the public validator: {recovered}"


def test_red_validator_outcome_on_student_constructible_input_is_invariant_to_withheld_counts():
    """The same leak as noninterference: two worlds that differ only in withheld
    counts give byte-identical student views, yet the validator's answer on one
    fixed input built from that student view differs between them."""
    outcomes, students = [], []
    for qs in ((7, 23), (8, 24)):
        registry = getattr(B, "_VIEW_BINDINGS", None)
        if registry is not None:  # a fresh issuing process per world
            with B._VIEW_BINDINGS_LOCK:
                registry.clear()
        student = B.produce_fixture_student_view_v2_bound(**_query_world(qs))
        B.produce_fixture_teacher_view_v2_bound(**_query_world(qs))
        students.append(student)
        outcomes.append(_outcome(_teacher_candidate(student, {"C0": 7, "C1": 23})))
    assert students[0] == students[1]  # precondition: the producer itself is noninterfering
    assert outcomes[0] == outcomes[1], outcomes


def _substitution_world(variant):
    """One physical world (same cells, same counts); only the issuer's policy differs."""
    world = {"cells": [{"cell_id": "C0", "donor_id": "D", "source_id": "S", "operator_id": "O",
                        "library_total": 9 + 4 + 11 + 2, "counts": {"B": 9, "E": 4, "Q": 11, "Z": 2}}],
             "address_rights": {"B": "RNA:BASE", "E": "RNA:EXT", "Q": "RNA:QUERY", "Z": "RNA:EXT"},
             "operator_states": {"O": {"B": MS, "E": MS, "Q": MS, "Z": MS}},
             "ladder": deepcopy(_LADDER), "query_address_id": "Q"}
    if variant == "ext_promoted_into_base":
        world["ladder"][0]["evidence_rights"] = ["RNA:BASE", "RNA:EXT"]
    elif variant == "true_query_relabelled_base_with_decoy_query":
        world["address_rights"].update(Q="RNA:BASE", Z="RNA:QUERY")
        world["query_address_id"] = "Z"
    return world


@pytest.mark.parametrize("variant", ["ext_promoted_into_base", "true_query_relabelled_base_with_decoy_query"])
def test_red_student_receipt_commits_to_the_rights_policy_it_enforced(variant):
    """Rights-roster / base-rights substitution and query relabelling at issuance.
    Any caller can issue, and the binding is whatever that caller supplied. The
    receipt does not say which rights were base or which address was the query,
    so a STUDENT receipt for a view that exposes EXT counts (or the true query
    gene's counts, under a decoy query) is indistinguishable from the honest one
    except for the content digest. A consumer holding a frozen policy cannot check
    the receipt against it."""
    honest_view = B.produce_fixture_student_view_v2_bound(**_substitution_world("honest"))
    swapped_view = B.produce_fixture_student_view_v2_bound(**_substitution_world(variant))
    honest = B.validate_fixture_observation_view_v2_bound(honest_view)
    swapped = B.validate_fixture_observation_view_v2_bound(swapped_view)
    exposed = {r["address_id"]: r["count"] for r in swapped_view["rows"] if r["state"] == MS}
    assert swapped["status"] == VALIDATED and swapped["view_kind"] == STUDENT
    assert exposed.get("E") == 4 or exposed.get("Q") == 11  # the substitution really exposes evidence
    differing = {k for k in set(honest) | set(swapped) if honest.get(k) != swapped.get(k)}
    assert differing - {"observable_sha256"}, "the receipt does not commit to the enforced rights policy"


# ------------------------------------------- GREEN characterizations (limitations)

def _rebuilt_481_world():
    """The #481 RED world, rebuilt here; the forgeries below are #481's A1/A2
    constructions applied to the NEW bound API (adapted, not the original file)."""
    return {"cells": [{"cell_id": "C1", "donor_id": "D1", "source_id": "SRC", "operator_id": "OP",
                       "library_total": 20, "counts": {"B1": 2, "B2": 1, "E1": 7, "Q1": 10}},
                      {"cell_id": "C2", "donor_id": "D2", "source_id": "SRC", "operator_id": "OP",
                       "library_total": 9, "counts": {"B1": 4, "E1": 1, "Q1": 4}}],
            "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "B3": "RNA:BASE",
                               "E1": "RNA:EXT", "Q1": "RNA:QUERY"},
            "operator_states": {"OP": {"B1": MS, "B2": MS, "B3": SU, "E1": MS, "Q1": MS}},
            "ladder": [{"level_id": "L0", "evidence_rights": ["RNA:BASE"]},
                       {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:EXT"]},
                       {"level_id": "L2", "evidence_rights": ["RNA:BASE", "RNA:EXT", "RNA:QUERY"]}],
            "query_address_id": "Q1"}


def test_characterize_adapted_481_a1_a2_forgeries_are_refused_by_registry_membership_only():
    """LIMITATION of the evidence, not of the code. Every #481 A1 depth forgery
    (physical total, depth + q, offset, scaled; student and teacher) and both A2
    exposures, rebuilt on the bound API, are refused by the issued-digest lookup
    before the D1 law runs. The adapted replay's A1/A2 passes therefore show a
    process-local hash allowlist working, not consumer-verifiable content."""
    world = _rebuilt_481_world()
    totals = {c["cell_id"]: c["library_total"] for c in world["cells"]}
    q = {c["cell_id"]: c["counts"]["Q1"] for c in world["cells"]}
    leaks = {"physical_total": lambda d, c: totals[c], "depth_plus_query": lambda d, c: d + q[c],
             "offset": lambda d, c: d + 1, "scaled": lambda d, c: 2 * d}
    messages = []
    for make in (B.produce_fixture_student_view_v2_bound, B.produce_fixture_teacher_view_v2_bound):
        for leak in leaks.values():
            forged = deepcopy(make(**_rebuilt_481_world()))
            for row in forged["rows"]:
                if row["state"] == MS:
                    row["base_rights_normalization_depth"] = leak(row["base_rights_normalization_depth"],
                                                                  row["cell_id"])
            messages.append(_outcome(_sign(forged)))
    for target, query in (("E1", "Q1"), ("Q1", "B3")):
        forged = deepcopy(B.produce_fixture_student_view_v2_bound(**_rebuilt_481_world()))
        forged["query_address_id"] = query
        depth = {r["cell_id"]: r["base_rights_normalization_depth"] for r in forged["rows"] if r["state"] == MS}
        for row in forged["rows"]:
            if row["address_id"] == target:
                row["state"] = MS
                row["count"] = next(c["counts"][target] for c in world["cells"] if c["cell_id"] == row["cell_id"])
                row["base_rights_normalization_depth"] = depth[row["cell_id"]]
        messages.append(_outcome(_sign(forged)))
    assert len(messages) == 10
    assert set(messages) == {"refused: bound-content rights not issued in this fixture process"}


def _inject(forged, honest):
    """#502's own test technique (test_observation_normalization_v2_bound_content.py):
    pretend the producer signed ``forged`` under the honest view's binding."""
    signed = _sign(forged)
    with B._VIEW_BINDINGS_LOCK:
        B._VIEW_BINDINGS[signed["observable_sha256"]] = B._VIEW_BINDINGS[honest["observable_sha256"]]
    return _outcome(signed)


def test_characterize_the_content_law_accepts_d1_preserving_forgeries_under_a_binding():
    """LIMITATION. With a binding present, the D1/coverage/rights law accepts
    forgeries that keep each cell's base sum and address set: a whole cell
    deleted, a donor or source relabelled, base counts swapped. Cell roster,
    identities and per-address values rest only on the process-local registry;
    D1 is a consistency law, not content authentication."""
    world = {"cells": [{"cell_id": f"C{i}", "donor_id": f"D{i}", "source_id": "S", "operator_id": "O",
                        "library_total": 5 + 2 + q, "counts": {"B1": 5, "B2": 2, "Q": q}}
                       for i, q in enumerate((3, 8))],
             "address_rights": {"B1": "RNA:BASE", "B2": "RNA:BASE", "Q": "RNA:QUERY"},
             "operator_states": {"O": {"B1": MS, "B2": MS, "Q": MS}},
             "ladder": deepcopy(_LADDER), "query_address_id": "Q"}
    honest = B.produce_fixture_student_view_v2_bound(**world)
    drop_cell = {**deepcopy(honest), "rows": [r for r in honest["rows"] if r["cell_id"] != "C1"]}
    relabel = deepcopy(honest)
    for r in relabel["rows"]:
        if r["cell_id"] == "C1":
            r.update(donor_id="D_OTHER", source_id="S_OTHER")
    swap = deepcopy(honest)
    for r in swap["rows"]:
        if r["cell_id"] == "C0" and r["address_id"] in ("B1", "B2"):
            r["count"] = {"B1": 2, "B2": 5}[r["address_id"]]
    assert [_inject(f, honest) for f in (drop_cell, relabel, swap)] == [VALIDATED] * 3


def test_characterize_the_first_issuer_pins_the_binding_for_identical_view_bytes():
    """LIMITATION. The binding is not a function of the view: a ladder with an
    extra base right that no address carries yields identical view bytes, so the
    first issuance pins the binding and a later honest issuance is refused."""
    phantom = _query_world()
    phantom["ladder"] = [{"level_id": "L0", "evidence_rights": ["RNA:BASE", "RNA:PHANTOM"]},
                         {"level_id": "L1", "evidence_rights": ["RNA:BASE", "RNA:PHANTOM", "RNA:QUERY"]}]
    first = B.produce_fixture_student_view_v2_bound(**phantom)
    with pytest.raises(QExcludedObservationError, match="ambiguous bound-content rights"):
        B.produce_fixture_student_view_v2_bound(**_query_world())
    assert _outcome(first) == VALIDATED


# ---------------------------------------------------------------- GREEN guards

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


def _hostile_view(where):
    view = B.produce_fixture_student_view_v2_bound(**_query_world())
    row = next(r for r in view["rows"] if r["state"] == MS)
    return {
        "whole_view_raises": lambda: _Raises(),
        "whole_view_lies": lambda: _Lies(),
        "schema_lies": lambda: {**view, "schema": _Lies()},
        "digest_raises": lambda: {**view, "observable_sha256": _Raises()},
        "query_class_property": lambda: {**view, "query_address_id": _ClassProperty()},
        "row_count_lies": lambda: {**view, "rows": [{**row, "count": _Lies()}] + view["rows"][1:]},
        "row_key_str_subclass": lambda: {**view, "rows": [{_KeyStr(k) if k == "count" else k: v
                                                            for k, v in row.items()}] + view["rows"][1:]},
        "row_dict_subclass": lambda: {**view, "rows": [_DictSub(row)] + view["rows"][1:]},
        "top_dict_subclass": lambda: _DictSub(view),
        "bool_count": lambda: _sign({**view, "rows": [{**row, "count": True}] + view["rows"][1:]}),
    }[where]()


_WHERE = ["whole_view_raises", "whole_view_lies", "schema_lies", "digest_raises", "query_class_property",
          "row_count_lies", "row_key_str_subclass", "row_dict_subclass", "top_dict_subclass", "bool_count"]


@pytest.mark.parametrize("where", _WHERE)
def test_bound_validator_refuses_hostile_types_without_running_payload_code(where):
    hostile = _hostile_view(where)
    _Meta.calls.clear()
    try:
        B.validate_fixture_observation_view_v2_bound(hostile)
        escaped = "validated"
    except QExcludedObservationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001 - the escape is the finding
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    assert (escaped, _Meta.calls) == (None, [])


@pytest.mark.parametrize("where", ["count_lies", "total_raises", "key_str_subclass", "query_class_property"])
def test_bound_producer_refuses_hostile_types_without_running_payload_code(where):
    world = _query_world()
    cell = world["cells"][0]
    if where == "count_lies":
        cell["counts"]["B"] = _Lies()
    elif where == "total_raises":
        cell["library_total"] = _Raises()
    elif where == "key_str_subclass":
        cell["counts"] = {_KeyStr("B"): 9, "Q": 7}
    elif where == "query_class_property":
        world["query_address_id"] = _ClassProperty()
    _Meta.calls.clear()
    try:
        B.produce_fixture_student_view_v2_bound(**world)
        escaped = "issued"
    except QExcludedObservationError:
        escaped = None
    except BaseException as exc:  # noqa: BLE001
        escaped = f"{type(exc).__module__}.{type(exc).__qualname__}"
    assert (escaped, _Meta.calls) == (None, [])


def test_legacy_and_bound_schemas_cannot_stand_in_for_each_other():
    """The legacy shape contract is unchanged and distinct: a bound view is not a
    legacy view, an honest legacy view is not a bound view, and the legacy
    receipt status never equals the bound content status."""
    world = _query_world()
    bound = B.produce_fixture_student_view_v2_bound(**world)
    legacy = LEGACY.produce_fixture_student_view_v2(**world)
    with pytest.raises(QExcludedObservationError):
        LEGACY.validate_fixture_observation_view_v2(bound)
    with pytest.raises(QExcludedObservationError, match="wrong V2 bound-content schema"):
        B.validate_fixture_observation_view_v2_bound(legacy)
    relabelled = LEGACY.validate_fixture_observation_view_v2(_sign({**bound, "schema": LEGACY._SCHEMA}))
    assert relabelled["status"] != VALIDATED


def test_issued_views_validate_and_the_student_view_carries_no_withheld_value():
    world = _query_world()
    student = B.produce_fixture_student_view_v2_bound(**world)
    assert _outcome(student) == VALIDATED
    rows = {(r["cell_id"], r["address_id"]): r for r in student["rows"]}
    for cid in ("C0", "C1"):
        assert (rows[(cid, "Q")]["state"], rows[(cid, "Q")]["count"]) == (WITHHELD, None)
        assert rows[(cid, "B")]["base_rights_normalization_depth"] == 9
