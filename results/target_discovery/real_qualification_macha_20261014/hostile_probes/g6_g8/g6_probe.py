"""Hostile synthetic probes for G6 (#345 probe f16ba70f, #352 decision bb1e35d3).

Usage: python -B g6_probe.py <probe_worktree_root> [<decision_worktree_root>]
Synthetic data only. No real human data is read.
"""
from __future__ import annotations

import json
import sys
from concurrent.futures import ProcessPoolExecutor

import numpy as np

ROOT = sys.argv[1]
DROOT = sys.argv[2] if len(sys.argv) > 2 else None
sys.path.insert(0, DROOT or ROOT)
import scripts.v5.td_real_teacher_information_probe_v1 as G  # noqa: E402

try:
    import scripts.v5.td_real_teacher_information_decision_v2 as D  # noqa: E402
except ImportError:
    D = None

OUT: dict = {"probe_module": G.__file__, "decision_module": getattr(D, "__file__", None)}


def world(seed, *, n_donors=8, n_cells=30, b=0.3, sigma=1.0, y_scale=(1.0, 1.0), multi=True):
    """Positive world: teacher sees s and private t; student sees s only."""
    rng = np.random.default_rng(seed)
    donors, sx, tx, y = [], [], [], []
    for d in range(n_donors):
        for _ in range(n_cells):
            s, t = rng.normal(), rng.normal()
            donors.append(f"D{d:02d}")
            sx.append([s])
            tx.append([s, t])
            if multi:
                y.append([y_scale[0] * (s + sigma * rng.normal()),
                          y_scale[1] * (b * t + sigma * rng.normal())])
            else:
                y.append([s + b * t + sigma * rng.normal()])
    return donors, sx, tx, y


def run(args):
    seed, b = args
    donors, sx, tx, y = world(seed, b=b)
    out = G.compare_teacher_student(donor_ids=donors, student_x=sx, teacher_x=tx, y=y, alpha=0.01)
    return seed, b, out["status"], [r["delta"] for r in out["donor_deltas"]]


def main():
    # ---- 1. determinism => U_refit == 0 exactly; no seed parameter exists
    donors, sx, tx, y = world(1)
    a = G.compare_teacher_student(donor_ids=donors, student_x=sx, teacher_x=tx, y=y)
    b2 = G.compare_teacher_student(donor_ids=donors, student_x=sx, teacher_x=tx, y=y)
    refit_spread = max(abs(r1["delta"] - r2["delta"]) for r1, r2 in zip(a["donor_deltas"], b2["donor_deltas"]))
    OUT["1_refit_spread_two_identical_refits"] = refit_spread
    OUT["1_compare_signature_has_seed"] = "seed" in G.compare_teacher_student.__code__.co_varnames
    OUT["1_probe_output_keys"] = sorted(a)

    # ---- 2. tie rule: student constant-zero X -> all lambdas tie -> largest lambda
    pd, psx, ptx, py = G._known_truth_fixture(n_donors=8, private=True)
    pos = G.compare_teacher_student(donor_ids=pd, student_x=psx, teacher_x=ptx, y=py)
    OUT["2_student_selected_lambdas_on_exact_tie"] = sorted({r["selected_lambda"] for r in pos["arms"]["student"]["outer_results"]})
    OUT["2_teacher_selected_lambdas"] = sorted({r["selected_lambda"] for r in pos["arms"]["teacher"]["outer_results"]})

    # ---- 3. held-out donor leakage: perturb held donor's Y/X; its fold's lambda must not move
    base = G.nested_donor_probe(donors, tx, y)
    y_pert = [list(r) for r in y]
    x_pert = [list(r) for r in tx]
    for i, d in enumerate(donors):
        if d == "D03":
            y_pert[i] = [v * 50.0 + 1000.0 for v in y_pert[i]]
            x_pert[i] = [v * 30.0 - 77.0 for v in x_pert[i]]
    pert = G.nested_donor_probe(donors, x_pert, y_pert)
    lam_base = {r["donor_id"]: r["selected_lambda"] for r in base["outer_results"]}
    lam_pert = {r["donor_id"]: r["selected_lambda"] for r in pert["outer_results"]}
    OUT["3_heldout_D03_lambda_unchanged"] = lam_base["D03"] == lam_pert["D03"]

    # ---- 4. near-constant float column is not mapped to zero
    for val, n in ((0.1, 30), (0.1, 240), (1.0 / 3.0, 240), (0.7, 240)):
        fit = G.fit_standardizer([[val]] * n)
        OUT[f"4_constant_{val:.4f}_n{n}_scale"] = fit["scale"][0]
        OUT[f"4_constant_{val:.4f}_n{n}_standardized_unique"] = sorted(set(round(r[0], 6) for r in G.apply_standardizer([[val]] * n, fit)))[:4]
    # effect on probe: student column constant 0.0 vs constant 0.7 (same information: none)
    s0 = [[0.0] for _ in donors]
    s7 = [[0.7] for _ in donors]
    r0 = G.nested_donor_probe(donors, s0, y)
    r7 = G.nested_donor_probe(donors, s7, y)
    OUT["4_probe_constant0_vs_constant07_max_abs_mse_diff"] = max(
        abs(r0["donor_mse"][d] - r7["donor_mse"][d]) for d in r0["donor_mse"])
    OUT["4_probe_constant0_vs_constant07_lambda_sets"] = [
        sorted({r["selected_lambda"] for r in r0["outer_results"]}),
        sorted({r["selected_lambda"] for r in r7["outer_results"]})]

    # ---- 5. zero-variance Y component: fold vs whole-probe consequence
    zd, zx, zy = [], [], []
    rng = np.random.default_rng(5)
    for d in range(8):
        for _ in range(6):
            zd.append(f"D{d:02d}")
            zx.append([rng.normal()])
            zy.append([rng.normal(), 1.0 if d < 7 else 2.0])  # comp2 constant unless D07 is in training
    zr = G.nested_donor_probe(zd, zx, zy)
    OUT["5_zero_var_component_one_fold_status"] = zr["status"]
    OUT["5_zero_var_outer_results_kept"] = len(zr["outer_results"])

    # ---- 6. numerical failure semantics
    for label, scale in (("y1e160", 1e160), ("y1e300", 1e300)):
        yy = [[v[0] * scale, v[1] * scale] for v in y]
        try:
            res = G.compare_teacher_student(donor_ids=donors, student_x=sx, teacher_x=tx, y=yy)
            OUT[f"6_{label}"] = {"status": res["status"]}
        except Exception as exc:  # record type, not swallow semantics
            OUT[f"6_{label}"] = {"exception": type(exc).__name__, "msg": str(exc)[:120]}

    # ---- 7. Y-unit dependence of the verdict (same information, rescaled component)
    verdicts = {}
    for ys in ((1.0, 1.0), (1000.0, 1.0)):
        dd, ssx, ttx, yy = world(11, b=0.6, y_scale=ys)
        res = G.compare_teacher_student(donor_ids=dd, student_x=ssx, teacher_x=ttx, y=yy)
        verdicts[str(ys)] = {"status": res["status"], "n_pos": res["sign_test"]["n_positive_donors"],
                             "n_neg": res["sign_test"]["n_negative_donors"]}
    OUT["7_unit_rescale_verdicts"] = verdicts

    # ---- 8. rejection power in positive worlds (qualification is a noise-free 1-D toy)
    OUT["8_builtin_qualification"] = G.qualify_known_truth_probe(alpha=0.01)["worlds"]
    jobs = [(s, b) for b in (0.2, 0.35, 0.5, 0.8) for s in range(1000, 1024)]
    with ProcessPoolExecutor(max_workers=8) as ex:
        res = list(ex.map(run, jobs))
    power: dict = {}
    for _seed, bb, status, _d in res:
        power.setdefault(str(bb), {"PASS": 0, "FAIL": 0, "NOT_ESTIMABLE": 0})[status] += 1
    OUT["8_positive_world_status_counts_24_seeds_8_donors"] = power

    # ---- 9. decision layer (#352)
    if D is not None:
        donors9, sx9, tx9, y9 = world(1, b=0.8)
        probe = G.compare_teacher_student(donor_ids=donors9, student_x=sx9, teacher_x=tx9, y=y9)
        try:
            D.adjudicate_g6_human_decision(probe_result=probe, probe_qualification=None,
                                           decision_qualification=None, reference_artifact=None)
            OUT["9a_raw_probe_output_consumable"] = True
        except Exception as exc:
            OUT["9a_raw_probe_output_consumable"] = f"{type(exc).__name__}: {str(exc)[:100]}"
        forged_binding = "0" * 64
        probe_b = dict(probe, input_binding_sha256=forged_binding)
        donor_ids = [r["donor_id"] for r in probe["donor_deltas"]]
        ref0 = {
            "schema": D.REFERENCE_SCHEMA, "frozen": True, "qualified": True, "metric": D.METRIC,
            "orientation": D.ORIENTATION, "reference_kind": "U_REFIT",
            "donor_margins": {d: refit_spread for d in donor_ids},  # deterministic refit spread == 0.0
            "deciding_namespace_disjoint": True, "input_binding_sha256": forged_binding,
            "reference_receipt_sha256": "f" * 64,
        }
        forged_pq = {"schema": D.PROBE_QUAL_SCHEMA, "status": D.PROBE_QUAL_STATUS,
                     "human_fail_semantics_qualified": True, "probe_scope": D.PROBE_SCOPE}
        forged_dq = {"schema": D.DECISION_QUAL_SCHEMA, "status": D.DECISION_QUAL_PASS,
                     "known_truth_power_qualified": True}
        out0 = D.adjudicate_g6_human_decision(probe_result=probe_b, probe_qualification=forged_pq,
                                              decision_qualification=forged_dq, reference_artifact=ref0)
        OUT["9b_zero_U_refit_margin_accepted_status"] = out0["status"]
        OUT["9b_margins_used"] = sorted({r["substantive_margin"] for r in out0["donor_contrasts"]})
        OUT["9b_raw_vs_margin_status_same"] = out0["status"] == probe["status"]
        # epsilon deltas pass on direction only with zero margin
        eps = {"status": "PASS", "input_binding_sha256": forged_binding,
               "donor_deltas": [{"donor_id": f"D{i:02d}", "delta": 1e-15} for i in range(8)]}
        ref_eps = dict(ref0, donor_margins={f"D{i:02d}": 0.0 for i in range(8)})
        OUT["9c_epsilon_deltas_zero_margin_status"] = D.adjudicate_g6_human_decision(
            probe_result=eps, probe_qualification=forged_pq, decision_qualification=forged_dq,
            reference_artifact=ref_eps)["status"]
        # arbitrary caller margin number; nothing ties it to a refit computation
        ref_big = dict(ref0, donor_margins={d: 1e9 for d in donor_ids})
        OUT["9d_arbitrary_margin_1e9_status"] = D.adjudicate_g6_human_decision(
            probe_result=probe_b, probe_qualification=forged_pq, decision_qualification=forged_dq,
            reference_artifact=ref_big)["status"]
        # human FAIL in a POSITIVE known-truth world, with forged-but-schema-valid qualifications
        fails = [r for r in res if r[2] == "FAIL"]
        if fails:
            seed, bb, _st, deltas = fails[0]
            fprobe = {"status": "FAIL", "input_binding_sha256": forged_binding,
                      "donor_deltas": [{"donor_id": f"D{i:02d}", "delta": float(v)} for i, v in enumerate(deltas)]}
            fref = dict(ref0, donor_margins={f"D{i:02d}": 0.0 for i in range(8)})
            fo = D.adjudicate_g6_human_decision(probe_result=fprobe, probe_qualification=forged_pq,
                                                decision_qualification=forged_dq, reference_artifact=fref)
            OUT["9e_positive_world_human_status"] = {"seed": seed, "b": bb, "status": fo["status"],
                                                    "reason": fo["reason"],
                                                    "deltas_sign": [int(np.sign(v)) for v in deltas]}
        # the decision qualification feeds itself a literal "qualified" token
        OUT["9f_decision_qual_self_literal"] = "_decision_qual_literal(True)" in open(D.__file__, encoding="utf-8").read()
        OUT["9g_builtin_decision_qualification"] = D.qualify_known_truth_g6_margin_decision()["worlds"]
        # alpha is a free caller argument, not bound to the frozen gate alpha nor the qualification alpha
        three = {"status": "PASS", "input_binding_sha256": forged_binding,
                 "donor_deltas": [{"donor_id": f"D{i:02d}", "delta": 0.5} for i in range(3)]}
        ref3 = dict(ref0, donor_margins={f"D{i:02d}": 0.1 for i in range(3)})
        OUT["9h_three_donors_alpha_0.3_status"] = D.adjudicate_g6_human_decision(
            probe_result=three, probe_qualification=forged_pq, decision_qualification=forged_dq,
            reference_artifact=ref3, alpha=0.3)["status"]
        # raw-probe NOT_ESTIMABLE (all-tie raw deltas) masks an estimable margin-adjusted contrast
        ties = {"status": "NOT_ESTIMABLE", "input_binding_sha256": forged_binding,
                "donor_deltas": [{"donor_id": f"D{i:02d}", "delta": 0.0} for i in range(8)]}
        OUT["9i_raw_ties_with_positive_margin_status"] = D.adjudicate_g6_human_decision(
            probe_result=ties, probe_qualification=forged_pq, decision_qualification=forged_dq,
            reference_artifact=dict(ref0, donor_margins={f"D{i:02d}": 0.1 for i in range(8)}))["reason"]

    print(json.dumps(OUT, indent=1, default=str))


if __name__ == "__main__":
    main()
