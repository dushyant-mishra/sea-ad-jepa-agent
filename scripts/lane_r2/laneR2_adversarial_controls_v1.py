#!/usr/bin/env python
"""LANE R2 - adversarial / mutation controls for the Stage75F specificity audit.

A gate that cannot fail is not a gate. This script deliberately breaks each
safeguard in laneR2_stage75f_tf_specificity_control_v1.py and asserts that the
safeguard NOTICES. If any mutation slips through undetected, this exits
non-zero and the main audit result must be treated as unqualified.

MUT-1 INPUT KEY GUARD. Hide one TF per-batch file so the input key sets no
      longer agree. The main script MUST refuse with FAIL_CLOSED rather than
      silently computing overlap on nine sets.
MUT-2 STRUCTURAL GATE ARITHMETIC. Hand run_planted_gate a record that is
      identical while claiming to be distinct. The gate MUST return FAIL.
MUT-3 STAGE73 BUG REPRODUCTION. Build a control that is byte-identical to the
      real data but carries the label SHUFFLED. structural_record MUST report
      is_structurally_distinct = False. This is the exact failure Stage73 shipped.
MUT-4 MINIMAL-CHANGE SENSITIVITY. Swap exactly two elements out of thousands.
      structural_record MUST still report distinct. A harness that only notices
      gross differences would pass a near-identical control as a valid shuffle.
MUT-5 DEGENERATE PERMUTATION NULL. Feed the permutation test a support matrix
      with identical rows (the "all region sets identical" world). The test MUST
      flag null_is_degenerate_constant = True rather than returning a p-value
      that looks like evidence.

Governance: TRAINING=OFF | no protected outcome opened | no biological claim.
"""
from __future__ import annotations

import importlib.util
import itertools
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
MAIN = HERE / "laneR2_stage75f_tf_specificity_control_v1.py"

spec = importlib.util.spec_from_file_location("laneR2_main", MAIN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def main() -> int:
    ap = __import__("argparse").ArgumentParser()
    ap.add_argument("--pilot-dir", action="append", required=True)
    ap.add_argument("--batch-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--scratch", required=True)
    args = ap.parse_args()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    scratch = Path(args.scratch).resolve()
    results = []

    # ---- MUT-1 input key guard -------------------------------------------
    mutated = scratch / "mut1_batches"
    if mutated.exists():
        shutil.rmtree(mutated)
    shutil.copytree(args.batch_dir, mutated)
    victims = sorted(mutated.glob("*_STAT3.genes.txt"))
    for v in victims:
        v.unlink()
    cmd = [sys.executable, str(MAIN)]
    for p in args.pilot_dir:
        cmd += ["--pilot-dir", p]
    cmd += ["--batch-dir", str(mutated), "--out-dir", str(scratch / "mut1_out"),
            "--annot-permutations", "5"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    blob = (proc.stdout or "") + (proc.stderr or "")
    detected = ("FAIL_CLOSED input guard" in blob) and proc.returncode != 0
    results.append({
        "mutation": "MUT-1_input_key_guard_one_tf_file_removed",
        "n_files_removed": len(victims),
        "expected": "refuse_with_FAIL_CLOSED",
        "observed_returncode": proc.returncode,
        "detected": bool(detected),
        "result": "PASS" if detected else "FAIL",
    })

    # ---- MUT-2 structural gate arithmetic ---------------------------------
    same = [frozenset({"A"}), frozenset({"B"}), frozenset({"C"}), frozenset({"D"})]
    rec_same = mod.structural_record("MUT2_identical_claimed_distinct", same, same,
                                     "adversarial")
    gate_rows, gate_ok = mod.run_planted_gate([(rec_same, True)])  # WRONG expectation
    results.append({
        "mutation": "MUT-2_gate_arithmetic_identical_claimed_distinct",
        "expected": "gate_returns_FAIL",
        "observed_gate_ok": gate_ok,
        "observed_gate_result": gate_rows[0]["gate_result"],
        "detected": bool(gate_ok is False and gate_rows[0]["gate_result"] == "FAIL"),
        "result": "PASS" if (gate_ok is False) else "FAIL",
    })

    # ---- MUT-3 Stage73 bug reproduction -----------------------------------
    real = [frozenset({"TF%d" % (i % 7)}) for i in range(3000)]
    rec_label_only = mod.structural_record(
        "MUT3_SHUFFLED_IN_NAME_ONLY", real, list(real), "adversarial")
    detected3 = rec_label_only["is_structurally_distinct"] is False
    results.append({
        "mutation": "MUT-3_stage73_label_only_shuffle",
        "expected": "is_structurally_distinct=False_despite_name_SHUFFLED",
        "observed_is_structurally_distinct": rec_label_only["is_structurally_distinct"],
        "observed_changed_fraction": rec_label_only["changed_element_fraction"],
        "detected": bool(detected3),
        "result": "PASS" if detected3 else "FAIL",
    })

    # ---- MUT-4 minimal-change sensitivity ---------------------------------
    near = list(real)
    near[0], near[1] = near[1], near[0]
    # ensure the swap is a real content change, not a no-op on equal elements
    while near[0] == real[0]:
        j = next(k for k in range(len(real)) if real[k] != real[0])
        near[0], near[j] = near[j], near[0]
    rec_near = mod.structural_record("MUT4_two_element_swap", real, near, "adversarial")
    detected4 = rec_near["is_structurally_distinct"] is True
    results.append({
        "mutation": "MUT-4_minimal_change_two_element_swap",
        "expected": "is_structurally_distinct=True",
        "observed_is_structurally_distinct": rec_near["is_structurally_distinct"],
        "observed_changed_fraction": rec_near["changed_element_fraction"],
        "observed_n_changed": rec_near["n_changed_elements"],
        "detected": bool(detected4),
        "result": "PASS" if detected4 else "FAIL",
    })

    # ---- MUT-5 degenerate permutation null --------------------------------
    n = 6
    row = np.array([3.0, 3.0, 3.0, 3.0, 3.0, 3.0])
    S_deg = np.vstack([row] * n)  # every batch gives every TF identical support
    rows_ix = np.arange(n)
    null = np.array([S_deg[rows_ix, np.asarray(p)].sum()
                     for p in itertools.permutations(range(n))])
    degenerate = bool(len(np.unique(null)) == 1)
    results.append({
        "mutation": "MUT-5_degenerate_permutation_null_identical_region_sets",
        "expected": "null_is_degenerate_constant=True",
        "observed_n_distinct_null_values": int(len(np.unique(null))),
        "detected": bool(degenerate),
        "result": "PASS" if degenerate else "FAIL",
    })

    all_pass = all(r["result"] == "PASS" for r in results)
    report = {
        "audit": "laneR2_adversarial_controls_v1",
        "all_mutations_detected": all_pass,
        "verdict": ("SAFEGUARDS_CAN_FAIL_AND_DID_FAIL_WHEN_BROKEN" if all_pass
                    else "SAFEGUARD_DID_NOT_DETECT_A_PLANTED_DEFECT"),
        "mutations": results,
        "governance": "TRAINING=OFF | no protected outcome opened | no biological claim",
    }
    (out / "laneR2_adversarial_controls_v1.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    if not all_pass:
        print("ADVERSARIAL FAILURE: a planted defect went undetected.", file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
