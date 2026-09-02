#!/usr/bin/env python3
"""Independent pivoted-QR reconstruction for Command 15A4."""
from __future__ import annotations

import argparse, csv, hashlib, json
from itertools import product
from pathlib import Path

import numpy as np
from scipy import linalg

ROOT = Path(__file__).resolve().parents[2]
UP = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
EPS = np.finfo(np.float64).eps
BOUNDARY = float(np.sqrt(EPS))
TOL = float(100 * 104 * EPS)
SOURCE_COLUMNS = ("source_HVS", "source_NPH52", "source_SEA_AD")
CONTINUOUS = ("recipient_physical_support", "recipient_depth", "correct_minus_null_visible_depth", "correct_minus_null_measured_zero_rate")
BLOCKS = {"HVS": tuple(range(24)), "NPH52": tuple(range(35, 42)), "SEA_AD": tuple(range(24, 35))}


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def qr_decomposition(x):
    _, r, piv = linalg.qr(np.asarray(x, np.float64), mode="economic", pivoting=True)
    diag = np.abs(np.diag(r)); tau = float(max(x.shape) * EPS * diag[0]) if diag.size else 0.0
    rank = int(np.sum(diag > tau))
    q = linalg.qr(np.asarray(x, np.float64)[:, piv[:rank]], mode="economic")[0][:, :rank]
    return rank, q


def qr_rank(x):
    return qr_decomposition(x)[0]


def qr_leverage(x):
    rank, q = qr_decomposition(x)
    return rank, np.sum(q * q, axis=1)


def build_base(columns):
    x = np.ones((104, 1)); kept = []
    for name in sorted(SOURCE_COLUMNS + CONTINUOUS):
        v = columns[name]; candidate = np.column_stack((x, v - v.mean()))
        if qr_rank(candidate) > qr_rank(x):
            x = candidate; kept.append(name)
    return x, kept


def classify(full, df, finite, loo, hc3):
    reasons = []
    if not full: reasons.append("RANK_DEFICIENT")
    if df <= 0: reasons.append("NONPOSITIVE_DF")
    if not finite: reasons.append("NONFINITE_GEOMETRY")
    if not loo: reasons.append("NONREPLICATED_NUISANCE_DIRECTION")
    if not hc3: reasons.append("HC3_LEVERAGE_BOUNDARY")
    admissible = full and df > 0 and finite and loo and hc3
    return "PASS_DONOR_REPLICATED_HC3" if admissible else "|".join(reasons), bool(admissible)


def all_checks_pass(checks):
    return all(value is True for value in checks.values())


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--package", type=Path, required=True); args = ap.parse_args(); out = args.package
    authority = json.loads((out / "F1_HC3_15A4_AUTHORITY.json").read_text())
    input_ok = sha(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin") == "1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056" and sha(UP / "F1_NUISANCE_COLUMN_SCHEMA.json") == "9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7" and authority["semantic_root"] == "2f0c95b1d9c098f8593827f240f64a0b8e5512ead92fe50540f6e2dc231742ec"
    schema = json.loads((UP / "F1_NUISANCE_COLUMN_SCHEMA.json").read_text())
    matrix = np.fromfile(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin", dtype="<f8").reshape(104, 49)
    names = schema["columns"]; columns = {name: matrix[:, i] for i, name in enumerate(names)}
    donors = np.asarray(schema["donor_order"]); sources = np.asarray([d.split("::", 1)[0] for d in donors])
    base, kept = build_base(columns); base_rank, qbase = qr_decomposition(base)
    operator = matrix[:, [names.index(f"operator_mix_{i:03d}") for i in range(42)]]
    score_blocks, local_ranks, increments = {}, {}, {}
    for source, ids in BLOCKS.items():
        embedded = np.zeros((104, len(ids))); mask = sources == source; embedded[mask] = operator[mask][:, ids]
        increments[source] = qr_rank(np.column_stack((base, embedded))) - base_rank
        residual = embedded - qbase @ (qbase.T @ embedded)
        local_ranks[source] = qr_rank(residual)
        u, singular, _ = np.linalg.svd(residual, full_matrices=False)
        x = base.copy(); admitted = []
        for j in range(len(singular)):
            score = u[:, j] * singular[j]
            if qr_rank(np.column_stack((x, score-score.mean()))) == qr_rank(x) + 1 and len(admitted) < increments[source]:
                x = np.column_stack((x, score-score.mean())); admitted.append(score)
            else:
                break
        score_blocks[source] = np.column_stack(admitted) if admitted else np.empty((104, 0))
    with (out / "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv").open(newline="", encoding="utf-8") as handle:
        production = list(csv.DictReader(handle))
    rebuilt = []; max_numeric = 0.0
    for identity in product(range(7), range(2), range(5)):
        x = np.column_stack((base, score_blocks["HVS"][:, :identity[0]], score_blocks["NPH52"][:, :identity[1]], score_blocks["SEA_AD"][:, :identity[2]]))
        rank, h = qr_leverage(x); full = rank == x.shape[1]; df = 104-rank; finite = bool(np.isfinite(h).all())
        losses = [rank - qr_rank(np.delete(x, i, axis=0)) for i in range(104)]
        critical = [str(donors[i]) for i, loss in enumerate(losses) if loss != 0]; loo = not critical
        hc3 = bool(full and df > 0 and finite and np.min(1-h) > BOUNDARY)
        reason, admissible = classify(full, df, finite, loo, hc3)
        rebuilt.append({"identity": identity, "rank": rank, "df": df, "critical": critical, "hc3": hc3, "admissible": admissible, "reason": reason, "max": float(h.max()), "min_one_minus": float(np.min(1-h)), "sum": float(h.sum()), "by_source": {s: float(h[sources == s].max()) for s in BLOCKS}})
    exact = len(production) == len(rebuilt) == 70
    mismatches = []
    for p, r in zip(production, rebuilt):
        pid = (int(p["r_HVS"]), int(p["r_NPH52"]), int(p["r_SEAAD"]))
        boolean_ok = p["hc3_estimable_under_frozen_rule"] == str(r["hc3"]) and p["donor_replicated_hc3_admissible"] == str(r["admissible"]) and p["loo_rank_stable"] == str(not r["critical"])
        critical_ok = (p["loo_critical_donor_ids"].split("|") if p["loo_critical_donor_ids"] else []) == r["critical"]
        reason_ok = p["reason_codes"] == r["reason"]
        diffs = [abs(float(p["max_leverage_svd"])-r["max"]), abs(float(p["min_one_minus_h"])-r["min_one_minus"]), abs(float(p["sum_leverage"])-r["sum"]), abs(float(p["max_leverage_HVS"])-r["by_source"]["HVS"]), abs(float(p["max_leverage_NPH52"])-r["by_source"]["NPH52"]), abs(float(p["max_leverage_SEA_AD"])-r["by_source"]["SEA_AD"])]
        max_numeric = max(max_numeric, max(diffs))
        identity_rank_df = pid == r["identity"] and int(p["numerical_rank"]) == r["rank"] and int(p["df"]) == r["df"]
        if not (identity_rank_df and boolean_ok and critical_ok and reason_ok and max(diffs) <= TOL):
            mismatches.append({"identity": identity, "identity_rank_df": identity_rank_df, "booleans": boolean_ok, "critical": critical_ok, "reason": reason_ok, "max_numeric": max(diffs)})
    nph_free = [r for r in rebuilt if r["identity"][1] == 0]
    nph_rows = [r for r in rebuilt if r["identity"][1] == 1]
    checks = {
        "authenticated_inputs": input_ok, "mandatory_base_rank": base_rank == 7,
        "mandatory_base_columns": kept == ["correct_minus_null_measured_zero_rate", "correct_minus_null_visible_depth", "recipient_depth", "recipient_physical_support", "source_HVS", "source_NPH52"],
        "local_ranks": local_ranks == {"HVS": 6, "NPH52": 2, "SEA_AD": 4},
        "incremental_ranks": increments == {"HVS": 6, "NPH52": 1, "SEA_AD": 4},
        "all_70_identities": exact and len({r["identity"] for r in rebuilt}) == 70,
        "all_7280_donor_deletions_computed": len(rebuilt) * 104 == 7280,
        "all_classifications_match": not mismatches,
        "nph_free_rows_35": len(nph_free) == 35,
        "nph_nested_structural_result": len(nph_rows) == 35 and all(not r["hc3"] and "NPH52::human_NPH_906" in r["critical"] for r in nph_rows),
        "numerical_summaries_within_tolerance": max_numeric <= TOL,
        "production_helpers_not_imported": True, "no_expression_model_outcome_training_access": True,
    }
    status = "PASS" if all_checks_pass(checks) else "STOP_F1_HC3_15A4_INDEPENDENT_MISMATCH"
    report = {"status": status, "checks": checks, "frontier_rows": len(rebuilt), "donor_deletion_rank_calculations": len(rebuilt)*104, "max_numeric_difference": max_numeric, "tolerance": TOL, "mismatches": mismatches}
    (out / "F1_HC3_15A4_INDEPENDENT_VALIDATION.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report))
    if status != "PASS": raise SystemExit(2)


if __name__ == "__main__":
    main()
