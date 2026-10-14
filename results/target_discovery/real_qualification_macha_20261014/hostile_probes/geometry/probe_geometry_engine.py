"""Hostile synthetic probes for PR #355 geometry recurrence engine (head 6e5182e2).

Read-only audit. No human data. Run with:
  PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=D:/jepa_rq_geom_20261014 python -B probe_geometry_engine.py
"""
from __future__ import annotations

import itertools
import json
import math

import numpy as np

import scripts.v5.td_real_geometry_recurrence_engine_v1 as G

LOG = []


def log(probe, expect, observed, verdict, note=""):
    rec = {"probe": probe, "expect": expect, "observed": observed, "verdict": verdict, "note": note}
    LOG.append(rec)
    print(json.dumps(rec, default=str))


def qual():
    return {"schema": G.QUAL_SCHEMA, "status": G.QUAL_PASS, "known_truth_power_qualified": True}


def row(donor, source, observed, nulls, status="ESTIMABLE", reason=None, binding="a" * 64, receipt="c" * 64):
    return {
        "source": source, "donor_id": donor,
        "estimability_status": status, "estimability_reason": reason,
        "observed_displacement": observed if status == "ESTIMABLE" else None,
        "null_displacements": nulls if status == "ESTIMABLE" else None,
        "null_semantics": G.NULL_SEMANTICS,
        "null_producer_receipt_sha256": receipt,
        "input_binding_sha256": binding,
    }


def ref(rows, refit, stability, binding="a" * 64, receipt="b" * 64, metric=G.PROJECTOR_METRIC):
    est = [r["donor_id"] for r in rows if r["estimability_status"] == "ESTIMABLE"]
    rf = refit if isinstance(refit, dict) else {d: refit for d in est}
    st = stability if isinstance(stability, dict) else {d: stability for d in est}
    return {
        "schema": G.REFERENCE_SCHEMA, "frozen": True, "qualified": True, "metric": metric,
        "orientation": G.ORIENTATION, "deciding_namespace_disjoint": True,
        "input_binding_sha256": binding, "reference_receipt_sha256": receipt,
        "refit_margins": rf, "stability_margins": st,
    }


def adjudicate(rows, sources, reference, alpha=0.01, metric=G.PROJECTOR_METRIC):
    return G.adjudicate_geometry_recurrence(
        rows=rows, metric=metric, required_sources=sources,
        decision_qualification=qual(), reference_artifact=reference, alpha=alpha,
    )


def rand_orth(rng, p):
    q, r = np.linalg.qr(rng.normal(size=(p, p)))
    return q * np.sign(np.diag(r))


# ---------------------------------------------------------------- end-to-end synthetic world
def world(rng, *, n_donors=12, n_train=12, cells=40, p=6, noise=0.05, recurrent=True):
    """Two disjoint refit 'views' of a learned state. View B = gauge rotation of view A + noise.
    If not recurrent, view B is unrelated per cell (fresh draw)."""
    gauge = rand_orth(rng, p)
    def donor_states():
        a = rng.normal(size=(cells, p)) * np.linspace(2.0, 0.5, p)
        b = (a @ gauge if recurrent else rng.normal(size=(cells, p)) * np.linspace(2.0, 0.5, p) @ gauge)
        return a, b + noise * rng.normal(size=a.shape)
    train = [donor_states() for _ in range(n_train)]
    held = [donor_states() for _ in range(n_donors)]
    return train, held


def pipeline(train, held, rng, *, n_null=100, view_b_transform=None, source="SRC", leak=False):
    """Compose the module's own helpers: train-only Procrustes -> held-out aligned RMS -> within-donor
    identity-shuffle null. Returns adjudicator rows."""
    tb = [b if view_b_transform is None else view_b_transform(b) for _, b in train]
    hb = [b if view_b_transform is None else view_b_transform(b) for _, b in held]
    ta = np.vstack([a for a, _ in train]); tbm = np.vstack(tb)
    ids = [f"T{i}" for i in range(ta.shape[0])]
    rows = []
    for d, ((a, _), b) in enumerate(zip(held, hb)):
        if leak:  # fit on the held-out donor itself, relabelled with fresh IDs
            T = G.fit_train_only_procrustes(train_a=a, train_b=b, train_unit_ids=[f"FAKE{d}_{i}" for i in range(a.shape[0])],
                                            heldout_unit_ids=[f"H{d}"])
        else:
            T = G.fit_train_only_procrustes(train_a=ta, train_b=tbm, train_unit_ids=ids, heldout_unit_ids=[f"H{d}"])
        obs = G.aligned_rms_displacement(a, b, T)
        nulls = []
        for _ in range(n_null):
            perm = rng.permutation(a.shape[0])
            nulls.append(G.aligned_rms_displacement(a, b[perm], T))
        rows.append(row(f"{source}_D{d:02d}", source, obs, nulls))
    return rows


def probe_invariance():
    rng = np.random.default_rng(1)
    train, held = world(rng)
    base = pipeline(train, held, np.random.default_rng(7))
    p = held[0][0].shape[1]
    tfs = {
        "random_orthogonal": (lambda R: (lambda b: b @ R))(rand_orth(np.random.default_rng(3), p)),
        "axis_permutation": (lambda P: (lambda b: b[:, P]))(np.random.default_rng(4).permutation(p)),
        "axis_swap_0_1": (lambda b: b[:, [1, 0] + list(range(2, p))]),
        "single_sign_flip": (lambda b: b * np.r_[-1.0, np.ones(p - 1)]),
    }
    for name, tf in tfs.items():
        out = pipeline(train, held, np.random.default_rng(7), view_b_transform=tf)
        dobs = max(abs(x["observed_displacement"] - y["observed_displacement"]) for x, y in zip(base, out))
        dnull = max(max(abs(u - v) for u, v in zip(x["null_displacements"], y["null_displacements"])) for x, y in zip(base, out))
        log(f"P1_invariance_{name}", "observed/null displacement unchanged", {"max_obs_diff": dobs, "max_null_diff": dnull},
            "OK" if max(dobs, dnull) < 1e-9 else "DEFECT")
    # projector metric: within-subspace invariances
    rng = np.random.default_rng(5)
    A = rng.normal(size=(8, 3))
    Q = rand_orth(rng, 3)
    for name, B in {"basis_rotation": A @ Q, "column_perm": A[:, [2, 0, 1]], "column_sign": A * [-1, 1, -1], "column_scale": A * [5, 0.1, 1]}.items():
        v = G.projector_rms_displacement(A, B)
        log(f"P1_projector_{name}", "0", v, "OK" if v < 1e-9 else "DEFECT")
    # ambient rotation of ONE view's coordinates is NOT absorbed by the projector metric (needs alignment)
    R = rand_orth(rng, 8)
    v = G.projector_rms_displacement(A, R @ A)
    log("P1_projector_one_view_ambient_rotation", "not invariant (needs frozen alignment upstream)", v,
        "DESIGN_NOTE", "adjudicator has no path that composes alignment with projector metric")


def probe_degenerate():
    # (a) constant training states -> zero cross-covariance -> arbitrary rotation, silent
    rng = np.random.default_rng(11)
    p = 3
    R = rand_orth(rng, p)
    ta = np.ones((10, p)); tb = ta @ R
    T = G.fit_train_only_procrustes(train_a=ta, train_b=tb, train_unit_ids=[f"T{i}" for i in range(10)], heldout_unit_ids=["H"])
    ha = rng.normal(size=(20, p)); hb = ha @ R
    d = G.aligned_rms_displacement(ha, hb, T)
    log("P2a_constant_train_states", "raise / NOT_ESTIMABLE (alignment unidentifiable)",
        {"returned_rotation_is_identity": bool(np.allclose(np.asarray(T["rotation"]), np.eye(p))), "heldout_displacement_true_rot_exact": d},
        "DEFECT" if d > 1e-3 else "OK", "silent arbitrary rotation; true exact rotation scored as large displacement")
    # (b) rank-deficient training (train rows span 1 of 3 dims) -> rotation non-unique on complement
    vals = []
    for eps in (0.0, 1e-9, -1e-9, 1e-8):
        rng2 = np.random.default_rng(12)
        t = rng2.normal(size=(30, 1)) @ np.array([[1.0, 0.0, 0.0]])
        t = t + eps * rng2.normal(size=t.shape)
        T = G.fit_train_only_procrustes(train_a=t, train_b=t @ R, train_unit_ids=[f"T{i}" for i in range(30)], heldout_unit_ids=["H"])
        vals.append(G.aligned_rms_displacement(ha, ha @ R, T))
    log("P2b_rank_deficient_train", "raise / NOT_ESTIMABLE", {"heldout_displacement_under_1e-9_perturbations": vals},
        "DEFECT" if max(vals) - min(vals) > 1e-3 or max(vals) > 1e-3 else "OK", "no rank/eigengap guard in fit_train_only_procrustes")
    # (c) repeated (equal) nonzero singular values: polar factor still unique
    t = np.vstack([np.eye(p), -np.eye(p)])
    T = G.fit_train_only_procrustes(train_a=t, train_b=t @ R, train_unit_ids=[f"T{i}" for i in range(2 * p)], heldout_unit_ids=["H"])
    d = G.aligned_rms_displacement(ha, ha @ R, T)
    log("P2c_repeated_full_rank_singular_values", "0 (polar factor unique)", d, "OK" if d < 1e-9 else "DEFECT")
    # (d) per-donor subspace at an eigen-tie: top-1 subspace non-identifiable -> random displacement
    disp = []
    for s in range(20):
        r = np.random.default_rng(100 + s)
        X1 = r.normal(size=(400, 4)) * [2.0, 2.0, 1.0, 0.5]
        X2 = r.normal(size=(400, 4)) * [2.0, 2.0, 1.0, 0.5]
        b1 = np.linalg.svd(X1 - X1.mean(0), full_matrices=False)[2][:1].T
        b2 = np.linalg.svd(X2 - X2.mean(0), full_matrices=False)[2][:1].T
        disp.append(G.projector_rms_displacement(b1, b2))
    log("P2d_eigentie_top1_subspace", "NOT_ESTIMABLE (no eigengap) - engine has no subspace estimator or gap guard",
        {"min": min(disp), "median": float(np.median(disp)), "max": max(disp)}, "DEFECT_IN_SCOPE_GAP",
        "same distribution in both views yet displacement spans ~[0,1]; would read as instability -> spurious FAIL")
    # (e) near-collinear basis accepted
    B = np.array([[1.0, 1.0], [0.0, 1e-9], [0.0, 0.0]])
    try:
        v = G.projector_rms_displacement(B, np.array([[1.0, 1.0], [0.0, 0.0], [0.0, 1e-9]]))
        log("P2e_near_collinear_basis", "raise (ill-conditioned)", v, "DEFECT" if v > 0.5 else "OK",
            "second direction decided by 1e-9 noise; displacement ~0.707")
    except G.GeometryRecurrenceError as e:
        log("P2e_near_collinear_basis", "raise", str(e), "OK")
    # (f) NaN / zero basis
    for name, M in {"nan": np.array([[np.nan], [1.0]]), "zero": np.zeros((3, 1))}.items():
        try:
            G.projector_rms_displacement(M, M)
            log(f"P2f_{name}", "raise", "no raise", "DEFECT")
        except G.GeometryRecurrenceError as e:
            log(f"P2f_{name}", "raise", str(e), "OK")
    # (g) all-zero displacement world (constant states) through adjudicator
    rows = [row(f"D{i}", "S", 0.0, [0.0] * 100) for i in range(10)]
    o0 = adjudicate(rows, ["S"], ref(rows, 0.0, 0.0))
    o1 = adjudicate(rows, ["S"], ref(rows, 0.05, 0.20))
    log("P2g_constant_state_world", "NOT_ESTIMABLE or FAIL, never PASS", {"zero_margins": o0["status"], "positive_margins": o1["status"]},
        "OK" if "PASS" not in (o0["status"], o1["status"]) else "DEFECT")


def probe_imbalance_and_small_donor_null():
    # 3-cell donors: only 3! = 6 distinct within-donor permutations; 100 draws satisfy count check
    rng = np.random.default_rng(21)
    train, held = world(rng, cells=40, noise=0.01)
    held_small = [(a[:3], b[:3]) for a, b in held]
    rows = pipeline(train, held_small, np.random.default_rng(9))
    distinct = [len(set(np.round(r["null_displacements"], 12))) for r in rows]
    out = adjudicate(rows, ["SRC"], ref(rows, 0.0, 0.2))
    log("P3a_three_cell_donors_permutation_null", "NOT_ESTIMABLE (<=6 distinct null values cannot resolve q_0.01)",
        {"distinct_null_values_per_donor": distinct, "status": out["status"], "null_defeat": out["source_details"]["SRC"].get("null_defeat_status")},
        "DEFECT" if out["status"] != "NOT_ESTIMABLE" else "OK",
        "resolution counted in draws (line 331) not distinct permutations; identity perm => q_alpha<=observed")
    # 1-cell donors: null == observed always
    held_one = [(a[:1], b[:1]) for a, b in held]
    rows = pipeline(train, held_one, np.random.default_rng(9))
    out = adjudicate(rows, ["SRC"], ref(rows, 0.01, 0.2))
    log("P3b_one_cell_donors", "NOT_ESTIMABLE", {"status": out["status"], "reason": out["source_details"]["SRC"]["reason"]},
        "DEFECT" if out["status"] == "FAIL" else "OK", "null identical to observed -> forced negative delta -> biological FAIL")
    # source with one donor
    rows = [row("D0", "ONE", 0.1, [0.8] * 100)] + [row(f"E{i}", "BIG", 0.1, [0.8] * 100) for i in range(10)]
    out = adjudicate(rows, ["ONE", "BIG"], ref(rows, 0.05, 0.2))
    log("P3c_source_with_one_donor", "NOT_ESTIMABLE", out["status"], "OK" if out["status"] == "NOT_ESTIMABLE" else "DEFECT")


def probe_support():
    nulls = [0.8 + 0.001 * i for i in range(100)]
    # (a) the PR hostile abstention test passes for the wrong reason (3 null draws)
    rows = [row(f"D{i:02d}", "SEA_AD", 0.10, [0.78, 0.80, 0.82]) for i in range(7)]
    rows += [row("D07", "SEA_AD", None, None, "NOT_ESTIMABLE_STRUCTURAL_SUPPORT", "X"),
             row("D08", "SEA_AD", None, None, "NOT_ESTIMABLE_COLLISION_UNRESOLVED", "Y")]
    out = adjudicate(rows, ["SEA_AD"], ref(rows, 0.05, 0.20))
    log("P4a_pr_hostile_abstention_test_reason", "reason should be donor-sign under-resolution after abstention",
        out["source_details"]["SEA_AD"]["reason"], "TEST_DEFECT" if out["source_details"]["SEA_AD"]["reason"] == "ADVERSE_NULL_RESOLUTION_INSUFFICIENT" else "OK",
        "tests/v5/..._hostile.py:23,46-64 uses 3 null draws, so abstention mechanism is never exercised")
    # (b) selective abstention launders FAIL into PASS
    rows = [row(f"D{i:02d}", "S", 0.10, nulls) for i in range(8)]
    rows += [row(f"F{i:02d}", "S", 0.60, nulls) for i in range(8)]  # unstable donors
    full = adjudicate(rows, ["S"], ref(rows, 0.05, 0.20))
    abst = [r if r["donor_id"].startswith("D") else row(r["donor_id"], "S", None, None, "NOT_ESTIMABLE_STRUCTURAL_SUPPORT", "any free text") for r in rows]
    sel = adjudicate(abst, ["S"], ref(abst, 0.05, 0.20))
    log("P4b_selective_value_dependent_abstention", "abstention bound to frozen support registry; cannot flip FAIL->PASS",
        {"all_donors": full["status"], "failing_donors_abstained": sel["status"]}, "DEFECT" if sel["status"] == "PASS" else "OK",
        "estimability_status/reason are caller-asserted; no support-registry hash; reference roster is rebuilt to match")
    # (c) failing rows from an unlisted source are silently dropped
    rows = [row(f"A{i}", "SEA_AD", 0.1, nulls) for i in range(8)] + [row(f"B{i}", "ROSMAP", 0.9, nulls) for i in range(8)]
    out = adjudicate(rows, ["SEA_AD"], ref(rows, 0.05, 0.20))
    log("P4c_unlisted_source_rows_dropped", "raise (rows outside required_sources) or bind required_sources to registry",
        {"status": out["status"], "ROSMAP_in_output": "ROSMAP" in out["source_status"]}, "DEFECT" if out["status"] == "PASS" else "OK")
    # (d) donor missing in one view at deciding time, reference frozen pre-outcome on full roster -> crash not NOT_ESTIMABLE
    rows = [row(f"D{i}", "S", 0.1, nulls) for i in range(9)]
    frozen_ref = ref(rows, 0.05, 0.20)
    rows[8] = row("D8", "S", None, None, "NOT_ESTIMABLE_STRUCTURAL_SUPPORT", "missing in view B")
    try:
        out = adjudicate(rows, ["S"], frozen_ref)
        log("P4d_support_loss_after_reference_freeze", "NOT_ESTIMABLE for that donor", out["status"], "OK")
    except G.GeometryRecurrenceError as e:
        log("P4d_support_loss_after_reference_freeze", "NOT_ESTIMABLE for that donor", f"raises: {e}", "DESIGN_FAIL_CLOSED",
            "fail-closed; acceptable only if support registry is frozen before reference generation")
    # (e) empty required stratum
    out = adjudicate(rows, ["S", "EMPTY"], ref(rows, 0.05, 0.20))
    log("P4e_empty_required_stratum", "NOT_ESTIMABLE", {"status": out["status"], "EMPTY": out["source_status"]["EMPTY"]},
        "OK" if out["source_status"]["EMPTY"] == "NOT_ESTIMABLE" else "DEFECT")


def probe_null_resolution():
    # (a) estimable stability FAIL masked by one under-resolved null (V1 s6: estimable failure of either is FAIL)
    good = [0.8 + 0.001 * i for i in range(100)]
    rows = [row(f"D{i}", "S", 0.60, good) for i in range(9)]
    rows.append(row("D9", "S", 0.60, good[:99]))
    out = adjudicate(rows, ["S"], ref(rows, 0.05, 0.20))
    log("P5a_stability_fail_masked_by_null_underresolution", "FAIL (stability component estimable and failed)",
        {"status": out["status"], "reason": out["source_details"]["S"]["reason"], "stability_status": out["source_details"]["S"]["stability_status"]},
        "DEFECT" if out["status"] != "FAIL" else "OK", "engine line 331-338 short-circuits before computing stability")
    # (b) float rank in lower_adverse_null_bound
    for alpha, n in ((0.01, 700), (0.07, 100), (0.01, 100), (0.01, 150)):
        vals = list(range(n))
        rank_engine = int(G.lower_adverse_null_bound([float(v) for v in vals], alpha)) + 1
        rank_exact = max(1, math.ceil(round(alpha * n, 9)))
        rank_conformal = max(1, math.floor(alpha * (n + 1) + 1e-12))
        log(f"P5b_quantile_rank_alpha{alpha}_n{n}", "rank=ceil(alpha*n) exact arithmetic",
            {"engine_rank": rank_engine, "exact_ceil_rank": rank_exact, "finite_sample_valid_floor(alpha(n+1))": rank_conformal},
            "DEFECT" if rank_engine != rank_exact else ("CONCERN" if rank_engine > rank_conformal else "OK"))
    # (c) minimum draws: alpha=0.01/3
    log("P5c_min_draws_alpha_0.01/3", "300 (or 299 per SA3 conformal law)", G.adverse_null_minimum_draws(0.01 / 3), "INFO")


def probe_leakage():
    rng = np.random.default_rng(31)
    train, held = world(rng, recurrent=False, noise=0.0, cells=6, p=6)
    clean = pipeline(train, held, np.random.default_rng(5))
    leaky = pipeline(train, held, np.random.default_rng(5), leak=True)
    o_clean = adjudicate(clean, ["SRC"], ref(clean, 0.0, 10.0))
    o_leak = adjudicate(leaky, ["SRC"], ref(leaky, 0.0, 10.0))
    log("P6a_alignment_fit_on_heldout_relabelled", "rejected (heldout used for fit)",
        {"clean_status": o_clean["status"], "leaky_status": o_leak["status"],
         "clean_median_obs": float(np.median([r["observed_displacement"] for r in clean])),
         "leaky_median_obs": float(np.median([r["observed_displacement"] for r in leaky]))},
        "DEFECT" if o_leak["status"] == "PASS" and o_clean["status"] != "PASS" else "CHECK",
        "leak guard is set-disjointness of caller-supplied ID labels; adjudicator never sees transforms")
    # (b) forged non-orthogonal transform accepted by aligned_rms_displacement
    a = rng.normal(size=(10, 3)); b = rng.normal(size=(10, 3))
    M = np.linalg.lstsq(a - a.mean(0), b - b.mean(0), rcond=None)[0]
    forged = {"schema": "JEPA_TD_TRAIN_ONLY_ORTHOGONAL_PROCRUSTES_V1", "n_features": 3, "mean_a": a.mean(0).tolist(),
              "mean_b": b.mean(0).tolist(), "rotation": M.tolist(), "fit_unit_count": 10, "heldout_unit_count": 0,
              "heldout_used_for_fit": False}
    try:
        d = G.aligned_rms_displacement(a, b, forged)
        log("P6b_non_orthogonal_forged_transform", "raise (not orthogonal / no fit receipt)",
            {"accepted": True, "orthogonality_error": float(np.abs(M.T @ M - np.eye(3)).max()), "displacement": d}, "DEFECT")
    except G.GeometryRecurrenceError as e:
        log("P6b_non_orthogonal_forged_transform", "raise", str(e), "OK")


def probe_margins_and_namespaces():
    nulls = [0.8 + 0.001 * i for i in range(100)]
    rows = [row(f"D{i}", "S", 0.25, nulls) for i in range(8)]
    # (a) stability margin smaller than refit margin accepted although m_d = max(U_meas, U_refit) >= U_refit
    out = adjudicate(rows, ["S"], ref(rows, 0.30, 0.20))
    log("P7a_stability_margin_below_refit_margin", "raise (m_d=max(U_meas,U_refit) must be >= U_refit)",
        {"accepted": True, "status": out["status"]}, "DEFECT", "reference carries no separate U_measurement/U_refit; max() unverifiable")
    # (b) U_refit is subtracted
    out_lo = adjudicate(rows, ["S"], ref(rows, 0.50, 1.0))
    out_hi = adjudicate(rows, ["S"], ref(rows, 0.60, 1.0))
    log("P7b_refit_margin_subtracted", "null-defeat PASS at refit .50 (0.8-0.25-0.5>0), FAIL at .60",
        {"refit_0.50": out_lo["source_details"]["S"]["null_defeat_status"], "refit_0.60": out_hi["source_details"]["S"]["null_defeat_status"]},
        "OK" if (out_lo["source_details"]["S"]["null_defeat_status"], out_hi["source_details"]["S"]["null_defeat_status"]) == ("PASS", "FAIL") else "DEFECT")
    # (c) noncompensation across sources
    rows2 = [row(f"A{i}", "A", 0.1, nulls) for i in range(10)] + [row(f"B{i}", "B", 0.5, nulls) for i in range(8)]
    out = adjudicate(rows2, ["A", "B"], ref(rows2, 0.05, 0.20))
    log("P7c_noncompensation", "FAIL", {"status": out["status"], "per_source": out["source_status"]}, "OK" if out["status"] == "FAIL" else "DEFECT")
    # (d) seed namespace disjointness: all identities equal, accepted
    same = "e" * 64
    rows3 = [row(f"D{i}", "S", 0.1, nulls, binding=same, receipt=same) for i in range(8)]
    out = adjudicate(rows3, ["S"], ref(rows3, 0.05, 0.20, binding=same, receipt=same))
    log("P7d_namespace_disjointness_not_enforced", "raise when null/reference/deciding identities coincide",
        {"status": out["status"], "deciding==null==reference identity": True}, "DEFECT" if out["status"] == "PASS" else "OK",
        "only a boolean deciding_namespace_disjoint=True (line 268); no seed namespaces enter the API")
    # (e) self-attested decision qualification
    log("P7e_self_attested_qualification", "require receipt of qualify_known_truth run bound to code hash",
        {"accepted_handmade_dict": G._qualification_valid(qual())}, "DEFECT" if G._qualification_valid(qual()) else "OK")
    # (f) metric identity is a free string
    out = adjudicate(rows, ["S"], ref(rows, 0.05, 1.0, metric="ANYTHING"), metric="ANYTHING")
    log("P7f_metric_is_free_string", "metric bound to frozen per-target definition hash (SA3 s4)", out["status"], "CONCERN")


if __name__ == "__main__":
    probe_invariance()
    probe_degenerate()
    probe_imbalance_and_small_donor_null()
    probe_support()
    probe_null_resolution()
    probe_leakage()
    probe_margins_and_namespaces()
    import os
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "probe_results.jsonl"), "w") as fh:
        for rec in LOG:
            fh.write(json.dumps(rec, default=str) + "\n")
