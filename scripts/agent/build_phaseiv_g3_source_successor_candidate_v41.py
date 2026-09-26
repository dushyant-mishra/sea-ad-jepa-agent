#!/usr/bin/env python3
"""Build a deterministic, NON-AUTHORIZING successor-source proposal for Phase IV.

This producer never modifies the frozen V1 sample, never creates an execution
contract, and never invokes an Audit-B burden estimator or protected result.
A future *independently approved* V2 freeze needs an independent producer,
a resolved scientific scope and actual GPU-side source replay.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

ROOT = Path(__file__).resolve().parents[2]
ORIGINAL = Path("analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json")
OLD_FREEZE_DIGEST = "c2c5e1b5addc50db7e9676ebf59e9c63b5d0b9eee882ef78aff5baa9d4a3b0ac"
OLD_PLANNER_SHA = "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
G3_PLANNER_SHA = "de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8"
EXPECTED_ROLES = (
    "target_universe", "split_receipt", "planner_source",
    "qualification_runner", "masking_parameters_authority",
    "evidence_budget_authority", "mask_plan_generator",
)
EXPECTED_LADDER = {"N1": 256, "N2": 1024, "N3": 4096}
G3_PARITY_TEST = Path("tests/test_v40_g3_historical_default_exact_parity.py")
G3_PARITY_TEST_SHA = None  # Read actual test source bytes, not a fabricated root.
PARITY_RUN_ID = 36250218148  # Sept26 hosted 7/7, independently reviewed; snapshot not credential.


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value: Mapping[str, Any]) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=True, allow_nan=False).encode("utf-8")


def _check_frozen(freeze: Mapping[str, Any]) -> None:
    if (freeze.get("schema") != "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1" or
        freeze.get("freeze_digest") != OLD_FREEZE_DIGEST or
        freeze.get("training_authorized") is not False or
        freeze.get("terminal_masking_outcomes_inspected") is not False or
        freeze.get("frozen_before_any_burden_was_computed") is not True):
        raise ValueError("original Phase-IV frozen sample identity/safety mismatch")
    inputs = freeze.get("bound_inputs")
    if not isinstance(inputs, dict) or tuple(inputs) != EXPECTED_ROLES:
        raise ValueError("original Phase-IV seven exact bound roles drifted")
    if inputs["planner_source"]["sha256"] != OLD_PLANNER_SHA:
        raise ValueError("original immutable planner root changed")
    declared = {
        "schema": freeze["schema"], "salt": freeze["salt"],
        "ladder": freeze["ladder"], "bound": inputs,
        "samples": {k: v["targets"] for k, v in freeze["samples"].items()},
    }
    if digest(canonical(declared)) != OLD_FREEZE_DIGEST:
        raise ValueError("original prospective freeze canonical digest mismatch")
    if list(freeze["ladder"]) != list(EXPECTED_LADDER.values()):
        raise ValueError("original sample ladder changed")
    if set(freeze["samples"]) != set(EXPECTED_LADDER):
        raise ValueError("original sample rung set changed")
    samples = freeze["samples"]
    for key, count in EXPECTED_LADDER.items():
        targets = samples[key]["targets"]
        if samples[key]["n"] != count or len(targets) != count or len(set(targets)) != count:
            raise ValueError(f"original sample {key} cardinality/injectivity changed")
    if not (set(samples["N1"]["targets"]) < set(samples["N2"]["targets"])
            < set(samples["N3"]["targets"])):
        raise ValueError("original sample ladder lost monotonicity")
    if freeze["escalation_criterion"]["depends_only_on_precision"] is not True:
        raise ValueError("original precision-only escalation changed")


def build_candidate(repo_root: Path = ROOT, *, freeze_override: Mapping[str, Any] | None = None) -> dict[str, Any]:
    root = repo_root.resolve()
    original_bytes = (root / ORIGINAL).read_bytes()
    old = json.loads(original_bytes) if freeze_override is None else freeze_override
    _check_frozen(old)
    changed = {}
    current = {}
    for role, rec in old["bound_inputs"].items():
        rel = Path(rec["path"])
        resolved = (root / rel).resolve()
        if resolved == root or not resolved.is_relative_to(root) or not resolved.is_file():
            raise ValueError(f"invalid/missing physical Phase-IV parent {role}")
        observed = digest(resolved.read_bytes())
        current[role] = {"path": rec["path"], "sha256": observed}
        if observed != rec["sha256"]:
            changed[role] = {"old_sha256": rec["sha256"], "new_sha256": observed}
    if changed != {"planner_source": {"old_sha256": OLD_PLANNER_SHA, "new_sha256": G3_PLANNER_SHA}}:
        raise ValueError(f"unexpected current Phase-IV source change(s): {changed}")
    candidate_rung_digests = {
        k: digest(canonical({"salt": old["salt"], "targets": old["samples"][k]["targets"]}))
        for k in EXPECTED_LADDER
    }
    v40 = root / G3_PARITY_TEST
    if not v40.is_file() or b"historical_source.run_primary_fold_streaming" not in v40.read_bytes():
        raise ValueError("V40 independent physical historical-default parity test missing")
    payload = {
        "schema": "V5_PHASE_IV_G3_SOURCE_SUCCESSOR_PROPOSAL_V1",
        "status": "DRAFT_REVIEW_REQUIRED__NOT_A_SAMPLE_FREEZE",
        "parent_original_freeze_file_sha256": digest(original_bytes),
        "parent_original_freeze_canonical_sha256": OLD_FREEZE_DIGEST,
        "parent_original_freeze_path": ORIGINAL.as_posix(),
        "sample_selection_policy": old["selection_rule"],
        "sample_salt": old["salt"],
        "sample_ladder": list(EXPECTED_LADDER.values()),
        "original_target_set_digests_by_rung": candidate_rung_digests,
        "all_seven_current_candidate_inputs": current,
        "changed_original_bound_roles": changed,
        "synthetic_functional_parity": {
            "test_source_path": G3_PARITY_TEST.as_posix(),
            "test_source_sha256": digest(v40.read_bytes()),
            "hosted_workflow_run_id": PARITY_RUN_ID,
            "hosted_7_of_7_reported_pass": True,
            "evidence_scope": "SYNTHETIC_12_DONORS_48_CELLS_8_COLUMNS__NOT_REAL_FULL104",
        },
        "prospective_scientist_signoff_present": False,
        "new_frozen_sample_issued": False,
        "audit_b_n1_execution_authorized": False,
        "terminal_masking_outcomes_inspected": False,
        "training_authorized": False,
    }
    payload["proposal_digest"] = digest(canonical(payload))
    return payload


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, help="optional local draft JSON path; never overwrite old freeze")
    args = ap.parse_args()
    proposal = build_candidate()
    if args.output is not None:
        out = args.output.resolve()
        old = (ROOT / ORIGINAL).resolve()
        if out == old or old in out.parents:
            raise ValueError("cannot write an original Phase-IV freeze or its children")
        if out.exists():
            raise FileExistsError("refuse overwriting an existing candidate: version instead")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(proposal, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(proposal, indent=2, sort_keys=True))
    print("V41_DRAFT_G3_SOURCE_SUCCESSOR_PROPOSAL_ONLY__NO_N1_NO_TRAINING")


if __name__ == "__main__":
    main()
