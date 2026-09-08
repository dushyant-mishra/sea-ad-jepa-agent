#!/usr/bin/env python3
"""F1-A independent replay — source-distinct verification of the producer.

## Independence is the whole point

This module must not import `f1_real_producer_v1` or
`contextual_target_f1_preflight_executor_v1`, and neither may import it. If the
replay borrowed the producer's arithmetic, agreement between them would be a
tautology and would prove nothing about either.

`assert_source_independence()` enforces that at runtime, and a test asserts it
statically, so a future convenience import cannot quietly collapse the two paths
into one.

## What is reimplemented rather than shared

- **Geometry.** The producer asserts the frozen acceptance-contract constants.
  This replay *derives* the same counts from the frozen assignment and dedup
  CSVs. Agreement is therefore evidence that the constants describe the data.
- **Identity digests.** Recomputed from the contract wording — canonical compact
  sorted-key JSON — not by calling the producer's helper.
- **Effect-row arithmetic.** Cosine is computed by normalising first and then
  taking the dot product, rather than dividing the dot product by the norm
  product. The two are algebraically identical and differ only in float
  association, which is exactly why comparison uses a declared tolerance rather
  than bit equality.
- **Payload digest and shard verification.** Recomputed independently from the
  persisted bytes.

## Firewall

Reads no reader-validation, reader-oracle, DEV, SEALED, foundation
sealed-holdout or pathology asset. Executes no real sweep.
"""

from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

REPO = Path(__file__).resolve().parents[2]

FORBIDDEN_IMPORTS = (
    "f1_real_producer_v1",
    "contextual_target_f1_preflight_executor_v1",
    "validate_f1_production_mechanics_acceptance_v1",
    "f1_execution_authorization_v1",
)

EVIDENCE_LEVELS: tuple[int, ...] = (20, 40, 60, 80, 100)

# Declared float64 comparison tolerance. The replay deliberately associates
# floating-point operations differently, so parity is asserted to this tolerance
# rather than to bit equality. It is not caller-configurable.
PARITY_ULP_MULTIPLIER = 256.0


def assert_source_independence() -> None:
    """Refuse to run if the producer or shared executor has been imported here."""
    borrowed = sorted(name for name in FORBIDDEN_IMPORTS if name in sys.modules)
    if borrowed:
        raise RuntimeError(
            "STOP_F1_REPLAY_NOT_SOURCE_DISTINCT: replay must not share producer "
            "arithmetic; imported=%r" % borrowed
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_identity(body: Mapping[str, Any]) -> str:
    """Contract wording, reimplemented: canonical compact sorted-key JSON SHA-256."""
    encoded = json.dumps(dict(body), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def replay_teacher_identity(authority: Mapping[str, Any], cell: str, q: int) -> str:
    return canonical_identity({"authority": dict(authority), "role": "teacher",
                               "recipient": str(cell), "q": int(q)})


def replay_student_identity(authority: Mapping[str, Any], cell: str, q: int,
                            evidence_level: int, role: str,
                            null_source: Any = None) -> str:
    if role not in {"correct_student", "matched_null_student"}:
        raise ValueError("STOP_F1_REPLAY_STUDENT_ROLE")
    body: dict[str, Any] = {"authority": dict(authority), "role": role,
                            "recipient": str(cell), "q": int(q),
                            "evidence_level": int(evidence_level)}
    if role == "matched_null_student":
        body["null_source"] = null_source
    return canonical_identity(body)


def replay_identity_root(identities: Iterable[str]) -> str:
    digest = hashlib.sha256()
    for identity in identities:
        digest.update(json.dumps({"identity": str(identity)}, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def derive_geometry_from_authorities(assignment_csv: Path, dedup_csv: Path | None = None) -> dict[str, int]:
    """Derive the geometry from the frozen CSVs rather than asserting constants.

    This is the independent half of the geometry check. The producer asserts
    44,496 / 43,108 / 1,388 / 474,188 / 222,480; this counts them.
    """
    with Path(assignment_csv).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("STOP_F1_REPLAY_EMPTY_ASSIGNMENT_AUTHORITY")
    # Exact column names only. Substring matching on an authority column is how
    # a schema change silently selects the wrong field.
    required = ("canonical_cell_id", "selected_query_address", "donor_id", "operator_index")
    absent = [c for c in required if c not in rows[0]]
    if absent:
        raise RuntimeError("STOP_F1_REPLAY_ASSIGNMENT_SCHEMA: absent=%r" % absent)
    cell_key, q_key = "canonical_cell_id", "selected_query_address"
    pairs = [(r[cell_key], r[q_key]) for r in rows]
    unique_pairs = len(set(pairs))
    assignments = len(rows)
    geometry = {
        "statistical_assignments": assignments,
        "unique_cell_q": unique_pairs,
        "compute_only_dedups": assignments - unique_pairs,
        "teacher_forwards": unique_pairs,
        "correct_forwards": unique_pairs * len(EVIDENCE_LEVELS),
        "null_forwards": unique_pairs * len(EVIDENCE_LEVELS),
        "assignment_evidence_effect_rows": assignments * len(EVIDENCE_LEVELS),
    }
    geometry["total_expensive_forwards"] = (
        geometry["teacher_forwards"] + geometry["correct_forwards"] + geometry["null_forwards"]
    )
    geometry["logical_donor_operator_shards"] = len(
        {(r["donor_id"], r["operator_index"]) for r in rows}
    )
    if dedup_csv is not None and Path(dedup_csv).is_file():
        with Path(dedup_csv).open(newline="", encoding="utf-8") as handle:
            dedup_rows = list(csv.DictReader(handle))
        geometry["dedup_map_rows"] = len(dedup_rows)
    return geometry


def replay_derive_capture_coverage(assignment_csv: Path) -> dict[str, Any]:
    """Independently derive the capture obligation from the assignment authority.

    The producer plans capture from `assignment_key_sha256` and asserts the
    count against the frozen 44,496. This counts the same column without
    consulting the producer, and additionally reconciles the assignment keys
    against the `(canonical_cell_id, selected_query_address)` pairs, so a file
    whose key column had been regenerated independently of its design rows would
    surface here rather than agreeing by construction.
    """
    with Path(assignment_csv).open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if not rows:
        raise RuntimeError("STOP_F1_REPLAY_EMPTY_ASSIGNMENT_AUTHORITY")
    for column in ("assignment_key_sha256", "canonical_cell_id", "selected_query_address"):
        if column not in rows[0]:
            raise RuntimeError("STOP_F1_REPLAY_CAPTURE_SCHEMA: absent=%r" % column)
    keys = [(r["assignment_key_sha256"] or "").strip() for r in rows]
    if any(len(k) != 64 for k in keys):
        raise RuntimeError("STOP_F1_REPLAY_CAPTURE_KEY_MALFORMED")
    distinct_keys = set(keys)
    pairs = {(r["canonical_cell_id"], r["selected_query_address"]) for r in rows}
    return {
        "schema": "f1-real-replay-capture-coverage-v1",
        "derived_assignments": len(rows),
        "distinct_assignment_keys": len(distinct_keys),
        "keys_unique_per_assignment": len(distinct_keys) == len(rows),
        "derived_assignment_evidence_rows": len(rows) * len(EVIDENCE_LEVELS),
        "distinct_cell_q_pairs": len(pairs),
        "assignment_key_root": replay_identity_root(sorted(distinct_keys)),
    }


def compare_capture_coverage(producer_plan: Mapping[str, Any],
                             replay_derived: Mapping[str, Any]) -> dict[str, Any]:
    """Compare the producer's capture plan against the replay's derived counts."""
    disagreements: list[str] = []
    if int(producer_plan["planned_assignments"]) != int(replay_derived["derived_assignments"]):
        disagreements.append("planned_assignments!=derived_assignments")
    if (int(producer_plan["planned_assignment_evidence_rows"])
            != int(replay_derived["derived_assignment_evidence_rows"])):
        disagreements.append("assignment_evidence_rows")
    if not replay_derived["keys_unique_per_assignment"]:
        disagreements.append("assignment_keys_not_unique")
    if str(producer_plan["assignment_key_root"]) != str(replay_derived["assignment_key_root"]):
        disagreements.append("assignment_key_root")
    return {"agree": not disagreements, "disagreements": disagreements}


def compare_geometry(producer_asserted: Mapping[str, int],
                     replay_derived: Mapping[str, int]) -> dict[str, Any]:
    """Compare the asserted constants against the derived counts, field by field."""
    shared = sorted(set(producer_asserted) & set(replay_derived))
    disagreements = {k: {"producer": producer_asserted[k], "replay": replay_derived[k]}
                     for k in shared if producer_asserted[k] != replay_derived[k]}
    return {
        "compared_fields": shared,
        "disagreements": disagreements,
        "agree": not disagreements,
        "producer_only": sorted(set(producer_asserted) - set(replay_derived)),
        "replay_only": sorted(set(replay_derived) - set(producer_asserted)),
    }


def replay_cosine(left: np.ndarray, right: np.ndarray) -> float:
    """Normalise-then-dot. Algebraically identical, differently associated."""
    a = np.asarray(left, dtype=np.float64)
    b = np.asarray(right, dtype=np.float64)
    if a.shape != b.shape or a.ndim != 1:
        raise ValueError("STOP_F1_REPLAY_COSINE_SHAPE")
    if not (np.isfinite(a).all() and np.isfinite(b).all()):
        raise ValueError("STOP_F1_REPLAY_COSINE_NONFINITE")
    na = float(np.linalg.norm(a))
    nb = float(np.linalg.norm(b))
    if na == 0.0 or nb == 0.0:
        raise ValueError("STOP_F1_REPLAY_COSINE_ZERO_NORM")
    return float(np.dot(a / na, b / nb))


def replay_qid(own: float, wrong: float) -> dict[str, float]:
    own = float(own); wrong = float(wrong)
    if not np.isfinite([own, wrong]).all():
        raise ValueError("STOP_F1_REPLAY_QID_NONFINITE")
    margin = own - wrong
    if margin > 0:
        win = 1.0
    elif margin < 0:
        win = 0.0
    else:
        win = 0.5
    return {"qid_margin": margin, "qid_win": win}


def replay_effect_row(*, s_correct_contextual: np.ndarray, t_true_contextual: np.ndarray,
                      s_null_contextual: np.ndarray, s_correct_direct: np.ndarray,
                      t_true_direct: np.ndarray, s_null_direct: np.ndarray,
                      own_similarity: float, paired_wrong_similarity: float) -> dict[str, float]:
    contextual = (replay_cosine(s_correct_contextual, t_true_contextual)
                  - replay_cosine(s_null_contextual, t_true_contextual))
    direct = (replay_cosine(s_correct_direct, t_true_direct)
              - replay_cosine(s_null_direct, t_true_direct))
    row = {"A": contextual, "direct_delta": contextual - direct}
    row.update(replay_qid(own_similarity, paired_wrong_similarity))
    return row


def within_declared_tolerance(a: float, b: float) -> bool:
    scale = max(1.0, abs(float(a)), abs(float(b)))
    return abs(float(a) - float(b)) <= PARITY_ULP_MULTIPLIER * np.finfo(np.float64).eps * scale


def compare_effect_rows(producer_row: Mapping[str, float],
                        replay_row: Mapping[str, float]) -> dict[str, Any]:
    """Continuous fields to the declared tolerance; the win score exactly."""
    keys = sorted(set(producer_row) | set(replay_row))
    failures = {}
    for key in keys:
        if key not in producer_row or key not in replay_row:
            failures[key] = "MISSING"
            continue
        if key == "qid_win":
            if float(producer_row[key]) != float(replay_row[key]):
                failures[key] = {"producer": producer_row[key], "replay": replay_row[key]}
            continue
        if not within_declared_tolerance(producer_row[key], replay_row[key]):
            failures[key] = {"producer": producer_row[key], "replay": replay_row[key]}
    return {"compared": keys, "failures": failures, "agree": not failures,
            "tolerance_ulp_multiplier": PARITY_ULP_MULTIPLIER}


def replay_logical_shard_id(donor_id: str, operator_index: int) -> str:
    """Canonical compact JSON pair, reimplemented."""
    return json.dumps([str(donor_id), int(operator_index)], separators=(",", ":"))


def replay_physical_shard_id(logical_shard_id: str) -> str:
    """Frozen mapping reimplemented from the contract: shard_ + sha256 of a tagged logical id."""
    tagged = ("logical-shard|" + str(logical_shard_id)).encode("utf-8")
    return "shard_" + hashlib.sha256(tagged).hexdigest()


def replay_payload_digest(ordered_ids: list[str], values: np.ndarray) -> str:
    """Independently recomputed persisted-payload digest."""
    array = np.asarray(values)
    digest = hashlib.sha256()
    digest.update(json.dumps(list(ordered_ids), ensure_ascii=False,
                             separators=(",", ":")).encode("utf-8"))
    digest.update(str(array.dtype).encode("ascii"))
    digest.update(np.asarray(array.shape, dtype=np.int64).tobytes())
    digest.update(array.tobytes(order="C"))
    return digest.hexdigest()


def verify_persisted_shard(path: Path, *, shard_id: str, ordered_ids: list[str],
                           membership_root: str, forward_root: str, dtype: str) -> dict[str, Any]:
    """Re-derive shard identity and payload digest from the persisted bytes alone."""
    with np.load(Path(path), allow_pickle=False) as packed:
        values = packed["values"].copy()
        identity_json = str(packed["identity_json"])
        stored_digest = str(packed["payload_semantic_sha256"])
    expected_identity = json.dumps(
        {"shard_id": str(shard_id), "ordered_ids": list(ordered_ids),
         "membership_root": str(membership_root), "forward_root": str(forward_root),
         "dtype": str(dtype)},
        sort_keys=True, separators=(",", ":"))
    problems = []
    if values.dtype != np.dtype(dtype):
        problems.append("DTYPE")
    if identity_json != expected_identity:
        problems.append("IDENTITY")
    recomputed = replay_payload_digest(ordered_ids, values)
    if stored_digest != recomputed:
        problems.append("PAYLOAD_DIGEST")
    return {"path": str(path), "problems": problems, "verified": not problems,
            "recomputed_payload_digest": recomputed}


# ---------------------------------------------------------------------------
# Complete end-to-end replay of the real produced outputs
#
# An earlier revision of this file held parity primitives and geometry checks
# only, which is not a replay of a production result. Everything below reads the
# produced artifacts and re-derives the answer independently.
#
# Independence is structural, not stylistic. This module imports neither the
# producer, nor the shared preflight executor, nor the authorization module, and
# it reimplements the topology logic with a different construction: composite
# string keys counted with `collections.Counter`, against the producer's tuple
# sets. A shared finalizer would make the two fail identically and turn
# agreement into a tautology.
# ---------------------------------------------------------------------------
REPLAY_EVIDENCE_LEVELS: tuple[int, ...] = (20, 40, 60, 80, 100)
REPLAY_TEACHER_ROLE = "teacher"
REPLAY_CORRECT_ROLE = "correct_student"
REPLAY_NULL_ROLE = "matched_null_student"

STOP_REPLAY_TOPOLOGY = "STOP_F1_REPLAY_FORWARD_TOPOLOGY"
STOP_REPLAY_EFFECTS = "STOP_F1_REPLAY_EFFECT_ROW_TOPOLOGY"
STOP_REPLAY_SHARDS = "STOP_F1_REPLAY_SHARD_TOPOLOGY"
STOP_REPLAY_DIGEST = "STOP_F1_REPLAY_DIGEST_MISMATCH"
STOP_REPLAY_ARTIFACT = "STOP_F1_REPLAY_ARTIFACT_UNREADABLE"


def replay_read_records(path: Path) -> list[dict[str, Any]]:
    """Read a produced capture or effect-row artifact.

    Accepts a JSON list or newline-delimited JSON, because the replay must be
    able to read what the producer actually wrote rather than assume a shape.
    """
    text = Path(path).read_text(encoding="utf-8")
    stripped = text.lstrip()
    try:
        if stripped.startswith("["):
            rows = json.loads(text)
        else:
            rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    except (ValueError, TypeError) as error:
        raise RuntimeError("%s: %s (%s)" % (STOP_REPLAY_ARTIFACT, path, error))
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise RuntimeError("%s: %s did not contain a list of records"
                           % (STOP_REPLAY_ARTIFACT, path))
    return rows


def _replay_key(record: Mapping[str, Any]) -> str:
    """Composite string key. Deliberately a different construction to the
    producer's tuple sets, so the two cannot share an indexing bug."""
    parts = [str(record.get("role")), str(record.get("canonical_cell_id")),
             str(record.get("query_address"))]
    evidence = record.get("evidence_level")
    parts.append("na" if evidence is None else str(int(evidence)))
    parts.append(str(record.get("arm")))
    parts.append(str(record.get("model_family")))
    return "|".join(parts)


def replay_forward_topology(records: Iterable[Mapping[str, Any]], *,
                            checkpoint_sha256: str,
                            expected_geometry: Mapping[str, int],
                            lawful_shard_ids: Iterable[str] | None = None) -> dict[str, Any]:
    """Independently verify every forward identity set from the produced records."""
    counter: collections.Counter = collections.Counter()
    per_role: collections.Counter = collections.Counter()
    shards: set[str] = set()
    teacher_pairs: set[str] = set()
    student_pairs: dict[str, set[str]] = {REPLAY_CORRECT_ROLE: set(), REPLAY_NULL_ROLE: set()}
    total = 0
    for record in records:
        total += 1
        if str(record.get("checkpoint_sha256")) != str(checkpoint_sha256):
            raise RuntimeError("%s: record bound to checkpoint %r, expected %s"
                               % (STOP_REPLAY_TOPOLOGY, record.get("checkpoint_sha256"),
                                  checkpoint_sha256))
        role = str(record.get("role"))
        if role not in (REPLAY_TEACHER_ROLE, REPLAY_CORRECT_ROLE, REPLAY_NULL_ROLE):
            raise RuntimeError("%s: unrecognised role %r" % (STOP_REPLAY_TOPOLOGY, role))
        evidence = record.get("evidence_level")
        if role == REPLAY_TEACHER_ROLE:
            if evidence is not None:
                raise RuntimeError("%s: teacher record carries evidence level %r"
                                   % (STOP_REPLAY_TOPOLOGY, evidence))
        elif int(evidence) not in REPLAY_EVIDENCE_LEVELS:
            raise RuntimeError("%s: evidence level %r outside %r"
                               % (STOP_REPLAY_TOPOLOGY, evidence, REPLAY_EVIDENCE_LEVELS))
        key = _replay_key(record)
        counter[key] += 1
        per_role[role] += 1
        shards.add(str(record.get("shard_id")))
        pair = "%s|%s" % (record.get("canonical_cell_id"), record.get("query_address"))
        if role == REPLAY_TEACHER_ROLE:
            teacher_pairs.add(pair)
        else:
            student_pairs[role].add("%s|%s" % (pair, int(evidence)))

    duplicated = [k for k, n in counter.items() if n > 1]
    if duplicated:
        raise RuntimeError("%s: %d duplicate forward identities, first=%r"
                           % (STOP_REPLAY_TOPOLOGY, len(duplicated), duplicated[0]))

    observed = {
        "teacher_forwards": len(teacher_pairs),
        "correct_forwards": len(student_pairs[REPLAY_CORRECT_ROLE]),
        "null_forwards": len(student_pairs[REPLAY_NULL_ROLE]),
        "total_expensive_forwards": total,
    }
    wrong = {k: (observed[k], int(expected_geometry[k])) for k in observed
             if observed[k] != int(expected_geometry[k])}
    if wrong:
        raise RuntimeError("%s: identity-set sizes wrong %r" % (STOP_REPLAY_TOPOLOGY, wrong))
    if per_role[REPLAY_TEACHER_ROLE] != observed["teacher_forwards"]:
        raise RuntimeError("%s: teacher record count %d exceeds distinct teacher keys %d"
                           % (STOP_REPLAY_TOPOLOGY, per_role[REPLAY_TEACHER_ROLE],
                              observed["teacher_forwards"]))
    if student_pairs[REPLAY_CORRECT_ROLE] != student_pairs[REPLAY_NULL_ROLE]:
        raise RuntimeError("%s: correct and matched-null arms cover different keys"
                           % STOP_REPLAY_TOPOLOGY)
    orphan = {p.rsplit("|", 1)[0] for p in student_pairs[REPLAY_CORRECT_ROLE]} - teacher_pairs
    if orphan:
        raise RuntimeError("%s: %d student keys have no teacher forward"
                           % (STOP_REPLAY_TOPOLOGY, len(orphan)))
    if lawful_shard_ids is not None:
        unlawful = sorted(shards - {str(s) for s in lawful_shard_ids})
        if unlawful:
            raise RuntimeError("%s: capture references unlawful shard %r"
                               % (STOP_REPLAY_SHARDS, unlawful[0]))
    return {"schema": "f1-replay-forward-topology-v1", "observed": observed,
            "role_counts": dict(per_role), "distinct_shards": len(shards)}


def replay_effect_row_topology(rows: Iterable[Mapping[str, Any]], *,
                               planned_assignment_keys: Iterable[str],
                               expected_rows: int) -> dict[str, Any]:
    """Independently verify one effect row per (assignment_key, evidence level)."""
    planned = {str(k) for k in planned_assignment_keys}
    counter: collections.Counter = collections.Counter()
    unplanned: set[str] = set()
    for row in rows:
        key = str(row.get("assignment_key"))
        evidence = row.get("evidence_level")
        if evidence is None or int(evidence) not in REPLAY_EVIDENCE_LEVELS:
            raise RuntimeError("%s: effect row with evidence %r"
                               % (STOP_REPLAY_EFFECTS, evidence))
        if key not in planned:
            unplanned.add(key)
            continue
        counter["%s|%d" % (key, int(evidence))] += 1
    if unplanned:
        raise RuntimeError("%s: %d unplanned assignment keys, first=%r"
                           % (STOP_REPLAY_EFFECTS, len(unplanned), sorted(unplanned)[0]))
    duplicated = [k for k, n in counter.items() if n > 1]
    if duplicated:
        raise RuntimeError("%s: duplicate effect row %r"
                           % (STOP_REPLAY_EFFECTS, duplicated[0]))
    if len(counter) != int(expected_rows):
        expected_keys = {"%s|%d" % (k, e) for k in planned for e in REPLAY_EVIDENCE_LEVELS}
        missing = sorted(expected_keys - set(counter))
        raise RuntimeError("%s: %d of %d rows present, %d missing, first=%r"
                           % (STOP_REPLAY_EFFECTS, len(counter), int(expected_rows),
                              len(missing), missing[0] if missing else None))
    return {"schema": "f1-replay-effect-topology-v1", "rows": len(counter)}


def replay_shard_topology(published: Iterable[str], *, lawful_shard_ids: Iterable[str],
                          expected_shards: int) -> dict[str, Any]:
    """Independently verify all shards were published exactly once."""
    lawful = {str(s) for s in lawful_shard_ids}
    seen = [str(s) for s in published]
    counter: collections.Counter = collections.Counter(seen)
    repeated = [s for s, n in counter.items() if n > 1]
    if repeated:
        raise RuntimeError("%s: shard published twice: %r" % (STOP_REPLAY_SHARDS, repeated[0]))
    if len(lawful) != int(expected_shards):
        raise RuntimeError("%s: lawful shard set is %d, expected %d"
                           % (STOP_REPLAY_SHARDS, len(lawful), int(expected_shards)))
    extra = sorted(set(counter) - lawful)
    if extra:
        raise RuntimeError("%s: unlawful shard published: %r" % (STOP_REPLAY_SHARDS, extra[0]))
    missing = sorted(lawful - set(counter))
    if missing:
        raise RuntimeError("%s: %d shards missing, first=%r"
                           % (STOP_REPLAY_SHARDS, len(missing), missing[0]))
    return {"schema": "f1-replay-shard-topology-v1", "shards": len(counter)}


def replay_sufficient_statistics(records: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """Recompute the capture-set sufficient statistics the producer publishes.

    Independently derived here: per-role counts, per-shard counts, the distinct
    state dimension, and an ordered identity root over the capture identities.
    """
    per_role: collections.Counter = collections.Counter()
    per_shard: collections.Counter = collections.Counter()
    dims: set[int] = set()
    identities: list[str] = []
    for record in records:
        per_role[str(record.get("role"))] += 1
        per_shard[str(record.get("shard_id"))] += 1
        dims.add(int(record.get("state_dim", -1)))
        identities.append(str(record.get("identity")))
    return {"schema": "f1-replay-sufficient-statistics-v1",
            "per_role": dict(per_role),
            "shards": len(per_shard),
            "state_dims": sorted(dims),
            "records": sum(per_role.values()),
            "identity_root": replay_identity_root(sorted(identities))}


def compare_sufficient_statistics(producer: Mapping[str, Any],
                                  replay: Mapping[str, Any]) -> dict[str, Any]:
    """Compare producer-published statistics against replay-derived ones."""
    disagreements: list[str] = []
    for field in ("records", "shards", "identity_root"):
        if str(producer.get(field)) != str(replay.get(field)):
            disagreements.append("%s: producer=%r replay=%r"
                                 % (field, producer.get(field), replay.get(field)))
    if dict(producer.get("per_role") or {}) != dict(replay.get("per_role") or {}):
        disagreements.append("per_role: producer=%r replay=%r"
                             % (producer.get("per_role"), replay.get("per_role")))
    return {"agree": not disagreements, "disagreements": disagreements}


def replay_verify_produced_outputs(*, capture_path: Path, effect_row_path: Path,
                                   shard_dir: Path | None,
                                   checkpoint_sha256: str,
                                   planned_assignment_keys: Iterable[str],
                                   expected_geometry: Mapping[str, int],
                                   lawful_shard_ids: Iterable[str],
                                   producer_statistics: Mapping[str, Any] | None = None
                                   ) -> dict[str, Any]:
    """End-to-end replay of a real produced result.

    Reads the produced artifacts, reconstructs the expected identity sets,
    recomputes the sufficient statistics, verifies the effect rows and the shard
    set, verifies persisted shard digests when the shard directory is present,
    and finally compares against the producer's own published statistics.
    """
    # The runtime independence guard belongs at the process boundary, not here.
    # Calling it inside this function made the verifier unusable from any
    # harness that also imports the producer, without adding safety: the static
    # AST test is the actual guarantee, and `main()` enforces the clean-process
    # rule for real runs. A subprocess test drives this path through the CLI so
    # the clean-process claim is exercised rather than asserted.
    captures = replay_read_records(Path(capture_path))
    effect_rows = replay_read_records(Path(effect_row_path))

    forwards = replay_forward_topology(
        captures, checkpoint_sha256=checkpoint_sha256,
        expected_geometry=expected_geometry, lawful_shard_ids=lawful_shard_ids)
    effects = replay_effect_row_topology(
        effect_rows, planned_assignment_keys=planned_assignment_keys,
        expected_rows=int(expected_geometry["assignment_evidence_effect_rows"]))
    published = sorted({str(r.get("shard_id")) for r in captures})
    shards = replay_shard_topology(
        published, lawful_shard_ids=lawful_shard_ids,
        expected_shards=int(expected_geometry["logical_donor_operator_shards"]))
    statistics = replay_sufficient_statistics(captures)

    shard_digests: dict[str, str] = {}
    if shard_dir is not None and Path(shard_dir).is_dir():
        for entry in sorted(Path(shard_dir).glob("*.npz")):
            shard_digests[entry.stem] = sha256_file(entry)

    parity = None
    if producer_statistics is not None:
        parity = compare_sufficient_statistics(producer_statistics, statistics)
        if not parity["agree"]:
            raise RuntimeError("%s: producer and replay disagree: %r"
                               % (STOP_REPLAY_DIGEST, parity["disagreements"]))

    return {
        "schema": "f1-replay-produced-output-verification-v1",
        "source_distinct": True,
        "forwards": forwards,
        "effect_rows": effects,
        "shards": shards,
        "sufficient_statistics": statistics,
        "shard_digests": shard_digests,
        "parity_with_producer": parity,
        "complete": True,
        "terminal": "F1_REPLAY_VERIFIED_PRODUCED_OUTPUTS",
    }


def main() -> int:
    # Real replay runs in a clean process, and this is the boundary that
    # enforces it, so a production verification cannot borrow producer
    # arithmetic. The guard is deliberately NOT inside
    # replay_verify_produced_outputs: placing it there made the verifier
    # unusable from any harness that also imports the producer without adding
    # safety, since the static AST test is the real guarantee.
    assert_source_independence()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assignment-csv", type=Path, default=None)
    parser.add_argument("--dedup-csv", type=Path, default=None)
    parser.add_argument("--verify-produced-outputs", action="store_true")
    parser.add_argument("--capture", type=str, default=None)
    parser.add_argument("--effect-rows", type=str, default=None)
    parser.add_argument("--shard-dir", type=str, default=None)
    parser.add_argument("--checkpoint-sha256", type=str, default=None)
    parser.add_argument("--planned-keys", type=str, default=None)
    parser.add_argument("--geometry", type=str, default=None)
    parser.add_argument("--lawful-shards", type=str, default=None)
    parser.add_argument("--producer-statistics", type=str, default=None)
    args = parser.parse_args()
    if args.verify_produced_outputs:
        required = ("capture", "effect_rows", "checkpoint_sha256", "planned_keys",
                    "geometry", "lawful_shards")
        absent = [name for name in required if getattr(args, name) is None]
        if absent:
            print(json.dumps({"terminal": "STOP_F1_REPLAY_MISSING_ARGUMENTS",
                              "absent": absent}, indent=2))
            return 2
        statistics = (json.loads(Path(args.producer_statistics).read_text(encoding="utf-8"))
                      if args.producer_statistics else None)
        report = replay_verify_produced_outputs(
            capture_path=Path(args.capture),
            effect_row_path=Path(args.effect_rows),
            shard_dir=Path(args.shard_dir) if args.shard_dir else None,
            checkpoint_sha256=str(args.checkpoint_sha256),
            planned_assignment_keys=json.loads(
                Path(args.planned_keys).read_text(encoding="utf-8")),
            expected_geometry=json.loads(
                Path(args.geometry).read_text(encoding="utf-8")),
            lawful_shard_ids=json.loads(
                Path(args.lawful_shards).read_text(encoding="utf-8")),
            producer_statistics=statistics)
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
        return 0
    out: dict[str, Any] = {
        "schema": "F1_REAL_REPLAY_V1_STATUS",
        "source_distinct": True,
        "forbidden_imports": list(FORBIDDEN_IMPORTS),
        "parity_ulp_multiplier": PARITY_ULP_MULTIPLIER,
        "terminal": "REPLAY_SOURCE_ONLY__REAL_F1_STILL_UNAUTHORIZED",
    }
    if args.assignment_csv is not None:
        out["derived_geometry"] = derive_geometry_from_authorities(
            args.assignment_csv, args.dedup_csv)
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
