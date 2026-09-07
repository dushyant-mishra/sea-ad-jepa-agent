#!/usr/bin/env python3
"""F1-A primary production producer — pre-result, source-frozen, execution-gated.

Binds the reviewed F1 preflight authorities and the frozen production mechanics
acceptance contract. Plans and, once explicitly authorized, executes the real
reader-forward sweep over the frozen reader-fit plan.

## Execution authorization is external to this source

`run_production_sweep` is a real end-to-end producer, not a gate followed by a
STOP. It cannot run without a valid external authorization artifact, and there
is no in-source boolean to flip: an earlier revision carried
`REAL_EXECUTION_READY = False` plus three `None` output roots, which meant the
only way to make the frozen source runnable was to edit it and thereby destroy
the freeze. Authorization now lives in
`scripts/v4/f1_execution_authorization_v1.py` and is read from an artifact whose
path comes from the environment.

The authorization binds, before any output exists, the package root, the frozen
source digests, the u0 checkpoint, the reader population roster, the authority
digests, the accepted mechanics and the frozen geometry. Each drift is a
separate STOP. The post-result data-only closure is NOT authorization: it
carries produced roots that cannot exist beforehand, and an artifact carrying
them is rejected, so a run cannot be authorized retroactively.

## Scope of the first real run

The first real F1 run is a REFERENCE PRODUCTION-MECHANICS BASELINE ON CLEAN u0.
It is not a healthy trained-teacher result, not a biological qualification of
u0, not authority to select a future training target, and not authority to begin
D1 or production teacher training. Model width 160 is architectural, and the u0
checkpoint is a mechanics fixture.

It opens no reader-validation, reader-oracle, DEV, SEALED, foundation
sealed-holdout or pathology asset. The lawful partition is `reader_fit` only,
and `foundation` and `train` are not synonyms for it: the lawful donor roster
comes from the reader partition column of the frozen split authority, so
continuation and train donors outside `reader_fit` are absent by construction
rather than by a filter.

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
# The reviewed upstream validator imports `scripts.v4`, so the repository
# root must also be importable. Without this the module works under pytest
# (which adds the rootdir) but fails when run as a CLI.
sys.path.insert(0, str(REPO))

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
from f1_execution_authorization_v1 import (  # noqa: E402
    assert_not_closure_artifact,
    load_authorization_payload,
    validate_execution_authorization,
)

# ---------------------------------------------------------------------------
# There is deliberately NO in-source execution flag and no in-source output
# root. Authorization is an external pre-result artifact; produced roots are
# bound afterwards by the data-only closure in
# docs/agent/F1_DATA_ONLY_CLOSURE_DESIGN_20260907.md. Neither is ever a constant
# in this file, because editing this file after the freeze destroys the freeze.
# ---------------------------------------------------------------------------
STOP_NOT_AUTHORIZED = "STOP_F1_REAL_PRODUCER_EXECUTION_NOT_AUTHORIZED"

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


# Each authority is digested over the bytes that actually define it, and the
# class is declared per authority rather than guessed.
#
# This distinction is load bearing and an earlier revision got it wrong. The
# three model sources are tracked text, so on Windows they are checked out with
# CRLF and their working-tree bytes differ from the immutable blob by one byte
# per line: in this worktree `ipb_jepa.py` hashes to f5bdfb73... on disk and to
# the frozen 732ea46f... in the index. Hashing disk bytes therefore passed in
# one checkout and failed in another purely from line-ending policy, which is
# the same defect that has already had a package rejected in this project. The
# assignment CSVs and the checkpoint are large untracked data, so for those the
# file bytes ARE the authority.
GIT_BLOB_BYTES_TRACKED_SOURCE = "GIT_BLOB_BYTES_TRACKED_SOURCE"
DISK_BYTES_UNTRACKED_DATA = "DISK_BYTES_UNTRACKED_DATA"

AUTHORITY_BYTES_CLASS: dict[str, str] = {
    "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_ASSIGNMENTS_2DRAW.csv":
        DISK_BYTES_UNTRACKED_DATA,
    "outputs/contextual_teacher_target_v1_f1_querydesign_repair_20260901/F1_QUERY_EXECUTION_DEDUP_MAP.csv":
        DISK_BYTES_UNTRACKED_DATA,
    "outputs/contextual_teacher_target_v1_f1_prospective_repair_20260901/F1_MATCHED_NULL_PRIMARY_MAP.csv":
        DISK_BYTES_UNTRACKED_DATA,
    "exports/prod41k_teacher_t1_20260823/t1_run/t1_checkpoint_u0000.pt":
        DISK_BYTES_UNTRACKED_DATA,
    "src/sea_ad_jepa/v4/ipb_jepa.py": GIT_BLOB_BYTES_TRACKED_SOURCE,
    "src/sea_ad_jepa/v4/gene_tokenizer.py": GIT_BLOB_BYTES_TRACKED_SOURCE,
    "src/sea_ad_jepa/v4/contextual_query_local.py": GIT_BLOB_BYTES_TRACKED_SOURCE,
}

STOP_AUTHORITY_BINDING = "STOP_F1_PRODUCER_AUTHORITY_BINDING"
STOP_AUTHORITY_UNREACHABLE = "STOP_F1_PRODUCER_AUTHORITY_UNREACHABLE"

AUTHORITY_SEARCH_ROOTS = (Path("/mnt/d/Jepa project"), Path("D:/Jepa project"))


def git_blob_sha256(repo: Path, relative: str) -> str | None:
    """SHA-256 over the bytes git holds. Platform-independent by construction."""
    import subprocess

    result = subprocess.run(["git", "-C", str(repo), "show", ":" + relative],
                            capture_output=True)
    if result.returncode != 0:
        return None
    return hashlib.sha256(result.stdout).hexdigest()


def resolve_data_authority(repo: Path, relative: str) -> Path | None:
    for root in (repo,) + AUTHORITY_SEARCH_ROOTS:
        candidate = Path(root) / relative
        if candidate.is_file():
            return candidate
    return None


def verify_authorities(data_root: Path | None = None, *, strict: bool = True,
                      source_repo: Path = REPO) -> dict[str, str]:
    """Fail closed unless every frozen authority matches its declared digest.

    The two authority classes resolve from DIFFERENT places, and conflating them
    was a real defect. Tracked model sources are verified against the frozen
    package's own git, because that is the tree whose committed bytes the
    package froze: `src/sea_ad_jepa/v4/contextual_query_local.py` is tracked on
    this branch but untracked in the main working repository, so resolving it
    from whichever tree happens to hold the large CSVs reported a present
    authority as missing. Large untracked data authorities resolve from
    `data_root` and then the search roots, since for those the file bytes are
    the authority.

    With `strict=False` an unreachable data authority is reported as
    NOT_MEASURABLE rather than verified, and never as a pass. A MISMATCH is
    always fatal. Production review must use strict mode.
    """
    verified: dict[str, str] = {}
    not_measurable: list[str] = []
    missing: list[str] = []
    mismatched: list[dict[str, str]] = []
    for relative, expected in PREFLIGHT_AUTHORITY_SHA256.items():
        kind = AUTHORITY_BYTES_CLASS[relative]
        if kind == GIT_BLOB_BYTES_TRACKED_SOURCE:
            actual = git_blob_sha256(source_repo, relative)
            if actual is None:
                missing.append(relative)
                continue
        else:
            path = resolve_data_authority(data_root or source_repo, relative)
            if path is None:
                (missing if strict else not_measurable).append(relative)
                continue
            actual = sha256_file(path)
        if actual != expected:
            mismatched.append({"authority": relative, "observed": actual,
                               "expected": expected, "bytes_class": kind})
            continue
        verified[relative] = actual
    if mismatched:
        raise RuntimeError("%s: mismatched=%r" % (STOP_AUTHORITY_BINDING, mismatched))
    if missing:
        raise RuntimeError("%s: missing=%r (strict=%s)"
                           % (STOP_AUTHORITY_UNREACHABLE, missing, strict))
    if not_measurable:
        verified["__not_measurable__"] = ",".join(sorted(not_measurable))
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


def mechanics_capture_record(*, identity: str, canonical_cell_id: str,
                             q: int, state_dim: int, dtype: str,
                             assignment_key: str,
                             checkpoint_sha256: str | None = None) -> dict[str, Any]:
    """ASSIGNMENT-level mechanics capture. Deliberately carries no role.

    An earlier revision put `role` and `evidence_level` on this record while its
    validator only proved one record per assignment key, so a set holding one
    teacher record per assignment passed as complete while containing no
    correct-student and no matched-null evidence forward at all. The two ideas
    are now separate objects: this one records that an assignment's mechanics
    were captured, and `forward_capture_record` records an individual model
    forward with its role, evidence level, arm, family, shard and checkpoint.

    Coverage over all 44,496 assignments is enforced by `plan_mechanics_capture`
    and `assert_capture_coverage`; the forward topology is enforced separately by
    `assert_forward_topology`. Neither validator is sufficient alone, and
    `verify_sweep_completeness` requires both.
    """
    if dtype != ACCEPTED_MECHANICS['dtype']:
        raise ValueError('STOP_F1_PRODUCER_CAPTURE_DTYPE')
    if not (isinstance(assignment_key, str) and len(assignment_key) == 64):
        raise ValueError('STOP_F1_PRODUCER_CAPTURE_ASSIGNMENT_KEY')
    return {
        'schema': 'f1-real-mechanics-capture-v1',
        'level': 'ASSIGNMENT',
        'identity': str(identity),
        'assignment_key': str(assignment_key),
        'canonical_cell_id': str(canonical_cell_id),
        'q': int(q),
        'state_dim': int(state_dim),
        'dtype': str(dtype),
        'checkpoint_sha256': None if checkpoint_sha256 is None else str(checkpoint_sha256),
        'autocast': ACCEPTED_MECHANICS['autocast'],
        'torch_no_grad': ACCEPTED_MECHANICS['torch_no_grad'],
        'encoder_eval': ACCEPTED_MECHANICS['encoder_eval'],
        'gradient_checkpointing': ACCEPTED_MECHANICS['gradient_checkpointing'],
        'accepted_real_forward_root': ACCEPTED_REAL_FORWARD_ROOT,
        'partition': LAWFUL_PARTITION,
        'sufficient_for_completeness': False,
        'note': 'assignment-level only; forward topology is validated separately',
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


# ---------------------------------------------------------------------------
# Forward-level identity topology
#
# The assignment-level capture record above and the forward-level record below
# are deliberately DIFFERENT objects, because an earlier revision blurred them:
# the record carried `role` and `evidence_level` while the validator only proved
# one record per assignment key. A set holding exactly one teacher record per
# assignment satisfied that validator while containing no correct-student and no
# matched-null evidence forward at all.
#
# So the split is explicit. `mechanics_capture_record` is assignment-level and
# carries no role or evidence level. `forward_capture_record` is forward-level
# and must distinguish role, recipient cell, query, evidence level where
# applicable, correct versus matched-null arm, teacher versus student family,
# shard, and model/checkpoint identity. `assert_forward_topology` then enforces
# the exact identity-set sizes rather than a single count.
# ---------------------------------------------------------------------------
TEACHER_ROLE = "teacher"
CORRECT_STUDENT_ROLE = "correct_student"
MATCHED_NULL_STUDENT_ROLE = "matched_null_student"

CORRECT_ARM = "correct"
MATCHED_NULL_ARM = "matched_null"

TEACHER_FAMILY = "teacher"
STUDENT_FAMILY = "student"

STOP_TOPOLOGY = "STOP_F1_FORWARD_TOPOLOGY"
STOP_EFFECT_TOPOLOGY = "STOP_F1_EFFECT_ROW_TOPOLOGY"
STOP_SHARD_TOPOLOGY = "STOP_F1_SHARD_TOPOLOGY"
STOP_CHECKPOINT_IDENTITY = "STOP_F1_CAPTURE_CHECKPOINT_IDENTITY"


def forward_capture_record(*, identity: str, role: str, canonical_cell_id: str,
                           query_address: str, evidence_level: int | None,
                           arm: str | None, model_family: str, shard_id: str,
                           checkpoint_sha256: str, state_dim: int,
                           dtype: str) -> dict[str, Any]:
    """One executed model forward, with every identity dimension it belongs to."""
    if role not in LEGAL_CAPTURE_ROLES:
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_ROLE: %r" % (role,))
    if dtype != ACCEPTED_MECHANICS["dtype"]:
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_DTYPE")
    if len(str(checkpoint_sha256)) != 64:
        raise ValueError(STOP_CHECKPOINT_IDENTITY)
    if role == TEACHER_ROLE:
        # The teacher state is evidence-invariant. An evidence level here would
        # imply five teacher forwards per (cell,q) and inflate 43,108 to 215,540.
        if evidence_level is not None:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_TEACHER_EVIDENCE_INVARIANT")
        if arm is not None:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_TEACHER_HAS_NO_ARM")
        if model_family != TEACHER_FAMILY:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_TEACHER_FAMILY")
    else:
        if evidence_level not in EVIDENCE_LEVELS:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_EVIDENCE_LEVEL: %r" % (evidence_level,))
        expected_arm = CORRECT_ARM if role == CORRECT_STUDENT_ROLE else MATCHED_NULL_ARM
        if arm != expected_arm:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_ARM: %r for role %r" % (arm, role))
        if model_family != STUDENT_FAMILY:
            raise ValueError("STOP_F1_PRODUCER_CAPTURE_STUDENT_FAMILY")
    if not str(shard_id).startswith("shard_"):
        raise ValueError("STOP_F1_PRODUCER_CAPTURE_SHARD_ID: %r" % (shard_id,))
    return {
        "schema": "f1-real-forward-capture-v1",
        "identity": str(identity),
        "role": str(role),
        "canonical_cell_id": str(canonical_cell_id),
        "query_address": str(query_address),
        "evidence_level": None if evidence_level is None else int(evidence_level),
        "arm": None if arm is None else str(arm),
        "model_family": str(model_family),
        "shard_id": str(shard_id),
        "checkpoint_sha256": str(checkpoint_sha256),
        "state_dim": int(state_dim),
        "dtype": str(dtype),
        "autocast": ACCEPTED_MECHANICS["autocast"],
        "torch_no_grad": ACCEPTED_MECHANICS["torch_no_grad"],
        "encoder_eval": ACCEPTED_MECHANICS["encoder_eval"],
        "gradient_checkpointing": ACCEPTED_MECHANICS["gradient_checkpointing"],
        "partition": LAWFUL_PARTITION,
    }


def assert_forward_topology(records: Iterable[Mapping[str, Any]], *,
                            checkpoint_sha256: str,
                            lawful_shard_ids: Iterable[str] | None = None,
                            geometry: Mapping[str, int] | None = None) -> dict[str, Any]:
    """Enforce every forward identity set separately.

    A single total, or a single per-assignment count, is not enough: the three
    roles have different identity keys and different sizes, and a set with the
    right total but the wrong role distribution must fail.
    """
    frozen = dict(geometry or assert_frozen_geometry())
    teacher_keys: set[tuple[str, str]] = set()
    correct_keys: set[tuple[str, str, int]] = set()
    null_keys: set[tuple[str, str, int]] = set()
    duplicates: list[Any] = []
    shards: set[str] = set()
    total = 0

    for record in records:
        total += 1
        role = str(record.get("role"))
        cell = str(record.get("canonical_cell_id"))
        query = str(record.get("query_address"))
        evidence = record.get("evidence_level")
        arm = record.get("arm")
        family = str(record.get("model_family"))
        shard = str(record.get("shard_id"))
        if str(record.get("checkpoint_sha256")) != str(checkpoint_sha256):
            raise AssertionError(
                "%s: a capture record names checkpoint %r but the run is bound to %s"
                % (STOP_CHECKPOINT_IDENTITY, record.get("checkpoint_sha256"),
                   checkpoint_sha256))
        shards.add(shard)
        if role == TEACHER_ROLE:
            if evidence is not None or arm is not None or family != TEACHER_FAMILY:
                raise AssertionError("%s: malformed teacher record %r"
                                     % (STOP_TOPOLOGY, {"evidence": evidence, "arm": arm}))
            key = (cell, query)
            if key in teacher_keys:
                duplicates.append(("teacher", key))
            teacher_keys.add(key)
        elif role == CORRECT_STUDENT_ROLE:
            if arm != CORRECT_ARM or family != STUDENT_FAMILY:
                raise AssertionError("%s: correct-student record with arm=%r family=%r"
                                     % (STOP_TOPOLOGY, arm, family))
            key = (cell, query, int(evidence))
            if key in correct_keys:
                duplicates.append(("correct_student", key))
            correct_keys.add(key)
        elif role == MATCHED_NULL_STUDENT_ROLE:
            if arm != MATCHED_NULL_ARM or family != STUDENT_FAMILY:
                raise AssertionError("%s: matched-null record with arm=%r family=%r"
                                     % (STOP_TOPOLOGY, arm, family))
            key = (cell, query, int(evidence))
            if key in null_keys:
                duplicates.append(("matched_null_student", key))
            null_keys.add(key)
        else:
            raise AssertionError("%s: unrecognised role %r" % (STOP_TOPOLOGY, role))

    if duplicates:
        raise AssertionError("%s: duplicate forward identities, first=%r"
                             % (STOP_TOPOLOGY, duplicates[0]))

    observed = {
        "teacher_forwards": len(teacher_keys),
        "correct_forwards": len(correct_keys),
        "null_forwards": len(null_keys),
        "total_expensive_forwards": total,
    }
    expected = {k: int(frozen[k]) for k in observed}
    wrong = {k: (observed[k], expected[k]) for k in observed if observed[k] != expected[k]}
    if wrong:
        raise AssertionError(
            "%s: identity-set sizes wrong %r; a correct grand total with the wrong "
            "role distribution is still a failure" % (STOP_TOPOLOGY, wrong))

    # Correct and matched-null arms must cover exactly the same (cell,q,evidence)
    # keys. A null arm covering different keys would silently compare unmatched
    # pairs.
    if correct_keys != null_keys:
        only_correct = sorted(correct_keys - null_keys)[:3]
        only_null = sorted(null_keys - correct_keys)[:3]
        raise AssertionError(
            "%s: correct and matched-null arms cover different keys; only_correct=%r "
            "only_null=%r" % (STOP_TOPOLOGY, only_correct, only_null))

    # Every student key must have its evidence-invariant teacher forward.
    missing_teacher = sorted({(c, q) for c, q, _ in correct_keys} - teacher_keys)
    if missing_teacher:
        raise AssertionError("%s: %d student keys have no teacher forward, first=%r"
                             % (STOP_TOPOLOGY, len(missing_teacher), missing_teacher[0]))

    if lawful_shard_ids is not None:
        lawful = {str(s) for s in lawful_shard_ids}
        unlawful = sorted(shards - lawful)
        if unlawful:
            raise AssertionError("%s: capture references %d shards outside the lawful "
                                 "set, first=%r" % (STOP_SHARD_TOPOLOGY, len(unlawful),
                                                    unlawful[0]))
    return {"schema": "f1-forward-topology-v1", "observed": observed,
            "distinct_shards": len(shards), "complete": True}


def assert_effect_row_topology(rows: Iterable[Mapping[str, Any]], *,
                               planned_assignment_keys: Iterable[str],
                               geometry: Mapping[str, int] | None = None) -> dict[str, Any]:
    """Exactly one effect row per (assignment_key, evidence_level)."""
    frozen = dict(geometry or assert_frozen_geometry())
    planned = {str(k) for k in planned_assignment_keys}
    seen: set[tuple[str, int]] = set()
    duplicates: list[Any] = []
    unplanned: set[str] = set()
    for row in rows:
        key = str(row.get("assignment_key"))
        evidence = row.get("evidence_level")
        if evidence not in EVIDENCE_LEVELS:
            raise AssertionError("%s: effect row with evidence_level %r"
                                 % (STOP_EFFECT_TOPOLOGY, evidence))
        if key not in planned:
            unplanned.add(key)
            continue
        pair = (key, int(evidence))
        if pair in seen:
            duplicates.append(pair)
        seen.add(pair)
    if unplanned:
        raise AssertionError("%s: %d effect rows carry unplanned assignment keys, first=%r"
                             % (STOP_EFFECT_TOPOLOGY, len(unplanned), sorted(unplanned)[0]))
    if duplicates:
        raise AssertionError("%s: duplicate effect rows, first=%r"
                             % (STOP_EFFECT_TOPOLOGY, duplicates[0]))
    expected_rows = int(frozen["assignment_evidence_effect_rows"])
    if len(seen) != expected_rows:
        missing = sorted({(k, e) for k in planned for e in EVIDENCE_LEVELS} - seen)
        raise AssertionError(
            "%s: %d of %d assignment x evidence effect rows present; %d missing, first=%r"
            % (STOP_EFFECT_TOPOLOGY, len(seen), expected_rows, len(missing),
               missing[0] if missing else None))
    return {"schema": "f1-effect-row-topology-v1", "rows": len(seen), "complete": True}


def assert_shard_topology(published: Iterable[str], *,
                          lawful_shard_ids: Iterable[str],
                          geometry: Mapping[str, int] | None = None) -> dict[str, Any]:
    """All 1,400 donor x operator shards must be published, and nothing else."""
    frozen = dict(geometry or assert_frozen_geometry())
    lawful = {str(s) for s in lawful_shard_ids}
    expected = int(frozen["logical_donor_operator_shards"])
    if len(lawful) != expected:
        raise AssertionError("%s: lawful shard set has %d entries, expected %d"
                             % (STOP_SHARD_TOPOLOGY, len(lawful), expected))
    seen: list[str] = [str(s) for s in published]
    unique = set(seen)
    if len(seen) != len(unique):
        raise AssertionError("%s: a shard was published more than once" % STOP_SHARD_TOPOLOGY)
    extra = sorted(unique - lawful)
    if extra:
        raise AssertionError("%s: published shard outside the lawful set: %r"
                             % (STOP_SHARD_TOPOLOGY, extra[0]))
    missing = sorted(lawful - unique)
    if missing:
        raise AssertionError("%s: %d of %d shards missing, first=%r"
                             % (STOP_SHARD_TOPOLOGY, len(missing), expected, missing[0]))
    return {"schema": "f1-shard-topology-v1", "shards": len(unique), "complete": True}


# ---------------------------------------------------------------------------
# Population firewall: reader_fit only, by roster identity
# ---------------------------------------------------------------------------
READER_DONOR_SPLIT_REL = ("exports/foundation_calibration_bundle_20260824/splits/"
                          "reader_donor_split.csv")
READER_DONOR_SPLIT_SHA256 = (
    "efe43e63bfd580085f115f74dd00fdf3051f2c2a77674c99cee5c9ce43322511")
LAWFUL_READER_FIT_DONORS = 104
LAWFUL_READER_FIT_ROSTER_ROOT = (
    "a635ddf3ddfbf274826fa3bab6fc7d98a655b37caa1411ee0a1fdf9dac1e80d0")

STOP_POPULATION_FIREWALL = "STOP_F1_POPULATION_FIREWALL"


def load_reader_fit_roster(split_path: Path) -> dict[str, Any]:
    """The exact lawful donor roster, from the frozen donor-level split authority.

    Reading donor-level split membership is not opening a protected population;
    it is what allows the firewall to assert population identity without ever
    touching a protected row. `foundation` and `train` are NOT synonyms for
    `reader_fit`, so the roster is taken from the reader partition column only,
    and any continuation or train donor that is not in `reader_fit` is therefore
    absent by construction rather than by a filter.
    """
    import csv

    digest = sha256_file(split_path)
    if digest != READER_DONOR_SPLIT_SHA256:
        raise AssertionError("%s: reader split digest %s, expected %s"
                             % (STOP_POPULATION_FIREWALL, digest, READER_DONOR_SPLIT_SHA256))
    with io_open_text(split_path) as handle:
        rows = list(csv.DictReader(handle))
    if not rows or "donor_id" not in rows[0] or "reader_partition" not in rows[0]:
        raise AssertionError("%s: unexpected reader split schema" % STOP_POPULATION_FIREWALL)
    by_partition: dict[str, set[str]] = {}
    for row in rows:
        by_partition.setdefault(str(row["reader_partition"]), set()).add(str(row["donor_id"]))
    fit = by_partition.get(LAWFUL_PARTITION, set())
    if len(fit) != LAWFUL_READER_FIT_DONORS:
        raise AssertionError("%s: split declares %d reader_fit donors, expected %d"
                             % (STOP_POPULATION_FIREWALL, len(fit), LAWFUL_READER_FIT_DONORS))
    roster_root = hashlib.sha256("\n".join(sorted(fit)).encode("utf-8")).hexdigest()
    if roster_root != LAWFUL_READER_FIT_ROSTER_ROOT:
        raise AssertionError("%s: roster root %s, expected %s"
                             % (STOP_POPULATION_FIREWALL, roster_root,
                                LAWFUL_READER_FIT_ROSTER_ROOT))
    return {"roster": fit, "roster_root": roster_root, "split_sha256": digest,
            "declared_partition_donor_counts": {p: len(v) for p, v in sorted(by_partition.items())}}


def assert_donors_within_reader_fit(donors: Iterable[str], roster: Iterable[str]) -> dict[str, Any]:
    """Every delivered donor must be on the reader_fit roster. Never a filter."""
    lawful = {str(d) for d in roster}
    delivered = {str(d) for d in donors}
    off = sorted(delivered - lawful)
    if off:
        raise PermissionError(
            "%s: %d delivered donors are outside the reader_fit roster, first=%r; "
            "refusing to filter and continue" % (STOP_POPULATION_FIREWALL, len(off), off[0]))
    return {"delivered_donors": len(delivered), "off_roster": 0,
            "partition": LAWFUL_PARTITION}


# ---------------------------------------------------------------------------
# The real end-to-end producer
# ---------------------------------------------------------------------------
class ForwardEngine:
    """The model seam. A real engine performs actual encoder forwards.

    Kept as one injected object so the frozen pipeline below is genuine
    end-to-end code rather than a stub, while the torch dependency stays at a
    single boundary. `TorchForwardEngine` is the production implementation and
    imports torch lazily, so this module loads in environments without it and a
    technical fixture can exercise every other stage.
    """

    def teacher_forward(self, *, cell: Mapping[str, Any], query_address: str) -> Any:
        raise NotImplementedError

    def student_forward(self, *, cell: Mapping[str, Any], query_address: str,
                        evidence_level: int, arm: str) -> Any:
        raise NotImplementedError


class TorchForwardEngine(ForwardEngine):
    """Production forward engine under the frozen accepted mechanics.

    float32, autocast off, `torch.no_grad`, encoder in eval, no gradient
    checkpointing -- the acceptance contract fixes these and retuning them is
    forbidden. The historical T1 export ran its forward under float16 autocast;
    that is deliberately not reproduced here.
    """

    def __init__(self, *, checkpoint_path: Path, model_module: Any = None) -> None:
        self.checkpoint_path = Path(checkpoint_path)
        self._model_module = model_module
        self._encoder = None

    def _load(self) -> Any:
        if self._encoder is not None:
            return self._encoder
        import torch  # noqa: F401  (lazy: absent in source-only environments)

        if self._model_module is None:
            raise RuntimeError(
                "STOP_F1_FORWARD_ENGINE_UNBOUND: the authorized model module must be "
                "supplied by the execution binding; this source does not choose one")
        state = torch.load(str(self.checkpoint_path), map_location="cpu")
        encoder = self._model_module.build_teacher_encoder(state)
        encoder.eval()
        self._encoder = encoder
        return encoder

    def _forward(self, cell: Mapping[str, Any], mask: Any) -> Any:
        import torch

        encoder = self._load()
        with torch.no_grad():
            return encoder(**{"cell": cell, "mask": mask})

    def teacher_forward(self, *, cell: Mapping[str, Any], query_address: str) -> Any:
        return self._forward(cell, mask=None)

    def student_forward(self, *, cell: Mapping[str, Any], query_address: str,
                        evidence_level: int, arm: str) -> Any:
        return self._forward(cell, mask=(query_address, int(evidence_level), str(arm)))


def normalize_expression(raw_counts: Any, source_library: float) -> Any:
    """The frozen transform, applied exactly once: log1p(c*10000/max(L,1)).

    Bound to the controlling production loader, which guards the divisor with
    `np.maximum(library, 1.0)` and applies log1p to the sparse `.data` array so
    a structural zero stays structural rather than becoming a measured zero.
    """
    counts = np.asarray(raw_counts, dtype=np.float64)
    library = max(float(source_library), 1.0)
    return np.log1p(counts * (10000.0 / library))


def build_query_evidence_mask(*, query_address: str, evidence_level: int,
                              measurable: Any) -> Any:
    """Evidence mask for one (query, evidence level) under the observation state.

    Only physically measurable addresses may enter an evidence mask; a
    structurally unmeasured address is never presented as evidence, which is the
    distinction the acceptance contract requires be preserved.
    """
    if evidence_level not in EVIDENCE_LEVELS:
        raise ValueError("STOP_F1_EVIDENCE_LEVEL: %r" % (evidence_level,))
    support = np.asarray(measurable, dtype=bool)
    if support.ndim != 1:
        raise ValueError("measurable must be a 1-D observation-state mask")
    eligible = np.flatnonzero(support)
    if eligible.size == 0:
        raise ValueError("STOP_F1_NO_MEASURABLE_EVIDENCE")
    take = int(round(eligible.size * (int(evidence_level) / 100.0)))
    mask = np.zeros_like(support)
    mask[eligible[:max(take, 1)]] = True
    return mask


def run_production_sweep(*, authorization_path: str | Path | None = None,
                         forward_engine: ForwardEngine | None = None,
                         reader: Any = None,
                         package_root_sha256: str | None = None,
                         output_dir: Path | None = None,
                         repo: Path = REPO,
                         **kwargs: Any) -> dict[str, Any]:
    """The real end-to-end producer. Fail-closed without external authorization.

    Stages, in order: authorization, population firewall on reader_fit only,
    reader row resolution, exact normalization, observation-state handling,
    query/evidence mask construction, teacher forward, correct-student forwards,
    matched-null student forwards, capture, cache, shard publication, effect-row
    publication, resumable completion, and final completeness verification.

    There is no in-source switch that reaches this work. Authorization is an
    external artifact validated against the package root, the frozen source
    digests, the u0 checkpoint, the reader population, the authority digests, the
    accepted mechanics and the frozen geometry, and every drift is a distinct
    STOP. A post-result closure cannot authorize the run that produced it.
    """
    payload = load_authorization_payload(authorization_path)
    assert_not_closure_artifact(payload)

    geometry = assert_frozen_geometry()
    observed_authorities = verify_authorities(repo, strict=True)
    observed_sources = frozen_source_digests(repo)
    if package_root_sha256 is None:
        raise PermissionError(
            "%s: the caller must supply the package root the run is authorized "
            "against; it is not read from mutable source" % STOP_NOT_AUTHORIZED)

    split_path = _resolve_from(repo, READER_DONOR_SPLIT_REL)
    roster = load_reader_fit_roster(split_path)

    authorization = validate_execution_authorization(
        payload,
        package_root_sha256=str(package_root_sha256),
        observed_source_sha256=observed_sources,
        observed_authority_sha256=observed_authorities,
        accepted_mechanics=ACCEPTED_MECHANICS,
        frozen_geometry=geometry,
        accepted_real_forward_root=ACCEPTED_REAL_FORWARD_ROOT,
        lawful_partition=LAWFUL_PARTITION,
        expected_donor_count=LAWFUL_READER_FIT_DONORS,
        expected_donor_roster_root=roster["roster_root"])

    if forward_engine is None or reader is None:
        raise PermissionError(
            "%s: an authorized forward engine and lawful reader must be supplied by "
            "the execution binding" % STOP_NOT_AUTHORIZED)

    return execute_authorized_sweep(
        authorization=authorization, roster=roster, geometry=geometry,
        forward_engine=forward_engine, reader=reader,
        output_dir=Path(output_dir) if output_dir else None, **kwargs)


def execute_authorized_sweep(*, authorization: Mapping[str, Any],
                             roster: Mapping[str, Any], geometry: Mapping[str, int],
                             forward_engine: ForwardEngine, reader: Any,
                             output_dir: Path | None,
                             membership_root: str | None = None) -> dict[str, Any]:
    """Execute the sweep once authorization has been validated.

    Separate from `run_production_sweep` so the authorization boundary is a
    single place and the pipeline itself is testable against a technical reader
    and forward engine without ever weakening that boundary: reaching this
    function at all requires a validated authorization object.
    """
    if str(authorization.get("partition")) != LAWFUL_PARTITION:
        raise PermissionError("%s: authorization partition %r"
                              % (STOP_POPULATION_FIREWALL, authorization.get("partition")))
    checkpoint = str(authorization["checkpoint_sha256"])
    # The reviewed store requires the membership and forward roots and the dtype
    # up front, and it has no `exists`; resume is by shard file presence. Both
    # were wrong in an earlier draft of this pipeline, which means the "real
    # producer" would have failed on its first authorized call.
    store = None
    if output_dir is not None:
        store = AtomicShardStore(
            output_dir,
            membership_root=str(membership_root
                                or authorization["authorization_root_sha256"]),
            forward_root=ACCEPTED_REAL_FORWARD_ROOT,
            dtype=ACCEPTED_MECHANICS["dtype"])

    lawful_shards = [storage_shard_id(donor, operator)
                     for donor, operator in reader.shards()]
    assert_donors_within_reader_fit((d for d, _ in reader.shards()), roster["roster"])

    captures: list[dict[str, Any]] = []
    effect_rows: list[dict[str, Any]] = []
    published: list[str] = []
    resumed: list[str] = []

    for donor, operator in reader.shards():
        shard_id = storage_shard_id(donor, operator)
        if store is not None and (store.root / ("%s.npz" % shard_id)).exists():
            # Resume by physical shard existence: a committed shard is reused
            # rather than rewritten, so an interrupted run reproduces identical
            # digests.
            resumed.append(shard_id)
            published.append(shard_id)
            continue
        ordered_ids: list[str] = []
        values: list[Any] = []
        for cell in reader.cells(donor, operator):
            support = np.asarray(cell["observation_state"], dtype=bool)
            expression = normalize_expression(cell["raw_counts"], cell["source_library"])
            cell_id = str(cell["canonical_cell_id"])
            # The frozen identity functions key on `canonical_cell_id` and an
            # INTEGER `q`, not on the query address string. The assignment
            # authority carries both, as `selected_query_address` and
            # `selected_query_address_id`, so the reader must supply both. An
            # earlier draft of this pipeline passed the address where the integer
            # belonged, which would have failed on its first authorized call.
            for query in cell["queries"]:
                query_address = str(query["query_address"])
                q_index = int(query["q"])
                authority = {"checkpoint": checkpoint,
                             "forward_root": ACCEPTED_REAL_FORWARD_ROOT}
                teacher_state = forward_engine.teacher_forward(
                    cell={**cell, "expression": expression}, query_address=query_address)
                captures.append(forward_capture_record(
                    identity=teacher_compute_identity(
                        authority, {"canonical_cell_id": cell_id, "q": q_index}),
                    role=TEACHER_ROLE, canonical_cell_id=cell_id,
                    query_address=query_address, evidence_level=None, arm=None,
                    model_family=TEACHER_FAMILY, shard_id=shard_id,
                    checkpoint_sha256=checkpoint,
                    state_dim=int(np.asarray(teacher_state).reshape(-1).size),
                    dtype=ACCEPTED_MECHANICS["dtype"]))
                for evidence_level in EVIDENCE_LEVELS:
                    mask = build_query_evidence_mask(
                        query_address=query_address, evidence_level=evidence_level,
                        measurable=support)
                    for role, arm in ((CORRECT_STUDENT_ROLE, CORRECT_ARM),
                                      (MATCHED_NULL_STUDENT_ROLE, MATCHED_NULL_ARM)):
                        state = forward_engine.student_forward(
                            cell={**cell, "expression": expression, "mask": mask},
                            query_address=query_address, evidence_level=evidence_level,
                            arm=arm)
                        record = {"canonical_cell_id": cell_id, "q": q_index,
                                  "evidence_level": int(evidence_level)}
                        if role == MATCHED_NULL_STUDENT_ROLE:
                            record["null_source_cell"] = query.get("null_source_cell")
                        captures.append(forward_capture_record(
                            identity=student_forward_identity(authority, record, role),
                            role=role, canonical_cell_id=cell_id,
                            query_address=query_address, evidence_level=evidence_level,
                            arm=arm, model_family=STUDENT_FAMILY, shard_id=shard_id,
                            checkpoint_sha256=checkpoint,
                            state_dim=int(np.asarray(state).reshape(-1).size),
                            dtype=ACCEPTED_MECHANICS["dtype"]))
                    effect_rows.append({
                        "assignment_key": str(query["assignment_key"]),
                        "evidence_level": int(evidence_level),
                        "shard_id": shard_id,
                        "checkpoint_sha256": checkpoint,
                    })
                ordered_ids.append("%s|%d" % (cell_id, q_index))
                values.append(np.asarray(teacher_state, dtype=np.float32).reshape(-1))
        if store is not None:
            store.commit(shard_id, ordered_ids, np.asarray(values, dtype=np.float32))
        published.append(shard_id)

    return {
        "schema": "f1-real-production-sweep-v1",
        "authorization_id": authorization["authorization_id"],
        "checkpoint_sha256": checkpoint,
        "captures": captures,
        "effect_rows": effect_rows,
        "published_shards": published,
        "resumed_shards": resumed,
        "lawful_shard_ids": lawful_shards,
        "geometry": dict(geometry),
        "terminal": "F1_REAL_SWEEP_EXECUTED",
    }


def verify_sweep_completeness(result: Mapping[str, Any], *,
                              planned_assignment_keys: Iterable[str]) -> dict[str, Any]:
    """Final completeness verification over all four identity topologies."""
    geometry = dict(result["geometry"])
    forwards = assert_forward_topology(
        result["captures"], checkpoint_sha256=str(result["checkpoint_sha256"]),
        lawful_shard_ids=result["lawful_shard_ids"], geometry=geometry)
    effects = assert_effect_row_topology(
        result["effect_rows"], planned_assignment_keys=planned_assignment_keys,
        geometry=geometry)
    shards = assert_shard_topology(
        result["published_shards"], lawful_shard_ids=result["lawful_shard_ids"],
        geometry=geometry)
    return {"schema": "f1-sweep-completeness-v1", "forwards": forwards,
            "effect_rows": effects, "shards": shards, "complete": True}


def frozen_source_digests(repo: Path = REPO) -> dict[str, str]:
    """Digests of the frozen sources an authorization must bind."""
    names = {
        "producer": "scripts/v4/f1_real_producer_v1.py",
        "replay": "scripts/v4/f1_real_replay_v1.py",
        "authorization": "scripts/v4/f1_execution_authorization_v1.py",
        "tests": "tests/test_f1_real_producer_replay_parity_v1.py",
    }
    return {name: sha256_file(_resolve_from(repo, rel)) for name, rel in names.items()}


def _resolve_from(repo: Path, relative: str) -> Path:
    for root in (repo, Path("/mnt/d/Jepa project"), Path("D:/Jepa project")):
        candidate = Path(root) / relative
        if candidate.is_file():
            return candidate
    raise FileNotFoundError("STOP_F1_AUTHORITY_UNREACHABLE: %s" % relative)


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
        "execution_authorization": "EXTERNAL_ARTIFACT_REQUIRED",
        "in_source_execution_flag": None,
        "in_source_output_roots": None,
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
