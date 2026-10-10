#!/usr/bin/env python3
"""V79 Output B: the identity-scrubbed, synthetic-consumable summary of the diagnosed posteriors.

Reads only the INTERNAL records (results/v79/internal/) and keeps population-level summaries: variance-fraction
posteriors (the across-gene median's 5/50/95% posterior quantiles, and the spread of per-gene posterior medians
across genes as 10/25/50/75/90% quantiles; no gene positions), detection against positive magnitude, donor-class
support, depth and detected-feature components, the nested-Bayesian-bootstrap geometry posteriors, and the
held-out posterior predictive shares. A fit that did not converge contributes its status and no numbers. Every
input must exist (fail closed), and the result must pass v79_firewall.scrub unchanged before it is written.

This is an estimation result, not authorization of any synthetic arm.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import v79_firewall as FW  # noqa: E402

ROOT = HERE.parents[1]
INTERNAL = ROOT / "results/v79/internal"
CONTRACT = ROOT / "docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json"
OUT = ROOT / "results/v79/V79_SYNTHETIC_GEOMETRY_ARTIFACT_V1.json"
INPUTS = {
    "A": "V79_PHASE_A_INTERNAL_V1.json", "B": "V79_PHASE_B_INTERNAL_V1.json", "B0": "V79_PHASE_B0_INTERNAL_V1.json",
    "C": "phase_c/V79_PHASE_C_INTERNAL_V1.json", "C_choice": "phase_c/V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1.json",
    "D1": "d1/V79_PHASE_D1_INTERNAL_V1.json",
    "ppc_A": "ppc/V79_HELDOUT_PPC_A_INTERNAL_V1.json", "ppc_B": "ppc/V79_HELDOUT_PPC_B_INTERNAL_V1.json",
    "ppc_B0": "ppc/V79_HELDOUT_PPC_B0_INTERNAL_V1.json",
    "support_A": "ppc/V79_DONOR_CLASS_SUPPORT_A_INTERNAL_V1.json",
    "support_B": "ppc/V79_DONOR_CLASS_SUPPORT_B_INTERNAL_V1.json",
}
SPREAD_Q = (0.1, 0.25, 0.5, 0.75, 0.9)
LABEL = {"cls": "broad_class", "src": "source", "op": "operator", "donor": "donor", "dk": "donor_class",
         "res": "residual"}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fractions(rec: dict) -> dict:
    """Population summaries of a phase's variance fractions and magnitudes; nothing per gene. Magnitudes: the
    spread across genes of each component's absolute realized variance (posterior medians), and the population
    hyperparameters (m_x: typical per-gene log sd; s_x: its spread across genes), from which a generator can draw
    anonymous per-gene effect sizes."""
    if not rec.get("diagnosed"):
        return dict(status="NOT_CONVERGED", note="estimates exist internally but are not interpreted or exported")
    out = {}
    for comp, f in rec["fractions"].items():
        med = np.asarray(f["per_gene_median"], dtype=np.float64)
        out[LABEL[comp]] = dict(
            across_gene_median_posterior_q05_q50_q95=[float(v) for v in f["across_gene_median_q"]],
            per_gene_median_spread_q10_q25_q50_q75_q90=[float(v) for v in np.quantile(med, SPREAD_Q)])
        if "variance_per_gene_median" in f:
            v = np.asarray(f["variance_per_gene_median"], dtype=np.float64)
            out[LABEL[comp]]["absolute_variance_spread_q10_q25_q50_q75_q90"] = \
                [float(x) for x in np.quantile(v, SPREAD_Q)]
    hyper = {k: v for k, v in (rec.get("hyperparameters") or {}).items()}
    return dict(status="CONVERGED", n_genes_summarised=int(len(med)), fractions=out,
                population_hyperparameters_posterior_q05_q50_q95=hyper)


def responses(rec: dict) -> dict:
    """B0: per named cell-level response (log depth, log detected features), each component's posterior median
    and 90% interval; the responses are cell totals, not genes."""
    if not rec.get("diagnosed"):
        return dict(status="NOT_CONVERGED", note="estimates exist internally but are not interpreted or exported")
    out = {}
    for i, name in enumerate(rec["responses"]):
        out[name] = {LABEL[c]: dict(posterior_median=float(f["per_gene_median"][i]),
                                    q05_q95=[float(f["per_gene_q05"][i]), float(f["per_gene_q95"][i])],
                                    **({} if "variance_per_gene_median" not in f else dict(
                                        absolute_variance_median=float(f["variance_per_gene_median"][i]),
                                        absolute_variance_q05_q95=[float(f["variance_per_gene_q05"][i]),
                                                                   float(f["variance_per_gene_q95"][i])])))
                     for c, f in rec["fractions"].items()}
    return dict(status="CONVERGED", fractions=out)


def build(internal: Path = INTERNAL) -> dict:
    missing = [k for k, v in INPUTS.items() if not (internal / v).exists()]
    if missing:
        raise SystemExit(f"refusing: missing internal inputs {missing}")
    r = {k: json.loads((internal / v).read_text(encoding="utf-8")) for k, v in INPUTS.items()}
    choice = r["C_choice"]
    d1 = {k: {x: v[x] for x in ("point", "q05", "median", "q95", "resampling_shift", "point_inside_bb90")}
          for k, v in r["D1"]["statistics"].items()}
    ppc = {}
    for ph in ("A", "B", "B0"):
        rec = r[f"ppc_{ph}"]
        ppc[ph] = dict(all_folds_converged=bool(rec["all_folds_diagnosed"]),
                       share_inside_90=({k: v["share_inside"] for k, v in rec["pooled_share_inside"].items()}
                                        if rec["all_folds_diagnosed"] else "NOT_CONVERGED"),
                       reading=("a share far below 0.9 marks the model inadequate for that statistic; never tuned"))
    art = dict(
        schema="V79_SYNTHETIC_GEOMETRY_ARTIFACT_V1",
        status="SCRUBBED__ESTIMATION_RESULT__NOT_SYNTHETIC_AUTHORIZATION",
        authority=("corrected S174 TRAIN only; dataset-geometry estimation; non-training; non-promoting; the "
                   "contract's terminal authority applies (bound by hash)"),
        contract_sha256=sha(CONTRACT),
        inputs_sha256={k: sha(internal / v) for k, v in INPUTS.items()},
        variance_fractions=dict(
            A_log1p_cp10k=fractions(r["A"]), B_detection_logit=fractions(r["B"]),
            C_positive_magnitude=dict(family=choice["comparison"]["winner"] if choice["comparison"] else None,
                                      family_rule_result=choice["decision"], **fractions(r["C"])),
            B0_depth_and_detected_features=responses(r["B0"])),
        donor_class_support={ph: dict(**{k: r[f"support_{ph}"]["comparison"][k] for k in
                                         ("mean_difference_per_observation", "donor_clustered_se", "supported",
                                          "rule")},
                                      both_runs_converged=r[f"support_{ph}"]["comparison"]["both_runs_diagnosed"])
                             for ph in ("A", "B")},
        geometry_bayesian_bootstrap=dict(method=r["D1"]["method"], draws=r["D1"]["draws"], statistics=d1),
        heldout_posterior_predictive=ppc,
        vocabulary=("CONVERGED: the fit met every sampler criterion of the contract (R-hat, ESS, no divergence "
                    "after the retry rule); medical vocabulary is reserved by the firewall, so sampler terms differ"),
        not_included=("gene, address, donor and operator identities; per-gene values; nothing from TEST, Morabito, "
                      "DEV, SEALED or protected data"))
    return FW.scrub(art)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--internal", default=str(INTERNAL))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args()
    art = build(Path(a.internal))
    with open(a.out, "w", encoding="utf-8", newline=chr(10)) as fh:
        fh.write(json.dumps(art, indent=1) + chr(10))
    print("written", a.out, sha(Path(a.out)))


if __name__ == "__main__":
    main()
