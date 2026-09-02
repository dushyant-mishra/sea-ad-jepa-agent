#!/usr/bin/env python3
"""Prospectively freeze the FULL104 shared-statistic promotion contract."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import pandas as pd

from jepa_scientific_promotion_harness_v1 import save_registry, sha256


ROOT = Path(__file__).resolve().parents[2]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase2-root", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    root, out = Path(args.phase2_root).resolve(), Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    amendment = root / "shared_procedure_amendment_v2/PHASE2_SHARED_PROCEDURE_AMENDMENT_MANIFEST.csv"
    freeze = root / "preexpression_freeze/PHASE2_PREEXPRESSION_MANIFEST.csv"
    rng = root / "preexpression_freeze/PHASE2_RNG_KEYS.json"
    contract = {
        "schema": "jepa-scientific-promotion-harness-v1",
        "status": "FROZEN_PROSPECTIVELY_BEFORE_LEVEL2_SHARED_STATISTICS",
        "allowed_result_states": ["EXPLORATORY", "PROVISIONAL", "QUALIFIED", "FROZEN"],
        "frozen_consumption_rule": "downstream stages consume only untainted FROZEN artifacts",
        "automatic_invalidation_rule": "a P0 invalidation returns the node and every transitive dependent to EXPLORATORY and marks each tainted until regenerated",
        "P0_statistics": {
            "generalized_shared_signal": "For donor d, W_d=E_v[x_v x_v^T]-mu_d mu_d^T and B_d=E_{v!=w}[x_v x_w^T]-mu_d mu_d^T. Equal-donor W,B are symmetrized. Solve B q=lambda (W+rho I) q; cumulative signal is sum_{j<=D} lambda_j.",
            "empirical_matched_null": "Within each frozen donor-by-operator stratum, deterministically permute view-to-cell assignments with matched_null RNG while preserving donor/source/operator/support/depth/view/evidence marginals; refit the full tested eigensystem for every replicate.",
            "refitted_subspace_stability": "For independently refitted orthonormal bases Q_D and Q'_D, S_D=||Q_D^T Q'_D||_F^2/D under source-stratified donor bootstrap; observed and null use identical refitting/statistics.",
            "donor_heldout_predictability": "Fit basis and linear cross-view shrinkage on outer-fold training donors only; R_D=1-SSE_D/VAR_D on held donors; empirical null repeats the complete fold fit.",
            "sketch_agreement": "A_D=||Q_A,D^T Q_B,D||_F^2/D in common donor-by-operator score sample space after independent sketch fitting.",
            "one_se_selection": "Among dimensions jointly supported above empirical null in both sketches, choose the smallest D with paired-donor mean predictability >= best_supported_mean-best_supported_donor_SE.",
            "ladder_convergence": "A nonzero level may stop only after successive nested levels have overlapping local-D brackets, previous predictability within one current donor SE, and cross-level principal overlap above the current donor-bootstrap one-SE floor in both sketches; otherwise advance through FULL104.",
        },
        "promotion_requirements": [
            "prospective mathematical contract", "synthetic planted-rank and null fixtures", "metamorphic tests",
            "observed/null executable symmetry", "independent non-reused implementation", "hash-bound agreement report",
            "dependency/taint registry", "ordered Representation-Geometry then Statistics/Leakage then Red-Team PASS",
        ],
        "independent_validator": {
            "implementation": "whiten W by independent symmetric eigendecomposition, solve standard symmetric eigenproblem with numpy.linalg.eigh, and reconstruct generalized coordinates; must not import or call production fit_basis/statistic routines",
            "real_agreement": "candidate D and all conclusion-bearing pass/fail booleans exact; scalar metrics absolute difference <=1e-6 or relative difference <=1e-5",
        },
        "fixture_expectations": {
            "planted_rank": "recover exact planted rank 4 jointly in two sketches; row/view/donor-order and orthogonal-coordinate metamorphisms preserve rank and subspace",
            "null": "no dimension qualifies jointly under the matched-null promotion rule",
        },
        "input_hashes": {"procedure_amendment": sha256(amendment), "preexpression_freeze": sha256(freeze), "rng": sha256(rng)},
        "code_hashes": {
            "state_machine": sha256(ROOT / "scripts/v4/jepa_scientific_promotion_harness_v1.py"),
            "freeze": sha256(Path(__file__)),
        },
        "no_private_standardization_direct_basis_gpu_optimizer_training_or_protected_data": True,
    }
    contract_path = out / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1.json"
    contract_path.write_text(json.dumps(contract, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    graph = {
        "promotion_contract": {"state": "FROZEN", "tainted": False, "depends_on": []},
        "harness_executable_tests": {"state": "PROVISIONAL", "tainted": False, "depends_on": ["promotion_contract"]},
        "level1_fixed_axis_stability": {"state": "EXPLORATORY", "tainted": True, "taint_reason": "statistic mismatch", "depends_on": ["promotion_contract"]},
        "level1_shared_selection": {"state": "EXPLORATORY", "tainted": True, "taint_reason": "depends on invalid fixed-axis stability", "depends_on": ["level1_fixed_axis_stability"]},
        "level2_shared_statistics": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["promotion_contract", "harness_executable_tests"]},
        "level2_shared_selection": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["level2_shared_statistics"]},
        "shared_state_final": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["level2_shared_selection"]},
        "private_state": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["shared_state_final"]},
        "teacher_standardization": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["private_state"]},
        "direct_basis_ridge": {"state": "EXPLORATORY", "tainted": False, "depends_on": ["teacher_standardization"]},
    }
    registry_path = out / "SCIENTIFIC_PROMOTION_REGISTRY.json"
    save_registry(registry_path, graph)
    dependency_path = out / "SCIENTIFIC_DEPENDENCY_GRAPH.csv"
    pd.DataFrame([{"artifact": node, "depends_on": "|".join(record.get("depends_on", [])), "state": record["state"], "tainted": record.get("tainted", False)} for node, record in graph.items()]).to_csv(dependency_path, index=False, lineterminator="\n")
    manifest = out / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1_MANIFEST.csv"
    files = [contract_path, registry_path, dependency_path, ROOT / "scripts/v4/jepa_scientific_promotion_harness_v1.py", Path(__file__)]
    pd.DataFrame([{"path": str(path.relative_to(ROOT)), "bytes": path.stat().st_size, "sha256": sha256(path)} for path in files]).to_csv(manifest, index=False, lineterminator="\n")
    (out / "JEPA_SCIENTIFIC_PROMOTION_HARNESS_V1_ROOT_SHA256.txt").write_text(sha256(manifest) + "\n", encoding="ascii")
    print(json.dumps({"status": contract["status"], "manifest_sha256": sha256(manifest)}, indent=2))


if __name__ == "__main__":
    main()
