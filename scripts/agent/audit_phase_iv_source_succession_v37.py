#!/usr/bin/env python3
"""Read-only, non-authorizing physical audit of Phase-IV planner-source succession.

The original September 21 sample freeze bound the PRE-G3 streaming executor.
PR #144 added explicit opt-in G3 fit masses without rewriting that freeze.
Never patch frozen SHA bytes or inspect N1/protected outcomes to fix workflow CI.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
FREEZE = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/evidence/phase_iv/AUDIT_B_FROZEN_TARGET_SAMPLE.json"
ROLE = "planner_source"
ORIGINAL_COMMIT = "2ebfd6ad52b0e2a99a4917391d3f0d97a667d79b"
G3_INTRO_COMMIT = "65ff187c9668cf0af28056222fde897380929141"
ORIGINAL_SHA = "143645becff6f6142d99224bfe188702b2400228b4af121738341ed4e3ebb86d"
OBSERVED_G3_SHA = "de2f019e28675e3258cfeede65f77557210f5fcd083f94ae09f97b1c8629f9f8"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def source_at(commit: str, path: str) -> bytes:
    return subprocess.check_output(
        ["git", "-C", str(ROOT), "show", f"{commit}:{path}"]
    )


def main() -> None:
    freeze = json.loads(FREEZE.read_bytes())
    assert freeze["schema"] == "V5_AUDIT_B_FROZEN_TARGET_SAMPLE_V1"
    assert freeze["training_authorized"] is False
    assert freeze["terminal_masking_outcomes_inspected"] is False
    assert freeze["frozen_before_any_burden_was_computed"] is True
    assert freeze["bound_inputs"][ROLE]["sha256"] == ORIGINAL_SHA
    assert set(freeze["bound_inputs"]) == {
        "target_universe", "split_receipt", "planner_source",
        "qualification_runner", "masking_parameters_authority",
        "evidence_budget_authority", "mask_plan_generator",
    }
    canonical = {
        "schema": freeze["schema"],
        "salt": freeze["salt"],
        "ladder": freeze["ladder"],
        "bound": freeze["bound_inputs"],
        "samples": {key: value["targets"] for key, value in freeze["samples"].items()},
    }
    expected_freeze_digest = sha(json.dumps(
        canonical, sort_keys=True, separators=(",", ":")
    ).encode())
    if expected_freeze_digest != freeze["freeze_digest"]:
        raise AssertionError("immutable original sample receipt digest changed")

    path = freeze["bound_inputs"][ROLE]["path"]
    original = source_at(ORIGINAL_COMMIT, path)
    g3_introduction = source_at(G3_INTRO_COMMIT, path)
    current = (ROOT / path).read_bytes()
    if sha(original) != ORIGINAL_SHA:
        raise AssertionError("historical predecessor does NOT match frozen SHA")
    if sha(g3_introduction) != OBSERVED_G3_SHA:
        raise AssertionError("original G3 introduction has unexpected bytes")
    if sha(current) != OBSERVED_G3_SHA:
        raise AssertionError("current audited PR144 planner source drifted again")
    if original == current or b"g3_explicit_attacker_fit_objective_v1" in original:
        raise AssertionError("historical source unexpectedly already contains G3")
    if (b"g3_explicit_attacker_fit_objective_v1" not in current or
        b"g3_fit_objective: str | None = None" not in current):
        raise AssertionError("current source lacks explicit opt-in G3 signature")

    differences = {}
    for role, rec in freeze["bound_inputs"].items():
        actual = sha((ROOT / rec["path"]).read_bytes())
        if actual != rec["sha256"]:
            differences[role] = {"frozen": rec["sha256"], "current": actual}
    if differences != {ROLE: {"frozen": ORIGINAL_SHA, "current": OBSERVED_G3_SHA}}:
        raise AssertionError(f"unexpected changed frozen roles: {differences}")

    report = {
        "scope": "NONAUTHORIZING_PHASE_IV_SOURCE_SUCCESSION",
        "original_freeze_digest": freeze["freeze_digest"],
        "sample_targets_rungs": {k: len(v["targets"]) for k,v in freeze["samples"].items()},
        "historical_source_commit": ORIGINAL_COMMIT,
        "g3_source_introduction_commit": G3_INTRO_COMMIT,
        "historical_sha256": ORIGINAL_SHA,
        "g3_sha256": OBSERVED_G3_SHA,
        "changed_original_freeze_roles": differences,
        "historical_sample_modified": False,
        "original_freeze_valid_against_current_runtime": False,
        "fresh_successor_sample_freeze_authorized": False,
        "audit_b_n1_authorized": False,
        "training_authorized": False,
    }
    print(json.dumps(report, sort_keys=True, indent=2))
    print("V37_EXACT_PREDECESSOR_SOURCE_AND_G3_DRIFT_PROVED__ORIGINAL_FREEZE_IMMUTABLE")


if __name__ == "__main__":
    main()
