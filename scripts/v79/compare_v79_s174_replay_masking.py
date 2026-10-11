#!/usr/bin/env python3
"""Old (V3, unmasked) vs structural-support-masked (V4) exact-S174 replay: machine-readable A-H audit.

DEVELOPMENT ONLY. Descriptive comparison for controller review (PR #286 ruling 6113874774). It decides nothing.

The per-gene nested deltas use exactly the convention of the committed V3 report
V79_S174_REPLAY_PER_GENE_NESTED_DELTAS.json:
- positive delta means the richer model predicts held-out donors better;
- gene-bootstrap of the median, 2000 resamples, one generator seeded 20261011+7000 and shared in the order
  detection A..D, then positive A..D.
The script first recomputes the V3 report from the V3 replay and refuses to run unless it matches exactly. The same
code is then applied to the masked replay.

Mechanical classes are applied identically to old and new, and are labelled descriptive (as in V3; only the operator
ruling was predeclared):
- A-C step: POSITIVE if median > 0 and the bootstrap interval excludes 0 above; NEGATIVE if the interval lies below
  0; otherwise INCLUDES_ZERO.
- D: the replay's own predeclared operator ruling across lambda {0.25, 1, 4}.
- E-G: supported-gene count against the chance reference (binomial q99 = 7 of 50), plus the sign of the mean
  observed-minus-null excess.
- H: every positive lognormal fit finite and no failed fit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

STEPS = [("A_quadratic_depth", "depth_linear", "depth_quad"), ("B_broad_class", "depth_quad", "depth_class"),
         ("C_source", "depth_class", "depth_class_source"),
         ("D_operator_lambda1", "depth_class_source", "depth_class_source_operator")]
PARTS = {"detection": ("per_gene_detection", "mean_logloss", False),
         "positive_lognormal": ("per_gene_positive", "mean_lpd", True)}
BOOT_SEED, BOOT_N = 20261011 + 7000, 2000
CHANCE_Q99 = 7
RATIFIED_V3 = {  # PR #285 ratified answers (docs/agent/V79_ACTIVE_STATE.json, s174_structure_replay.answers)
    "A_depth_quadratic": "SUPPORTED", "B_broad_class": "SUPPORTED", "C_source": "SUPPORTED_detection__WEAK_positive",
    "D_operator": "detection PRIOR_SENSITIVE__UNRESOLVED; positive NOT_SUPPORTED", "E_donor": "SUPPORTED",
    "F_operator_beyond_donor": "residual structure above chance; unresolved as a transferable effect",
    "G_donor_class": "NOT_BROADLY_EARNED__STAYS_OUT", "H_positive_lognormal": "STABLE_DEVELOPMENT_REPRESENTATION"}


def sha(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def gene_deltas(rep: dict, part: str, a: str, b: str, genes=None) -> np.ndarray:
    key_list, metric, higher = PARTS[part]
    out = []
    for g in rep[key_list]:
        if genes is not None and g["gene_position"] not in genes:
            continue
        x, y = g["models"][a][metric], g["models"][b][metric]
        if x is None or y is None or not (np.isfinite(x) and np.isfinite(y)):
            continue
        out.append(y - x if higher else x - y)
    return np.asarray(out, dtype=np.float64)


def describe(d: np.ndarray, rng) -> dict:
    if d.size == 0:
        return {"n_genes": 0}
    boot = np.median(rng.choice(d, size=(BOOT_N, d.size), replace=True), axis=1)
    return dict(n_genes=int(d.size), median=float(np.median(d)), mean=float(d.mean()),
                iqr=[float(np.quantile(d, .25)), float(np.quantile(d, .75))],
                p10_p90=[float(np.quantile(d, .1)), float(np.quantile(d, .9))], fraction_improved=float((d > 0).mean()),
                median_bootstrap_95=[float(x) for x in np.quantile(boot, [0.025, 0.975])])


def nested_deltas(rep: dict) -> dict:
    rng = np.random.default_rng(BOOT_SEED)
    return {part: {name: describe(gene_deltas(rep, part, a, b), rng) for name, a, b in STEPS} for part in PARTS}


def step_class(s: dict) -> str:
    if not s.get("n_genes"):
        return "UNDEFINED"
    lo, hi = s["median_bootstrap_95"]
    if s["median"] > 0 and lo > 0:
        return "POSITIVE"
    if hi < 0:
        return "NEGATIVE"
    return "INCLUDES_ZERO"


def support_class(c: dict) -> dict:
    return {"supported_genes": c["supported_genes"], "eligible_genes": c["eligible_genes"],
            "above_chance_q99": bool(c["supported_genes"] > CHANCE_Q99),
            "mean_excess_sign": (None if c["mean_observed_minus_null_q95"] is None
                                 else ("+" if c["mean_observed_minus_null_q95"] > 0 else "-")),
            "mean_observed_minus_null_q95": c["mean_observed_minus_null_q95"]}


def h_stability(rep: dict) -> dict:
    bad, n = 0, 0
    for g in rep["per_gene_positive"]:
        for model, r in g["models"].items():
            n += 1
            if r["mean_lpd"] is None or not np.isfinite(r["mean_lpd"]):
                bad += 1
        for lam, r in g["operator_penalty_sensitivity"].items():
            n += 1
            if r["mean_lpd"] is None or not np.isfinite(r["mean_lpd"]):
                bad += 1
    return {"positive_model_fits": n, "nonfinite_or_failed": bad, "stable": bad == 0}


def compare(v3_path, v4_path, v3_deltas_path, out_path) -> dict:
    v3 = json.loads(Path(v3_path).read_text(encoding="utf-8"))
    v4 = json.loads(Path(v4_path).read_text(encoding="utf-8"))
    committed = json.loads(Path(v3_deltas_path).read_text(encoding="utf-8"))
    old = nested_deltas(v3)
    if old != committed["parts"]:
        raise SystemExit("STOP: the comparison code does not reproduce the committed V3 per-gene deltas exactly")
    new = nested_deltas(v4)
    if v3["panel_positions_internal"] != v4["panel_positions_internal"] or \
            v3["support_panel_positions_internal"] != v4["support_panel_positions_internal"]:
        raise SystemExit("STOP: the masked replay did not evaluate the same genes")
    for k in ("folds", "seed", "permutations", "models", "ridge", "n_cells", "n_donors", "n_cache_genes"):
        if v3[k] != v4[k]:
            raise SystemExit(f"STOP: replay setting {k} differs")
    affected = set(v4["replay_genes_affected_by_support"])
    affected_support = set(v4["support_genes_affected_by_support"])
    clean = set(v4["panel_positions_internal"]) - affected

    steps = {}
    for part in PARTS:
        steps[part] = {}
        rng_split = np.random.default_rng(BOOT_SEED + 1)
        for name, a, b in STEPS:
            o, n = old[part][name], new[part][name]
            steps[part][name] = {
                "old_v3": o, "masked": n,
                "delta_masked_minus_old": {k: n[k] - o[k] for k in ("median", "mean", "fraction_improved")},
                "old_class": step_class(o), "masked_class": step_class(n),
                "mechanical_class_preserved": step_class(o) == step_class(n),
                "split_by_structural_support": {
                    "old_affected": describe(gene_deltas(v3, part, a, b, affected), rng_split),
                    "old_clean": describe(gene_deltas(v3, part, a, b, clean), rng_split),
                    "masked_affected": describe(gene_deltas(v4, part, a, b, affected), rng_split),
                    "masked_clean": describe(gene_deltas(v4, part, a, b, clean), rng_split)},
            }

    rob = {}
    for part in ("detection", "positive_lognormal"):
        o, n = v3["operator_increment_robustness"][part], v4["operator_increment_robustness"][part]
        rob[part] = {"old_ruling": o["ruling"], "masked_ruling": n["ruling"], "ruling_preserved": o["ruling"] == n["ruling"],
                     "by_lambda": {lam: {"old": o["by_lambda"][lam], "masked": n["by_lambda"][lam],
                                         "median_delta": (None if None in (o["by_lambda"][lam]["median_increment"],
                                                                          n["by_lambda"][lam]["median_increment"])
                                                          else n["by_lambda"][lam]["median_increment"]
                                                          - o["by_lambda"][lam]["median_increment"])}
                                   for lam in o["by_lambda"]}}

    supp = {}
    for part in ("detection", "positive"):
        supp[part] = {}
        for comp in ("donor", "operator", "donor_class_increment"):
            o = support_class(v3["random_effect_support"][part][comp])
            n = support_class(v4["random_effect_support"][part][comp])
            supp[part][comp] = {"old": o, "masked": n,
                                "supported_genes_delta": n["supported_genes"] - o["supported_genes"],
                                "mechanical_class_preserved": (o["above_chance_q99"] == n["above_chance_q99"]
                                                               and o["mean_excess_sign"] == n["mean_excess_sign"])}

    # No nonzero count sits on an unmeasured entry (builder custody check), so the positive cells, and with them every
    # positive-part fit and positive permutation test, should be identical in V3 and the masked replay.
    pos_identical = all({k: n[k] for k in o} == o for o, n in zip(v3["per_gene_positive"], v4["per_gene_positive"]))
    pos_support_identical = all(o["positive"] == n["positive"] for o, n in
                                zip(v3["per_gene_random_effect_support"], v4["per_gene_random_effect_support"]))
    h_old, h_new = h_stability(v3), h_stability(v4)
    questions = {
        "A_quadratic_depth": {"ratified_v3": RATIFIED_V3["A_depth_quadratic"],
                              "detection": steps["detection"]["A_quadratic_depth"]["masked_class"],
                              "positive": steps["positive_lognormal"]["A_quadratic_depth"]["masked_class"],
                              "affected_by_structural_support": True,
                              "mechanical_class_preserved": all(steps[p]["A_quadratic_depth"]["mechanical_class_preserved"] for p in PARTS)},
        "B_broad_class": {"ratified_v3": RATIFIED_V3["B_broad_class"],
                          "detection": steps["detection"]["B_broad_class"]["masked_class"],
                          "positive": steps["positive_lognormal"]["B_broad_class"]["masked_class"],
                          "affected_by_structural_support": True,
                          "mechanical_class_preserved": all(steps[p]["B_broad_class"]["mechanical_class_preserved"] for p in PARTS)},
        "C_source": {"ratified_v3": RATIFIED_V3["C_source"],
                     "detection": steps["detection"]["C_source"]["masked_class"],
                     "positive": steps["positive_lognormal"]["C_source"]["masked_class"],
                     "affected_by_structural_support": True,
                     "mechanical_class_preserved": all(steps[p]["C_source"]["mechanical_class_preserved"] for p in PARTS)},
        "D_operator": {"ratified_v3": RATIFIED_V3["D_operator"],
                       "detection": rob["detection"]["masked_ruling"], "positive": rob["positive_lognormal"]["masked_ruling"],
                       "affected_by_structural_support": True,
                       "mechanical_class_preserved": rob["detection"]["ruling_preserved"] and rob["positive_lognormal"]["ruling_preserved"]},
        "E_donor": {"ratified_v3": RATIFIED_V3["E_donor"], "detection": supp["detection"]["donor"]["masked"],
                    "positive": supp["positive"]["donor"]["masked"], "affected_by_structural_support": bool(affected_support),
                    "mechanical_class_preserved": supp["detection"]["donor"]["mechanical_class_preserved"] and supp["positive"]["donor"]["mechanical_class_preserved"]},
        "F_operator_beyond_donor": {"ratified_v3": RATIFIED_V3["F_operator_beyond_donor"],
                                    "detection": supp["detection"]["operator"]["masked"], "positive": supp["positive"]["operator"]["masked"],
                                    "affected_by_structural_support": bool(affected_support),
                                    "mechanical_class_preserved": supp["detection"]["operator"]["mechanical_class_preserved"] and supp["positive"]["operator"]["mechanical_class_preserved"]},
        "G_donor_class": {"ratified_v3": RATIFIED_V3["G_donor_class"],
                          "detection": supp["detection"]["donor_class_increment"]["masked"],
                          "positive": supp["positive"]["donor_class_increment"]["masked"],
                          "affected_by_structural_support": bool(affected_support),
                          "mechanical_class_preserved": supp["detection"]["donor_class_increment"]["mechanical_class_preserved"] and supp["positive"]["donor_class_increment"]["mechanical_class_preserved"]},
        "H_positive_lognormal": {"ratified_v3": RATIFIED_V3["H_positive_lognormal"], "old": h_old, "masked": h_new,
                                 "affected_by_structural_support": True,
                                 "mechanical_class_preserved": h_old["stable"] == h_new["stable"]},
    }

    obs = {str(g["gene_position"]): g["measured_observations"] for g in v4["per_gene_detection"]}
    ss = v4["structural_support"]
    out = {
        "schema": "V79_S174_REPLAY_MASKING_AUDIT_V1",
        "label": "DESCRIPTIVE_COMPARISON_FOR_CONTROLLER_REVIEW__DECIDES_NOTHING",
        "inputs": {"v3_replay": {"path": str(v3_path), "sha256": sha(v3_path)},
                   "masked_replay": {"path": str(v4_path), "sha256": sha(v4_path)},
                   "v3_committed_deltas": {"path": str(v3_deltas_path), "sha256": sha(v3_deltas_path)}},
        "v3_deltas_reproduced_exactly": True,
        "same_genes_settings_and_seeds": True,
        "positive_part_identical_to_v3": {"per_gene_positive": pos_identical,
                                          "positive_random_effect_support": pos_support_identical,
                                          "reason": ("no nonzero count lies on an unmeasured entry, so masking cannot "
                                                     "change the positive cells")},
        "conventions": __doc__,
        "removed_observations": {
            "replay_panel_entries": ss["entries_in_replay_panel"],
            "replay_panel_unmeasured_entries": ss["entries_unmeasured_in_replay_panel"],
            "replay_panel_fraction_removed": ss["fraction_unmeasured_in_replay_panel"],
            "support_panel_entries": ss["entries_in_support_panel"],
            "support_panel_unmeasured_entries": ss["entries_unmeasured_in_support_panel"],
            "support_panel_fraction_removed": ss["fraction_unmeasured_in_support_panel"],
            "whole_cache_entries": ss["support_record"].get("entries"),
            "whole_cache_unmeasured_entries": ss["support_record"].get("entries_unmeasured"),
            "whole_cache_fraction_removed": ss["support_record"].get("fraction_unmeasured")},
        "replay_genes_affected": sorted(affected), "n_replay_genes_affected": len(affected),
        "support_genes_affected": sorted(affected_support), "n_support_genes_affected": len(affected_support),
        "undefined_estimands": v4["undefined_estimands"],
        "questions_A_to_H": questions,
        "nested_steps": steps, "operator_robustness": rob, "random_effect_support": supp,
        "model_summaries": {"detection": {"old": v3["detection_summary"], "masked": v4["detection_summary"]},
                            "positive_lognormal": {"old": v3["positive_lognormal_summary"],
                                                   "masked": v4["positive_lognormal_summary"]}},
        "measured_observations_per_gene_and_source": obs,
        "decision": "NONE__CONTROLLER_DECIDES_WHETHER_V2_CORE_REMAINS_FROZEN",
    }
    Path(out_path).write_text(json.dumps(out, indent=1, allow_nan=False) + "\n", encoding="utf-8")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("v3_replay")
    ap.add_argument("masked_replay")
    ap.add_argument("v3_deltas")
    ap.add_argument("out")
    ap.add_argument("--masked-deltas-out", default=None, help="also write the masked per-gene nested deltas report")
    a = ap.parse_args()
    res = compare(a.v3_replay, a.masked_replay, a.v3_deltas, a.out)
    if a.masked_deltas_out:
        masked = json.loads(Path(a.masked_replay).read_text(encoding="utf-8"))
        Path(a.masked_deltas_out).write_text(json.dumps({
            "schema": "V79_S174_REPLAY_PER_GENE_NESTED_DELTAS_V1",
            "label": "DESCRIPTIVE_POST_HOC_SUMMARY__NOT_A_PREDECLARED_RULE (only the operator ruling was predeclared)",
            "replay_sha256_source": Path(a.masked_replay).name, "replay_sha256": sha(a.masked_replay),
            "sign": "positive delta = the richer model predicts held-out donors better (detection: lower log loss; positive: higher LPD)",
            "bootstrap": "gene resampling of the median, 2000 resamples, seed 20261011+7000; genes share donors, so intervals are optimistic",
            "parts": nested_deltas(masked)}, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({q: {k: v for k, v in r.items() if k in ("mechanical_class_preserved", "detection", "positive")}
                      for q, r in res["questions_A_to_H"].items()}, indent=1, default=str)[:6000])


if __name__ == "__main__":
    main()
