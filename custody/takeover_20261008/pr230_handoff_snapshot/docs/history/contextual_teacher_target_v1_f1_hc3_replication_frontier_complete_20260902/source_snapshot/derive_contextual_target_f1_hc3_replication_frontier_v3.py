#!/usr/bin/env python3
"""Command 15A4: complete outcome-blind donor-replicated HC3 frontier."""
from __future__ import annotations

import argparse, csv, hashlib, json
from itertools import product
from pathlib import Path

import numpy as np
from scipy import linalg

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
V2 = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_incremental_rank_diagnostic_v2_20260902"
EPS = np.finfo(np.float64).eps
HC3_BOUNDARY = float(np.sqrt(EPS))
SOURCES = ("HVS", "NPH52", "SEA_AD")
SOURCE_COLUMNS = ("source_HVS", "source_NPH52", "source_SEA_AD")
CONTINUOUS_COLUMNS = (
    "recipient_physical_support", "recipient_depth",
    "correct_minus_null_visible_depth", "correct_minus_null_measured_zero_rate",
)
BLOCKS = {"HVS": tuple(range(24)), "NPH52": tuple(range(35, 42)), "SEA_AD": tuple(range(24, 35))}
EXPECTED = {
    V2 / "F1_HC3_INCREMENTAL_MANIFEST.csv": "b43d8947e8b86e99166903479ae033ce2ffc0e5b449fa12c796fbec2c1bf85e5",
    V2 / "source_snapshot/derive_contextual_target_f1_hc3_incremental_rank_v2.py": "4b8690b415218b357f02251023c164ea6ab435455a38f8fafbe616036ab58571",
    V2 / "source_snapshot/validate_contextual_target_f1_hc3_incremental_rank_v2.py": "4adfe014e524c0a4fa8ebe754d3ed237c1594f5443af591809d664a30a452640",
    V2 / "source_snapshot/finalize_contextual_target_f1_hc3_incremental_rank_v2.py": "184283b702c750b882f360a33bd9aa495125c54d6c68cc30c9e2f9efc0161fea",
    UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin": "1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056",
    UP / "F1_NUISANCE_COLUMN_SCHEMA.json": "9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7",
}


def file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def tolerance(n: int) -> float:
    return float(100 * n * EPS)


def svd_rank_detail(x: np.ndarray) -> dict:
    x = np.asarray(x, np.float64)
    singular = np.linalg.svd(x, compute_uv=False)
    tau = float(max(x.shape) * EPS * singular[0]) if singular.size else 0.0
    rank = int(np.sum(singular > tau))
    return {"rank": rank, "tau": tau, "singular_values": singular, "shape": x.shape}


def svd_geometry(x: np.ndarray) -> dict:
    x = np.asarray(x, np.float64)
    u, singular, _ = np.linalg.svd(x, full_matrices=False)
    tau = float(max(x.shape) * EPS * singular[0]) if singular.size else 0.0
    rank = int(np.sum(singular > tau))
    leverage = np.sum(u[:, :rank] ** 2, axis=1)
    return {"rank": rank, "tau": tau, "singular_values": singular, "leverage": leverage}


def qr_geometry(x: np.ndarray) -> dict:
    """Test/cross-check route; conclusion-bearing production leverage is SVD."""
    x = np.asarray(x, np.float64)
    _, r, piv = linalg.qr(x, mode="economic", pivoting=True)
    diag = np.abs(np.diag(r))
    tau = float(max(x.shape) * EPS * diag[0]) if diag.size else 0.0
    rank = int(np.sum(diag > tau))
    qrank = linalg.qr(x[:, piv[:rank]], mode="economic")[0][:, :rank]
    return {"rank": rank, "tau": tau, "r_diagonal": diag, "leverage": np.sum(qrank * qrank, axis=1)}


def frontier_identities() -> list[tuple[int, int, int]]:
    return list(product(range(7), range(2), range(5)))


def classify_geometry(full_column_rank: bool, df: int, finite: bool, loo_stable: bool, hc3_estimable: bool):
    reasons = []
    if not full_column_rank:
        reasons.append("RANK_DEFICIENT")
    if df <= 0:
        reasons.append("NONPOSITIVE_DF")
    if not finite:
        reasons.append("NONFINITE_GEOMETRY")
    if not loo_stable:
        reasons.append("NONREPLICATED_NUISANCE_DIRECTION")
    if not hc3_estimable:
        reasons.append("HC3_LEVERAGE_BOUNDARY")
    admissible = full_column_rank and df > 0 and finite and loo_stable and hc3_estimable
    return (["PASS_DONOR_REPLICATED_HC3"] if admissible else reasons), bool(admissible)


def select_design(columns: dict[str, np.ndarray], names) -> tuple[np.ndarray, list[str]]:
    x = np.ones((len(next(iter(columns.values()))), 1), np.float64)
    kept = []
    for name in sorted(names):
        v = np.asarray(columns[name], np.float64)
        candidate = np.column_stack((x, v - v.mean()))
        if svd_rank_detail(candidate)["rank"] > svd_rank_detail(x)["rank"]:
            x = candidate
            kept.append(name)
    return x, kept


def orient_svd(u: np.ndarray, vt: np.ndarray):
    u, vt = u.copy(), vt.copy()
    for j in range(vt.shape[0]):
        max_index = int(np.flatnonzero(np.abs(vt[j]) == np.max(np.abs(vt[j])))[0])
        if vt[j, max_index] < 0:
            u[:, j] *= -1
            vt[j] *= -1
    return u, vt


def design_record(x, donor_ids, source_ids, identity):
    n, p = x.shape
    tol = tolerance(n)
    sg = svd_geometry(x)
    qg = qr_geometry(x)
    if sg["rank"] != qg["rank"]:
        raise RuntimeError("STOP_F1_HC3_15A4_RANK_METHOD_DISAGREEMENT")
    h, hq, rank = sg["leverage"], qg["leverage"], sg["rank"]
    hdiff = float(np.max(np.abs(h - hq)))
    if hdiff > tol:
        raise RuntimeError("STOP_F1_HC3_15A4_LEVERAGE_METHOD_MISMATCH")
    finite = bool(np.isfinite(h).all())
    invariants = finite and float(h.min()) >= -tol and float(h.max()) <= 1 + tol and abs(float(h.sum()) - rank) <= tol
    if not invariants:
        raise RuntimeError("STOP_F1_HC3_15A4_LEVERAGE_METHOD_MISMATCH")
    losses = [rank - svd_rank_detail(np.delete(x, i, axis=0))["rank"] for i in range(n)]
    critical = [str(donor_ids[i]) for i, loss in enumerate(losses) if loss != 0]
    full = rank == p
    df = n - rank
    hc3 = bool(full and df > 0 and finite and np.min(1 - h) > HC3_BOUNDARY)
    reasons, admissible = classify_geometry(full, df, finite, len(critical) == 0, hc3)
    singular = sg["singular_values"]
    out = {
        "r_HVS": identity[0], "r_NPH52": identity[1], "r_SEAAD": identity[2],
        "constructed_columns": p, "numerical_rank": rank, "full_column_rank": full,
        "df": df, "n_over_rank": n / rank, "condition_number": float(singular[0] / singular[rank - 1]),
        "smallest_retained_singular_value": float(singular[rank - 1]),
        "max_leverage_svd": float(h.max()), "max_leverage_donor": str(donor_ids[int(np.argmax(h))]),
        "max_leverage_HVS": float(h[source_ids == "HVS"].max()),
        "max_leverage_NPH52": float(h[source_ids == "NPH52"].max()),
        "max_leverage_SEA_AD": float(h[source_ids == "SEA_AD"].max()),
        "min_one_minus_h": float(np.min(1 - h)), "sum_leverage": float(h.sum()),
        "h_svd_vs_qr_max_abs": hdiff, "hc3_estimable_under_frozen_rule": hc3,
        "loo_rank_stable": not critical, "worst_loo_rank_loss": int(max(losses)),
        "count_loo_critical_donors": len(critical), "loo_critical_donor_ids": "|".join(critical),
        "donor_replicated_hc3_admissible": admissible, "reason_codes": "|".join(reasons),
    }
    return out, losses, h, hq


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path, rows):
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", type=Path, required=True); args = ap.parse_args()
    out = args.out; out.mkdir(parents=True, exist_ok=False)
    actual = {str(p.relative_to(ROOT)).replace("\\", "/"): file_sha256(p) for p in EXPECTED}
    if any(file_sha256(path) != expected for path, expected in EXPECTED.items()):
        raise RuntimeError("STOP_F1_HC3_15A4_AUTHORITY_MISMATCH")
    schema = json.loads((UP / "F1_NUISANCE_COLUMN_SCHEMA.json").read_text())
    upstream = json.loads((UP / "F1_NUISANCE_DONOR_DESIGN_AUTHORITY.json").read_text())
    if upstream["semantic_root_sha256"] != "2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec":
        raise RuntimeError("STOP_F1_HC3_15A4_AUTHORITY_MISMATCH")
    matrix = np.fromfile(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin", dtype="<f8").reshape(104, 49)
    names = schema["columns"]; columns = {name: matrix[:, i] for i, name in enumerate(names)}
    donors = np.asarray(schema["donor_order"]); sources = np.asarray([d.split("::", 1)[0] for d in donors])
    base, base_kept = select_design(columns, SOURCE_COLUMNS + CONTINUOUS_COLUMNS)
    base_row, _, _, _ = design_record(base, donors, sources, (0, 0, 0))
    operator = matrix[:, [names.index(f"operator_mix_{i:03d}") for i in range(42)]]
    qbase = np.linalg.svd(base, full_matrices=False)[0][:, :7]
    local_ranks, incremental_ranks, score_blocks, local_singular = {}, {}, {}, {}
    for source, op_ids in BLOCKS.items():
        embedded = np.zeros((104, len(op_ids))); mask = sources == source; embedded[mask] = operator[mask][:, op_ids]
        incremental = svd_rank_detail(np.column_stack((base, embedded)))["rank"] - 7
        residual = embedded - qbase @ (qbase.T @ embedded)
        u, singular, vt = np.linalg.svd(residual, full_matrices=False); u, vt = orient_svd(u, vt)
        local = svd_rank_detail(residual)["rank"]
        x = base.copy(); admitted = []
        for j in range(len(singular)):
            score = u[:, j] * singular[j]
            if svd_rank_detail(np.column_stack((x, score - score.mean())))["rank"] == svd_rank_detail(x)["rank"] + 1 and len(admitted) < incremental:
                x = np.column_stack((x, score - score.mean())); admitted.append(score)
            else:
                break
        local_ranks[source] = local; incremental_ranks[source] = incremental
        score_blocks[source] = np.column_stack(admitted) if admitted else np.empty((104, 0))
        local_singular[source] = singular
    joint_blocks = []
    for source, op_ids in BLOCKS.items():
        embedded = np.zeros((104, len(op_ids))); mask = sources == source; embedded[mask] = operator[mask][:, op_ids]; joint_blocks.append(embedded)
    joint_increment = svd_rank_detail(np.column_stack([base] + joint_blocks))["rank"] - 7
    if (base_row["numerical_rank"], base_row["df"], base_row["loo_rank_stable"], base_row["hc3_estimable_under_frozen_rule"], local_ranks, incremental_ranks, joint_increment) != (7, 97, True, True, {"HVS": 6, "NPH52": 2, "SEA_AD": 4}, {"HVS": 6, "NPH52": 1, "SEA_AD": 4}, 11):
        raise RuntimeError("STOP_F1_HC3_15A4_REPRODUCTION_MISMATCH")
    authority = {"status": "PASS", "input_sha256": actual, "semantic_root": upstream["semantic_root_sha256"],
        "authority_amendment": {"class": "COMMAND_15A3_AUTHORITY_TYPO / PREFIX-STATE-CONFLATION", "mandatory_B_rank": 7, "mandatory_B_df": 97, "B_plus_NPH_C1_rank": 8, "B_plus_NPH_C1_C2_rank": 8},
        "production_leverage": "SVD_COLUMN_SPACE_PROJECTION", "independent_leverage": "PIVOTED_QR_COLUMN_SPACE_PROJECTION", "tolerance": tolerance(104),
        "hc3_boundary": HC3_BOUNDARY, "design_selected_or_frozen": False,
        "firewall": {"expression": False, "model_or_checkpoint": False, "forward_or_outcome": False, "training_or_ema": False}}
    write_json(out / "F1_HC3_15A4_AUTHORITY.json", authority)
    records, loss_map, cross = [], {}, []
    for identity in frontier_identities():
        x = np.column_stack((base, score_blocks["HVS"][:, :identity[0]], score_blocks["NPH52"][:, :identity[1]], score_blocks["SEA_AD"][:, :identity[2]]))
        record, losses, hs, hq = design_record(x, donors, sources, identity)
        records.append(record); loss_map[identity] = losses
        cross.append({"identity": list(identity), "svd_rank": record["numerical_rank"], "qr_rank": qr_geometry(x)["rank"], "max_abs_leverage_difference": record["h_svd_vs_qr_max_abs"], "svd_hc3": record["hc3_estimable_under_frozen_rule"], "qr_hc3": bool(x.shape[1] == qr_geometry(x)["rank"] and len(x)-qr_geometry(x)["rank"] > 0 and np.min(1-hq) > HC3_BOUNDARY), "svd_boundary_donors": [str(donors[i]) for i in np.flatnonzero(1-hs <= HC3_BOUNDARY)], "qr_boundary_donors": [str(donors[i]) for i in np.flatnonzero(1-hq <= HC3_BOUNDARY)]})
    if len(records) != 70 or len({(r["r_HVS"], r["r_NPH52"], r["r_SEAAD"]) for r in records}) != 70:
        raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL")
    write_csv(out / "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv", records)
    prefix = []
    for source, max_r in (("HVS", 6), ("NPH52", 1), ("SEA_AD", 4)):
        for r in range(max_r + 1):
            identity = (r, 0, 0) if source == "HVS" else ((0, r, 0) if source == "NPH52" else (0, 0, r))
            row = next(x for x in records if (x["r_HVS"], x["r_NPH52"], x["r_SEAAD"]) == identity)
            prefix.append({"source": source, "prefix": r, "local_numerical_rank": local_ranks[source], "full_design_incremental_rank": incremental_ranks[source], "numerical_rank": row["numerical_rank"], "hc3_estimable": row["hc3_estimable_under_frozen_rule"], "loo_rank_stable": row["loo_rank_stable"], "donor_replicated_hc3_admissible": row["donor_replicated_hc3_admissible"], "reason_codes": row["reason_codes"]})
    write_csv(out / "F1_HC3_SOURCE_PREFIX_REPLICATION.csv", prefix)
    write_json(out / "F1_HC3_LEVERAGE_SVD_QR_CROSSCHECK.json", {"tolerance": tolerance(104), "rows": cross, "all_70_rank_and_leverage_checks_pass": all(r["svd_rank"] == r["qr_rank"] and r["max_abs_leverage_difference"] <= tolerance(104) and r["svd_hc3"] == r["qr_hc3"] and r["svd_boundary_donors"] == r["qr_boundary_donors"] for r in cross)})
    nph_rows = [r for r in records if r["r_NPH52"] == 1]
    nph_c1 = next(r for r in records if (r["r_HVS"], r["r_NPH52"], r["r_SEAAD"]) == (0, 1, 0))
    nph_indispensable = {"NPH52_C1": "HC3_DONOR_INDISPENSABLE_DIRECTION", "rank": nph_c1["numerical_rank"], "df": nph_c1["df"], "donor": "NPH52::human_NPH_906", "loo_rank_loss": loss_map[(0,1,0)][list(donors).index("NPH52::human_NPH_906")], "h_svd": nph_c1["max_leverage_svd"], "h_qr": float(qr_geometry(np.column_stack((base, score_blocks["NPH52"][:, :1])))["leverage"][list(donors).index("NPH52::human_NPH_906")]), "min_one_minus_h": nph_c1["min_one_minus_h"], "classification": nph_c1["reason_codes"], "all_35_nested_NPH_rows_recomputed": len(nph_rows) == 35, "all_35_nonreplicated_and_hc3_nonestimable_at_same_donor": all((not r["loo_rank_stable"] and not r["hc3_estimable_under_frozen_rule"] and "NPH52::human_NPH_906" in r["loo_critical_donor_ids"]) for r in nph_rows)}
    if not nph_indispensable["all_35_nonreplicated_and_hc3_nonestimable_at_same_donor"]:
        raise RuntimeError("STOP_F1_HC3_15A4_NESTED_GEOMETRY_CONTRADICTION")
    write_json(out / "F1_HC3_NPH52_DONOR_INDISPENSABILITY.json", nph_indispensable)
    free = [r for r in records if r["r_NPH52"] == 0]; admissible = [r for r in free if r["donor_replicated_hc3_admissible"]]
    free_summary = {"nph_free_rows": len(free), "donor_replicated_hc3_admissible_rows": len(admissible), "max_HVS_prefix_among_admissible": max(r["r_HVS"] for r in admissible) if admissible else None, "max_SEA_AD_prefix_among_admissible": max(r["r_SEAAD"] for r in admissible) if admissible else None, "six_zero_four_admissible": next(r["donor_replicated_hc3_admissible"] for r in free if r["r_HVS"] == 6 and r["r_SEAAD"] == 4), "HVS_or_SEA_AD_donor_indispensable_rows": [{"identity": [r["r_HVS"],0,r["r_SEAAD"]], "donors": r["loo_critical_donor_ids"]} for r in free if not r["loo_rank_stable"]], "first_nonreplicated_prefix_by_source": {s: next((r["prefix"] for r in prefix if r["source"] == s and not r["loo_rank_stable"]), None) for s in ("HVS", "SEA_AD")}, "descriptive_only_no_selection": True}
    if len(free) != 35: raise RuntimeError("STOP_PROVENANCE_OR_FIREWALL")
    write_json(out / "F1_HC3_NPH_FREE_FRONTIER_SUMMARY.json", free_summary)
    contract = """# F1 HC3 reusable nuisance admissibility contract

This freezes a cohort-agnostic procedure, not the current cohort's ranks and not a model-selection rule.

For every later lawful donor cohort: (A) rebuild the mandatory nuisance base from that cohort's frozen primitives; (B) recompute source/operator residual spaces; (C) recompute `LOCAL_NUMERICAL_RANK`, `FULL_DESIGN_INCREMENTAL_RANK`, `DONOR_REPLICATED_RANK`, and `HC3_ADMISSIBLE_RANK`; (D) admit a prefix/direction only through the unchanged full-design rank, leave-one-donor-out replication, and HC3 geometry checks. The procedure must not carry forward HVS rank 6, NPH52 rank 1 or 0, SEA-AD rank 4, donor NPH_906, or any current leverage value.

The authoritative numerical rank is computed from the float64 singular values of each actual design matrix X: `tau(X) = max(X.shape) * float64_eps * s_max(X)` and `rank(X) = count(s > tau(X))`. Production leverage is the SVD column-space projection `h_i = sum_j U[i,j]^2` over the retained numerical rank. It must be finite, lie in `[-TOL, 1+TOL]`, and sum to the numerical rank within `TOL`, where `TOL = 100 * n * float64_eps` is recalculated from the current cohort size.

The independent cross-check uses pivoted QR `Q0,R,piv = scipy.linalg.qr(X, mode='economic', pivoting=True)`. QR rank is `count(abs(diag(R)) > max(X.shape) * float64_eps * abs(diag(R))[0])`; an orthonormal basis is rebuilt from `X[:,piv[:rank]]`, and its projection leverage must agree with SVD leverage within `TOL`. Any SVD/QR rank or leverage disagreement is a STOP, not a tuning opportunity.

HC3 is admissible only when constructed columns equal SVD numerical rank, `df=n-rank>0`, all projection invariants hold, every donor deletion preserves rank, and `min(1-h) > sqrt(float64_eps)`. Leverage is never clamped. Normal-equation leverage, pseudoinverse substitution, ridge regularization, donor deletion as repair, and HC0/HC1/HC2 substitution are forbidden.

A `NONREPLICATED_NUISANCE_DIRECTION` in this cohort may become estimable when a larger cohort supplies independent donor replication. A direction estimable here may fail in a larger cohort if new rare operator/source geometry creates a `HC3_DONOR_INDISPENSABLE_DIRECTION`. Measured cohort geometry determines ranks; the algorithm remains frozen. This contract does not authorize automatic model selection.
"""
    (out / "F1_HC3_REUSABLE_NUISANCE_ADMISSIBILITY_CONTRACT.md").write_text(contract, encoding="utf-8")
    print(json.dumps({"status":"DERIVATION_COMPLETE","frontier_rows":len(records),"nph_free_rows":len(free),"admissible_rows":sum(r["donor_replicated_hc3_admissible"] for r in records),"nph_free_admissible":len(admissible)}))


if __name__ == "__main__":
    main()
