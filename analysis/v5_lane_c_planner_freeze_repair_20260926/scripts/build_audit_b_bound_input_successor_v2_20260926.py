"""Build the versioned successor binding for the drifted Phase-IV planner source.

This script does NOT edit ``AUDIT_B_FROZEN_TARGET_SAMPLE.json``. The parent
freeze stays byte-identical forever; this emits a separate, digest-pinned record
that says exactly which bound input moved, from which bytes to which bytes, why,
and on what executed evidence.

The load-bearing step is the **sample-identity re-derivation**. A freeze exists
to stop a sample being re-rolled after a result is seen, so before anything is
superseded this script re-derives N1/N2/N3 from the parent's salt and the parent's
target universe and requires them to be identical to the parent's recorded
targets. If they are not, it refuses: no successor can rescue a re-rolled sample.

Nothing here opens an Audit-B N1 burden outcome, a terminal masking result,
D_shared, G5, pathology, DEV/SEALED expression, or authorizes training.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

SCHEMA = "V5_AUDIT_B_BOUND_INPUT_SUCCESSOR_V2"

PARENT_FREEZE_REL = (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_FROZEN_TARGET_SAMPLE.json"
)
EQUIVALENCE_RECEIPT_REL = (
    "analysis/v5_lane_c_planner_freeze_repair_20260926/evidence/"
    "PLANNER_DEFAULT_PATH_EQUIVALENCE_V1.json"
)
PREEXECUTION_STATUS_REL = (
    "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/"
    "AUDIT_B_PREEXECUTION_STATUS_V1.json"
)

PLANNER_RATIONALE = (
    "PR #144 commit 65ff187c9668cf0af28056222fde897380929141 added an opt-in "
    "G3 attacker-fit objective to the streaming planner. The change is purely "
    "additive (39 insertions, 0 deletions) and every new behaviour is guarded by "
    "an explicit non-None fit_objective argument that no Audit-B call site "
    "supplies, so the Audit-B default path is unchanged. That claim is not "
    "asserted from the diff: the frozen bytes and the successor bytes were both "
    "executed over three authenticated stream geometries and every emitted row, "
    "every per-fold row and every _ridge_partners result compared bitwise equal. "
    "The binding therefore continues at the new digest, with the planner "
    "execution mode pinned to the historical default."
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def samples_digest(samples: dict[str, Any]) -> str:
    material = json.dumps(
        {key: list(map(int, value["targets"])) for key, value in samples.items()},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def ordered_targets(addresses: list[int], salt: str) -> list[int]:
    """The parent's selection rule, restated here so identity is re-derived."""
    return sorted(
        addresses,
        key=lambda a: hashlib.sha256(f"{salt}|{int(a)}".encode()).digest(),
    )


def canonical_digest(payload: dict[str, Any]) -> str:
    material = json.dumps(
        {
            "schema": payload["schema"],
            "parent_freeze_digest": payload["parent_freeze_digest"],
            "parent_freeze_artifact_sha256": payload["parent_freeze_artifact_sha256"],
            "parent_freeze_path": payload["parent_freeze_path"],
            "sample_identity": payload["sample_identity"],
            "superseded_bindings": payload["superseded_bindings"],
            "unchanged_bindings": payload["unchanged_bindings"],
            "required_execution_mode": payload["required_execution_mode"],
            "frozen_before_any_burden_was_computed": payload[
                "frozen_before_any_burden_was_computed"
            ],
            "execution_authorized": payload["execution_authorized"],
            "terminal_masking_outcomes_inspected": payload[
                "terminal_masking_outcomes_inspected"
            ],
            "training_authorized": payload["training_authorized"],
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(material).hexdigest()


def git_commit_for(repo: Path, relative: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%H", "--", relative],
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        return out.stdout.strip() or "UNRESOLVED"
    except Exception:  # pragma: no cover - provenance must never be invented
        return "UNRESOLVED"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path("."))
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    repo = args.repo.resolve()

    parent_path = repo / PARENT_FREEZE_REL
    parent = json.loads(parent_path.read_text(encoding="utf-8"))
    if parent.get("schema") != "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1":
        raise SystemExit("parent freeze schema mismatch")

    bound = parent["bound_inputs"]

    # ---- sample identity: re-derive before superseding anything --------------
    eligibility_rel = bound["target_universe"]["path"]
    eligibility_path = repo / eligibility_rel
    if sha256_file(eligibility_path) != bound["target_universe"]["sha256"]:
        raise SystemExit(
            "the target universe itself drifted; the sample cannot be re-derived "
            "and no successor is lawful"
        )
    eligibility = json.loads(eligibility_path.read_text(encoding="utf-8"))
    addresses = [int(a) for a in eligibility["eligible_target_cols_all_folds"]]
    order = ordered_targets(addresses, parent["salt"])
    rederived = {
        f"N{i + 1}": {"n": n, "targets": sorted(order[:n])}
        for i, n in enumerate(parent["ladder"])
    }
    parent_digest = samples_digest(parent["samples"])
    rederived_digest = samples_digest(rederived)
    if parent_digest != rederived_digest:
        raise SystemExit(
            "the frozen sample does not re-derive from its own salt and universe; "
            "refusing to write a successor"
        )
    for index in range(len(parent["ladder"]) - 1):
        smaller = set(rederived[f"N{index + 1}"]["targets"])
        larger = set(rederived[f"N{index + 2}"]["targets"])
        if not smaller.issubset(larger):
            raise SystemExit("re-derived ladder is not a prefix ordering")

    # ---- which bound inputs actually drifted ---------------------------------
    drifted: dict[str, tuple[str, str]] = {}
    unchanged: dict[str, str] = {}
    for role, rec in sorted(bound.items()):
        observed = sha256_file(repo / rec["path"])
        if observed == rec["sha256"]:
            unchanged[role] = observed
        else:
            drifted[role] = (rec["sha256"], observed)

    if set(drifted) != {"planner_source"}:
        raise SystemExit(
            "this successor covers exactly the planner_source transition; "
            f"observed drifted roles: {sorted(drifted)}"
        )

    receipt_path = repo / EQUIVALENCE_RECEIPT_REL
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt.get("equivalent") is not True:
        raise SystemExit("equivalence receipt did not pass; refusing to write a successor")
    from_sha, to_sha = drifted["planner_source"]
    if receipt.get("frozen_planner_sha256") != from_sha:
        raise SystemExit("equivalence receipt did not compare the recorded frozen bytes")
    if receipt.get("successor_planner_sha256") != to_sha:
        raise SystemExit("equivalence receipt did not compare the observed new bytes")

    status = json.loads((repo / PREEXECUTION_STATUS_REL).read_text(encoding="utf-8"))
    protected = status["protected_state"]
    for key in (
        "audit_b_n1_burden_outcomes_opened",
        "terminal_masking_outcomes_opened",
        "d_shared_opened",
        "g5_margin_selected",
        "training_authorized",
    ):
        if protected.get(key) is not False:
            raise SystemExit(
                f"pre-execution status reports {key}=True; a successor freeze cannot "
                "claim it precedes any burden computation"
            )

    payload: dict[str, Any] = {
        "schema": SCHEMA,
        "purpose": (
            "Continue ONE Phase-IV bound-input binding across ONE verified, "
            "purely additive planner version. Supersedes nothing else."
        ),
        "parent_freeze_path": PARENT_FREEZE_REL,
        "parent_freeze_artifact_sha256": sha256_file(parent_path),
        "parent_freeze_digest": parent["freeze_digest"],
        "parent_freeze_is_unmodified": True,
        "sample_identity": {
            "sample_is_unchanged": True,
            "rederived_from_parent_salt_and_universe": True,
            "salt": parent["salt"],
            "selection_rule": parent["selection_rule"],
            "ladder": list(parent["ladder"]),
            "universe_targets": len(addresses),
            "target_universe_sha256": bound["target_universe"]["sha256"],
            "parent_samples_digest": parent_digest,
            "rederived_samples_digest": rederived_digest,
            "prefix_ordering_reverified": True,
            "note": (
                "The draw depends only on the salt and the target universe, neither "
                "of which changed. The planner is an execution binding, not an input "
                "to the draw, so the sample is provably the same sample."
            ),
        },
        "superseded_bindings": {
            "planner_source": {
                "path": bound["planner_source"]["path"],
                "from_sha256": from_sha,
                "to_sha256": to_sha,
                "classification": "LEGITIMATE_VERSION_CHANGE",
                "rationale": PLANNER_RATIONALE,
                "source_commit": git_commit_for(repo, bound["planner_source"]["path"]),
                "source_pull_request": 144,
                "diff_insertions": 39,
                "diff_deletions": 0,
                "equivalence_receipt_path": EQUIVALENCE_RECEIPT_REL,
                "equivalence_receipt_sha256": sha256_file(receipt_path),
                "equivalence_comparison": receipt["comparison"],
                "equivalence_evidence_class": receipt["evidence_class"],
            }
        },
        "unchanged_bindings": unchanged,
        "required_execution_mode": {
            "planner_entrypoints": [
                "run_primary_fold_streaming",
                "run_all_primary_folds_streaming",
                "_fit_ridge_weights",
                "_ridge_primary_score",
                "_ridge_partners",
            ],
            "g3_fit_objective": "MUST_BE_ABSENT__HISTORICAL_DEFAULT_PATH_ONLY",
            "reason": (
                "The successor planner can compute a second, explicitly opt-in fit "
                "objective. A byte digest alone no longer pins behaviour to the "
                "historical computation, so the mode is pinned here as well. Audit-B "
                "must call the planner without a G3 fit objective."
            ),
        },
        "frozen_before_any_burden_was_computed": True,
        "audit_b_n1_burden_outcomes_opened": False,
        "execution_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
        "authorizes": [
            "continuation of the planner_source binding at the new digest only"
        ],
        "does_not_authorize": [
            "Audit-B N1 execution",
            "resolution of the precision scope",
            "any terminal masking outcome",
            "any pathology, DEV or SEALED access",
            "training",
        ],
    }
    payload["successor_digest"] = canonical_digest(payload)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Explicit LF: the record is digest-pinned, so its bytes must not depend
    # on which platform wrote it.
    with args.out.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(payload, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "successor_digest": payload["successor_digest"],
        "superseded": sorted(payload["superseded_bindings"]),
        "unchanged": sorted(payload["unchanged_bindings"]),
        "sample_identity_verified": parent_digest == rederived_digest,
        "parent_samples_digest": parent_digest,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
