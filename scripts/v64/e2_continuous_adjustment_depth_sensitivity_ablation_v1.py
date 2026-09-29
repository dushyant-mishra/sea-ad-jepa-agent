#!/usr/bin/env python3
"""Execute the prospectively frozen V64 depth-sensitivity ablation.

Authority:
  results/v64/V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1.json

This executor changes exactly one thing relative to the V63 continuous-adjustment
implementation: it removes the two feature columns
  - rna_depth_sensitivity
  - atac_depth_sensitivity
from the nuisance model. All worlds, seeds, arm construction, M_MIN, ridge alpha,
promoter cross-fitting, scoring and remaining features are inherited unchanged.

It intentionally imports and reuses the V63 estimator implementation rather than
reimplementing the estimator.

TRAINING=OFF. TD60=BLOCKED. Synthetic only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
PARENT = os.path.join(REPO, "scripts", "v63", "e2_continuous_adjustment_estimator_v1.py")
BASELINE_JSON = os.path.join(
    REPO, "results", "v63", "V63_E2_CONTINUOUS_ADJUSTMENT_PRIMARY_V1.json"
)
CONTRACT = os.path.join(
    REPO, "results", "v64",
    "V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1.json",
)

spec = importlib.util.spec_from_file_location("v63ca", PARENT)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
T = C.T

DROP_NAMES = ["rna_depth_sensitivity", "atac_depth_sensitivity"]
DROP_IDX = [C.FEATURE_NAMES.index(x) for x in DROP_NAMES]
KEEP_IDX = [i for i in range(len(C.FEATURE_NAMES)) if i not in DROP_IDX]
ABLATION_FEATURE_NAMES = [C.FEATURE_NAMES[i] for i in KEEP_IDX]

_ORIGINAL_BUILD_FEATURES = C.build_features


def build_features_without_depth_sensitivity(w, rna_sens, atac_sens):
    """Return the frozen V63 feature matrix with only the two forbidden columns removed."""
    X = _ORIGINAL_BUILD_FEATURES(w, rna_sens, atac_sens)
    return X[:, KEEP_IDX]


def summarise(arm_seed_fold, diag):
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in arm_seed_fold.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_stack = np.vstack([arm_seed[p] for p in T.POSITIVES])
    pos_min = pos_stack.min(0)

    def fam(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        margin = pos_min - neg
        return float(margin.mean()), T.lower_confidence_bound(margin)

    families = {}
    for name, arms in T.FAMILIES.items():
        mm, ll = fam(arms)
        families[name] = {
            "margin": mm,
            "lcb95": ll,
            "passes_M_MIN": bool(ll > C.M_MIN),
        }

    heldout = {}
    for name, arms in T.HELDOUT_FAMILY.items():
        mm, ll = fam(arms)
        heldout[name] = {
            "margin": mm,
            "lcb95": ll,
            "generalises_at_M_MIN": bool(ll > C.M_MIN),
        }

    det = pos_min - arm_seed["NEG_NULL_0"]
    det_lcb = T.lower_confidence_bound(det)
    ordering_ok = bool(
        med["POS_BIO_1"] > med["POS_BIO_2"] >
        max(med[x] for x in T.NEG_ARMS)
    )
    twin_identical = bool(
        np.allclose(arm_seed[T.TWIN], arm_seed["POS_BIO_1"], rtol=0, atol=0)
    )

    n_linked = int(T.N_PROM * T.N_LINKED_PER_PROM)
    conc = {
        p: float(np.mean([row[p] for row in diag["concentration"]]))
        for p in (1, 5, 10)
    }
    rc = {
        k: float(np.mean([row[k] for row in diag["resid_corr"] if row[k] is not None]))
        for k in diag["resid_corr"][0]
    }
    smd = {
        k: float(np.mean([row[k] for row in diag["linked_vs_control_smd"]]))
        for k in diag["linked_vs_control_smd"][0]
    }
    ess = float(np.mean(diag["ess"]))

    return {
        "arm_medians": med,
        "families": families,
        "heldout_family": heldout,
        "positive_detectability_lcb95": det_lcb,
        "positive_detectable": bool(det_lcb > C.M_MIN),
        "ordering_POS1_gt_POS2_gt_negatives": ordering_ok,
        "twin_identical": twin_identical,
        "support": {
            "linked_pairs_scored": n_linked,
            "linked_pairs_total": n_linked,
            "fraction_of_linked_scored": 1.0,
            "kish_effective_sample_size": ess,
            "ess_fraction_of_linked": ess / n_linked,
            "contribution_concentration_top_pct": conc,
            "residual_correlation_with_adjustment_vars_on_LINKED": rc,
            "worst_abs_residual_correlation": float(max(abs(v) for v in rc.values())),
            "linked_vs_control_SMD_before_adjustment": smd,
            "worst_abs_linked_vs_control_SMD": float(max(abs(v) for v in smd.values())),
            "nuisance_model_out_of_fold_r2": float(np.mean(diag["nuisance_r2"])),
        },
        "broad_coverage": bool(conc[10] < 0.5 and ess > 0.3 * n_linked),
    }


def compare_to_baseline(result, baseline):
    base_fam = baseline["A_REPRESENTED_NUISANCE_SPECIFICITY"]["families"]
    comparisons = {}
    for name, now in result["families"].items():
        old = base_fam[name]
        comparisons[name] = {
            "baseline_margin": old["margin"],
            "ablated_margin": now["margin"],
            "delta_margin": now["margin"] - old["margin"],
            "baseline_lcb95": old["lcb95"],
            "ablated_lcb95": now["lcb95"],
            "delta_lcb95": now["lcb95"] - old["lcb95"],
            "baseline_pass": old["passes_M_MIN"],
            "ablated_pass": now["passes_M_MIN"],
        }

    pos = {}
    for name in T.POSITIVES:
        b = baseline["arm_medians"][name]
        a = result["arm_medians"][name]
        pos[name] = {
            "baseline_median": b,
            "ablated_median": a,
            "delta": a - b,
        }

    b_support = baseline["SUPPORT_PROOF"]
    a_support = result["support"]
    support = {
        "baseline_ess": b_support["kish_effective_sample_size"],
        "ablated_ess": a_support["kish_effective_sample_size"],
        "baseline_ess_fraction": b_support["ess_fraction_of_linked"],
        "ablated_ess_fraction": a_support["ess_fraction_of_linked"],
        "baseline_concentration_top_pct": b_support["contribution_concentration_top_pct"],
        "ablated_concentration_top_pct": a_support["contribution_concentration_top_pct"],
        "baseline_worst_abs_residual_correlation":
            b_support["worst_abs_residual_correlation"],
        "ablated_worst_abs_residual_correlation":
            a_support["worst_abs_residual_correlation"],
    }
    return {"families": comparisons, "positives": pos, "support": support}


def main() -> int:
    T.assert_sealed()
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--donors", type=int, default=18)
    ap.add_argument("--seeds", type=int, default=24)
    ap.add_argument("--base-seed", type=int, default=20260929)
    args = ap.parse_args()

    if os.path.exists(args.out_dir) and os.listdir(args.out_dir):
        raise SystemExit("STOP_OUTPUT_EXISTS")
    os.makedirs(args.out_dir, exist_ok=True)

    if args.donors != 18 or args.seeds != 24 or args.base_seed != 20260929:
        raise SystemExit("STOP_FROZEN_CONFIG_MISMATCH")

    with open(BASELINE_JSON) as fh:
        baseline = json.load(fh)
    with open(CONTRACT) as fh:
        contract = json.load(fh)

    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        raise SystemExit("STOP_CONTRACT_NOT_FROZEN")
    if baseline["config"]["ridge_alpha"] != C.RIDGE_ALPHA:
        raise SystemExit("STOP_BASELINE_ALPHA_MISMATCH")
    if baseline["config"]["M_MIN"] != C.M_MIN:
        raise SystemExit("STOP_BASELINE_MMIN_MISMATCH")
    if baseline["config"]["features"] != C.FEATURE_NAMES:
        raise SystemExit("STOP_BASELINE_FEATURE_LINEAGE_MISMATCH")

    # Exact frozen intervention: remove two columns and change nothing else.
    C.build_features = build_features_without_depth_sensitivity
    C.FEATURE_NAMES = ABLATION_FEATURE_NAMES

    arm_seed_fold, diag = C.run(
        args.donors, args.seeds, base_seed=args.base_seed, ablate=None
    )
    result = summarise(arm_seed_fold, diag)
    comparison = compare_to_baseline(result, baseline)

    represented_all_pass = all(
        row["passes_M_MIN"] for row in result["families"].values()
    )
    heldout_all_pass = all(
        row["generalises_at_M_MIN"] for row in result["heldout_family"].values()
    )
    survives = bool(
        represented_all_pass
        and heldout_all_pass
        and result["positive_detectable"]
        and result["twin_identical"]
        and result["broad_coverage"]
    )

    out = {
        "schema": "V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_ABLATION_RESULT_V1",
        "date": "2026-09-29",
        "contract":
            "results/v64/V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_LEAKAGE_DIAGNOSTIC_V1.json",
        "parent_estimator":
            "scripts/v63/e2_continuous_adjustment_estimator_v1.py",
        "baseline_result":
            "results/v63/V63_E2_CONTINUOUS_ADJUSTMENT_PRIMARY_V1.json",
        "governance": {
            "training": "OFF",
            "td60": "BLOCKED",
            "real_data_read": False,
        },
        "frozen_intervention": {
            "removed_only": DROP_NAMES,
            "removed_parent_feature_indices": DROP_IDX,
            "remaining_features": ABLATION_FEATURE_NAMES,
            "ridge_alpha": C.RIDGE_ALPHA,
            "M_MIN": C.M_MIN,
            "donors": args.donors,
            "seeds": args.seeds,
            "base_seed": args.base_seed,
            "cross_fitting": "unchanged; K=5 by promoter",
            "worlds_arms_scoring": "inherited unchanged from V63 parent",
        },
        "ablated_result": result,
        "comparison_to_committed_baseline": comparison,
        "contract_readout": {
            "pass_survives_without_depth_sensitivity_features": survives,
            "represented_families_all_pass": represented_all_pass,
            "heldout_families_all_generalise": heldout_all_pass,
            "TECH_pass": result["families"]["TECH"]["passes_M_MIN"],
            "TECH_lcb95": result["families"]["TECH"]["lcb95"],
            "positive_detectability_preserved": result["positive_detectable"],
            "broad_support_preserved": result["broad_coverage"],
            "note":
                "Magnitude-based interpretation of whether positive biology is "
                "'materially restored' is reported numerically and not invented "
                "here because the frozen contract does not specify a numeric "
                "materiality threshold.",
        },
    }

    out_path = os.path.join(
        args.out_dir,
        "V64_CONTINUOUS_ADJUSTMENT_DEPTH_SENSITIVITY_ABLATION_RESULT_V1.json",
    )
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)

    tech = result["families"]["TECH"]
    print(
        f"TECH margin={tech['margin']:+.5f} LCB95={tech['lcb95']:+.5f} "
        f"{'PASS' if tech['passes_M_MIN'] else 'FAIL'}"
    )
    print(
        f"ESS={result['support']['kish_effective_sample_size']:.1f} "
        f"({100*result['support']['ess_fraction_of_linked']:.1f}%), "
        f"top10={result['support']['contribution_concentration_top_pct'][10]:.3f}"
    )
    print(
        "CONTRACT READOUT: "
        + ("A_PASS_SURVIVES" if survives else "PASS_DOES_NOT_SURVIVE_OR_REQUIRES_REVIEW")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
