#!/usr/bin/env python3
"""Execute the prospectively frozen V64 out-of-span TECH stress.

Authority:
  results/v64/V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1.json

This wrapper preserves the V63 continuous-adjustment estimator and all existing
synthetic arms unchanged. It adds exactly one new negative arm,
NEG_TECH_OUTSPAN_1, with the frozen nonlinear geometry from the V64 contract,
and evaluates it as its own OUTSPAN_TECH nuisance family.

No estimator basis terms are added. Ridge alpha, M_MIN, worlds, seeds, existing
arm amplitudes, positive amplitudes, cross-fitting and scoring are inherited.

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
CONTRACT = os.path.join(
    REPO, "results", "v64",
    "V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1.json",
)

spec = importlib.util.spec_from_file_location("v63ca", PARENT)
C = importlib.util.module_from_spec(spec)
spec.loader.exec_module(C)
T = C.T

NEW_ARM = "NEG_TECH_OUTSPAN_1"
NEW_FAMILY = "OUTSPAN_TECH"
_ORIGINAL_SIMULATE = T.simulate
_ORIGINAL_ALL_ARMS = tuple(T.ALL_ARMS)
_ORIGINAL_FAMILIES = dict(T.FAMILIES)
_ORIGINAL_NEG_ARMS = tuple(T.NEG_ARMS)


def zscore(x):
    x = np.asarray(x, float)
    return (x - x.mean()) / (x.std() + 1e-9)


def outspan_geometry(w):
    """Frozen V64 geometry:
    zscore(sin(2.5*z_log_distance)
           + 0.5*tanh(z_degree*z_anchor_frequency)
           + 0.35*z_accessibility*z_re_density))

    z_* terms are standardised over the full pair universe in the synthetic world.
    Promoter degree is repeated across distal positions before standardisation.
    """
    P, D = T.N_PROM, T.N_DISTAL
    z_log_distance = zscore(np.log(w["distance"]))
    z_degree = zscore(np.repeat(w["degree"][:, None].astype(float), D, axis=1))
    z_anchor_frequency = zscore(w["anchor_freq"])
    z_accessibility = zscore(w["distal_acc"])
    z_re_density = zscore(w["re_density"])
    raw = (
        np.sin(2.5 * z_log_distance)
        + 0.5 * np.tanh(z_degree * z_anchor_frequency)
        + 0.35 * z_accessibility * z_re_density
    )
    return zscore(raw)


def simulate_with_outspan(w, arm, n_donors, seed, twin_source=None):
    if arm != NEW_ARM:
        return _ORIGINAL_SIMULATE(
            w, arm, n_donors, seed, twin_source=twin_source
        )

    g = outspan_geometry(w)
    out = []
    for dn in range(n_donors):
        # Exactly the same arm-independent base draws and effect RNG lineage as
        # the frozen tournament simulator.
        base = np.random.default_rng(seed * 1_000_003 + dn)
        eff = np.random.default_rng(seed * 1_000_003 + dn + 7_777_777)

        rna_depth = base.normal(0, 1, T.N_METACELL)
        atac_depth = (
            0.45 * rna_depth
            + base.normal(0, np.sqrt(1 - 0.45 ** 2), T.N_METACELL)
        )
        operator = base.normal(0, 1)
        R = (
            base.normal(0, 1, (T.N_METACELL, T.N_PROM))
            + 0.35 * rna_depth[:, None]
        )
        A = (
            base.normal(0, 1, (T.N_METACELL, T.N_PROM, T.N_DISTAL))
            + 0.35 * atac_depth[:, None, None]
        )

        # Same NEG_TECH_2 hidden-quality latent and mixing.
        z_meas = 0.5 * (rna_depth + atac_depth) / np.sqrt(2)
        hq = 0.6 * z_meas + 0.8 * eff.normal(0, 1, T.N_METACELL)

        # Frozen V64 change: only the ATAC-side geometry is replaced by the
        # nonlinear out-of-span function. Amplitude remains 0.60 on both sides.
        R += 0.60 * hq[:, None]
        A += 0.60 * hq[:, None, None] * g[None, :, :]

        out.append(
            {
                "R": R,
                "A": A,
                "rna_depth": rna_depth,
                "atac_depth": atac_depth,
            }
        )
    return out


def summarise(arm_seed_fold, diag):
    arm_seed = {k: np.array([f.mean() for f in v]) for k, v in arm_seed_fold.items()}
    med = {k: float(np.median(v)) for k, v in arm_seed.items()}
    pos_stack = np.vstack([arm_seed[p] for p in T.POSITIVES])
    pos_min = pos_stack.min(0)

    def family(arms):
        neg = np.vstack([arm_seed[x] for x in arms]).max(0)
        m = pos_min - neg
        return float(m.mean()), T.lower_confidence_bound(m)

    families = {}
    for name, arms in T.FAMILIES.items():
        mm, ll = family(arms)
        families[name] = {
            "arms": list(arms),
            "margin": mm,
            "lcb95": ll,
            "passes_M_MIN": bool(ll > C.M_MIN),
        }

    heldout = {}
    for name, arms in T.HELDOUT_FAMILY.items():
        mm, ll = family(arms)
        heldout[name] = {
            "arms": list(arms),
            "margin": mm,
            "lcb95": ll,
            "generalises_at_M_MIN": bool(ll > C.M_MIN),
        }

    det = pos_min - arm_seed["NEG_NULL_0"]
    det_lcb = T.lower_confidence_bound(det)
    ordering_ok = bool(
        med["POS_BIO_1"] > med["POS_BIO_2"] >
        max(med[x] for x in _ORIGINAL_NEG_ARMS)
    )
    twin_identical = bool(
        np.allclose(arm_seed[T.TWIN], arm_seed["POS_BIO_1"], rtol=0, atol=0)
    )

    n_linked = int(T.N_PROM * T.N_LINKED_PER_PROM)
    conc = {
        p: float(np.mean([row[p] for row in diag["concentration"]]))
        for p in (1, 5, 10)
    }
    ess = float(np.mean(diag["ess"]))
    rc = {
        k: float(np.mean([row[k] for row in diag["resid_corr"] if row[k] is not None]))
        for k in diag["resid_corr"][0]
    }

    return {
        "arm_medians": med,
        "families": families,
        "heldout_family": heldout,
        "positive_detectability_lcb95": det_lcb,
        "positive_detectable": bool(det_lcb > C.M_MIN),
        "ordering_POS1_gt_POS2_gt_existing_negatives": ordering_ok,
        "semantic_twin_identical": twin_identical,
        "support": {
            "linked_pairs_scored": n_linked,
            "linked_pairs_total": n_linked,
            "fraction_of_linked_scored": 1.0,
            "kish_effective_sample_size": ess,
            "ess_fraction_of_linked": ess / n_linked,
            "contribution_concentration_top_pct": conc,
            "residual_correlation_with_adjustment_vars_on_LINKED": rc,
            "worst_abs_residual_correlation":
                float(max(abs(v) for v in rc.values())),
        },
        "broad_support":
            bool(conc[10] < 0.50 and ess > 0.30 * n_linked),
    }


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

    with open(CONTRACT) as fh:
        contract = json.load(fh)
    if contract.get("status") != "FROZEN_BEFORE_EXECUTION":
        raise SystemExit("STOP_CONTRACT_NOT_FROZEN")

    # Add exactly one arm/family. Existing arm order and definitions remain.
    T.simulate = simulate_with_outspan
    T.FAMILIES = dict(_ORIGINAL_FAMILIES)
    T.FAMILIES[NEW_FAMILY] = (NEW_ARM,)
    T.NEG_ARMS = _ORIGINAL_NEG_ARMS + (NEW_ARM,)
    T.ALL_ARMS = (
        T.POSITIVES
        + tuple(a for fam in T.FAMILIES.values() for a in fam)
        + tuple(T.HELDOUT_FAMILY["HELDOUT_NOT_USED_IN_DESIGN"])
        + (T.TWIN,)
    )

    arm_seed_fold, diag = C.run(
        args.donors, args.seeds, base_seed=args.base_seed, ablate=None
    )
    result = summarise(arm_seed_fold, diag)

    represented_existing_pass = all(
        result["families"][name]["passes_M_MIN"]
        for name in _ORIGINAL_FAMILIES
    )
    outspan_pass = result["families"][NEW_FAMILY]["passes_M_MIN"]
    heldout_pass = all(
        row["generalises_at_M_MIN"]
        for row in result["heldout_family"].values()
    )

    if not represented_existing_pass:
        classification = "C_EXISTING_FAMILY_BREAKS__STOP"
    elif not result["broad_support"]:
        classification = "D_SUPPORT_CONCENTRATES__DISGUISED_FAILURE"
    elif outspan_pass:
        classification = "A_OUTSPAN_PASSES__GENERALISES_WITHIN_FROZEN_STRESS_CLASS"
    else:
        classification = "B_OUTSPAN_FAILS_ONLY__LIMIT_TO_NEAR_MODEL_SPAN"

    out = {
        "schema": "V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_RESULT_V1",
        "date": "2026-09-29",
        "contract":
            "results/v64/V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_CONTRACT_V1.json",
        "parent_estimator":
            "scripts/v63/e2_continuous_adjustment_estimator_v1.py",
        "governance": {
            "training": "OFF",
            "td60": "BLOCKED",
            "real_data_read": False,
        },
        "frozen_new_arm": {
            "name": NEW_ARM,
            "family": NEW_FAMILY,
            "geometry_function":
                "zscore(sin(2.5*z_log_distance) + "
                "0.5*tanh(z_degree*z_anchor_frequency) + "
                "0.35*z_accessibility*z_re_density)",
            "zscore_scope":
                "full pair universe within each synthetic world",
            "rna_effect_amplitude": 0.60,
            "atac_effect_amplitude": 0.60,
            "hidden_quality_mixing":
                "same as NEG_TECH_2: 0.6*z_meas + 0.8*orthogonal latent",
        },
        "estimator_invariance": {
            "feature_names": list(C.FEATURE_NAMES),
            "ridge_alpha": C.RIDGE_ALPHA,
            "M_MIN": C.M_MIN,
            "k_folds_by_promoter": C.K_FOLDS,
            "basis_terms_added": [],
            "basis_changed": False,
        },
        "result": result,
        "contract_readout": {
            "classification": classification,
            "existing_represented_families_all_pass": represented_existing_pass,
            "outspan_TECH_pass": outspan_pass,
            "outspan_TECH_lcb95":
                result["families"][NEW_FAMILY]["lcb95"],
            "heldout_family_generalises": heldout_pass,
            "positive_detectability_preserved": result["positive_detectable"],
            "semantic_twin_identity_preserved":
                result["semantic_twin_identical"],
            "broad_support_preserved": result["broad_support"],
        },
    }

    out_path = os.path.join(
        args.out_dir,
        "V64_CONTINUOUS_ADJUSTMENT_OUT_OF_SPAN_STRESS_RESULT_V1.json",
    )
    with open(out_path, "w") as fh:
        json.dump(out, fh, indent=2)

    f = result["families"][NEW_FAMILY]
    print(
        f"OUTSPAN_TECH margin={f['margin']:+.5f} "
        f"LCB95={f['lcb95']:+.5f} "
        f"{'PASS' if f['passes_M_MIN'] else 'FAIL'}"
    )
    print(f"CLASSIFICATION: {classification}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
