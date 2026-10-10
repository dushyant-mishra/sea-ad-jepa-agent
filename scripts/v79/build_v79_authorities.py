#!/usr/bin/env python3
"""V79 posterior-generative authorities (contract amendment A6): what the factorial synthetic-world generator
may consume, built only from CONVERGED real fits and their saved posterior draws.

  BIOLOGY authority (H1)     the fitted hierarchy for anonymous synthetic biology: population hyperparameter draws
                             (typical per-gene log sd m_x and its across-gene spread s_x, for donor and donor-class),
                             across-gene distributions of class-effect magnitude and profile (sorted, so no class is
                             named), residual within-class spread, baseline level, variance fractions, donor-class
                             support (Q5), and the bootstrap posterior of the corrected reference geometry (D1)
  OBSERVATION authority (H2) source and operator effect magnitudes (sources keep their authenticated names: they are
                             measurement categories), capture/depth structure (B0), detection propensity and its depth
                             slope, positive-count dispersion, and the joint across-phase depth slopes per gene
  REALISM diagnostic         INTERNAL ONLY: posterior means of every per-gene and per-level parameter with the gene
                             address indices, so a maximum-realism fitted world can be regenerated to ask how close the
                             model gets to corrected TRAIN. Never planted truth; never synthetic-consumable.

Per-gene values enter the authorities only as anonymous samples: genes are reordered by one permutation seeded from
the SHA-256 of the internal inputs (reproducible; positions cannot be mapped back without the internal records), the
same permutation for every per-gene array so within-gene couplings (e.g. depth slopes across phases) survive. The gene sample is stratified with equal numbers per prevalence decile, so
it is self-weighting for the 14,417-address universe. A phase that did not converge contributes its status only.
Both authorities must pass v79_firewall.scrub unchanged. training_authorized is false.
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
SPREAD_Q = (0.05, 0.1, 0.25, 0.5, 0.75, 0.9, 0.95)
PHASES = {"A": ("V79_PHASE_A_INTERNAL_V1.json", "V79_PHASE_A_DRAWS_V1.npz"),
          "B": ("V79_PHASE_B_INTERNAL_V1.json", "V79_PHASE_B_DRAWS_V1.npz"),
          "B0": ("V79_PHASE_B0_INTERNAL_V1.json", "V79_PHASE_B0_DRAWS_V1.npz"),
          "C": ("phase_c/V79_PHASE_C_INTERNAL_V1.json", "phase_c/V79_PHASE_C_DRAWS_V1.npz")}
OTHER = {"C_choice": "phase_c/V79_PHASE_C_FAMILY_CHOICE_INTERNAL_V1.json", "D1": "d1/V79_PHASE_D1_INTERNAL_V1.json",
         "support_A": "ppc/V79_DONOR_CLASS_SUPPORT_A_INTERNAL_V1.json",
         "support_B": "ppc/V79_DONOR_CLASS_SUPPORT_B_INTERNAL_V1.json",
         "ppc_A": "ppc/V79_HELDOUT_PPC_A_INTERNAL_V1.json", "ppc_B": "ppc/V79_HELDOUT_PPC_B_INTERNAL_V1.json",
         "ppc_B0": "ppc/V79_HELDOUT_PPC_B0_INTERNAL_V1.json"}
NOT_CONVERGED = dict(status="NOT_CONVERGED", note="estimates exist internally but are not interpreted or exported")
NON_AUTH = dict(training_authorized=False, synthetic_arm_promotion_authorized=False,
                note="estimation result; consumption by a synthetic arm requires the lane's own prospective freeze")


def sha(p: Path) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def q(x) -> list:
    return [float(v) for v in np.quantile(np.asarray(x, dtype=np.float64), SPREAD_Q)]


def draws_q(x) -> list:
    return [float(v) for v in np.quantile(np.asarray(x, dtype=np.float64), (0.05, 0.5, 0.95))]


def lognormal_family(x) -> dict:
    """Moment fit of a log-normal family to positive values (with the empirical quantiles beside it)."""
    lx = np.log(np.asarray(x, dtype=np.float64))
    return dict(family="lognormal", meanlog=float(lx.mean()), sdlog=float(lx.std(ddof=1)) if len(lx) > 1 else 0.0)


def effect_sd(a: np.ndarray) -> np.ndarray:
    """draws x levels x genes -> per-gene posterior-median sd of the level effects (realized spread)."""
    return np.median(np.asarray(a, dtype=np.float64).std(axis=1), axis=0)


def hyper_draws(d: dict, x: str) -> dict:
    out = {}
    for p in ("m", "s"):
        k = f"{p}_{x}"
        if k in d:
            out[k] = dict(posterior_q05_q50_q95=draws_q(d[k]), draws=[float(v) for v in np.asarray(d[k])])
    return out


def class_profile(a_cls: np.ndarray, class_levels) -> dict:
    """Class-effect magnitude per gene and the sorted (unnamed) profile; class-level shares are population counts."""
    med = np.median(np.asarray(a_cls, dtype=np.float64), axis=0)          # levels x genes
    sd = med.std(axis=0)
    prof = np.sort(med - med.mean(axis=0), axis=0)[::-1]                  # largest to smallest, no class names
    top = np.argmax(med, axis=0)
    return dict(magnitude_sd_across_genes_quantiles=q(sd), magnitude_family=lognormal_family(np.maximum(sd, 1e-8)),
                sorted_profile_median_by_rank=[float(v) for v in np.median(prof, axis=1)],
                share_of_genes_highest_in_class={str(c): float((top == i).mean()) for i, c in enumerate(class_levels)})


def build(internal: Path) -> tuple:
    recs, draws = {}, {}
    for ph, (j, n) in PHASES.items():
        if not (internal / j).exists() or not (internal / n).exists():
            raise SystemExit(f"refusing: phase {ph} record or draws missing")
        recs[ph] = json.loads((internal / j).read_text(encoding="utf-8"))
        with np.load(internal / n) as z:
            draws[ph] = {k: z[k] for k in z.files}
    other = {}
    for k, v in OTHER.items():
        if not (internal / v).exists():
            raise SystemExit(f"refusing: {k} missing")
        other[k] = json.loads((internal / v).read_text(encoding="utf-8"))
    n_genes = recs["A"]["gene_sample"]["n"]
    digest = hashlib.sha256("".join(sha(internal / f) for ph in PHASES for f in PHASES[ph]).encode()).hexdigest()
    perm = np.random.default_rng(int(digest[:16], 16)).permutation(n_genes)   # anonymizing, reproducible order
    conv = {ph: bool(recs[ph].get("diagnosed")) for ph in PHASES}
    levels = recs["A"]["design_levels"]
    cls_levels, src_levels = levels["class_levels"], levels["source_levels"]

    def gene_values(ph, arr):
        return [float(v) for v in np.asarray(arr)[perm]]

    bio = dict(schema="V79_BIOLOGY_GEOMETRY_AUTHORITY_V1", consumer="H1 hierarchical anonymous biology", **NON_AUTH,
               gene_population=("equal numbers per prevalence decile of the 14,417-address universe: self-weighting; "
                                "per-gene values are anonymous samples in an unrecorded random order"),
               phases={})
    obs = dict(schema="V79_OBSERVATION_GEOMETRY_AUTHORITY_V1", consumer="H2 observation operator", **NON_AUTH, phases={})
    for ph, name in (("A", "expression_log1p_cp10k"), ("B", "detection_logit"), ("C", "positive_magnitude")):
        if not conv[ph]:
            bio["phases"][name] = dict(NOT_CONVERGED)
            obs["phases"][name] = dict(NOT_CONVERGED)
            continue
        d = draws[ph]
        b = dict(status="CONVERGED",
                 donor=hyper_draws(d, "donor"), donor_class=hyper_draws(d, "dk"),
                 class_effects=class_profile(d["a_cls"], cls_levels),
                 baseline_level_across_genes=dict(quantiles=q(np.median(d["mu"], 0)),
                                                   samples=gene_values(ph, np.median(d["mu"], 0))),
                 donor_effect_sd_across_genes=dict(quantiles=q(effect_sd(d["a_donor"])),
                                                   family=lognormal_family(np.maximum(effect_sd(d["a_donor"]), 1e-8))),
                 donor_class_effect_sd_across_genes=dict(quantiles=q(effect_sd(d["a_dk"])),
                                                         family=lognormal_family(np.maximum(effect_sd(d["a_dk"]), 1e-8))))
        if "logsd_res" in d:
            sd_res = np.median(np.exp(d["logsd_res"]), 0)
            b["residual_within_class_sd"] = dict(quantiles=q(sd_res), family=lognormal_family(sd_res),
                                                 **hyper_draws(d, "res"))
        bio["phases"][name] = b
        o = dict(status="CONVERGED", operator=hyper_draws(d, "op"),
                 operator_effect_sd_across_genes=dict(quantiles=q(effect_sd(d["a_op"])),
                                                      family=lognormal_family(np.maximum(effect_sd(d["a_op"]), 1e-8))),
                 source_effect_sd_across_genes=dict(quantiles=q(effect_sd(d["a_src"]))),
                 source_effect_by_source={str(s_): q(np.median(d["a_src"], 0)[i]) for i, s_ in enumerate(src_levels)},
                 depth_slope_across_genes=dict(quantiles=q(np.median(d["b_depth"], 0))))
        if "logphi" in d:
            o["count_dispersion_log_phi"] = dict(quantiles=q(np.median(d["logphi"], 0)), **hyper_draws(d, "phi"))
        obs["phases"][name] = o
    # joint per-gene depth slopes across phases (same anonymous order): depth/detection/count coupling
    if all(conv[p] for p in ("A", "B", "C")):
        obs["joint_depth_slopes_per_gene"] = {p: gene_values(p, np.median(draws[p]["b_depth"], 0)) for p in ("A", "B", "C")}
    # capture/depth structure (B0, cell-level responses)
    if conv["B0"]:
        obs["capture_and_depth_B0"] = {r: {c: dict(fraction_median=f["per_gene_median"][i],
                                                    fraction_q05_q95=[f["per_gene_q05"][i], f["per_gene_q95"][i]],
                                                    variance_median=f.get("variance_per_gene_median", [None] * 2)[i])
                                            for c, f in recs["B0"]["fractions"].items()}
                                       for i, r in enumerate(recs["B0"]["responses"])}
    else:
        obs["capture_and_depth_B0"] = dict(NOT_CONVERGED)
    obs["positive_family"] = other["C_choice"]["decision"]
    bio["variance_fractions"] = {ph: ({c: f["across_gene_median_q"] for c, f in recs[ph]["fractions"].items()}
                                      if conv[ph] else "NOT_CONVERGED") for ph in ("A", "B", "C")}
    bio["donor_class_support_Q5"] = {ph: {k: other[f"support_{ph}"]["comparison"][k]
                                          for k in ("mean_difference_per_observation", "donor_clustered_se", "supported")}
                                     for ph in ("A", "B")}
    bio["reference_geometry_bootstrap_D1"] = {k: {x: v[x] for x in ("point", "q05", "median", "q95")}
                                              for k, v in other["D1"]["statistics"].items()}
    for art in (bio, obs):
        art["inputs_sha256"] = {**{f"{ph}_record": sha(internal / PHASES[ph][0]) for ph in PHASES},
                                **{f"{ph}_draws": sha(internal / PHASES[ph][1]) for ph in PHASES},
                                **{k: sha(internal / v) for k, v in OTHER.items()}}
        art["contract_sha256"] = sha(CONTRACT)
        art["ppc_limitations"] = {p: {k: v["share_inside"] for k, v in other[f"ppc_{p}"]["pooled_share_inside"].items()
                                      if v["share_inside"] is not None and v["share_inside"] < 0.8}
                                  for p in ("A", "B", "B0")}
        FW.scrub(art)
    realism = dict(schema="V79_REALISM_GENERATIVE_DIAGNOSTIC_V1",
                   status="INTERNAL__REALISM_DIAGNOSTIC__NOT_PLANTED_TRUTH__NOT_SYNTHETIC_CONSUMABLE",
                   gene_address_indices=recs["A"]["gene_sample"]["internal_address_indices"],
                   posterior_means={ph: {k: np.asarray(v, dtype=np.float64).mean(0).tolist() for k, v in draws[ph].items()}
                                    for ph in PHASES if conv[ph]},
                   converged=conv)
    return bio, obs, realism


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--internal", default=str(INTERNAL))
    ap.add_argument("--out-dir", default=str(ROOT / "results/v79"))
    a = ap.parse_args()
    bio, obs, realism = build(Path(a.internal))
    out = Path(a.out_dir)
    for name, art in (("V79_BIOLOGY_GEOMETRY_AUTHORITY_V1.json", bio), ("V79_OBSERVATION_GEOMETRY_AUTHORITY_V1.json", obs),
                      ("internal/V79_REALISM_GENERATIVE_DIAGNOSTIC_V1.json", realism)):
        p = out / name
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "w", encoding="utf-8", newline=chr(10)) as fh:
            fh.write(json.dumps(art, indent=1) + chr(10))
        print("written", p, sha(p))


if __name__ == "__main__":
    main()
