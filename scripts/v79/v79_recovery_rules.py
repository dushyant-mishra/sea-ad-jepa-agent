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
