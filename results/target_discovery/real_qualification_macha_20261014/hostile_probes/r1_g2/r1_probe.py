"""Hostile synthetic probes for R1 (PR #350 manifest V2 + PR #353 stress). No real data.

Run with cwd = scratch dir; worktree paths are inserted explicitly.
"""
from __future__ import annotations

import copy
import json
import math
import sys

import numpy as np

R1_WT = "D:/jepa_rq_r1_20261014"
R1S_WT = "D:/jepa_rq_r1s_20261014"
sys.path.insert(0, R1S_WT)
import scripts.v5.td_r1_known_truth_stress_v1 as S  # noqa: E402

sys.path.pop(0)
for k in [k for k in sys.modules if k.startswith("scripts")]:
    del sys.modules[k]
sys.path.insert(0, R1_WT)
import scripts.v5.td_real_relational_manifest_v2 as R  # noqa: E402

OUT = {}


def pair(pid, a, b):
    return {"pair_id": pid, "member_address_ids": [a, b], "address_binding_state": "REPAIRED_41K_ADDRESS_BOUND"}


def manifest(views):
    return {
        "schema": R.SCHEMA, "frozen": True, "candidate_id": R.CANDIDATE_ID,
        "relation_family": R.RELATION_FAMILY, "scale_class": R.SCALE_CLASS,
        "required_sources": list(R.REQUIRED_SOURCES), "lawful_views": views,
        "minimum_informative_pair_coordinates": 1,
        "relation_construction": dict(R.RELATION_CONSTRUCTION),
        "null_permutation_unit": R.NULL_PERMUTATION_UNIT,
        "support_semantics": dict(R.SUPPORT_SEMANTICS),
    }


# ---- P1: manifest accepts duplicated / reversed pair coordinates and arbitrary unbound address strings
views = [
    {"view_id": "X", "pair_coordinates": [pair("X1", "A1", "A2"), pair("X2", "A2", "A1"), pair("X3", "A1", "A2")]},
    {"view_id": "Y", "pair_coordinates": [pair("Y1", "not_a_real_address", "B2")]},
]
try:
    c = R.derive_relational_contract(manifest(views))
    OUT["P1_duplicate_reversed_pairs_and_unbound_address_accepted"] = {
        "accepted": True, "view_X_pairs": len(c["lawful_views"][0]["pair_coordinates"]),
        "contract_has_tau": any("tau" in k.lower() or "tol" in k.lower() for k in c),
        "contract_has_triplet_sampling_rule": any("sampl" in k.lower() or "triplet_count" in k.lower() for k in c),
        "contract_has_null_draw_count": any("draw" in k.lower() for k in c),
        "contract_has_view_construction_rule_or_digest": any("digest" in k.lower() or "sha" in k.lower() for k in c),
        "contract_has_depth_or_detection_in_null": ("DEPTH" in c["null_permutation_unit"] or "DETECTION" in c["null_permutation_unit"]),
        "contract_has_alpha": any("alpha" in k.lower() for k in c),
    }
except R.RelationalManifestError as e:
    OUT["P1_duplicate_reversed_pairs_and_unbound_address_accepted"] = {"accepted": False, "error": str(e)}

# ---- P2: no-biology world where relations are driven only by per-cell library size shared across
# address-disjoint views. Distance = tie-aware pair-order discordance (|s_i - s_j|/2 averaged over pairs).
rng = np.random.default_rng(20261014)


def make_world(n_cells, n_genes, depth_sd, bio_strength, rng):
    base = rng.lognormal(mean=-1.0, sigma=1.0, size=n_genes)  # gene baseline rates (no biology)
    depth = np.exp(rng.normal(0.0, depth_sd, size=n_cells))
    if bio_strength > 0:
        z = rng.normal(size=(n_cells, 1))
        load = rng.normal(size=(1, n_genes))
        lam = np.outer(depth, base) * np.exp(bio_strength * z @ load)
    else:
        lam = np.outer(depth, base)
    return rng.poisson(lam)


def pair_signs(X, genes):
    g = np.asarray(genes)
    a, b = g[0::2], g[1::2]
    return np.sign(X[:, a] - X[:, b])


def dist(Si, Sj):
    return float(np.mean(np.abs(Si - Sj)) / 2.0)


def triplet_rows(X, view_x_genes, view_y_genes, donor, n_triplets, rng, source="SEA_AD"):
    Sx = pair_signs(X, view_x_genes)
    Sy = pair_signs(X, view_y_genes)
    n = X.shape[0]
    rows = []
    seen = set()
    while len(rows) < n_triplets:
        i, j, k = rng.choice(n, size=3, replace=False)
        j, k = sorted((j, k))
        rid = f"{i}|{j}|{k}"
        if rid in seen:
            continue
        seen.add(rid)
        qx = S.anchored_triplet_order(dist(Sx[i], Sx[j]), dist(Sx[i], Sx[k]))
        qy = S.anchored_triplet_order(dist(Sy[i], Sy[j]), dist(Sy[i], Sy[k]))
        rows.append({"donor_id": donor, "relation_id": rid, "source_x": source, "source_y": source,
                     "operator_x": "opA", "operator_y": "opA", "support_stratum_x": "S", "support_stratum_y": "S",
                     "q_x": qx, "q_y": qy, "eligible": True, "cell_weight": 1})
    return rows


def null_q99(rows, draws, rng, alpha=0.01):
    qx = np.array([r["q_x"] for r in rows])
    qy = np.array([r["q_y"] for r in rows])
    stats = np.empty(draws)
    for t in range(draws):
        stats[t] = np.mean(qx == rng.permutation(qy))
    r = math.ceil((draws + 1) * (1 - alpha))
    return float(np.sort(stats)[r - 1]), float(np.median(stats))


def run_world(label, depth_sd, bio_strength, n_donors=8, n_cells=120, n_genes=400, n_triplets=600):
    genes = np.arange(n_genes)
    vx, vy = genes[: n_genes // 2], genes[n_genes // 2:]  # address-disjoint views
    donors = {}
    all_rows = []
    for d in range(n_donors):
        X = make_world(n_cells, n_genes, depth_sd, bio_strength, rng)
        rows = triplet_rows(X, vx, vy, f"D{d}", n_triplets, rng)
        all_rows += rows
        q99, med = null_q99(rows, 999, rng)
        obs = float(np.mean([r["q_x"] == r["q_y"] for r in rows]))
        tie_frac = float(np.mean([r["q_x"] == 0 and r["q_y"] == 0 for r in rows]))
        donors[f"D{d}"] = {"obs": round(obs, 4), "null_q99": round(q99, 4), "null_median": round(med, 4),
                           "delta_vs_q99": round(obs - q99, 4), "both_tie_frac": round(tie_frac, 4)}
    summ = S.summarize_recurrence(all_rows, minimum_informative_relations_per_donor=1)
    n_pos = sum(v["delta_vs_q99"] > 0 for v in donors.values())
    OUT[label] = {"summary_status": summ["status"], "donor_mean_agreement": round(summ["donor_mean_agreement"], 4),
                  "donors_defeating_null_q99": f"{n_pos}/{n_donors}", "per_donor": donors}


run_world("P2a_CLEAN_INDEPENDENT_NEGATIVE_no_depth_no_bio", depth_sd=0.0, bio_strength=0.0)
run_world("P2b_TECHNICAL_ONLY_NEGATIVE_library_size_only_no_bio", depth_sd=1.0, bio_strength=0.0)
run_world("P2c_PLANTED_BIOLOGY_POSITIVE_no_depth", depth_sd=0.0, bio_strength=0.6)

# ---- P3: tie inflation: two views that both tie on every relation (e.g. all-zero sparse cells)
ties = [S._row("D1", f"R{i}", 0, 0) for i in range(50)]
OUT["P3_all_ties_both_views_counts_as_perfect_agreement"] = S.summarize_recurrence(
    ties, minimum_informative_relations_per_donor=1)["donor_agreement"]

# ---- P4: value-dependent eligibility: caller marks disagreeing relations ineligible
rows = [S._row("D1", f"R{i}", 1, 1 if i % 2 else -1, eligible=bool(i % 2)) for i in range(100)]
s4 = S.summarize_recurrence(rows, minimum_informative_relations_per_donor=1)
OUT["P4_value_dependent_eligibility_accepted"] = {"status": s4["status"], "donor_mean": s4["donor_mean_agreement"],
                                                  "true_agreement_if_all_counted": 0.5}

# ---- P5: silent donor attrition below minimum + cross-source pooling (no per-source output)
rows = [S._row("D_GOOD", f"R{i}", 1, 1, source="SEA_AD") for i in range(50)]
rows += [S._row("D_BAD_HVS", f"R{i}", 1, -1, source="HVS") for i in range(9)]
s5 = S.summarize_recurrence(rows, minimum_informative_relations_per_donor=10)
OUT["P5_silent_attrition_and_source_pooling"] = {"status": s5["status"], "donor_agreement": s5["donor_agreement"],
                                                 "has_per_source_output": any("source" in k for k in s5),
                                                 "dropped_donor_reported": "D_BAD_HVS" in json.dumps(s5)}

# ---- P6: same donor id appearing under two sources is pooled into one donor estimate
rows = [S._row("D1", f"R{i}", 1, 1, source="SEA_AD") for i in range(10)]
rows += [S._row("D1", f"H{i}", 1, -1, source="HVS") for i in range(10)]
OUT["P6_same_donor_two_sources_pooled"] = S.summarize_recurrence(rows, minimum_informative_relations_per_donor=1)["donor_agreement"]

# ---- P7: #353 qualify() world list
q = S.qualify_r1_known_truth_stress()
OUT["P7_stress_worlds_present"] = sorted(q["worlds"])

print(json.dumps(OUT, indent=1))
