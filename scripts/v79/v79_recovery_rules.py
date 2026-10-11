#!/usr/bin/env python3
"""V79 recovery pass rules (contract simulation_recovery.criteria), with no sampler dependency so CI can test
them. Imported by run_v79_recovery."""
from __future__ import annotations

import numpy as np
from scipy import stats


def criteria(res: dict) -> dict:
    out = {}
    s1 = res["S1_present"]["components_result"]
    for name, r in res.items():
        cov = [c for x in r["components_result"].values() if x["planted_and_scored"] for c in x["covered"]]
        if cov:
            n = len(cov)
            bound = stats.binom.ppf(0.01, n, 0.9) / n
            out[f"{name}.coverage"] = dict(observed=float(np.mean(cov)), bound=float(bound), n=n,
                                           pass_=bool(np.mean(cov) >= bound))
    s1_cls_q05 = s1["cls"]["across_gene_median_q"][0]
    for name in ("S0_class_absent", "S2_class_permuted", "S3_donor_only", "S4_operator_only"):
        q95 = res[name]["components_result"]["cls"]["across_gene_median_q"][2]
        out[f"{name}.no_invented_class"] = dict(q95=q95, s1_q05=s1_cls_q05, pass_=bool(q95 < s1_cls_q05))
    out["S5_labels_removed.labels_matter"] = dict(
        s5_res_q05=res["S5_labels_removed"]["components_result"]["res"]["across_gene_median_q"][0],
        s1_res_q95=s1["res"]["across_gene_median_q"][2],
        pass_=bool(res["S5_labels_removed"]["components_result"]["res"]["across_gene_median_q"][0]
                   > s1["res"]["across_gene_median_q"][2]))
    diagnosed = {name: r["diagnostics"]["diagnosed"] for name, r in res.items()}
    out["all_fits_diagnosed"] = dict(per_fit=diagnosed, pass_=all(diagnosed.values()))
    return out


def world_failures(fits: dict) -> dict:
    """The frozen suite criteria, attributed to worlds and evaluated on whichever worlds exist so far (for the
    fail-closed family gate). A world fails if it is not diagnosed, if its own planted-component coverage is below
    the binomial bound, or, once S1 exists, if its cross-world control fails (no_invented_class for S0/S2/S3/S4,
    labels_matter for S5). Same tests and thresholds as criteria(); nothing new is decided here."""
    out = {name: [] for name in fits}
    for name, r in fits.items():
        if not r["diagnostics"]["diagnosed"]:
            out[name].append("not_diagnosed")
        cov = [c for x in r["components_result"].values() if x["planted_and_scored"] for c in x["covered"]]
        if cov and np.mean(cov) < stats.binom.ppf(0.01, len(cov), 0.9) / len(cov):
            out[name].append("coverage")
    if "S1_present" in fits:
        s1 = fits["S1_present"]["components_result"]
        for name in ("S0_class_absent", "S2_class_permuted", "S3_donor_only", "S4_operator_only"):
            if name in fits and not (fits[name]["components_result"]["cls"]["across_gene_median_q"][2]
                                     < s1["cls"]["across_gene_median_q"][0]):
                out[name].append("no_invented_class")
        if "S5_labels_removed" in fits and not (
                fits["S5_labels_removed"]["components_result"]["res"]["across_gene_median_q"][0]
                > s1["res"]["across_gene_median_q"][2]):
            out["S5_labels_removed"].append("labels_matter")
    return out


SCENARIOS_REQUIRED = ("S1_present", "S0_class_absent", "S2_class_permuted", "S3_donor_only", "S4_operator_only",
                      "S5_labels_removed")


def combine_parts(recs: list) -> dict:
    """One terminal receipt for a likelihood's suite, or a refusal. Every part must be schema V2, from the same
    likelihood, the same frozen sampler configuration, the same sampler rules and the same code snapshot; every
    required world must be present exactly once. Launch or runtime failures never reach here: a world with no
    part file is reported as missing, not as a statistical failure."""
    problems = []
    if any(r.get("schema") != "V79_SIMULATION_RECOVERY_V2" for r in recs):
        problems.append("a part is not schema V2 (no frozen configuration identity)")
    for key, label in (("likelihood", "likelihoods"), ("code_snapshot", "code snapshots")):
        vals = {r.get(key) for r in recs}
        if len(vals) != 1:
            problems.append(f"parts mix {label}: {sorted(map(str, vals))}")
    for key in ("sampler_config", "sampler_rules"):
        shas = {(r.get(key) or {}).get("sha256") for r in recs}
        if len(shas) != 1 or None in shas:
            problems.append(f"parts mix {key} identities: {sorted(map(str, shas))}")
    if any(str(r.get("code_snapshot", "")).startswith("LIVE_TREE") for r in recs):
        problems.append("a part ran from the live tree, not a snapshot")
    fits = {}
    for r in recs:
        for k, v in r["fits"].items():
            if k in fits:
                problems.append(f"world {k} appears twice")
            fits[k] = v
    missing = sorted(set(SCENARIOS_REQUIRED) - set(fits))
    if problems:
        raise ValueError("refusing to combine: " + "; ".join(problems))
    r0 = recs[0]
    per_fit = {}
    for name, f in fits.items():
        d = f["diagnostics"]
        per_fit[name] = dict(
            scenario=f["scenario"], modification=f["modification"], diagnosed=bool(d["diagnosed"]),
            worst_rhat=d["worst_rhat"], worst_ess=d["worst_ess"],
            worst_bulk_ess=min(v["min_ess_bulk"] for v in d["per_site"].values()),
            worst_tail_ess=min(v["min_ess_tail"] for v in d["per_site"].values()),
            divergences_final=d["divergences"],
            a5_extension_used=any(a.get("extended") for a in d.get("attempts", [])),
            attempts=d.get("attempts", []),
            coverage={c: f"{sum(v['covered'])}/{len(v['covered'])}"
                      for c, v in f["components_result"].items() if v["planted_and_scored"]})
    crit = criteria(fits) if not missing else None
    terminal = ("MISSING_WORLDS" if missing else
                "PASS" if all(v["pass_"] for v in crit.values()) else "FAIL")
    return dict(schema="V79_RECOVERY_SUITE_RECEIPT_V1", likelihood=r0["likelihood"], terminal=terminal,
                code_snapshot=r0["code_snapshot"], sampler_config=r0["sampler_config"],
                sampler_rules=r0["sampler_rules"], missing_worlds=missing, per_fit=per_fit, criteria=crit,
                counts_loaded=any(r.get("counts_loaded") for r in recs), fits=fits)
