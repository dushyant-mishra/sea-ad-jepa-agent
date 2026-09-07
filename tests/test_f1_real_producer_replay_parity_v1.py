"""Producer/replay parity, source-distinctness, resume, and cache-identity attacks.

Synthetic and technical fixtures only. No real sweep, no protected partition.
"""

from __future__ import annotations

import ast
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import f1_execution_authorization_v1 as authorization  # noqa: E402
import f1_real_producer_v1 as producer  # noqa: E402
import f1_real_replay_v1 as replay  # noqa: E402

ASSIGNMENT_REL = ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/"
                  "F1_QUERY_ASSIGNMENTS_2DRAW.csv")
DEDUP_REL = ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/"
             "F1_QUERY_EXECUTION_DEDUP_MAP.csv")
READER_SPLIT_REL = ("exports/foundation_calibration_bundle_20260824/splits/"
                    "reader_donor_split.csv")

# The frozen assignment authority is 30 MB and the dedup map 8 MB, and neither is
# tracked, so neither can be a package member. They are therefore resolved from
# an external tree. An external reviewer will not have the hardcoded local paths
# below, so `F1_PREFREEZE_AUTHORITY_ROOT` is the supported way to point at them.
# When the variable is set it is the *only* root consulted. The local fallbacks
# below are this machine's absolute paths and mean nothing on a reviewer's
# machine; leaving them in the search order would also make the unreachable case
# impossible to exercise here, so an explicit root replaces them rather than
# being prepended to them.
AUTHORITY_ROOT_ENV = "F1_PREFREEZE_AUTHORITY_ROOT"
_EXPLICIT_ROOT = os.environ.get(AUTHORITY_ROOT_ENV)
CANONICAL_ROOTS = ((Path(_EXPLICIT_ROOT),) if _EXPLICIT_ROOT
                   else (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), ROOT))

# Set F1_PREFREEZE_REQUIRE_AUTHORITIES=1 to turn an unreachable authority into a
# hard failure. Without it these checks skip, and a skip is NOT a pass: under
# this project's own precedence INVALID > FAIL > NOT_MEASURABLE > PASS, an
# authority-dependent check that did not run is NOT_MEASURABLE. It is recorded
# here because the geometry-and-coverage evidence is the strongest content of
# this package, and a reviewer reading a silent skip as a pass would be reading
# the package's central claim as verified when it was never evaluated.
REQUIRE_AUTHORITIES = os.environ.get("F1_PREFREEZE_REQUIRE_AUTHORITIES") == "1"

# Every check that cannot run without the external authority files. Declared so
# a reviewer can count NOT_MEASURABLE outcomes instead of inferring them.
AUTHORITY_DEPENDENT_TESTS = (
    "test_authorities_verify_against_bytes_on_disk",
    "test_mechanics_capture_plan_covers_every_statistical_assignment",
    "test_producer_asserted_geometry_matches_replay_derived_counts",
    "test_producer_capture_plan_agrees_with_replay_derived_coverage",
    "test_the_reader_fit_roster_is_bound_by_identity",
)


def _authority(relative: str) -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    message = ("NOT_MEASURABLE (not a pass): frozen authority not reachable: %s. "
               "Set %s to a tree containing it, or %s=1 to make this a failure."
               % (relative, AUTHORITY_ROOT_ENV, "F1_PREFREEZE_REQUIRE_AUTHORITIES"))
    if REQUIRE_AUTHORITIES:
        pytest.fail(message)
    pytest.skip(message)


# ------------------------------------------------------------------ independence
def test_replay_source_does_not_import_the_producer() -> None:
    """Static check. Agreement is only evidence if the code paths are separate."""
    tree = ast.parse((SCRIPTS / "f1_real_replay_v1.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in replay.FORBIDDEN_IMPORTS:
        assert forbidden not in imported, forbidden


def test_producer_source_does_not_import_the_replay() -> None:
    tree = ast.parse((SCRIPTS / "f1_real_producer_v1.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    assert "f1_real_replay_v1" not in imported


def test_runtime_independence_guard_actually_fires() -> None:
    """The guard must reject a process that has borrowed producer arithmetic."""
    with pytest.raises(RuntimeError) as excinfo:
        replay.assert_source_independence()   # producer is imported in this module
    assert "NOT_SOURCE_DISTINCT" in str(excinfo.value)


def test_replay_cli_passes_the_guard_in_a_clean_process() -> None:
    """In its own process the replay imports nothing forbidden and runs."""
    result = subprocess.run(
        [sys.executable, str(SCRIPTS / "f1_real_replay_v1.py")],
        capture_output=True, text=True, cwd=str(ROOT))
    assert result.returncode == 0, result.stderr[-400:]
    payload = json.loads(result.stdout)
    assert payload["source_distinct"] is True
    assert payload["terminal"] == "REPLAY_SOURCE_ONLY__REAL_F1_STILL_UNAUTHORIZED"


# --------------------------------------------------------------------- geometry
def test_producer_asserted_geometry_matches_replay_derived_counts() -> None:
    """The substantive check: constants versus counts over the frozen CSVs."""
    assignment = _authority(ASSIGNMENT_REL)
    dedup = _authority(DEDUP_REL)
    asserted = producer.assert_frozen_geometry()
    derived = replay.derive_geometry_from_authorities(assignment, dedup)
    comparison = replay.compare_geometry(asserted, derived)
    assert comparison["agree"], comparison["disagreements"]
    # The four counts the lane must hard-assert.
    assert derived["statistical_assignments"] == 44496
    assert derived["unique_cell_q"] == 43108
    assert derived["assignment_evidence_effect_rows"] == 222480
    assert derived["total_expensive_forwards"] == 474188


def test_geometry_disagreement_is_reported_not_averaged() -> None:
    asserted = producer.assert_frozen_geometry()
    tampered = dict(asserted); tampered["unique_cell_q"] = 43107
    comparison = replay.compare_geometry(asserted, tampered)
    assert not comparison["agree"]
    assert "unique_cell_q" in comparison["disagreements"]


def test_frozen_geometry_reconciliations_are_enforced() -> None:
    with pytest.raises(AssertionError):
        producer.assert_frozen_geometry({"unique_cell_q": 43107})


# -------------------------------------------------------------- effect-row parity
def _states(seed: int, dim: int = 32) -> dict[str, np.ndarray]:
    rng = np.random.default_rng(seed)
    keys = ("s_correct_contextual", "t_true_contextual", "s_null_contextual",
            "s_correct_direct", "t_true_direct", "s_null_direct")
    return {k: rng.normal(size=dim) for k in keys}


def test_effect_rows_agree_within_the_declared_tolerance() -> None:
    for seed in (1, 7, 20260907):
        states = _states(seed)
        extra = {"own_similarity": 0.42, "paired_wrong_similarity": 0.11}
        p_row = producer.effect_row_for_test(**states, **extra)
        r_row = replay.replay_effect_row(**states, **extra)
        comparison = replay.compare_effect_rows(p_row, r_row)
        assert comparison["agree"], comparison["failures"]


def test_effect_row_parity_detects_a_perturbed_producer_value() -> None:
    """Guard the comparator: a real disagreement must not pass."""
    states = _states(3)
    extra = {"own_similarity": 0.5, "paired_wrong_similarity": 0.25}
    p_row = dict(producer.effect_row_for_test(**states, **extra))
    r_row = replay.replay_effect_row(**states, **extra)
    p_row["A"] = p_row["A"] + 1e-6
    comparison = replay.compare_effect_rows(p_row, r_row)
    assert not comparison["agree"] and "A" in comparison["failures"]


def test_qid_win_is_compared_exactly_and_ties_score_half() -> None:
    assert replay.replay_qid(0.3, 0.3)["qid_win"] == 0.5
    assert replay.replay_qid(0.4, 0.1)["qid_win"] == 1.0
    assert replay.replay_qid(0.1, 0.4)["qid_win"] == 0.0
    mismatch = replay.compare_effect_rows({"qid_win": 1.0}, {"qid_win": 0.5})
    assert not mismatch["agree"]


# ------------------------------------------------------ cache-identity attacks
AUTHORITY = {"forward_root": producer.ACCEPTED_REAL_FORWARD_ROOT, "dtype": "float32"}


def test_teacher_identity_is_evidence_invariant() -> None:
    base = {"canonical_cell_id": "cellA", "q": 11}
    a = producer.teacher_compute_identity(AUTHORITY, dict(base, evidence_level=20))
    b = producer.teacher_compute_identity(AUTHORITY, dict(base, evidence_level=80))
    assert a == b
    assert replay.replay_teacher_identity(AUTHORITY, "cellA", 11) == a


def test_correct_and_null_identities_never_collide() -> None:
    record = {"canonical_cell_id": "cellA", "q": 11, "evidence_level": 60,
              "null_source_cell": "cellZ"}
    correct = producer.student_forward_identity(AUTHORITY, record, "correct_student")
    null = producer.student_forward_identity(AUTHORITY, record, "matched_null_student")
    assert correct != null
    assert replay.replay_student_identity(AUTHORITY, "cellA", 11, 60, "correct_student") == correct
    assert replay.replay_student_identity(
        AUTHORITY, "cellA", 11, 60, "matched_null_student", null_source="cellZ") == null


def test_identity_separates_query_recipient_evidence_and_null_source() -> None:
    base = {"canonical_cell_id": "cellA", "q": 11, "evidence_level": 60,
            "null_source_cell": "cellZ"}
    seen = set()
    for mutation in (
        {},
        {"q": 12},
        {"canonical_cell_id": "cellB"},
        {"evidence_level": 80},
        {"null_source_cell": "cellY"},
    ):
        record = dict(base); record.update(mutation)
        seen.add(producer.student_forward_identity(AUTHORITY, record, "matched_null_student"))
    assert len(seen) == 5, "a cache-identity field failed to separate"


def test_identity_changes_when_the_bound_authority_changes() -> None:
    record = {"canonical_cell_id": "cellA", "q": 11, "evidence_level": 60}
    a = producer.student_forward_identity(AUTHORITY, record, "correct_student")
    b = producer.student_forward_identity(
        dict(AUTHORITY, forward_root="0" * 64), record, "correct_student")
    assert a != b, "identity must not be reusable across a different forward root"


def test_identity_root_agrees_between_producer_and_replay() -> None:
    identities = ["a" * 64, "b" * 64, "c" * 64]
    assert producer.identity_root(identities) == replay.replay_identity_root(identities)
    assert producer.identity_root(identities) != producer.identity_root(identities[::-1])


# ------------------------------------------------- shard store, resume, digests
def _store(tmp_path: Path):
    return producer.AtomicShardStore(tmp_path, membership_root="m" * 64,
                                     forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT,
                                     dtype="float32")


def test_payload_digest_agrees_and_shard_verifies_from_persisted_bytes(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ids = ["id0", "id1", "id2"]
    values = np.arange(3, dtype=np.float32)
    path = producer.produce_shard_for_test(store, donor_id="D1", operator_index=7,
                                           ordered_ids=ids, values=values)
    verdict = replay.verify_persisted_shard(
        path, shard_id=producer.storage_shard_id("D1", 7), ordered_ids=ids,
        membership_root="m" * 64, forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT,
        dtype="float32")
    assert verdict["verified"], verdict["problems"]
    assert verdict["recomputed_payload_digest"] == replay.replay_payload_digest(ids, values)


def test_interrupted_and_resumed_execution_reproduces_identical_bytes(tmp_path: Path) -> None:
    """Uninterrupted and interrupted/resumed runs must agree on ordered bytes and roots."""
    plan = [("D1", 1, ["a", "b"], np.array([1.0, 2.0], dtype=np.float32)),
            ("D1", 2, ["c"], np.array([3.0], dtype=np.float32)),
            ("D2", 1, ["d", "e"], np.array([4.0, 5.0], dtype=np.float32))]

    def run(root: Path, stop_after: int | None):
        store = producer.AtomicShardStore(root, membership_root="m" * 64,
                                          forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT,
                                          dtype="float32")
        written = []
        for index, (donor, op, ids, values) in enumerate(plan):
            if stop_after is not None and index >= stop_after:
                break
            sid = producer.storage_shard_id(donor, op)
            if (root / (sid + ".npz")).exists():
                continue           # valid committed shard is reused, never rewritten
            written.append(store.commit(sid, ids, values))
        return store, written

    whole = tmp_path / "uninterrupted"
    run(whole, None)
    part = tmp_path / "resumed"
    run(part, 2)                    # interrupt after two shards
    run(part, None)                 # resume; must not rewrite committed shards

    def roots(root: Path) -> list[str]:
        out = []
        for donor, op, ids, values in plan:
            sid = producer.storage_shard_id(donor, op)
            out.append(replay.verify_persisted_shard(
                root / (sid + ".npz"), shard_id=sid, ordered_ids=ids,
                membership_root="m" * 64,
                forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT,
                dtype="float32")["recomputed_payload_digest"])
        return out

    assert roots(whole) == roots(part)
    assert replay.replay_identity_root(roots(whole)) == replay.replay_identity_root(roots(part))


def test_shard_attacks_fail_closed(tmp_path: Path) -> None:
    store = _store(tmp_path)
    ids = ["id0", "id1"]
    values = np.array([1.0, 2.0], dtype=np.float32)
    path = producer.produce_shard_for_test(store, donor_id="D1", operator_index=3,
                                           ordered_ids=ids, values=values)
    sid = producer.storage_shard_id("D1", 3)

    with pytest.raises(RuntimeError):                       # duplicate shard write
        store.commit(sid, ids, values)
    with pytest.raises(TypeError):                          # wrong dtype
        store.commit(producer.storage_shard_id("D9", 9), ids, values.astype(np.float64))

    good = dict(shard_id=sid, ordered_ids=ids, membership_root="m" * 64,
                forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT, dtype="float32")
    assert replay.verify_persisted_shard(path, **good)["verified"]
    for label, override in (("stale_membership_root", {"membership_root": "z" * 64}),
                            ("wrong_forward_root", {"forward_root": "0" * 64}),
                            ("wrong_shard_id", {"shard_id": producer.storage_shard_id("D1", 99)}),
                            ("reordered_payload", {"ordered_ids": ids[::-1]}),
                            ("wrong_dtype", {"dtype": "float64"})):
        verdict = replay.verify_persisted_shard(path, **dict(good, **override))
        assert not verdict["verified"], label


# ------------------------------------------------------- external authorization
def test_the_in_source_execution_dead_end_is_gone() -> None:
    """Authorization must not be an editable in-source constant.

    The previous design carried REAL_EXECUTION_READY = False plus three None
    output roots, so the only way to make the frozen source runnable was to edit
    it, which destroys the freeze. Those names must no longer exist.
    """
    for banned in ("REAL_EXECUTION_READY", "FROZEN_REAL_CAPTURE_ROOT_SHA256",
                   "FROZEN_REAL_SHARD_SET_ROOT_SHA256",
                   "FROZEN_REAL_EFFECT_ROW_ROOT_SHA256"):
        assert not hasattr(producer, banned), banned
    text = (SCRIPTS / "f1_real_producer_v1.py").read_text(encoding="utf-8")
    for banned in ("REAL_EXECUTION_READY: bool", "FROZEN_REAL_CAPTURE_ROOT_SHA256:"):
        assert banned not in text, banned


def test_lawful_partition_only() -> None:
    producer.assert_lawful_partition(["reader_fit"])
    for forbidden in ("reader_validation", "reader_oracle", "development",
                      "sealed_holdout", "whole_study_external_holdout"):
        with pytest.raises(RuntimeError):
            producer.assert_lawful_partition(["reader_fit", forbidden])


def test_authorities_verify_against_bytes_on_disk() -> None:
    for relative in producer.PREFLIGHT_AUTHORITY_SHA256:
        _authority(relative)        # skips cleanly if the tree lacks them
    for root in CANONICAL_ROOTS:
        if (root / ASSIGNMENT_REL).is_file():
            verified = producer.verify_authorities(root)
            assert len(verified) == len(producer.PREFLIGHT_AUTHORITY_SHA256)
            return
    message = ("NOT_MEASURABLE (not a pass): no root carries the full frozen "
               "authority set. Set %s, or %s=1 to make this a failure."
               % (AUTHORITY_ROOT_ENV, "F1_PREFREEZE_REQUIRE_AUTHORITIES"))
    if REQUIRE_AUTHORITIES:
        pytest.fail(message)
    pytest.skip(message)


def test_assignment_level_capture_schema_carries_no_role_or_evidence() -> None:
    """The assignment record and the forward record are different objects."""
    record = producer.mechanics_capture_record(
        identity="a" * 64, canonical_cell_id="cellA", q=11, state_dim=160,
        dtype="float32", assignment_key="b" * 64)
    for field in ("schema", "level", "identity", "assignment_key",
                  "canonical_cell_id", "q", "state_dim", "dtype", "autocast",
                  "torch_no_grad", "encoder_eval", "gradient_checkpointing",
                  "accepted_real_forward_root", "partition",
                  "sufficient_for_completeness"):
        assert field in record, field
    assert record["level"] == "ASSIGNMENT"
    assert "role" not in record and "evidence_level" not in record
    assert record["partition"] == "reader_fit"
    assert record["autocast"] is False and record["torch_no_grad"] is True
    with pytest.raises(ValueError, match="CAPTURE_DTYPE"):
        producer.mechanics_capture_record(
            identity="a" * 64, canonical_cell_id="c", q=1, state_dim=160,
            dtype="float64", assignment_key="b" * 64)
    with pytest.raises(ValueError, match="CAPTURE_ASSIGNMENT_KEY"):
        producer.mechanics_capture_record(
            identity="a" * 64, canonical_cell_id="c", q=1, state_dim=160,
            dtype="float32", assignment_key="short")


def test_planned_identities_reconcile_with_the_frozen_per_pair_arithmetic() -> None:
    records = [{"canonical_cell_id": "c%d" % i, "q": i, "null_source_cell": "z%d" % i}
               for i in range(4)]
    records.append(dict(records[0]))          # a compute-only duplicate
    plan = producer.plan_forward_identities(records, AUTHORITY)
    assert plan["unique_cell_q"] == 4
    assert plan["teacher_forwards"] == 4
    assert plan["correct_forwards"] == 4 * 5
    assert plan["null_forwards"] == 4 * 5
    assert plan["total_expensive_forwards"] == 4 + 20 + 20
    assert plan["identity_root_sha256"] == replay.replay_identity_root(
        [row["identity"] for row in plan["ordered"]])


def test_physical_shard_id_agrees_and_is_filesystem_safe() -> None:
    """The logical pair is an identity; only the hashed physical id becomes a filename."""
    logical = producer.logical_shard_id("D1", 7)
    assert logical == replay.replay_logical_shard_id("D1", 7)
    physical = producer.storage_shard_id("D1", 7)
    assert physical == replay.replay_physical_shard_id(logical)
    assert physical.startswith("shard_") and len(physical) == len("shard_") + 64
    for illegal in (":", "*", "?", chr(34), "<", ">", "|", chr(92), "/"):
        assert illegal not in physical, illegal
    # Distinct pairs must not collide, including near-miss donor/operator swaps.
    ids = {producer.storage_shard_id(d, o)
           for d, o in (("D1", 7), ("D1", 70), ("D17", 0), ("D7", 1))}
    assert len(ids) == 4


# ------------------------------------------------- mechanics capture coverage
def test_mechanics_capture_plan_covers_every_statistical_assignment() -> None:
    """The capture obligation is enumerated, not asserted in prose.

    An earlier revision only claimed coverage in a docstring while nothing
    counted the assignments. This counts them.
    """
    plan = producer.plan_mechanics_capture(_authority(ASSIGNMENT_REL))
    assert plan["planned_assignments"] == 44496
    assert plan["planned_assignment_evidence_rows"] == 222480
    assert len(set(plan["assignment_keys"])) == 44496
    assert list(plan["evidence_levels"]) == [20, 40, 60, 80, 100]
    assert list(plan["capture_roles"]) == list(producer.LEGAL_CAPTURE_ROLES)


def test_producer_capture_plan_agrees_with_replay_derived_coverage() -> None:
    plan = producer.plan_mechanics_capture(_authority(ASSIGNMENT_REL))
    derived = replay.replay_derive_capture_coverage(_authority(ASSIGNMENT_REL))
    comparison = replay.compare_capture_coverage(plan, derived)
    assert comparison["agree"], comparison["disagreements"]
    assert derived["derived_assignments"] == 44496
    assert derived["distinct_assignment_keys"] == 44496
    assert derived["distinct_cell_q_pairs"] == 43108


def _synthetic_plan(n: int) -> dict:
    keys = [("%064x" % i) for i in range(n)]
    return {
        "assignment_keys": keys,
        "planned_assignments": n,
        "planned_assignment_evidence_rows": n * len(producer.EVIDENCE_LEVELS),
    }


def _capture_for(keys) -> list:
    return [{"assignment_key": k} for k in keys]


def test_capture_coverage_accepts_exactly_once_per_assignment() -> None:
    plan = _synthetic_plan(64)
    result = producer.assert_capture_coverage(_capture_for(plan["assignment_keys"]), plan)
    assert result["complete"] and result["captured_assignments"] == 64


def test_capture_coverage_rejects_a_dropped_assignment() -> None:
    """A dropped forward must fail closed, not be averaged away."""
    plan = _synthetic_plan(64)
    partial = _capture_for(plan["assignment_keys"][:-1])
    with pytest.raises(AssertionError) as excinfo:
        producer.assert_capture_coverage(partial, plan)
    assert "STOP_F1_PRODUCER_CAPTURE_INCOMPLETE" in str(excinfo.value)


def test_capture_coverage_rejects_a_double_counted_assignment() -> None:
    plan = _synthetic_plan(64)
    doubled = _capture_for(plan["assignment_keys"]) + _capture_for(plan["assignment_keys"][:1])
    with pytest.raises(AssertionError) as excinfo:
        producer.assert_capture_coverage(doubled, plan)
    assert "STOP_F1_PRODUCER_CAPTURE_DUPLICATED" in str(excinfo.value)


def test_capture_coverage_rejects_an_unplanned_assignment() -> None:
    """A forward whose key is not in the plan is unauthorised, not extra credit."""
    plan = _synthetic_plan(64)
    smuggled = _capture_for(plan["assignment_keys"]) + [{"assignment_key": "f" * 64}]
    with pytest.raises(AssertionError) as excinfo:
        producer.assert_capture_coverage(smuggled, plan)
    assert "STOP_F1_PRODUCER_CAPTURE_UNPLANNED_ASSIGNMENT" in str(excinfo.value)


# ============================================================================
# Repaired-lane attacks: external authorization, forward topology, complete
# replay. Every attack pairs a lawful case that must PASS with a mutated case
# that must FAIL, so no attack can pass merely because everything refuses.
# ============================================================================
CHECKPOINT = "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4"

# A deliberately tiny geometry. The real constants are 43,108 / 215,540 /
# 215,540 / 474,188 / 222,480 / 1,400 and are asserted separately against the
# acceptance contract; building 474,188 records in a unit test would prove
# nothing extra about the logic, so the topology validators take an explicit
# geometry and the mechanics are attacked at a size that can be enumerated.
SMALL_GEOMETRY = {
    "statistical_assignments": 2,
    "unique_cell_q": 2,
    "compute_only_dedups": 0,
    "teacher_forwards": 2,
    "correct_forwards": 10,
    "null_forwards": 10,
    "total_expensive_forwards": 22,
    "assignment_evidence_effect_rows": 10,
    "logical_donor_operator_shards": 2,
}
SMALL_PAIRS = (("cellA", "qA", "D0", 0), ("cellB", "qB", "D1", 1))


def _small_shards() -> list[str]:
    return [producer.storage_shard_id(donor, operator)
            for _, _, donor, operator in SMALL_PAIRS]


def _complete_capture_set() -> list[dict]:
    """A complete, lawful forward capture set for SMALL_GEOMETRY."""
    records: list[dict] = []
    for cell, query, donor, operator in SMALL_PAIRS:
        shard = producer.storage_shard_id(donor, operator)
        records.append(producer.forward_capture_record(
            identity="t|%s|%s" % (cell, query), role=producer.TEACHER_ROLE,
            canonical_cell_id=cell, query_address=query, evidence_level=None,
            arm=None, model_family=producer.TEACHER_FAMILY, shard_id=shard,
            checkpoint_sha256=CHECKPOINT, state_dim=160, dtype="float32"))
        for evidence in producer.EVIDENCE_LEVELS:
            for role, arm in ((producer.CORRECT_STUDENT_ROLE, producer.CORRECT_ARM),
                              (producer.MATCHED_NULL_STUDENT_ROLE, producer.MATCHED_NULL_ARM)):
                records.append(producer.forward_capture_record(
                    identity="%s|%s|%s|%d" % (role, cell, query, evidence), role=role,
                    canonical_cell_id=cell, query_address=query,
                    evidence_level=evidence, arm=arm,
                    model_family=producer.STUDENT_FAMILY, shard_id=shard,
                    checkpoint_sha256=CHECKPOINT, state_dim=160, dtype="float32"))
    return records


def _planned_keys() -> list[str]:
    return ["%064x" % index for index in range(SMALL_GEOMETRY["statistical_assignments"])]


def _complete_effect_rows() -> list[dict]:
    rows = []
    for key in _planned_keys():
        for evidence in producer.EVIDENCE_LEVELS:
            rows.append({"assignment_key": key, "evidence_level": evidence,
                         "shard_id": _small_shards()[0],
                         "checkpoint_sha256": CHECKPOINT})
    return rows


def test_a_complete_capture_set_passes_every_topology() -> None:
    """The positive case, so the attacks below are discriminating."""
    records = _complete_capture_set()
    assert len(records) == SMALL_GEOMETRY["total_expensive_forwards"]
    out = producer.assert_forward_topology(
        records, checkpoint_sha256=CHECKPOINT, lawful_shard_ids=_small_shards(),
        geometry=SMALL_GEOMETRY)
    assert out["complete"] is True
    assert out["observed"]["teacher_forwards"] == 2
    assert out["observed"]["correct_forwards"] == 10
    assert out["observed"]["null_forwards"] == 10
    assert producer.assert_effect_row_topology(
        _complete_effect_rows(), planned_assignment_keys=_planned_keys(),
        geometry=SMALL_GEOMETRY)["rows"] == 10
    assert producer.assert_shard_topology(
        _small_shards(), lawful_shard_ids=_small_shards(),
        geometry=SMALL_GEOMETRY)["shards"] == 2


# ------------------------------------------------- Pass 3: incomplete topology
def test_one_record_per_assignment_does_not_pass_as_complete() -> None:
    """The defect the external review identified.

    A set holding exactly one teacher record per assignment satisfied the
    assignment-level coverage validator while containing no correct-student and
    no matched-null evidence forward at all.
    """
    teacher_only = [r for r in _complete_capture_set()
                    if r["role"] == producer.TEACHER_ROLE]
    assert len(teacher_only) == SMALL_GEOMETRY["statistical_assignments"]
    with pytest.raises(AssertionError, match="FORWARD_TOPOLOGY"):
        producer.assert_forward_topology(
            teacher_only, checkpoint_sha256=CHECKPOINT,
            lawful_shard_ids=_small_shards(), geometry=SMALL_GEOMETRY)
    # And the assignment-level record no longer even carries a role, so the two
    # ideas cannot be conflated again.
    record = producer.mechanics_capture_record(
        identity="a" * 64, canonical_cell_id="cellA", q=1, state_dim=160,
        dtype="float32", assignment_key="b" * 64)
    assert record["level"] == "ASSIGNMENT"
    assert "role" not in record and "evidence_level" not in record
    assert record["sufficient_for_completeness"] is False


def test_the_right_total_with_the_wrong_role_distribution_fails() -> None:
    """22 records, but 12 teachers and 10 correct and no matched-null."""
    records = _complete_capture_set()
    kept = [r for r in records if r["role"] != producer.MATCHED_NULL_STUDENT_ROLE]
    padding = []
    for index in range(SMALL_GEOMETRY["total_expensive_forwards"] - len(kept)):
        padding.append(producer.forward_capture_record(
            identity="pad%d" % index, role=producer.TEACHER_ROLE,
            canonical_cell_id="pad%d" % index, query_address="qP",
            evidence_level=None, arm=None, model_family=producer.TEACHER_FAMILY,
            shard_id=_small_shards()[0], checkpoint_sha256=CHECKPOINT,
            state_dim=160, dtype="float32"))
    mutated = kept + padding
    assert len(mutated) == SMALL_GEOMETRY["total_expensive_forwards"]
    with pytest.raises(AssertionError, match="FORWARD_TOPOLOGY"):
        producer.assert_forward_topology(
            mutated, checkpoint_sha256=CHECKPOINT, lawful_shard_ids=None,
            geometry=SMALL_GEOMETRY)


def test_a_complete_forward_set_with_incomplete_effect_rows_fails() -> None:
    rows = _complete_effect_rows()[:-1]
    with pytest.raises(AssertionError, match="EFFECT_ROW_TOPOLOGY"):
        producer.assert_effect_row_topology(
            rows, planned_assignment_keys=_planned_keys(), geometry=SMALL_GEOMETRY)


def test_complete_effect_rows_with_a_missing_shard_fails() -> None:
    with pytest.raises(AssertionError, match="SHARD_TOPOLOGY"):
        producer.assert_shard_topology(
            _small_shards()[:1], lawful_shard_ids=_small_shards(),
            geometry=SMALL_GEOMETRY)


def test_mismatched_correct_and_null_arms_fail() -> None:
    """A null arm covering different keys would compare unmatched pairs."""
    records = [r for r in _complete_capture_set()
               if not (r["role"] == producer.MATCHED_NULL_STUDENT_ROLE
                       and r["evidence_level"] == 100)]
    records.append(producer.forward_capture_record(
        identity="extra-null", role=producer.MATCHED_NULL_STUDENT_ROLE,
        canonical_cell_id="cellA", query_address="qOTHER", evidence_level=100,
        arm=producer.MATCHED_NULL_ARM, model_family=producer.STUDENT_FAMILY,
        shard_id=_small_shards()[0], checkpoint_sha256=CHECKPOINT,
        state_dim=160, dtype="float32"))
    records.append(producer.forward_capture_record(
        identity="extra-null-2", role=producer.MATCHED_NULL_STUDENT_ROLE,
        canonical_cell_id="cellB", query_address="qOTHER", evidence_level=100,
        arm=producer.MATCHED_NULL_ARM, model_family=producer.STUDENT_FAMILY,
        shard_id=_small_shards()[1], checkpoint_sha256=CHECKPOINT,
        state_dim=160, dtype="float32"))
    with pytest.raises(AssertionError, match="FORWARD_TOPOLOGY"):
        producer.assert_forward_topology(
            records, checkpoint_sha256=CHECKPOINT, lawful_shard_ids=None,
            geometry=SMALL_GEOMETRY)


# ------------------------------------------------------- Pass 2: fail-open attacks
def test_every_identity_mutation_fails_closed() -> None:
    """Mutate one identity dimension at a time; each must be rejected."""
    base = dict(identity="x", role=producer.CORRECT_STUDENT_ROLE,
                canonical_cell_id="cellA", query_address="qA", evidence_level=60,
                arm=producer.CORRECT_ARM, model_family=producer.STUDENT_FAMILY,
                shard_id=_small_shards()[0], checkpoint_sha256=CHECKPOINT,
                state_dim=160, dtype="float32")
    assert producer.forward_capture_record(**base)["role"] == producer.CORRECT_STUDENT_ROLE
    for label, override, pattern in (
        ("unknown role", {"role": "student"}, "CAPTURE_ROLE"),
        ("evidence off-set", {"evidence_level": 50}, "EVIDENCE_LEVEL"),
        ("student with no evidence", {"evidence_level": None}, "EVIDENCE_LEVEL"),
        ("wrong arm", {"arm": producer.MATCHED_NULL_ARM}, "CAPTURE_ARM"),
        ("student in teacher family", {"model_family": producer.TEACHER_FAMILY},
         "STUDENT_FAMILY"),
        ("teacher with evidence", {"role": producer.TEACHER_ROLE,
                                   "model_family": producer.TEACHER_FAMILY,
                                   "arm": None}, "TEACHER_EVIDENCE_INVARIANT"),
        ("teacher with an arm", {"role": producer.TEACHER_ROLE,
                                 "model_family": producer.TEACHER_FAMILY,
                                 "evidence_level": None}, "TEACHER_HAS_NO_ARM"),
        ("malformed shard id", {"shard_id": "D1::99"}, "CAPTURE_SHARD_ID"),
        ("wrong dtype", {"dtype": "float16"}, "CAPTURE_DTYPE"),
        ("short checkpoint", {"checkpoint_sha256": "abc"}, "CHECKPOINT_IDENTITY"),
    ):
        with pytest.raises(ValueError, match=pattern):
            producer.forward_capture_record(**dict(base, **override))


def test_a_capture_record_bound_to_another_checkpoint_fails() -> None:
    records = _complete_capture_set()
    records[0] = dict(records[0], checkpoint_sha256="f" * 64)
    with pytest.raises(AssertionError, match="CHECKPOINT_IDENTITY"):
        producer.assert_forward_topology(
            records, checkpoint_sha256=CHECKPOINT, lawful_shard_ids=None,
            geometry=SMALL_GEOMETRY)


def test_duplicate_and_missing_captures_both_fail() -> None:
    complete = _complete_capture_set()
    duplicated = complete + [dict(complete[0])]
    with pytest.raises(AssertionError, match="FORWARD_TOPOLOGY"):
        producer.assert_forward_topology(
            duplicated, checkpoint_sha256=CHECKPOINT, lawful_shard_ids=None,
            geometry=SMALL_GEOMETRY)
    with pytest.raises(AssertionError, match="FORWARD_TOPOLOGY"):
        producer.assert_forward_topology(
            complete[:-1], checkpoint_sha256=CHECKPOINT, lawful_shard_ids=None,
            geometry=SMALL_GEOMETRY)


def test_duplicate_and_unplanned_effect_rows_both_fail() -> None:
    rows = _complete_effect_rows()
    with pytest.raises(AssertionError, match="EFFECT_ROW_TOPOLOGY"):
        producer.assert_effect_row_topology(
            rows + [dict(rows[0])], planned_assignment_keys=_planned_keys(),
            geometry=SMALL_GEOMETRY)
    smuggled = rows + [{"assignment_key": "e" * 64, "evidence_level": 20}]
    with pytest.raises(AssertionError, match="EFFECT_ROW_TOPOLOGY"):
        producer.assert_effect_row_topology(
            smuggled, planned_assignment_keys=_planned_keys(), geometry=SMALL_GEOMETRY)


def test_a_capture_referencing_an_unlawful_shard_fails() -> None:
    records = _complete_capture_set()
    records[0] = dict(records[0], shard_id=producer.storage_shard_id("DX", 77))
    with pytest.raises(AssertionError, match="SHARD_TOPOLOGY"):
        producer.assert_forward_topology(
            records, checkpoint_sha256=CHECKPOINT,
            lawful_shard_ids=_small_shards(), geometry=SMALL_GEOMETRY)


# ------------------------------------------- Pass 6: authorization and freeze
def _authorization_body(**overrides) -> dict:
    body = {
        "schema": authorization.AUTHORIZATION_SCHEMA,
        "authorization_id": "F1-AUTH-TEST-0001",
        "scope": authorization.LAWFUL_SCOPE,
        "issued_by": "test",
        "issued_at": "2026-09-07T00:00:00Z",
        "package_root_sha256": "1" * 64,
        "source_sha256": {"producer": "2" * 64, "replay": "3" * 64,
                          "authorization": "4" * 64, "tests": "5" * 64},
        "checkpoint_sha256": authorization.FROZEN_U0_CHECKPOINT_SHA256,
        "reader_population": {"partition": "reader_fit", "donor_count": 104,
                              "donor_roster_root": "6" * 64,
                              "forbidden_populations_accessed": []},
        "authority_sha256": {"a": "7" * 64},
        "accepted_mechanics": dict(producer.ACCEPTED_MECHANICS),
        "frozen_geometry": {"statistical_assignments": 44496},
        "accepted_real_forward_root": producer.ACCEPTED_REAL_FORWARD_ROOT,
    }
    body.update(overrides)
    body["authorization_root_sha256"] = authorization.authorization_body_root(body)
    return body


def _validate(body: dict, **kwargs):
    defaults = dict(
        package_root_sha256="1" * 64,
        observed_source_sha256={"producer": "2" * 64, "replay": "3" * 64,
                                "authorization": "4" * 64, "tests": "5" * 64},
        observed_authority_sha256={"a": "7" * 64},
        accepted_mechanics=dict(producer.ACCEPTED_MECHANICS),
        frozen_geometry={"statistical_assignments": 44496},
        accepted_real_forward_root=producer.ACCEPTED_REAL_FORWARD_ROOT,
        lawful_partition="reader_fit",
        expected_donor_count=104,
        expected_donor_roster_root="6" * 64)
    defaults.update(kwargs)
    return authorization.validate_execution_authorization(body, **defaults)


def test_a_valid_authorization_unlocks_the_frozen_source_without_editing_it() -> None:
    """The positive half: authorization is external and sufficient."""
    validated = _validate(_authorization_body())
    assert validated["scope"] == authorization.LAWFUL_SCOPE
    assert validated["checkpoint_sha256"] == CHECKPOINT
    assert validated["binds_output_roots"] is False
    assert validated["is_closure"] is False
    assert "biological qualification of u0" in " ".join(validated["does_not_authorize"])
    # No source edit was required, and no in-source flag exists to edit.
    assert not hasattr(producer, "REAL_EXECUTION_READY")
    assert not hasattr(producer, "FROZEN_REAL_CAPTURE_ROOT_SHA256")


def test_the_producer_cannot_run_without_external_authorization(monkeypatch) -> None:
    monkeypatch.delenv(authorization.AUTHORIZATION_ENV, raising=False)
    with pytest.raises(PermissionError, match="AUTHORIZATION_ABSENT"):
        producer.run_production_sweep()
    with pytest.raises(PermissionError, match="AUTHORIZATION_ABSENT"):
        producer.run_production_sweep(real_execution_ready=True, force=True,
                                      package_root_sha256="0" * 64)


def test_no_caller_parameter_can_relax_the_authorization_boundary() -> None:
    import inspect
    names = {p.name for p in inspect.signature(producer.run_production_sweep).parameters.values()}
    for banned in ("allow_synthetic_test_fixture", "force", "bypass",
                   "real_execution_ready", "skip_authorization"):
        assert banned not in names


def test_every_authorization_drift_is_a_distinct_stop() -> None:
    for label, body, kwargs, pattern in (
        ("wrong package root", _authorization_body(package_root_sha256="9" * 64), {},
         "WRONG_PACKAGE_ROOT"),
        ("wrong source root", _authorization_body(),
         {"observed_source_sha256": {"producer": "0" * 64, "replay": "3" * 64,
                                     "authorization": "4" * 64, "tests": "5" * 64}},
         "WRONG_SOURCE_ROOT"),
        ("wrong checkpoint", _authorization_body(checkpoint_sha256="8" * 64), {},
         "WRONG_CHECKPOINT"),
        ("wrong partition", _authorization_body(
            reader_population={"partition": "reader_oracle", "donor_count": 104,
                               "donor_roster_root": "6" * 64}), {},
         "WRONG_READER_POPULATION"),
        ("wrong donor count", _authorization_body(
            reader_population={"partition": "reader_fit", "donor_count": 126,
                               "donor_roster_root": "6" * 64}), {},
         "WRONG_READER_POPULATION"),
        ("wrong roster root", _authorization_body(
            reader_population={"partition": "reader_fit", "donor_count": 104,
                               "donor_roster_root": "0" * 64}), {},
         "WRONG_READER_POPULATION"),
        ("authority drift", _authorization_body(authority_sha256={"a": "0" * 64}), {},
         "AUTHORITY_DRIFT"),
        ("retuned mechanics", _authorization_body(
            accepted_mechanics=dict(producer.ACCEPTED_MECHANICS, autocast=True)), {},
         "WRONG_MECHANICS"),
        ("wrong geometry", _authorization_body(
            frozen_geometry={"statistical_assignments": 44495}), {},
         "WRONG_GEOMETRY"),
        ("wrong scope", _authorization_body(scope="D1_PRODUCTION"), {}, "WRONG_SCOPE"),
    ):
        with pytest.raises(PermissionError, match=pattern):
            _validate(body, **kwargs)


def test_a_tampered_authorization_body_is_detected() -> None:
    """Changing the authorization after it was issued must be caught."""
    body = _authorization_body()
    tampered = dict(body, authorization_id="F1-AUTH-TEST-9999")
    with pytest.raises(PermissionError, match="ROOT_MISMATCH"):
        _validate(tampered)


def test_a_closure_artifact_can_never_authorize_the_run_that_produced_it() -> None:
    """Post-run closure is not authorization; retroactive authorization is closed."""
    closure = _authorization_body()
    closure["capture_root_sha256"] = "a" * 64
    closure["authorization_root_sha256"] = authorization.authorization_body_root(closure)
    with pytest.raises(PermissionError, match="IS_A_CLOSURE_ARTIFACT"):
        _validate(closure)
    with pytest.raises(PermissionError, match="IS_A_CLOSURE_ARTIFACT"):
        authorization.assert_not_closure_artifact(
            {"schema": "f1-real-closure-binding-v1"})
    with pytest.raises(PermissionError, match="IS_A_CLOSURE_ARTIFACT"):
        authorization.assert_not_closure_artifact(
            {"effect_row_root_sha256": "b" * 64})


def test_authorization_is_read_from_the_environment_not_from_source(tmp_path: Path,
                                                                    monkeypatch) -> None:
    artifact = tmp_path / "auth.json"
    artifact.write_text(json.dumps(_authorization_body()), encoding="utf-8")
    monkeypatch.setenv(authorization.AUTHORIZATION_ENV, str(artifact))
    payload = authorization.load_authorization_payload()
    assert payload["authorization_id"] == "F1-AUTH-TEST-0001"
    assert payload["_artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    monkeypatch.setenv(authorization.AUTHORIZATION_ENV, str(tmp_path / "absent.json"))
    with pytest.raises(PermissionError, match="AUTHORIZATION_ABSENT"):
        authorization.load_authorization_payload()


# ------------------------------------- Pass 4: replay independence on outputs
def _write_outputs(tmp_path: Path, captures, effect_rows):
    tmp_path.mkdir(parents=True, exist_ok=True)
    capture_path = tmp_path / "captures.json"
    effect_path = tmp_path / "effects.json"
    capture_path.write_text(json.dumps(captures), encoding="utf-8")
    effect_path.write_text(json.dumps(effect_rows), encoding="utf-8")
    return capture_path, effect_path


def test_replay_independently_verifies_a_complete_produced_result(tmp_path: Path) -> None:
    captures = _complete_capture_set()
    rows = _complete_effect_rows()
    capture_path, effect_path = _write_outputs(tmp_path, captures, rows)
    producer_statistics = {
        "records": len(captures),
        "shards": len(_small_shards()),
        "per_role": {producer.TEACHER_ROLE: 2, producer.CORRECT_STUDENT_ROLE: 10,
                     producer.MATCHED_NULL_STUDENT_ROLE: 10},
        "identity_root": replay.replay_identity_root(
            sorted(str(r["identity"]) for r in captures)),
    }
    out = replay.replay_verify_produced_outputs(
        capture_path=capture_path, effect_row_path=effect_path, shard_dir=None,
        checkpoint_sha256=CHECKPOINT, planned_assignment_keys=_planned_keys(),
        expected_geometry=SMALL_GEOMETRY, lawful_shard_ids=_small_shards(),
        producer_statistics=producer_statistics)
    assert out["complete"] is True
    assert out["terminal"] == "F1_REPLAY_VERIFIED_PRODUCED_OUTPUTS"
    assert out["parity_with_producer"]["agree"] is True


def test_replay_detects_a_producer_result_mutation_independently(tmp_path: Path) -> None:
    """Pass 4: mutate the produced output and require the replay to catch it."""
    captures = _complete_capture_set()
    rows = _complete_effect_rows()
    for label, mutate in (
        ("dropped forward", lambda c, r: (c[:-1], r)),
        ("duplicated forward", lambda c, r: (c + [dict(c[0])], r)),
        ("role flipped", lambda c, r: ([dict(x, role=producer.TEACHER_ROLE,
                                             evidence_level=None, arm=None,
                                             model_family=producer.TEACHER_FAMILY)
                                        if i == 1 else x for i, x in enumerate(c)], r)),
        ("evidence altered", lambda c, r: ([dict(x, evidence_level=20)
                                            if x["role"] != producer.TEACHER_ROLE and
                                            x["evidence_level"] == 40 else x for x in c], r)),
        ("recipient altered", lambda c, r: ([dict(x, canonical_cell_id="cellZ")
                                             if i == 0 else x for i, x in enumerate(c)], r)),
        ("checkpoint altered", lambda c, r: ([dict(x, checkpoint_sha256="0" * 64)
                                              if i == 0 else x for i, x in enumerate(c)], r)),
        ("effect row dropped", lambda c, r: (c, r[:-1])),
        ("effect row duplicated", lambda c, r: (c, r + [dict(r[0])])),
    ):
        mutated_captures, mutated_rows = mutate(list(captures), list(rows))
        capture_path, effect_path = _write_outputs(
            tmp_path / label.replace(" ", "_"), mutated_captures, mutated_rows)
        with pytest.raises(RuntimeError) as excinfo:
            replay.replay_verify_produced_outputs(
                capture_path=capture_path, effect_row_path=effect_path, shard_dir=None,
                checkpoint_sha256=CHECKPOINT, planned_assignment_keys=_planned_keys(),
                expected_geometry=SMALL_GEOMETRY, lawful_shard_ids=_small_shards())
        assert "STOP_F1_REPLAY" in str(excinfo.value), label


def test_replay_detects_a_statistics_mutation_even_when_topology_is_intact(
        tmp_path: Path) -> None:
    """Parity must catch a producer that published statistics it did not compute."""
    captures = _complete_capture_set()
    rows = _complete_effect_rows()
    capture_path, effect_path = _write_outputs(tmp_path, captures, rows)
    lying = {"records": len(captures), "shards": len(_small_shards()),
             "per_role": {producer.TEACHER_ROLE: 2,
                          producer.CORRECT_STUDENT_ROLE: 10,
                          producer.MATCHED_NULL_STUDENT_ROLE: 10},
             "identity_root": "0" * 64}
    with pytest.raises(RuntimeError, match="REPLAY_DIGEST_MISMATCH"):
        replay.replay_verify_produced_outputs(
            capture_path=capture_path, effect_row_path=effect_path, shard_dir=None,
            checkpoint_sha256=CHECKPOINT, planned_assignment_keys=_planned_keys(),
            expected_geometry=SMALL_GEOMETRY, lawful_shard_ids=_small_shards(),
            producer_statistics=lying)


def test_the_replay_does_not_import_the_producer_or_any_shared_finalizer() -> None:
    tree = ast.parse((SCRIPTS / "f1_real_replay_v1.py").read_text(encoding="utf-8"))
    imported: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module.split(".")[0])
    for forbidden in replay.FORBIDDEN_IMPORTS:
        assert forbidden not in imported, forbidden
    assert "f1_execution_authorization_v1" in replay.FORBIDDEN_IMPORTS


# ------------------------------------------ Pass 5: population firewall on real roster
def test_the_reader_fit_roster_is_bound_by_identity() -> None:
    split = _authority(READER_SPLIT_REL)
    roster = producer.load_reader_fit_roster(split)
    assert len(roster["roster"]) == 104
    assert roster["roster_root"] == producer.LAWFUL_READER_FIT_ROSTER_ROOT
    declared = roster["declared_partition_donor_counts"]
    assert declared["reader_fit"] == 104
    # foundation and train are NOT synonyms for reader_fit: the other reader
    # partitions exist in the same authority and are not part of the roster.
    assert declared["reader_validation"] == 22
    assert declared["reader_oracle"] == 23
    assert producer.assert_donors_within_reader_fit(
        sorted(roster["roster"])[:5], roster["roster"])["off_roster"] == 0
    with pytest.raises(PermissionError, match="POPULATION_FIREWALL"):
        producer.assert_donors_within_reader_fit(["not_a_fit_donor"], roster["roster"])


def test_a_tampered_reader_split_is_rejected(tmp_path: Path) -> None:
    fake = tmp_path / "reader_donor_split.csv"
    rows = ["donor_id,reader_partition"] + ["D%03d,reader_fit" % i for i in range(104)]
    fake.write_text("\n".join(rows) + "\n", encoding="utf-8")
    with pytest.raises(AssertionError, match="POPULATION_FIREWALL"):
        producer.load_reader_fit_roster(fake)


# ---------------------------------------------- normalization bound to the loader
def test_normalization_is_the_frozen_transform_with_the_library_guard() -> None:
    counts = np.array([0.0, 1.0, 7.0, 250.0])
    library = 12345.0
    expected = np.log1p(counts * (10000.0 / library))
    assert np.allclose(producer.normalize_expression(counts, library), expected)
    # The loader guards the divisor with max(L, 1.0); a zero library must not
    # divide by zero or silently produce inf.
    guarded = producer.normalize_expression(np.array([1.0]), 0.0)
    assert np.isfinite(guarded).all()
    assert guarded[0] == pytest.approx(np.log1p(10000.0))


def test_evidence_masks_only_use_physically_measurable_addresses() -> None:
    measurable = np.array([True, False, True, True, False, True])
    for level in producer.EVIDENCE_LEVELS:
        mask = producer.build_query_evidence_mask(
            query_address="qA", evidence_level=level, measurable=measurable)
        assert not bool((mask & ~measurable).any()), level
        assert int(mask.sum()) >= 1
    with pytest.raises(ValueError, match="EVIDENCE_LEVEL"):
        producer.build_query_evidence_mask(query_address="qA", evidence_level=50,
                                           measurable=measurable)
    with pytest.raises(ValueError, match="NO_MEASURABLE_EVIDENCE"):
        producer.build_query_evidence_mask(query_address="qA", evidence_level=60,
                                           measurable=np.zeros(4, dtype=bool))


# ------------------------------- the real frozen geometry, asserted separately
def test_the_real_frozen_geometry_constants_are_unchanged() -> None:
    """The small fixture above must never be mistaken for the real geometry."""
    geometry = producer.assert_frozen_geometry()
    assert geometry["statistical_assignments"] == 44496
    assert geometry["unique_cell_q"] == 43108
    assert geometry["teacher_forwards"] == 43108
    assert geometry["correct_forwards"] == 215540
    assert geometry["null_forwards"] == 215540
    assert geometry["total_expensive_forwards"] == 474188
    assert geometry["assignment_evidence_effect_rows"] == 222480
    assert geometry["logical_donor_operator_shards"] == 1400
    assert producer.EVIDENCE_LEVELS == (20, 40, 60, 80, 100)


def test_authority_digests_use_the_right_bytes_for_each_authority_class() -> None:
    """Tracked text sources are git-blob bytes; large data authorities are file bytes.

    An earlier revision hashed working-tree bytes for everything, so the three
    tracked model sources passed in a checkout with LF endings and failed in a
    CRLF checkout of the same commit. In this worktree ipb_jepa.py hashes to a
    different value on disk than in the index.
    """
    classes = producer.AUTHORITY_BYTES_CLASS
    assert set(classes) == set(producer.PREFLIGHT_AUTHORITY_SHA256)
    for relative, kind in classes.items():
        if relative.startswith("src/"):
            assert kind == producer.GIT_BLOB_BYTES_TRACKED_SOURCE, relative
        else:
            assert kind == producer.DISK_BYTES_UNTRACKED_DATA, relative
    # The tracked model sources verify from git bytes regardless of checkout.
    for relative in ("src/sea_ad_jepa/v4/ipb_jepa.py",
                     "src/sea_ad_jepa/v4/gene_tokenizer.py",
                     "src/sea_ad_jepa/v4/contextual_query_local.py"):
        assert producer.git_blob_sha256(ROOT, relative) == \
            producer.PREFLIGHT_AUTHORITY_SHA256[relative], relative


# ============================================================================
# The producer actually runs: authorization -> pipeline -> verified completeness
#
# Without these the "real producer" claim would be untested, and two genuine
# bugs did surface here: the reviewed shard store takes four required arguments
# and has no `exists` method, so the first authorized call would have crashed.
# The reader and forward engine are technical fixtures; no real sweep is run and
# no real biological data is touched.
# ============================================================================
class _TechnicalReader:
    """A lawful-shaped reader over a tiny technical fixture.

    Shapes and identity fields match what the pipeline requires, so the
    pipeline code under test is the real one. The donors are named from the real
    reader_fit roster when it is reachable, so the population firewall is
    exercised rather than bypassed.
    """

    def __init__(self, donors: list[str], addresses: int = 6) -> None:
        self._donors = list(donors)
        self._addresses = int(addresses)

    def shards(self):
        return [(donor, index) for index, donor in enumerate(self._donors)]

    def cells(self, donor: str, operator: int):
        support = np.ones(self._addresses, dtype=bool)
        support[1] = False              # a structurally unmeasured address
        cell_id = "cell_%s_%d" % (donor, operator)
        query = "q_%s" % donor
        yield {
            "canonical_cell_id": cell_id,
            # Both the address string and the integer q, because the frozen
            # identity contract keys on canonical_cell_id and an integer q.
            "queries": [{"query_address": query, "q": operator + 1,
                         "assignment_key": hashlib.sha256(cell_id.encode()).hexdigest(),
                         "null_source_cell": "null_%s" % donor}],
            "observation_state": support,
            "raw_counts": np.arange(self._addresses, dtype=np.float64),
            "source_library": 12345.0,
            "donor_id": donor,
            "operator_index": operator,
        }


class _TechnicalForwardEngine(producer.ForwardEngine):
    """Deterministic technical states. Never a model, never real biology."""

    def __init__(self, dim: int = 8) -> None:
        self.dim = int(dim)
        self.teacher_calls = 0
        self.student_calls = 0

    def _state(self, tag: str):
        rng = np.random.default_rng(
            int(hashlib.sha256(tag.encode()).hexdigest()[:8], 16))
        return rng.normal(size=self.dim)

    def teacher_forward(self, *, cell, query_address):
        self.teacher_calls += 1
        return self._state("t|%s|%s" % (cell["canonical_cell_id"], query_address))

    def student_forward(self, *, cell, query_address, evidence_level, arm):
        self.student_calls += 1
        return self._state("s|%s|%s|%d|%s" % (cell["canonical_cell_id"],
                                              query_address, evidence_level, arm))


def _fixture_geometry(donors: int) -> dict:
    """Geometry for the technical fixture: one cell and one query per shard."""
    pairs = donors
    return {
        "statistical_assignments": pairs,
        "unique_cell_q": pairs,
        "compute_only_dedups": 0,
        "teacher_forwards": pairs,
        "correct_forwards": pairs * len(producer.EVIDENCE_LEVELS),
        "null_forwards": pairs * len(producer.EVIDENCE_LEVELS),
        "total_expensive_forwards": pairs + 2 * pairs * len(producer.EVIDENCE_LEVELS),
        "assignment_evidence_effect_rows": pairs * len(producer.EVIDENCE_LEVELS),
        "logical_donor_operator_shards": pairs,
    }


def _validated_authorization(package_root: str = "1" * 64) -> dict:
    body = _authorization_body(package_root_sha256=package_root)
    return dict(_validate(body), authorization_root_sha256=body["authorization_root_sha256"])


def test_an_authorized_sweep_runs_end_to_end_and_verifies_complete(tmp_path: Path) -> None:
    """A valid authorization reaches the pipeline and produces a complete result."""
    donors = ["D_a", "D_b", "D_c"]
    reader = _TechnicalReader(donors)
    engine = _TechnicalForwardEngine()
    geometry = _fixture_geometry(len(donors))
    authorized = _validated_authorization()

    result = producer.execute_authorized_sweep(
        authorization=authorized, roster={"roster": set(donors)}, geometry=geometry,
        forward_engine=engine, reader=reader, output_dir=tmp_path / "shards")

    assert result["terminal"] == "F1_REAL_SWEEP_EXECUTED"
    assert engine.teacher_calls == len(donors)
    assert engine.student_calls == len(donors) * len(producer.EVIDENCE_LEVELS) * 2
    assert len(result["captures"]) == geometry["total_expensive_forwards"]
    assert len(result["effect_rows"]) == geometry["assignment_evidence_effect_rows"]
    assert sorted(result["published_shards"]) == sorted(result["lawful_shard_ids"])

    planned = sorted({r["assignment_key"] for r in result["effect_rows"]})
    completeness = producer.verify_sweep_completeness(
        result, planned_assignment_keys=planned)
    assert completeness["complete"] is True
    assert completeness["forwards"]["observed"]["teacher_forwards"] == len(donors)
    assert completeness["shards"]["shards"] == len(donors)
    # Shards were actually written.
    assert len(list((tmp_path / "shards").glob("*.npz"))) == len(donors)


def test_an_interrupted_authorized_sweep_resumes_without_rewriting_shards(
        tmp_path: Path) -> None:
    """Resume is by shard presence; a committed shard is reused, not rewritten.

    The reviewed store raises on a duplicate shard write, so a resume that did
    not detect existing shards would crash rather than silently double-write.
    """
    donors = ["D_a", "D_b", "D_c"]
    geometry = _fixture_geometry(len(donors))
    authorized = _validated_authorization()
    shard_dir = tmp_path / "shards"

    first = producer.execute_authorized_sweep(
        authorization=authorized, roster={"roster": set(donors)}, geometry=geometry,
        forward_engine=_TechnicalForwardEngine(),
        reader=_TechnicalReader(donors[:2]), output_dir=shard_dir)
    assert len(first["published_shards"]) == 2
    assert first["resumed_shards"] == []

    engine = _TechnicalForwardEngine()
    second = producer.execute_authorized_sweep(
        authorization=authorized, roster={"roster": set(donors)}, geometry=geometry,
        forward_engine=engine, reader=_TechnicalReader(donors), output_dir=shard_dir)
    # The two already-committed shards were reused, so only the third ran.
    assert len(second["resumed_shards"]) == 2
    assert engine.teacher_calls == 1
    assert sorted(second["published_shards"]) == sorted(second["lawful_shard_ids"])
    assert len(list(shard_dir.glob("*.npz"))) == len(donors)


def test_the_sweep_refuses_a_donor_outside_the_reader_fit_roster(tmp_path: Path) -> None:
    """Population firewall inside the executing pipeline, not just at planning."""
    donors = ["D_a", "D_b"]
    with pytest.raises(PermissionError, match="POPULATION_FIREWALL"):
        producer.execute_authorized_sweep(
            authorization=_validated_authorization(),
            roster={"roster": {"D_a"}},           # D_b is not on the roster
            geometry=_fixture_geometry(len(donors)),
            forward_engine=_TechnicalForwardEngine(),
            reader=_TechnicalReader(donors), output_dir=tmp_path / "s")


def test_the_sweep_refuses_an_authorization_for_the_wrong_partition(tmp_path: Path) -> None:
    bad = dict(_validated_authorization(), partition="reader_oracle")
    with pytest.raises(PermissionError, match="POPULATION_FIREWALL"):
        producer.execute_authorized_sweep(
            authorization=bad, roster={"roster": {"D_a"}},
            geometry=_fixture_geometry(1),
            forward_engine=_TechnicalForwardEngine(),
            reader=_TechnicalReader(["D_a"]), output_dir=tmp_path / "s")


def test_run_production_sweep_requires_engine_and_reader_even_when_authorized(
        tmp_path: Path, monkeypatch) -> None:
    """Authorization alone is not enough; the bindings must be supplied.

    This drives the real `run_production_sweep` entry point with a genuine
    authorization artifact on disk, so the authorization plumbing is exercised
    end to end rather than only the inner executor.
    """
    package_root = "1" * 64
    sources = producer.frozen_source_digests(ROOT)
    authorities = producer.verify_authorities(strict=False)
    body = _authorization_body(
        package_root_sha256=package_root,
        source_sha256=dict(sources),
        authority_sha256={k: v for k, v in authorities.items()
                          if not k.startswith("__")},
        frozen_geometry=producer.assert_frozen_geometry(),
        reader_population={"partition": "reader_fit", "donor_count": 104,
                           "donor_roster_root": producer.LAWFUL_READER_FIT_ROSTER_ROOT,
                           "forbidden_populations_accessed": []})
    artifact = tmp_path / "authorization.json"
    artifact.write_text(json.dumps(body), encoding="utf-8")
    monkeypatch.setenv(authorization.AUTHORIZATION_ENV, str(artifact))

    # Authorization validates, so the refusal must be about the missing bindings
    # rather than about authorization.
    with pytest.raises(PermissionError, match="EXECUTION_NOT_AUTHORIZED"):
        producer.run_production_sweep(package_root_sha256=package_root)

    # And a wrong package root is caught before anything else runs.
    with pytest.raises(PermissionError, match="WRONG_PACKAGE_ROOT"):
        producer.run_production_sweep(package_root_sha256="0" * 64,
                                      forward_engine=_TechnicalForwardEngine(),
                                      reader=_TechnicalReader(["D_a"]))


def test_run_production_sweep_requires_an_explicit_package_root(monkeypatch,
                                                                tmp_path: Path) -> None:
    artifact = tmp_path / "auth.json"
    artifact.write_text(json.dumps(_authorization_body()), encoding="utf-8")
    monkeypatch.setenv(authorization.AUTHORIZATION_ENV, str(artifact))
    with pytest.raises(PermissionError, match="EXECUTION_NOT_AUTHORIZED"):
        producer.run_production_sweep()


def test_the_replay_cli_verifies_a_produced_result_in_a_clean_process(
        tmp_path: Path) -> None:
    """Pass 4 and 5 together: end-to-end replay in a genuinely clean process.

    The replay's runtime independence guard only fires in a process that has not
    imported the producer, so driving the verification through the CLI is the
    only way to exercise the clean-process rule rather than assert it.
    """
    captures = _complete_capture_set()
    rows = _complete_effect_rows()
    capture_path, effect_path = _write_outputs(tmp_path, captures, rows)
    keys_path = tmp_path / "keys.json"
    keys_path.write_text(json.dumps(_planned_keys()), encoding="utf-8")
    geometry_path = tmp_path / "geometry.json"
    geometry_path.write_text(json.dumps(SMALL_GEOMETRY), encoding="utf-8")
    shards_path = tmp_path / "shards.json"
    shards_path.write_text(json.dumps(_small_shards()), encoding="utf-8")

    command = [sys.executable, str(SCRIPTS / "f1_real_replay_v1.py"),
               "--verify-produced-outputs",
               "--capture", str(capture_path), "--effect-rows", str(effect_path),
               "--checkpoint-sha256", CHECKPOINT,
               "--planned-keys", str(keys_path), "--geometry", str(geometry_path),
               "--lawful-shards", str(shards_path)]
    result = subprocess.run(command, capture_output=True, text=True, cwd=str(ROOT))
    assert result.returncode == 0, result.stderr[-600:]
    report = json.loads(result.stdout)
    assert report["complete"] is True
    assert report["terminal"] == "F1_REPLAY_VERIFIED_PRODUCED_OUTPUTS"
    assert report["forwards"]["observed"]["total_expensive_forwards"] == 22

    # A mutated result must fail in the same clean process.
    bad_capture, bad_effect = _write_outputs(tmp_path / "bad", captures[:-1], rows)
    bad = subprocess.run(
        [c if c != str(capture_path) else str(bad_capture) for c in command],
        capture_output=True, text=True, cwd=str(ROOT))
    assert bad.returncode != 0
    assert "STOP_F1_REPLAY" in (bad.stderr + bad.stdout)


def test_authority_dependent_declaration_matches_the_ast() -> None:
    """The declared NOT_MEASURABLE set must match reality.

    Written because the first draft of that declaration was wrong in both
    directions: it named a test that does not touch an authority and omitted one
    that does. A stale declaration would let a reviewer miscount which evidence
    actually ran.
    """
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    actual = set()
    for node in tree.body:
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
            for inner in ast.walk(node):
                if (isinstance(inner, ast.Call) and isinstance(inner.func, ast.Name)
                        and inner.func.id == "_authority"):
                    actual.add(node.name)
    assert actual == set(AUTHORITY_DEPENDENT_TESTS), {
        "undeclared": sorted(actual - set(AUTHORITY_DEPENDENT_TESTS)),
        "declared_but_not_authority_dependent": sorted(set(AUTHORITY_DEPENDENT_TESTS) - actual),
    }
