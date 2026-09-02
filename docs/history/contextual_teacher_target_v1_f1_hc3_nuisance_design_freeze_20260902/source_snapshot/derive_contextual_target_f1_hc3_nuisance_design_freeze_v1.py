#!/usr/bin/env python3
"""Command 15B: prospectively select and materialize the HC3 nuisance design."""
from __future__ import annotations

import argparse, csv, hashlib, json
from pathlib import Path

import numpy as np
from scipy import linalg

ROOT = Path(__file__).resolve().parents[2]
P15A4 = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902"
UP = ROOT / "outputs/contextual_teacher_target_v1_f1_nuisance_authority_recovery_20260902"
MANIFEST_SHA = "a112bd4907f2c20b4346179264391ceb8d3e9ceee42f7a8bcb1bcd153e4cb09f"
CONTRACT_SHA = "3fc95316ad51205dd758bf93c6425ecfaebe3ed52e2bfacd6f03bb0406d0a4ac"
RAW_MATRIX_SHA = "1d8f837d18cedd8d1b8fd6138d1b25f886b8352c097a4723ca06421573334056"
RAW_SCHEMA_SHA = "9f90c764d0d97b5a10badc03dfcbafc364e0bf40e120a9aed6609e036b5924a7"
EPS = np.finfo(np.float64).eps
BOUNDARY = float(np.sqrt(EPS))
SOURCE_COLUMNS = ("source_HVS", "source_NPH52", "source_SEA_AD")
CONTINUOUS = ("recipient_physical_support", "recipient_depth", "correct_minus_null_visible_depth", "correct_minus_null_measured_zero_rate")
BLOCKS = {"HVS": tuple(range(24)), "NPH52": tuple(range(35, 42)), "SEA_AD": tuple(range(24, 35))}


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(8 << 20), b""):
            h.update(block)
    return h.hexdigest()


def write_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


def write_csv(path: Path, rows) -> None:
    rows = list(rows)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)


def verify_manifest() -> dict[str, str]:
    manifest = P15A4 / "F1_HC3_15A4_MANIFEST.csv"
    if sha256(manifest) != MANIFEST_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
    verified = {}
    with manifest.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    for row in rows:
        path = P15A4 / row["relative_path"]
        if not path.is_file() or path.stat().st_size != int(row["bytes"]) or sha256(path) != row["sha256"]:
            raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
        verified[row["relative_path"]] = row["sha256"]
    return verified


def triple(row) -> tuple[int, int, int]:
    return int(row["r_HVS"]), int(row["r_NPH52"]), int(row["r_SEAAD"])


def admissible(row) -> bool:
    value = row["donor_replicated_hc3_admissible"]
    return value is True or value == "True"


def dominates(a, b) -> bool:
    ta, tb = triple(a), triple(b)
    return all(x >= y for x, y in zip(ta, tb))


def strictly_dominates(a, b) -> bool:
    return dominates(a, b) and triple(a) != triple(b)


def select_unique_componentwise_maximum(rows) -> dict:
    rows = list(rows)
    accepted = [row for row in rows if admissible(row)]
    maximal = [a for a in accepted if not any(strictly_dominates(b, a) for b in accepted)]
    universal = [a for a in accepted if all(dominates(a, b) for b in accepted)]
    if len(maximal) != 1 or len(universal) != 1 or triple(maximal[0]) != triple(universal[0]):
        raise RuntimeError("STOP_F1_HC3_15B_SELECTION_UNRESOLVED")
    return {
        "admissible_count": len(accepted),
        "inadmissible_count": len(rows) - len(accepted),
        "maximal_triples": [triple(x) for x in maximal],
        "universal_maximum_triples": [triple(x) for x in universal],
        "selected_triple": triple(universal[0]),
        "selected_row": universal[0],
        "dominates_every_admissible": True,
    }


def svd_geometry(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=np.float64)
    u, s, _ = np.linalg.svd(x, full_matrices=False)
    tau = float(max(x.shape) * EPS * s[0]) if s.size else 0.0
    rank = int(np.sum(s > tau))
    h = np.sum(u[:, :rank] ** 2, axis=1)
    return {"rank": rank, "tau": tau, "singular_values": s, "leverage": h}


def qr_geometry(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=np.float64)
    _, r, piv = linalg.qr(x, mode="economic", pivoting=True)
    diag = np.abs(np.diag(r))
    tau = float(max(x.shape) * EPS * diag[0]) if diag.size else 0.0
    rank = int(np.sum(diag > tau))
    q = linalg.qr(x[:, piv[:rank]], mode="economic")[0][:, :rank]
    return {"rank": rank, "leverage": np.sum(q * q, axis=1)}


def rank(x: np.ndarray) -> int:
    return svd_geometry(x)["rank"]


def build_base(columns: dict[str, np.ndarray]) -> tuple[np.ndarray, list[str]]:
    x = np.ones((len(next(iter(columns.values()))), 1), dtype=np.float64)
    kept = []
    for name in sorted(SOURCE_COLUMNS + CONTINUOUS):
        v = np.asarray(columns[name], dtype=np.float64)
        candidate = np.column_stack((x, v - v.mean(dtype=np.float64)))
        if rank(candidate) == rank(x) + 1:
            x = candidate; kept.append(name)
    return x, kept


def orient_svd(u: np.ndarray, vt: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    u, vt = u.copy(), vt.copy()
    for j in range(vt.shape[0]):
        i = int(np.flatnonzero(np.abs(vt[j]) == np.max(np.abs(vt[j])))[0])
        if vt[j, i] < 0:
            u[:, j] *= -1; vt[j] *= -1
    return u, vt


def reconstruct_components() -> dict:
    if sha256(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin") != RAW_MATRIX_SHA or sha256(UP / "F1_NUISANCE_COLUMN_SCHEMA.json") != RAW_SCHEMA_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
    schema = json.loads((UP / "F1_NUISANCE_COLUMN_SCHEMA.json").read_text(encoding="utf-8"))
    raw = np.fromfile(UP / "F1_NUISANCE_DONOR_DESIGN_F64LE.bin", dtype="<f8").reshape(104, 49)
    names = schema["columns"]
    columns = {name: raw[:, i] for i, name in enumerate(names)}
    donors = np.asarray(schema["donor_order"])
    sources = np.asarray([d.split("::", 1)[0] for d in donors])
    base, kept = build_base(columns)
    if rank(base) != 7:
        raise RuntimeError("STOP_F1_HC3_15B_SELECTED_DESIGN_GEOMETRY_MISMATCH")
    operator = raw[:, [names.index(f"operator_mix_{i:03d}") for i in range(42)]]
    qbase = np.linalg.svd(base, full_matrices=False)[0][:, :7]
    scores, local, incremental = {}, {}, {}
    for source, ids in BLOCKS.items():
        embedded = np.zeros((104, len(ids)), dtype=np.float64)
        mask = sources == source
        embedded[mask] = operator[mask][:, ids]
        incremental[source] = rank(np.column_stack((base, embedded))) - 7
        residual = embedded - qbase @ (qbase.T @ embedded)
        local[source] = rank(residual)
        u, singular, vt = np.linalg.svd(residual, full_matrices=False)
        u, vt = orient_svd(u, vt)
        x, accepted = base.copy(), []
        for j in range(len(singular)):
            score = u[:, j] * singular[j]
            centered = score - score.mean(dtype=np.float64)
            if rank(np.column_stack((x, centered))) == rank(x) + 1 and len(accepted) < incremental[source]:
                x = np.column_stack((x, centered)); accepted.append(centered)
            else:
                break
        scores[source] = np.column_stack(accepted) if accepted else np.empty((104, 0))
    if local != {"HVS": 6, "NPH52": 2, "SEA_AD": 4} or incremental != {"HVS": 6, "NPH52": 1, "SEA_AD": 4}:
        raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
    return {"raw": raw, "schema": schema, "donors": donors, "sources": sources, "base": base, "base_kept": kept, "scores": scores, "local": local, "incremental": incremental}


def make_selected_design(parts: dict, selected: tuple[int, int, int]) -> tuple[np.ndarray, list[dict]]:
    blocks = [parts["base"], parts["scores"]["HVS"][:, :selected[0]], parts["scores"]["NPH52"][:, :selected[1]], parts["scores"]["SEA_AD"][:, :selected[2]]]
    x = np.ascontiguousarray(np.column_stack(blocks), dtype=np.float64)
    identities = [{"column_index": 0, "kind": "mandatory", "identity": "intercept"}]
    identities += [{"column_index": i + 1, "kind": "mandatory", "identity": name} for i, name in enumerate(parts["base_kept"])]
    index = len(identities)
    for source, count in zip(("HVS", "NPH52", "SEA_AD"), selected):
        for component in range(1, count + 1):
            identities.append({"column_index": index, "kind": "optional_source_residual_svd_score", "source": source, "component": component, "identity": f"{source}_residual_svd_score_{component:02d}"})
            index += 1
    return x, identities


def selected_geometry(x: np.ndarray, donors: np.ndarray, sources: np.ndarray) -> dict:
    n, p = x.shape; tol = float(100 * n * EPS)
    sg, qg = svd_geometry(x), qr_geometry(x)
    if sg["rank"] != qg["rank"] or np.max(np.abs(sg["leverage"] - qg["leverage"])) > tol:
        raise RuntimeError("STOP_F1_HC3_15B_SELECTED_DESIGN_GEOMETRY_MISMATCH")
    h, r = sg["leverage"], sg["rank"]
    losses = [r - rank(np.delete(x, i, axis=0)) for i in range(n)]
    critical = [str(donors[i]) for i, loss in enumerate(losses) if loss != 0]
    finite = bool(np.isfinite(x).all() and np.isfinite(h).all() and np.isfinite(sg["singular_values"]).all())
    hc3 = bool(r == p and n-r > 0 and finite and np.min(1-h) > BOUNDARY)
    source_max = {source: float(np.max(h[sources == source])) for source in sorted(set(sources))}
    return {
        "shape": [n, p], "constructed_columns": p, "numerical_rank": r, "df": n-r,
        "n_over_rank": float(n/r), "rank_tolerance": sg["tau"],
        "condition_number": float(sg["singular_values"][0] / sg["singular_values"][r-1]),
        "singular_values": [float(v) for v in sg["singular_values"]],
        "all_finite": finite, "max_leverage": float(np.max(h)),
        "max_leverage_donor": str(donors[int(np.argmax(h))]), "max_leverage_by_source": source_max,
        "min_one_minus_h": float(np.min(1-h)), "sum_leverage": float(np.sum(h)),
        "sum_leverage_minus_rank": float(np.sum(h)-r), "svd_qr_max_abs_leverage_difference": float(np.max(np.abs(h-qg["leverage"]))),
        "loo_rank_losses": [{"donor_id": str(d), "rank_loss": int(loss)} for d, loss in zip(donors, losses)],
        "loo_rank_stable": not critical, "loo_critical_donors": critical,
        "hc3_estimable": hc3, "hc3_boundary": BOUNDARY,
        "conventional_2k_over_n_report_only": float(2*p/n), "conventional_3k_over_n_report_only": float(3*p/n),
        "count_leverage_above_2k_over_n_report_only": int(np.sum(h > 2*p/n)),
        "count_leverage_above_3k_over_n_report_only": int(np.sum(h > 3*p/n)),
    }


def hc3_fit(x: np.ndarray, y: np.ndarray) -> dict:
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    q, r = linalg.qr(x, mode="economic")
    beta = linalg.solve_triangular(r, q.T @ y)
    fitted = x @ beta; residual = y - fitted
    h = np.sum(q*q, axis=1)
    adjusted = residual / (1-h)
    xpinv = linalg.solve_triangular(r, q.T)
    covariance = (xpinv * adjusted[None, :]) @ (xpinv * adjusted[None, :]).T
    return {"beta": beta, "fitted": fitted, "leverage": h, "covariance": covariance, "se": np.sqrt(np.diag(covariance))}


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("--staging", type=Path, required=True); args = ap.parse_args()
    out = args.staging.resolve()
    contract = out / "F1_HC3_15B_SELECTION_CONTRACT.md"
    if not out.is_dir() or not contract.is_file() or sha256(contract) != CONTRACT_SHA:
        raise RuntimeError("STOP_F1_HC3_15B_PROSPECTIVE_ORDER_VIOLATION")
    verified = verify_manifest()
    authority15a4 = json.loads((P15A4 / "F1_HC3_15A4_AUTHORITY.json").read_text(encoding="utf-8"))
    validation15a4 = json.loads((P15A4 / "F1_HC3_15A4_INDEPENDENT_VALIDATION.json").read_text(encoding="utf-8"))
    terminal15a4 = json.loads((P15A4 / "F1_HC3_15A4_TERMINAL_STATUS.json").read_text(encoding="utf-8"))
    with (P15A4 / "F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv").open(newline="", encoding="utf-8") as handle:
        frontier = list(csv.DictReader(handle))
    if len(frontier) != 70 or sum(int(r["r_NPH52"]) == 0 for r in frontier) != 35 or sum(admissible(r) for r in frontier) != 30 or validation15a4["status"] != "PASS" or authority15a4["design_selected_or_frozen"] or terminal15a4["terminal_status"] != "PASS_F1_HC3_REPLICATION_FRONTIER_COMPLETE_AWAITING_EXTERNAL_REVIEW":
        raise RuntimeError("STOP_F1_HC3_15B_AUTHORITY_MISMATCH")
    choice = select_unique_componentwise_maximum(frontier)
    selected = choice["selected_triple"]
    audit = []
    for row in frontier:
        t = triple(row)
        audit.append({"r_HVS": t[0], "r_NPH52": t[1], "r_SEAAD": t[2], "admissible": admissible(row), "strictly_dominated_by_selected": bool(admissible(row) and t != selected and all(a >= b for a,b in zip(selected,t))), "is_pareto_maximal_admissible": t in choice["maximal_triples"], "is_universal_maximum": t in choice["universal_maximum_triples"], "reason_codes": row["reason_codes"], "loo_critical_donor_ids": row["loo_critical_donor_ids"]})
    write_csv(out / "F1_HC3_15B_DOMINANCE_AUDIT.csv", audit)
    immediate = [tuple(max(0, v-(i==j)) for i,v in enumerate(selected)) for j in range(3) if selected[j] > 0]
    excluded = [row for row in frontier if not admissible(row) and any(triple(row)[j] > selected[j] for j in range(3))]
    selected_json = {k:v for k,v in choice.items() if k != "selected_row"}
    selected_json.update({"selected_triple": list(selected), "selection_contract_sha256": CONTRACT_SHA, "immediate_predecessor_prefixes": [list(x) for x in immediate], "excluded_increment_reasons": [{"triple": list(triple(r)), "reason_codes": r["reason_codes"], "critical_donors": r["loo_critical_donor_ids"]} for r in excluded]})
    write_json(out / "F1_HC3_SELECTED_TRIPLE.json", selected_json)
    parts = reconstruct_components(); x, identities = make_selected_design(parts, selected)
    x.astype("<f8", copy=False).tofile(out / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin")
    design_sha = sha256(out / "F1_HC3_SELECTED_DONOR_DESIGN_F64LE.bin")
    schema = {"shape": list(x.shape), "dtype": "float64", "byte_order": "little-endian", "layout": "row-major C", "donor_order": parts["donors"].tolist(), "selected_triple": list(selected), "columns": identities, "reconstruction": {"raw_design_sha256": RAW_MATRIX_SHA, "raw_schema_sha256": RAW_SCHEMA_SHA, "frontier_manifest_sha256": MANIFEST_SHA, "selection_contract_sha256": CONTRACT_SHA}, "selected_design_sha256": design_sha}
    write_json(out / "F1_HC3_SELECTED_DONOR_DESIGN_SCHEMA.json", schema)
    geometry = selected_geometry(x, parts["donors"], parts["sources"])
    optional = x[:, 7:]
    transform = np.eye(optional.shape[1]); transform[0, -1] = 0.25; transform[-1, 0] = -0.125
    transformed = np.column_stack((x[:, :7], optional @ transform))
    transformed_h = svd_geometry(transformed)["leverage"]
    geometry["invertible_reparameterization_hat_max_abs_difference"] = float(np.max(np.abs(svd_geometry(x)["leverage"]-transformed_h)))
    geometry["invertible_reparameterization_hat_invariant"] = geometry["invertible_reparameterization_hat_max_abs_difference"] <= float(100*104*EPS)
    if not (geometry["constructed_columns"] == geometry["numerical_rank"] and geometry["df"] > 0 and geometry["all_finite"] and geometry["loo_rank_stable"] and geometry["hc3_estimable"] and geometry["invertible_reparameterization_hat_invariant"]):
        raise RuntimeError("STOP_F1_HC3_15B_SELECTED_DESIGN_GEOMETRY_MISMATCH")
    write_json(out / "F1_HC3_SELECTED_GEOMETRY.json", geometry)
    prefix_rows = list(csv.DictReader((P15A4 / "F1_HC3_SOURCE_PREFIX_REPLICATION.csv").open(newline="", encoding="utf-8")))
    interpretation = {}
    for source, value in zip(("HVS", "NPH52", "SEA_AD"), selected):
        rows = [r for r in prefix_rows if r["source"] == source]
        next_row = next((r for r in rows if int(r["prefix"]) == value + 1), None)
        interpretation[source] = {"local_numerical_rank": int(rows[0]["local_numerical_rank"]), "full_design_incremental_rank": int(rows[0]["full_design_incremental_rank"]), "selected_prefix_rank": value, "donor_replicated_hc3_admissible_retained_rank": value, "next_excluded_component": value+1 if next_row else None, "next_exclusion_reason": next_row["reason_codes"] if next_row and next_row["donor_replicated_hc3_admissible"] != "True" else None, "critical_donors": next((r["loo_critical_donor_ids"] for r in frontier if triple(r) == ((value+1,0,0) if source=="HVS" else ((0,value+1,0) if source=="NPH52" else (0,0,value+1)))), "") if next_row else ""}
    interpretation["semantic_guard"] = {"excluded_direction_language": "NONREPLICATED_NUISANCE_DIRECTION / HC3_DONOR_INDISPENSABLE_DIRECTION", "source_or_biology_excluded": False, "mandatory_source_adjustment_retained_in_B": True, "current_cohort_rank_is_future_constant": False}
    write_json(out / "F1_HC3_SELECTED_SOURCE_INTERPRETATION.json", interpretation)
    ys = [np.sin(np.arange(104)/7.0), np.cos(np.arange(104)/11.0) + np.arange(104)/104.0]
    runs = [hc3_fit(x, y) for y in ys]; replay = [hc3_fit(x, y) for y in ys]
    engine = {"synthetic_only": True, "all_finite": all(np.isfinite(v).all() for run in runs for v in (run["beta"],run["covariance"],run["se"])), "deterministic_replay_exact": all(np.array_equal(a[key],b[key]) for a,b in zip(runs,replay) for key in ("beta","fitted","leverage","covariance","se")), "optional_basis_fitted_invariance_max_abs": float(max(np.max(np.abs(hc3_fit(transformed,y)["fitted"]-run["fitted"])) for y,run in zip(ys,runs))), "optional_basis_leverage_invariance_max_abs": float(np.max(np.abs(svd_geometry(x)["leverage"]-transformed_h)))}
    nph_bad = np.column_stack((x, parts["scores"]["NPH52"][:, :1]))
    bad_geometry = selected_geometry(nph_bad, parts["donors"], parts["sources"])
    engine.update({"known_donor_indispensable_direction": "NPH52_residual_svd_score_01", "known_direction_hc3_estimable": bad_geometry["hc3_estimable"], "known_direction_loo_rank_stable": bad_geometry["loo_rank_stable"], "known_direction_critical_donors": bad_geometry["loo_critical_donors"], "known_direction_recreates_fail_closed": (not bad_geometry["hc3_estimable"] and not bad_geometry["loo_rank_stable"] and "NPH52::human_NPH_906" in bad_geometry["loo_critical_donors"]), "synthetic_se_not_used_for_selection": True})
    if not all((engine["all_finite"], engine["deterministic_replay_exact"], engine["optional_basis_fitted_invariance_max_abs"] <= 1e-10, engine["optional_basis_leverage_invariance_max_abs"] <= float(100*104*EPS), engine["known_direction_recreates_fail_closed"])):
        raise RuntimeError("STOP_F1_HC3_15B_SELECTED_DESIGN_GEOMETRY_MISMATCH")
    write_json(out / "F1_HC3_SELECTED_SYNTHETIC_ENGINE_CHECK.json", engine)
    authority = {"status":"PASS", "selection_contract_sha256":CONTRACT_SHA, "selection_contract_frozen_before_application":True, "selection_contract_created_utc":"2026-09-02T16:51:16Z", "selection_application_started_after_utc":"2026-09-02T16:51:18Z", "15A4_manifest_sha256":MANIFEST_SHA, "15A4_manifest_entries_verified":len(verified), "selected_design_sha256":design_sha, "current_F1_104_design_authority":{"selected_triple":list(selected),"design_sha256":design_sha}, "reusable_larger_cohort_procedure":{"contract_sha256":sha256(P15A4 / "F1_HC3_REUSABLE_NUISANCE_ADMISSIBILITY_CONTRACT.md"),"current_values_must_not_transfer":True}, "firewall":{"expression":False,"model_or_checkpoint":False,"forward_or_outcome":False,"training_or_ema":False}, "production_f1_engine_patched":False, "f1_evaluation_run":False}
    write_json(out / "F1_HC3_15B_AUTHORITY.json", authority)
    print(json.dumps({"status":"DERIVATION_COMPLETE","selected_triple":selected,"selected_design_sha256":design_sha,"rank":geometry["numerical_rank"],"df":geometry["df"]}))


if __name__ == "__main__":
    main()
