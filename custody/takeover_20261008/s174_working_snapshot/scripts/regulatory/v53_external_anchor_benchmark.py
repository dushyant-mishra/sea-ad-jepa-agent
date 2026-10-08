#!/usr/bin/env python
"""V53 synthetic external-anchor identifiability benchmark.

Synthetic/technical only. No real biological outcome is opened.

Primary statistic
-----------------
An independently defined, direction-oriented regulatory anchor maps each gene to a
set of supported local peaks. Each supported peak is paired to a *local cis decoy*
with the same analytic orientation and closely matched static locus features. For each
donor we compute the ordinal across-gene correspondence between RNA and oriented
supported-peak activity, minus the corresponding RNA/decoy correspondence. Donors are
the replication units. A one-sided exact sign test over donor deltas is the fixed pass
rule (p < 0.05 and mean delta > 0).

This benchmark deliberately includes a semantic-twin world in which the observed
arrays are byte-identical to the positive cis-regulatory world but the edge-specific
shared latent is interpreted as technical. It is expected to pass; that is the declared
non-identifiability boundary rather than a failure to be tuned away.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy.stats import rankdata

N_DONORS = 18
N_GENES = 24
N_SUPPORT = 3
N_DECOY = 3
N_FEATURES = 3
ALPHA = 0.05
DECOY_MAX_SMD = 0.10

PERMITTED_NEGATIVES = (
    "NEG0_INDEPENDENT",
    "NEG1_GLOBAL_SHARED_QUALITY",
    "NEG2_LOCUS_FEATURE_MEASURED",
    "NEG3_LOCUS_FEATURE_LATENT",
    "NEG4_GLOBAL_BIOLOGY_ONLY",
)
POSITIVES = ("POS1_EDGE_SPECIFIC_CIS", "POS2_EDGE_SPECIFIC_CIS_PLUS_TECH")
SEMANTIC_TWIN = "NEG5_ANCHOR_KEYED_SEMANTIC_TWIN"
BAD_DECOY = "MUT1_UNMATCHED_LOCAL_DECOYS"
ALL_WORLDS = PERMITTED_NEGATIVES + POSITIVES + (SEMANTIC_TWIN, BAD_DECOY)


@dataclass
class WorldData:
    rna: np.ndarray
    supported: np.ndarray
    decoy: np.ndarray
    orientation: np.ndarray
    supported_features: np.ndarray
    decoy_features: np.ndarray
    measured_qc: np.ndarray


def _row_spearman(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    ar = rankdata(a, axis=1)
    br = rankdata(b, axis=1)
    ar = ar - ar.mean(axis=1, keepdims=True)
    br = br - br.mean(axis=1, keepdims=True)
    den = np.sqrt(np.sum(ar * ar, axis=1) * np.sum(br * br, axis=1))
    return np.divide(np.sum(ar * br, axis=1), den, out=np.zeros(a.shape[0]), where=den > 0)


def _residualize_over_donors(y: np.ndarray, x: np.ndarray) -> np.ndarray:
    shape = y.shape
    yy = y.reshape(N_DONORS, -1)
    design = np.column_stack([np.ones(N_DONORS), x])
    beta = np.linalg.lstsq(design, yy, rcond=None)[0]
    return (yy - design @ beta).reshape(shape)


def _max_smd(a: np.ndarray, b: np.ndarray) -> float:
    aa = a.reshape(-1, a.shape[-1])
    bb = b.reshape(-1, b.shape[-1])
    pooled = np.sqrt((aa.var(axis=0, ddof=1) + bb.var(axis=0, ddof=1)) / 2.0)
    smd = np.divide(np.abs(aa.mean(axis=0) - bb.mean(axis=0)), pooled,
                    out=np.zeros_like(pooled), where=pooled > 0)
    return float(np.max(smd))


def _exact_sign_p(deltas: np.ndarray) -> float:
    nonzero = deltas[np.abs(deltas) > 1e-15]
    n = len(nonzero)
    if n == 0:
        return 1.0
    k = int(np.sum(nonzero > 0))
    return float(sum(math.comb(n, j) for j in range(k, n + 1)) / (2 ** n))


def _array_digest(data: WorldData) -> str:
    h = hashlib.sha256()
    for arr in (data.rna, data.supported, data.decoy, data.orientation,
                data.supported_features, data.decoy_features, data.measured_qc):
        h.update(np.ascontiguousarray(arr).view(np.uint8))
    return h.hexdigest()


def generate(seed: int, world: str) -> WorldData:
    if world not in ALL_WORLDS:
        raise ValueError(world)
    r = np.random.default_rng(seed)

    gene_feat = r.normal(size=(N_GENES, N_FEATURES))
    supp_feat = gene_feat[:, None, :] + 0.15 * r.normal(size=(N_GENES, N_SUPPORT, N_FEATURES))
    dec_feat = gene_feat[:, None, :] + 0.15 * r.normal(size=(N_GENES, N_DECOY, N_FEATURES))
    if world == BAD_DECOY:
        # Mutation: destroy the local feature match. The structural balance gate must refuse it.
        dec_feat = r.normal(size=(N_GENES, N_DECOY, N_FEATURES))

    orientation = r.choice([-1.0, 1.0], size=(N_GENES, N_SUPPORT))
    # Decoys inherit the exact analytic orientation of the supported partner. This is
    # load-bearing: different random signs create a false support-vs-decoy contrast.
    decoy_orientation = orientation.copy()

    q_global = r.normal(size=N_DONORS)
    q_locus = r.normal(size=(N_DONORS, N_FEATURES))
    global_bio = r.normal(size=N_DONORS)
    global_gene_loading = r.normal(size=N_GENES)
    edge_shared = r.normal(size=(N_DONORS, N_GENES))
    q_extra = r.normal(size=N_DONORS)

    rna = 0.8 * r.normal(size=(N_DONORS, N_GENES))
    supported = 0.8 * r.normal(size=(N_DONORS, N_GENES, N_SUPPORT))
    decoy = 0.8 * r.normal(size=(N_DONORS, N_GENES, N_DECOY))

    if world == "NEG0_INDEPENDENT":
        measured_qc = np.zeros((N_DONORS, 1))
        return WorldData(rna, supported, decoy, orientation, supp_feat, dec_feat, measured_qc)

    if world == "NEG1_GLOBAL_SHARED_QUALITY":
        rna += 0.8 * q_global[:, None]
        supported += 0.8 * q_global[:, None, None]
        decoy += 0.8 * q_global[:, None, None]
        measured_qc = q_global[:, None]
        return WorldData(rna, supported, decoy, orientation, supp_feat, dec_feat, measured_qc)

    # Shared technical state with locus-feature-dependent loadings.
    rna += 0.6 * q_global[:, None] + 0.7 * np.einsum("df,gf->dg", q_locus, gene_feat)
    supported += 0.6 * q_global[:, None, None] + 0.7 * np.einsum("df,gkf->dgk", q_locus, supp_feat)
    decoy += 0.6 * q_global[:, None, None] + 0.7 * np.einsum("df,gkf->dgk", q_locus, dec_feat)

    measured_qc = np.column_stack([q_global, q_locus])
    if world in ("NEG3_LOCUS_FEATURE_LATENT", BAD_DECOY):
        # Locus technical factors exist but are not available to residualization.
        measured_qc = q_global[:, None]

    if world in ("NEG4_GLOBAL_BIOLOGY_ONLY",) + POSITIVES + (SEMANTIC_TWIN,):
        # A broad biological state changes RNA and local chromatin broadly. This is
        # biologically real but does not establish correct peak-gene assignment.
        rna += 0.7 * global_bio[:, None] * global_gene_loading[None, :]
        supported += 0.7 * global_bio[:, None, None] * global_gene_loading[None, :, None]
        decoy += 0.7 * global_bio[:, None, None] * global_gene_loading[None, :, None]

    if world in ("POS1_EDGE_SPECIFIC_CIS", SEMANTIC_TWIN):
        # OBSERVABLES ARE IDENTICAL for these two worlds at the same seed. Only the
        # semantic interpretation of edge_shared differs (regulatory vs technical).
        rna += 0.9 * edge_shared
        supported += 0.9 * edge_shared[:, :, None] * orientation[None, :, :]

    if world == "POS2_EDGE_SPECIFIC_CIS_PLUS_TECH":
        rna += 0.9 * edge_shared
        supported += 0.9 * edge_shared[:, :, None] * orientation[None, :, :]
        rna += 0.8 * q_extra[:, None] * gene_feat[:, 0][None, :]
        supported += 0.8 * q_extra[:, None, None] * supp_feat[:, :, 0][None, :, :]
        decoy += 0.8 * q_extra[:, None, None] * dec_feat[:, :, 0][None, :, :]
        measured_qc = np.column_stack([measured_qc, q_extra])

    return WorldData(rna, supported, decoy, orientation, supp_feat, dec_feat, measured_qc)


def evaluate(data: WorldData) -> dict:
    max_smd = _max_smd(data.supported_features, data.decoy_features)
    balance_pass = max_smd <= DECOY_MAX_SMD

    rna = _residualize_over_donors(data.rna, data.measured_qc)
    supported = _residualize_over_donors(data.supported, data.measured_qc)
    decoy = _residualize_over_donors(data.decoy, data.measured_qc)

    support_activity = (supported * data.orientation[None, :, :]).mean(axis=2)
    # The local decoy gets the same orientation as its supported partner.
    decoy_activity = (decoy * data.orientation[None, :, :]).mean(axis=2)

    donor_delta = _row_spearman(rna, support_activity) - _row_spearman(rna, decoy_activity)
    p = _exact_sign_p(donor_delta)
    mean_delta = float(np.mean(donor_delta))
    statistical_pass = bool(p < ALPHA and mean_delta > 0)
    return {
        "max_static_feature_smd": max_smd,
        "decoy_balance_pass": balance_pass,
        "mean_donor_delta": mean_delta,
        "median_donor_delta": float(np.median(donor_delta)),
        "n_donors_positive": int(np.sum(donor_delta > 0)),
        "exact_sign_p_one_sided": p,
        "statistical_pass": statistical_pass,
        "gate_pass": bool(balance_pass and statistical_pass),
    }


def run_world(world: str, seeds: list[int]) -> dict:
    rows = []
    for seed in seeds:
        d = generate(seed, world)
        ev = evaluate(d)
        rows.append(ev)
    passes = np.array([r["gate_pass"] for r in rows], dtype=float)
    stats_pass = np.array([r["statistical_pass"] for r in rows], dtype=float)
    balance_pass = np.array([r["decoy_balance_pass"] for r in rows], dtype=float)
    effects = np.array([r["mean_donor_delta"] for r in rows])
    smds = np.array([r["max_static_feature_smd"] for r in rows])
    return {
        "world": world,
        "n_replicates": len(rows),
        "gate_pass_rate": float(passes.mean()),
        "statistical_pass_rate_before_balance_gate": float(stats_pass.mean()),
        "balance_pass_rate": float(balance_pass.mean()),
        "mean_effect": float(effects.mean()),
        "effect_q05": float(np.quantile(effects, 0.05)),
        "effect_q50": float(np.quantile(effects, 0.50)),
        "effect_q95": float(np.quantile(effects, 0.95)),
        "max_smd_q50": float(np.quantile(smds, 0.50)),
        "max_smd_q95": float(np.quantile(smds, 0.95)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replicates", type=int, default=500)
    ap.add_argument("--seed-base", type=int, default=530000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    seeds = [args.seed_base + i * 1009 for i in range(args.replicates)]
    results = {w: run_world(w, seeds) for w in ALL_WORLDS}

    # Exact semantic-twin witness: same seed, same observable arrays, different meaning.
    twin_seed = args.seed_base + 777777
    pos = generate(twin_seed, "POS1_EDGE_SPECIFIC_CIS")
    neg = generate(twin_seed, SEMANTIC_TWIN)
    twin = {
        "seed": twin_seed,
        "positive_digest": _array_digest(pos),
        "technical_twin_digest": _array_digest(neg),
        "byte_identical_observables": _array_digest(pos) == _array_digest(neg),
        "logical_implication": (
            "No statistic restricted to these observables can be required to pass the "
            "biological interpretation and fail the anchor-keyed technical interpretation."
        ),
    }

    criteria = {
        "permitted_negative_max_pass_rate": 0.10,
        "positive_min_pass_rate": 0.90,
        "bad_decoy_max_balance_pass_rate": 0.10,
        "semantic_twin_expected_to_track_positive": True,
    }
    checks = {
        "permitted_negatives_controlled": all(results[w]["gate_pass_rate"] <= 0.10 for w in PERMITTED_NEGATIVES),
        "positives_detected": all(results[w]["gate_pass_rate"] >= 0.90 for w in POSITIVES),
        "bad_decoy_refused_by_balance_gate": results[BAD_DECOY]["balance_pass_rate"] <= 0.10,
        "semantic_twin_is_byte_identical": twin["byte_identical_observables"],
        "semantic_twin_tracks_positive": abs(results[SEMANTIC_TWIN]["gate_pass_rate"] - results["POS1_EDGE_SPECIFIC_CIS"]["gate_pass_rate"]) <= 0.05,
    }
    protocol_qualified = all(checks.values())
    payload = {
        "schema": "v53_external_anchor_synthetic_identifiability_v1",
        "governance": "TRAINING=OFF | SYNTHETIC_TECHNICAL_ONLY | NO_REAL_BIOLOGICAL_OUTCOME_OPENED",
        "replication_unit": "donor",
        "n_donors": N_DONORS,
        "n_genes": N_GENES,
        "primary_signature": (
            "per-donor ordinal RNA correspondence to externally oriented supported local peaks "
            "minus orientation-matched local-cis decoy correspondence"
        ),
        "fixed_statistical_rule": "one-sided exact donor sign test p<0.05 AND mean donor delta>0",
        "decoy_balance_rule": f"max static-feature SMD <= {DECOY_MAX_SMD}",
        "qc_rule": "only measured technical covariates generated independently of program/edge biology are residualized",
        "criteria": criteria,
        "checks": checks,
        "world_results": results,
        "semantic_twin": twin,
        "protocol_qualified_for_next_design_step": protocol_qualified,
        "claim_boundary": (
            "Qualified only against the prospectively represented nuisance class. The exact anchor-keyed "
            "semantic twin remains nonidentifiable and prevents an unconditional claim of biological specificity."
        ),
        "real_data_authorized": False,
    }
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(json.dumps(payload, indent=2))
    return 0 if protocol_qualified else 3


if __name__ == "__main__":
    raise SystemExit(main())
