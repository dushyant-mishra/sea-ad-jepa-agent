#!/usr/bin/env python3
"""F1-A primary production producer — pre-result, source-frozen, execution-gated.

Binds the reviewed F1 preflight authorities and the frozen production mechanics
acceptance contract. Plans and, once explicitly authorized, executes the real
reader-forward sweep over the frozen reader-fit plan.

## What this file does NOT do

It does not execute the real sweep. `REAL_EXECUTION_READY` is `False` and the
real output roots are unset, so `run_production_sweep` raises. Real execution
requires a separate prospective authorization plus the data-only closure step,
and neither is granted here.

It opens no reader-validation, reader-oracle, DEV, SEALED, foundation
sealed-holdout or pathology asset. The lawful partition is `reader_fit` only.

## Relationship to the replay

`scripts/v4/f1_real_replay_v1.py` is the independent verification path. It must
not import this module and this module must not import it. Agreement between the
two is only evidence if neither can borrow the other's arithmetic:

- this producer ASSERTS the frozen geometry constants from the acceptance
  contract;
- the replay DERIVES the same counts from the frozen assignment and dedup CSVs.

A shared helper would make agreement tautological, so the producer uses the
reviewed preflight primitives while the replay reimplements them.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "scripts" / "v4"))

from contextual_target_f1_preflight_executor_v1 import (  # noqa: E402
    AtomicShardStore,
    build_effect_row,
    full_geometry,
    student_forward_identity,
    teacher_compute_identity,
)
from validate_f1_production_mechanics_acceptance_v1 import (  # noqa: E402
    physical_shard_id,
)

# ---------------------------------------------------------------------------
# Execution gate. Real outputs may only be bound by the data-only closure step
# described in docs/agent/F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md, and never by
# editing this source after outcomes exist.
# ---------------------------------------------------------------------------
REAL_EXECUTION_READY: bool = False
FROZEN_REAL_CAPTURE_ROOT_SHA256: str | None = None
FROZEN_REAL_SHARD_SET_ROOT_SHA256: str | None = None
FROZEN_REAL_EFFECT_ROW_ROOT_SHA256: str | None = None

STOP_NOT_AUTHORIZED = "STOP_F1_REAL_PRODUCER_EXECUTION_NOT_AUTHORIZED"
STOP_OUTPUT_ROOTS_UNSET = "STOP_F1_REAL_PRODUCER_OUTPUT_ROOTS_NOT_FROZEN"

# Frozen authority digests, transcribed from the reviewed preflight bindings.
# Every one is re-verified against bytes on disk before any planning.
PREFLIGHT_AUTHORITY_SHA256: dict[str, str] = {
    "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv":
        "12fd5f1549bb600e6bf52605196024f91bae28d7d20cb35a327d67c383f2c617",
    "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv":
        "3fcd11908723e2cc80db0f5a0f017ad382bd1ed9be522f97081587ae989c2423",
    "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv":
        "aba31aea56190c32a00ac27a0356ea860761143f00f874db9c71c2080eb371a6",
    "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt":
        "19fb0c25d9f7549c37de39285807d5b6a6e828ced94af63927e83fa3c5c6b7c4",
    "src/sea_ad_jepa/v4/ipb_jepa.py":
        "732ea46f72384f29d503de1e0cc9d853315e2493cace054cced74849aa77485a",
    "src/sea_ad_jepa/v4/gene_tokenizer.py":
        "2a2ba7f4c2e52364cce471466ebacceefc2a1fccb29f4959860c885f281a89f4",
    "src/sea_ad_jepa/v4/contextual_query_local.py":
        "6bd641cd22c160dfbec4e1ae4a0cc31929af436526487383f290397f4f55eeaa",
}

# Accepted real-forward root from the production mechanics acceptance contract.
ACCEPTED_REAL_FORWARD_ROOT = "007bc6f182354a133a2ec49ce0ef5966831d4995a0a2a5f004bb845772469ad3"

# Fixed accepted mechanics. Retuning is forbidden by the acceptance contract.
ACCEPTED_MECHANICS: dict[str, Any] = {
    "forward_batch": 4,
    "reader_block": 4,
    "workers": 4,
    "prefetch": 4,
    "pinned_memory": False,
    "dtype": "float32",
    "autocast": False,
    "torch_no_grad": True,
    "encoder_eval": True,
    "gradient_checkpointing": False,
}

EVIDENCE_LEVELS: tuple[int, ...] = (20, 40, 60, 80, 100)

# The three forward roles the sweep executes. A capture record carrying any
# other role is rejected rather than stored, because an unrecognised role is how
# an uncounted forward enters the capture set.
LEGAL_CAPTURE_ROLES: tuple[str, ...] = ("teacher", "correct_student",
                                        "matched_null_student")

# Canonical per-assignment identity column in F1_QUERY_ASSIGNMENTS_2DRAW.csv.
# Named exactly; substring matching on an authority column is how a schema
# change silently selects the wrong field.
ASSIGNMENT_KEY_COLUMN = "assignment_key_sha256"

LAWFUL_PARTITION = "reader_fit"
FORBIDDEN_PARTITIONS = ("reader_validation", "reader_oracle", "development",
                        "sealed_holdout", "whole_study_external_holdout")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_authorities(repo: Path = REPO) -> dict[str, str]:
    """Fail closed unless every frozen authority matches its declared digest."""
    verified: dict[str, str] = {}
    missing: list[str] = []
    mismatched: list[str] = []
    for relative, expected in PREFLIGHT_AUTHORITY_SHA256.items():
        path = repo / relative
        if not path.is_file():
            missing.append(relative)
            continue
        actual = sha256_file(path)
        if actual != expected:
            mismatched.append(relative)
            continue
        verified[relative] = actual
    if missing or mismatched:
        raise RuntimeError(
            "STOP_F1_PRODUCER_AUTHORITY_BINDING: missing=%r mismatched=%r"
            % (missing, mismatched)
        )
    return verified


def assert_frozen_geometry(observed: Mapping[str, int] | None = None) -> dict[str, int]:
    """Assert the acceptance-contract geometry. Constants, not derived counts.

    The replay derives these independently from the frozen CSVs, so an
    inconsistency between the two surfaces here rather than being averaged away.
    """
    geometry = full_geometry()
    required = {
        "statistical_assignments": 44496,
        "unique_cell_q": 43108,
        "compute_only_dedups": 1388,
        "teacher_forwards": 43108,
        "correct_forwards": 215540,
        "null_forwards": 215540,
        "total_expensive_forwards": 474188,
        "assignment_evidence_effect_rows": 222480,
        "logical_donor_operator_shards": 1400,
    }
    wrong = {k: (geometry.get(k), v) for k, v in required.items() if geometry.get(k) != v}
    if wrong:
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY: " + repr(wrong))
    # Internal reconciliations, restated so a future edit to one side is caught.
    if geometry["statistical_assignments"] - geometry["unique_cell_q"] != geometry["compute_only_dedups"]:
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_DEDUP_RECONCILIATION")
    if geometry["correct_forwards"] != geometry["unique_cell_q"] * (len(EVIDENCE_LEVELS)):
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_CORRECT_PER_EVIDENCE")
    if geometry["null_forwards"] != geometry["correct_forwards"]:
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_NULL_SYMMETRY")
    if (geometry["teacher_forwards"] + geometry["correct_forwards"]
            + geometry["null_forwards"] != geometry["total_expensive_forwards"]):
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_FORWARD_RECONCILIATION")
    if geometry["assignment_evidence_effect_rows"] != geometry["statistical_assignments"] * len(EVIDENCE_LEVELS):
        raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_EFFECT_ROWS")
    if observed is not None:
        disagree = {k: (observed.get(k), geometry[k]) for k in geometry
                    if k in observed and observed[k] != geometry[k]}
        if disagree:
            raise AssertionError("STOP_F1_PRODUCER_GEOMETRY_OBSERVED: " + repr(disagree))
    return geometry


def assert_lawful_partition(partitions: Iterable[str]) -> None:
    """Only reader_fit may be planned. Any protected partition is fail-closed."""
    seen = {str(p) for p in partitions}
    forbidden = sorted(seen & set(FORBIDDEN_PARTITIONS))
    if forbidden:
        raise RuntimeError("STOP_F1_PRODUCER_FORBIDDEN_PARTITION: " + repr(forbidden))
    unexpected = sorted(seen - {LAWFUL_PARTITION})
    if unexpected:
        raise RuntimeError("STOP_F1_PRODUCER_UNEXPECTED_PARTITION: " + repr(unexpected))


def plan_forward_identities(records: list[Mapping[str, Any]], authority: Mapping[str, Any]) -> dict[str, Any]:
    """Enumerate the ordered expensive-forward identity set for the given records.

    Teacher identity is evidence-invariant and appears once per unique `(cell,q)`
    in first-appearance order. Each unique `(cell,q)` then contributes one correct
    and one matched-null student identity at each ordered evidence level.
    """
    auth = dict(authority)
    teacher_order: list[str] = []
    seen_pairs: set[tuple[str, int]] = set()
    ordered: list[dict[str, Any]] = []
    for record in records:
        pair = (str(record["canonical_cell_id"]), int(record["q"]))
        if pair in seen_pairs:
            continue
        seen_pairs.add(pair)
        identity = teacher_compute_identity(auth, record)
        teacher_order.append(identity)
        ordered.append({"role": "teacher", "identity": identity,
                        "canonical_cell_id": pair[0], "q": pair[1]})
        for level in EVIDENCE_LEVELS:
            scoped = dict(record); scoped["evidence_level"] = int(level)
            for role in ("correct_student", "matched_null_student"):
                ordered.append({
                    "role": role,
                    "identity": student_forward_identity(auth, scoped, role),
                    "canonical_cell_id": pair[0], "q": pair[1],
                    "evidence_level": int(level),
                })
    identities = [row["identity"] for row in ordered]
    if len(set(identities)) != len(identities):
        raise AssertionError("STOP_F1_PRODUCER_IDENTITY_COLLISION")
    return {
        "unique_cell_q": len(seen_pairs),
        "teacher_forwards": len(teacher_order),
        "correct_forwards": sum(1 for r in ordered if r["role"] == "correct_student"),
        "null_forwards": sum(1 for r in ordered if r["role"] == "matched_null_student"),
        "total_expensive_forwards": len(ordered),
        "ordered": ordered,
        "identity_root_sha256": identity_root(identities),
    }


def identity_root(identities: list[str]) -> str:
    """SHA-256 over LF-separated canonical compact sorted-key identity records."""
    digest = hashlib.sha256()
    for identity in identities:
        digest.update(json.dumps({"identity": identity}, sort_keys=True,
                                 separators=(",", ":")).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def logical_shard_id(donor_id: str, operator_index: int) -> str:
    """Logical shard identity: the frozen (donor_id, operator_index) pair.

    Encoded as canonical compact JSON so the pair is injective with no delimiter
    ambiguity. This string is an identity, never a filename.
    """
    return json.dumps([str(donor_id), int(operator_index)], separators=(",", ":"))


def storage_shard_id(donor_id: str, operator_index: int) -> str:
    """Physical storage id, via the frozen acceptance-contract mapping.

    An earlier draft here built the filename directly from the donor and
    operator with a `::` separator, which is an illegal Windows filename
    character. The reviewed acceptance validator had already solved this by
    hashing the logical id into `shard_<sha256>`, so this binds that mapping
    rather than reinventing an encoding over a solved problem.
    """
    return physical_shard_id(logical_shard_id(donor_id, operator_index))


def mechanics_capture_record(*, identity: str, role: str, canonical_cell_id: str,
                             q: int, evidence_level: int | None,
                             state_dim: int, dtype: str,
                             assignment_key: str) -> dict[str, Any]:
    """The per-assignment mechanics capture schema.

    Records what was executed and under which bound authority, never a
    biological verdict.

    Coverage over all 44,496 assignments is deliberately *not* asserted by this
    function and must not be claimed from it. An earlier revision stated in its
    docstring that it "covers every one of the 44,496 assignments" while nothing
    enumerated or enforced that -- the unverified prose claim this project
    exists to reject. Coverage is enforced by `plan_mechanics_capture` and
    `assert_capture_coverage`, which fail closed on a missing, duplicated or
    unplanned assignment key.
    """
    if dtype != ACCEPTED_MECHANICS["dtype"]:
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_DTYPE")
    if role not in LEGAL_CAPTURE_ROLES:
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_ROLE: %r not in %r"
                         % (role, LEGAL_CAPTURE_ROLES))
    if role == "teacher":
        # The teacher state is evidence-invariant, so an evidence level on a
        # teacher record would imply five distinct teacher forwards per (cell,q)
        # and silently inflate the forward count.
        if evidence_level is not None:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_TEACHER_EVIDENCE_INVARIANT")
    elif evidence_level not in EVIDENCE_LEVELS:
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_EVIDENCE_LEVEL: %r not in %r"
                         % (evidence_level, EVIDENCE_LEVELS))
    if not (isinstance(assignment_key, str) and len(assignment_key) == 64):
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_ASSIGNMENT_KEY")
    return {
        "schema": "f1-real-mechanics-capture-v1",
        "identity": str(identity),
        "assignment_key": str(assignment_key),
        "role": str(role),
        "canonical_cell_id": str(canonical_cell_id),
        "q": int(q),
        "evidence_level": None if evidence_level is None else int(evidence_level),
        "state_dim": int(state_dim),
        "dtype": str(dtype),
        "autocast": ACCEPTED_MECHANICS["autocast"],
        "torch_no_grad": ACCEPTED_MECHANICS["torch_no_grad"],
        "encoder_eval": ACCEPTED_MECHANICS["encoder_eval"],
        "gradient_checkpointing": ACCEPTED_MECHANICS["gradient_checkpointing"],
        "accepted_real_forward_root": ACCEPTED_REAL_FORWARD_ROOT,
        "partition": LAWFUL_PARTITION,
    }


def plan_mechanics_capture(assignment_csv: Path) -> dict[str, Any]:
    """Enumerate the mechanics-capture plan over every statistical assignment.

    Reads the frozen assignment authority and returns the ordered set of
    `assignment_key_sha256` values that capture must cover, one per assignment.
    The count is asserted against the frozen 44,496 and the assignment-by-
    evidence expansion against the frozen 222,480, so a truncated or extended
    authority file cannot quietly shrink the capture obligation.

    This is a *plan*, not an execution. It reads a reader-fit design authority
    and touches no biological state, no checkpoint and no forward pass.
    """
    import csv

    keys: list[str] = []
    with io_open_text(assignment_csv) as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None or ASSIGNMENT_KEY_COLUMN not in reader.fieldnames:
            raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_SCHEMA: %s absent"
                                 % ASSIGNMENT_KEY_COLUMN)
        for row in reader:
            key = (row.get(ASSIGNMENT_KEY_COLUMN) or "").strip()
            if len(key) != 64:
                raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_KEY_MALFORMED")
            keys.append(key)

    geometry = assert_frozen_geometry()
    expected = geometry["statistical_assignments"]
    if len(keys) != expected:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_ROWS: %d != %d"
                             % (len(keys), expected))
    distinct = set(keys)
    if len(distinct) != expected:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_NOT_DISTINCT: %d distinct of %d"
                             % (len(distinct), expected))
    rows = len(keys) * len(EVIDENCE_LEVELS)
    if rows != geometry["assignment_evidence_effect_rows"]:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_EVIDENCE_EXPANSION: %d != %d"
                             % (rows, geometry["assignment_evidence_effect_rows"]))
    return {
        "schema": "f1-real-mechanics-capture-plan-v1",
        "assignment_keys": keys,
        "planned_assignments": len(keys),
        "planned_assignment_evidence_rows": rows,
        "evidence_levels": list(EVIDENCE_LEVELS),
        "capture_roles": list(LEGAL_CAPTURE_ROLES),
        "assignment_key_root": identity_root(sorted(keys)),
    }


def assert_capture_coverage(captured: Iterable[Mapping[str, Any]],
                            plan: Mapping[str, Any]) -> dict[str, Any]:
    """Fail closed unless capture covers each planned assignment exactly once.

    Three separate failures, kept distinct because they have different causes:
    a planned assignment with no capture record (a dropped forward), a planned
    assignment captured twice (a double count), and a capture record whose key
    is not in the plan at all (an unauthorised forward).
    """
    planned: set[str] = set(plan["assignment_keys"])
    if len(planned) != int(plan["planned_assignments"]):
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_PLAN_INTERNALLY_INCONSISTENT")

    seen: dict[str, int] = {}
    unplanned: set[str] = set()
    for record in captured:
        key = str(record.get("assignment_key", ""))
        if key not in planned:
            unplanned.add(key)
            continue
        seen[key] = seen.get(key, 0) + 1

    missing = sorted(planned - set(seen))
    duplicated = sorted(k for k, n in seen.items() if n > 1)
    if unplanned:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_UNPLANNED_ASSIGNMENT: %d, first=%r"
                             % (len(unplanned), sorted(unplanned)[0]))
    if missing:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_INCOMPLETE: %d uncaptured of %d, first=%r"
                             % (len(missing), len(planned), missing[0]))
    if duplicated:
        raise AssertionError("STOP_F1_PRODUCER_CAPTURE_DUPLICATED: %d, first=%r"
                             % (len(duplicated), duplicated[0]))
    return {
        "schema": "f1-real-mechanics-capture-coverage-v1",
        "planned_assignments": len(planned),
        "captured_assignments": len(seen),
        "complete": True,
    }


def io_open_text(path: Path):
    """Open a frozen CSV authority as text with an explicit newline policy."""
    return open(path, "r", encoding="utf-8", newline="")


def _require_real_execution() -> None:
    if REAL_EXECUTION_READY is not True:
        raise RuntimeError(STOP_NOT_AUTHORIZED)
    if not all((FROZEN_REAL_CAPTURE_ROOT_SHA256,
                FROZEN_REAL_SHARD_SET_ROOT_SHA256,
                FROZEN_REAL_EFFECT_ROW_ROOT_SHA256)):
        raise RuntimeError(STOP_OUTPUT_ROOTS_UNSET)


def run_production_sweep(**kwargs: Any) -> dict[str, Any]:
    """Sole real-execution entrypoint. Fail-closed and currently unreachable.

    There is deliberately no parameter that relaxes the gate. A caller cannot
    pass a flag to reach the sweep, and the gate is checked before any argument
    is inspected.
    """
    _require_real_execution()
    raise RuntimeError(STOP_NOT_AUTHORIZED)  # unreachable while the gate holds


def produce_shard_for_test(store: AtomicShardStore, *, donor_id: str, operator_index: int,
                           ordered_ids: list[str], values: np.ndarray) -> Path:
    """Diagnostic shard commit for synthetic/technical fixtures only."""
    return store.commit(storage_shard_id(donor_id, operator_index), ordered_ids, values)


def effect_row_for_test(**kwargs: Any) -> dict[str, float]:
    """Diagnostic effect-row construction on synthetic states only."""
    return build_effect_row(**kwargs)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-authorities", action="store_true")
    parser.add_argument("--report-geometry", action="store_true")
    args = parser.parse_args()
    out: dict[str, Any] = {
        "schema": "F1_REAL_PRODUCER_V1_STATUS",
        "real_execution_ready": REAL_EXECUTION_READY,
        "frozen_real_output_roots_set": bool(FROZEN_REAL_CAPTURE_ROOT_SHA256),
        "accepted_mechanics": ACCEPTED_MECHANICS,
        "accepted_real_forward_root": ACCEPTED_REAL_FORWARD_ROOT,
        "lawful_partition": LAWFUL_PARTITION,
        "terminal": "PRODUCER_SOURCE_ONLY__REAL_F1_STILL_UNAUTHORIZED",
    }
    if args.report_geometry:
        out["geometry"] = assert_frozen_geometry()
    if args.verify_authorities:
        out["verified_authorities"] = {k: v[:16] for k, v in verify_authorities().items()}
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
