#!/usr/bin/env python3
"""Prospective guarded rare-tail molecular ENTRYPOINT, not execution authority.

Default operation re-authenticates the frozen, *physical* V2 preflight without
opening expression. An expression-opening run additionally requires an exact
independently reviewed preflight FILE SHA and an explicit opt-in. The original
frozen molecular runner remains unchanged and technically directly callable;
repository governance must prohibit bypass until a separately frozen mandatory
runner/contract successor is reviewed. No real molecular run in this PR.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
from typing import Any

from sea_ad_jepa.v5.full104_rare_tail_molecular_authority_v1 import (
    FAIL_TERMINAL, NOT_ESTIMABLE_TERMINAL, PASS_TERMINAL, full_gate_terminal,
)
from scripts.agent.preflight_full104_rare_tail_molecular_readonly_v2_20260922 import (
    SCHEMA as PREFLIGHT_SCHEMA,
    canonical_digest,
    run_preflight_v2,
    sha256_file,
    normalized_text_sha256,
)

RUNNER_MODULE = "scripts.agent.run_full104_rare_tail_molecular_prequalification_v1_20260922"
SCHEMA = "V5_FULL104_RARE_TAIL_GUARDED_EXECUTION_EVIDENCE_V1"
EXPECTED_PREFLIGHT_STATE = "READY_FOR_INDEPENDENT_REVIEW__NO_RNA_OPENED"


def verify_reviewed_preflight(
    *, reviewed_receipt: Path, approved_file_sha256: str,
    physical_inputs: dict[str, Path],
) -> dict[str, Any]:
    if len(approved_file_sha256) != 64 or any(c not in "0123456789abcdef" for c in approved_file_sha256):
        raise ValueError("approved V2 preflight file SHA-256 must be exact lowercase hex")
    if sha256_file(reviewed_receipt) != approved_file_sha256:
        raise ValueError("V2 preflight file differs from externally reviewed immutable SHA")
    published = json.loads(reviewed_receipt.read_text(encoding="utf-8"))
    if published.get("schema") != PREFLIGHT_SCHEMA or published.get("state") != EXPECTED_PREFLIGHT_STATE:
        raise ValueError("reviewed preflight receipt schema/state mismatch")
    declared_sha = published.get("receipt_sha256")
    body = {k: v for k, v in published.items() if k != "receipt_sha256"}
    if declared_sha != canonical_digest(body):
        raise ValueError("reviewed V2 preflight receipt self-digest mismatch")
    recomputed = run_preflight_v2(**physical_inputs)
    if published != recomputed:
        raise ValueError("reviewed preflight differs from today's authenticated physical inputs")
    return recomputed


def validate_scientific_result(result: dict[str, Any], *, preflight: dict[str, Any],
                               exit_code: int) -> str:
    if result.get("schema") != "V5_FULL104_RARE_TAIL_MOLECULAR_RESULT_V1":
        raise ValueError("frozen molecular result schema mismatch")
    for field, expected in (
        ("authority_sha256", preflight["molecular_authority_sha256"]),
        ("sample_receipt_sha256", preflight["sample_receipt_sha256"]),
        ("full104_manifest_sha256", preflight["full104_manifest_sha256"]),
        ("outer_split_receipt_sha256", preflight["outer_split_receipt_sha256"]),
    ):
        if result.get(field) != expected:
            raise ValueError("result differs from frozen preflight root: " + field)
    cases = result.get("cases")
    if not isinstance(cases, list) or len(cases) != 24 or result.get("case_count") != 24:
        raise ValueError("result must include exactly 24 panel/source/fold cases")
    observed = set()
    states: list[str] = []
    for row in cases:
        if not isinstance(row, dict):
            raise ValueError("malformed molecular case")
        key = (row.get("panel"), row.get("source_code"), row.get("fold_index"))
        if key in observed or key not in {
            (p, s, f) for p in (0, 1) for s in range(3) for f in range(4)
        }:
            raise ValueError("duplicate/invalid molecular panel x source x fold case")
        observed.add(key)
        if row.get("state") not in ("PASS", "FAIL", "NOT_ESTIMABLE"):
            raise ValueError("unrecognized molecular case terminal")
        states.append(row["state"])
    if len(observed) != 24 or not isinstance(result.get("panel_results"), list) or len(result["panel_results"]) != 2:
        raise ValueError("incomplete molecular result/case grid")
    expected_terminal = full_gate_terminal(tuple(states))
    if result.get("terminal") != expected_terminal:
        raise ValueError("molecular terminal disagrees with all 24 frozen cases")
    if result.get("molecular_prequalification_passed") is not (expected_terminal == PASS_TERMINAL):
        raise ValueError("molecular PASS flag disagrees with terminal")
    expected_exit_code = 0 if expected_terminal == PASS_TERMINAL else 2
    if exit_code != expected_exit_code:
        raise ValueError("frozen runner exit status disagrees with molecular terminal")
    for flag in ("teacher_tail_evaluation_authorized", "td60_authorized",
                 "training_authorized", "pathology_labels_used",
                 "disease_labels_used", "native_class_labels_used",
                 "rare_state_labels_used"):
        if result.get(flag) is not False:
            raise ValueError("molecular result has missing/unsafe protected flag: " + flag)
    return expected_terminal


def run_guarded(
    *, inputs: dict[str, Path], reviewed_receipt: Path, approved_file_sha256: str,
    out: Path, out_receipt: Path, execute_after_independent_review: bool,
    approved_gateway_source_sha256: str | None = None,
) -> dict[str, Any]:
    preflight = verify_reviewed_preflight(
        reviewed_receipt=reviewed_receipt,
        approved_file_sha256=approved_file_sha256,
        physical_inputs=inputs,
    )
    if not execute_after_independent_review:
        return {"state": "GATE_VERIFIED__EXPRESSION_NOT_OPENED",
                "v2_receipt_sha256": preflight["receipt_sha256"],
                "training_authorized": False}
    gateway_sha = normalized_text_sha256(Path(__file__))
    if (
        not isinstance(approved_gateway_source_sha256, str)
        or len(approved_gateway_source_sha256) != 64
        or any(c not in "0123456789abcdef" for c in approved_gateway_source_sha256)
    ):
        raise ValueError("execution requires an exact independently approved gateway source SHA-256")
    if gateway_sha != approved_gateway_source_sha256:
        raise ValueError("gateway source differs from independently approved source SHA-256")
    if out.exists() or out_receipt.exists():
        raise ValueError("result or execution receipt exists: refuse overwrite")
    root = inputs["repo_root"].resolve()
    runner = root / "scripts/agent/run_full104_rare_tail_molecular_prequalification_v1_20260922.py"
    if normalized_text_sha256(runner) != preflight["source_hashes"]["runner_normalized_text_sha256"]:
        raise ValueError("frozen molecular runner source bytes changed after reviewed preflight")

    intent = out.with_name(out.name + ".intent.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out_receipt.parent.mkdir(parents=True, exist_ok=True)
    # Crash leaves an exclusive intent: never auto-resume or launch twice.
    fd = os.open(str(intent), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump({"schema": "RARE_TAIL_EXECUTION_INTENT_V1",
                   "reviewed_v2_preflight_file_sha256": approved_file_sha256,
                   "frozen_runner_source_sha256": preflight["source_hashes"]["runner_normalized_text_sha256"],
                   "approved_gateway_source_sha256": approved_gateway_source_sha256,
                   "out": str(out.resolve()), "training_authorized": False}, f, sort_keys=True)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    stage = out.parent / ("." + out.name + ".staged-" + secrets.token_hex(8) + ".json")
    if stage.exists():
        raise ValueError("random stage collision")
    env = os.environ.copy()
    env["PYTHONPATH"] = os.pathsep.join((str(root / "src"), str(root)))
    command = [
        sys.executable, "-m", RUNNER_MODULE,
        "--authority", str(inputs["authority_path"]),
        "--sample-dir", str(inputs["sample_dir"]),
        "--split-receipt", str(inputs["split_receipt_path"]),
        "--level4-root", str(inputs["level4_root"]),
        "--target-eligibility", str(inputs["target_eligibility_path"]),
        "--out", str(stage),
    ]
    child = subprocess.run(command, cwd=str(root), env=env, check=False)
    if child.returncode not in (0, 2) or not stage.is_file():
        raise RuntimeError("frozen runner failed mechanically; leave exclusive intent, do not relaunch")
    result = json.loads(stage.read_text(encoding="utf-8"))
    terminal = validate_scientific_result(result, preflight=preflight, exit_code=child.returncode)
    file_sha = sha256_file(stage)
    with stage.open("rb") as f:
        os.fsync(f.fileno())
    # Outcome file is atomic. An interruption between the two commits yields
    # NO admissible science receipt, and the intent prevents automatic retry.
    os.replace(stage, out)
    payload = {
        "schema": SCHEMA,
        "state": "RESULT_COMMITTED__NOT_TRAINING_AUTHORITY",
        "terminal": terminal,
        "molecular_result_file_sha256": file_sha,
        "reviewed_preflight_file_sha256": approved_file_sha256,
        "reviewed_preflight_canonical_sha256": preflight["receipt_sha256"],
        "molecular_authority_sha256": preflight["molecular_authority_sha256"],
        "execution_contract_sha256": preflight["execution_contract_sha256"],
        "structural_receipt_file_sha256": preflight["structural_receipt_file_sha256"],
        "runner_source_normalized_sha256": preflight["source_hashes"]["runner_normalized_text_sha256"],
        "gateway_source_normalized_sha256": gateway_sha,
        "child_return_code": child.returncode,
        "teacher_tail_evaluation_authorized": False,
        "td60_authorized": False,
        "training_authorized": False,
    }
    payload["receipt_sha256"] = canonical_digest(payload)
    receipt_stage = out_receipt.with_name("." + out_receipt.name + ".staged.json")
    fd = os.open(str(receipt_stage), os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(payload, f, sort_keys=True, indent=2)
        f.write("\n")
        f.flush()
        os.fsync(f.fileno())
    os.replace(receipt_stage, out_receipt)
    return payload


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    for name in ("authority", "execution-contract", "sample-dir", "split-receipt",
                 "level4-root", "target-eligibility", "structural-receipt",
                 "structural-provenance", "repo-root"):
        p.add_argument("--" + name, type=Path, required=True)
    p.add_argument("--reviewed-v2-preflight", type=Path, required=True)
    p.add_argument("--externally-approved-v2-file-sha256", required=True)
    p.add_argument("--externally-approved-gateway-source-sha256")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--out-receipt", type=Path, required=True)
    p.add_argument("--execute-after-independent-review", action="store_true")
    args = p.parse_args()
    names = ("authority", "execution_contract", "sample_dir", "split_receipt",
             "level4_root", "target_eligibility", "structural_receipt",
             "structural_provenance", "repo_root")
    fields = ("authority_path", "execution_contract_path", "sample_dir",
              "split_receipt_path", "level4_root", "target_eligibility_path",
              "structural_receipt_path", "structural_provenance_path", "repo_root")
    inputs = {field: getattr(args, name) for name, field in zip(names, fields)}
    record = run_guarded(
        inputs=inputs, reviewed_receipt=args.reviewed_v2_preflight,
        approved_file_sha256=args.externally_approved_v2_file_sha256,
        out=args.out, out_receipt=args.out_receipt,
        execute_after_independent_review=args.execute_after_independent_review,
        approved_gateway_source_sha256=args.externally_approved_gateway_source_sha256,
    )
    print(json.dumps(record, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
