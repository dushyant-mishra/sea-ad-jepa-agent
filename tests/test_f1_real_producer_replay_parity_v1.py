"""Producer/replay parity, source-distinctness, resume, and cache-identity attacks.

Synthetic and technical fixtures only. No real sweep, no protected partition.
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import f1_real_producer_v1 as producer  # noqa: E402
import f1_real_replay_v1 as replay  # noqa: E402

CANONICAL_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"), ROOT)
ASSIGNMENT_REL = ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/"
                  "F1_QUERY_ASSIGNMENTS_2DRAW.csv")
DEDUP_REL = ("outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/"
             "F1_QUERY_EXECUTION_DEDUP_MAP.csv")


def _authority(relative: str) -> Path:
    for root in CANONICAL_ROOTS:
        candidate = root / relative
        if candidate.is_file():
            return candidate
    pytest.skip("frozen authority not reachable: " + relative)


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


# --------------------------------------------------------------- execution gate
def test_real_execution_is_gated_and_output_roots_are_unset() -> None:
    assert producer.REAL_EXECUTION_READY is False
    assert producer.FROZEN_REAL_CAPTURE_ROOT_SHA256 is None
    assert producer.FROZEN_REAL_SHARD_SET_ROOT_SHA256 is None
    assert producer.FROZEN_REAL_EFFECT_ROW_ROOT_SHA256 is None
    with pytest.raises(RuntimeError) as excinfo:
        producer.run_production_sweep()
    assert excinfo.value.args[0] == producer.STOP_NOT_AUTHORIZED


def test_no_caller_parameter_can_relax_the_execution_gate() -> None:
    import inspect
    signature = inspect.signature(producer.run_production_sweep)
    names = {p.name for p in signature.parameters.values()}
    for banned in ("allow_synthetic_test_fixture", "force", "bypass",
                   "real_execution_ready", "require_frozen"):
        assert banned not in names
    # Arbitrary kwargs are accepted syntactically but the gate precedes them.
    with pytest.raises(RuntimeError) as excinfo:
        producer.run_production_sweep(real_execution_ready=True, force=True)
    assert excinfo.value.args[0] == producer.STOP_NOT_AUTHORIZED


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
    pytest.skip("no root carries the full frozen authority set")


def test_mechanics_capture_schema_is_complete_and_dtype_bound() -> None:
    record = producer.mechanics_capture_record(
        identity="a" * 64, role="correct_student", canonical_cell_id="cellA",
        q=11, evidence_level=60, state_dim=160, dtype="float32")
    for field in ("schema", "identity", "role", "canonical_cell_id", "q",
                  "evidence_level", "state_dim", "dtype", "autocast",
                  "torch_no_grad", "encoder_eval", "gradient_checkpointing",
                  "accepted_real_forward_root", "partition"):
        assert field in record, field
    assert record["partition"] == "reader_fit"
    assert record["autocast"] is False and record["torch_no_grad"] is True
    with pytest.raises(ValueError):
        producer.mechanics_capture_record(
            identity="a" * 64, role="teacher", canonical_cell_id="c", q=1,
            evidence_level=None, state_dim=160, dtype="float64")


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
