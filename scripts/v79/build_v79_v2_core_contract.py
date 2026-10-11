#!/usr/bin/env python3
"""Build the frozen V79 V2_CORE prospective synthetic-qualification contract (JSON) before any qualification fit.

This file is the single authority for every number in the contract. Declared constants are listed once, with a
rationale or an explicit CONVENTION label. Derived quantities are computed here from the declared constants and from
the committed development inputs: the multiplicity level, the binomial thresholds, the gene count from the precision
budget, and the planting magnitudes from the masked development calibration. Fitting and scoring code reads the
contract JSON and must refuse a JSON whose SHA-256 differs from the frozen value. The code never re-declares these
numbers.

Usage: build_v79_v2_core_contract.py <repo_root> [--check]
  --check   rebuild in memory and compare to the committed JSON byte for byte (no write)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
from scipy import stats

SCHEMA = "V79_V2_CORE_QUALIFICATION_CONTRACT_V2"
CONTRACT_REL = "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json"
CONTRACT_STATUS = "PENDING_CONTROLLER_ACCEPTANCE__NO_WORLD_GENERATION"
SUPERSEDED = {  # preserved unchanged at its path; historical pre-controller draft, never launch authority
    "path": "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V1.json",
    "sha256": "70edabb86c93a9f4ddb4dfb27bded60bab355c90b99d49f49cb851b4c1e58540",
    "status": "HISTORICAL_PRE_CONTROLLER_DRAFT__NOT_LAUNCH_AUTHORITY",
    "superseded_by_ruling": "PR #286 controller ruling 6113874774",
}
INPUTS = {
    "s174_design_only": "results/v79/v2_core_qualification/inputs/V79_S174_DESIGN_ONLY_V1.npz",
    "s174_design_only_record": "results/v79/v2_core_qualification/inputs/V79_S174_DESIGN_ONLY_V1.json",
    "planting_calibration_masked": "results/v79/development/v2_core_planting_calibration/V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json",
    "structural_support_dev": "results/v79/development/v2_core_planting_calibration/V79_G500_STRUCTURAL_SUPPORT_DEV.json",
    "structural_support_v1_record": "results/v79/development/s174_structure_replay_v4_masked/V79_G500_STRUCTURAL_SUPPORT_V1.json",
    "masked_replay": "results/v79/development/s174_structure_replay_v4_masked/V79_S174_STRUCTURE_REPLAY_DEVELOPMENT_V4_MASKED.json",
    "masking_audit": "results/v79/development/s174_structure_replay_v4_masked/V79_S174_REPLAY_MASKING_AUDIT_V1.json",
    "env_lock": "results/v79/v2_core_qualification/inputs/V79_BAYES_ENV_PIP_FREEZE.txt",
}

# ---------------------------------------------------------------------------------------------------------------
# Declared constants (each appears exactly once)
# ---------------------------------------------------------------------------------------------------------------
SEED_ROOT = 31000000                 # verified absent from the repository before freeze (grep, 2026-10-11)
ENGINEERING_SEED_ROOT = 31999999     # engineering smoke benchmark only; never a qualification world
FAMILYWISE_FALSE_FAIL = 0.05         # CONVENTION: P(a correctly calibrated V2_CORE fails >=1 statistical gate) <= 5%
INTERVAL_MASS = 0.90                 # central posterior interval used for coverage, false positives and type-S
BIAS_DETECT_STD = 0.75               # precision budget: detect a standardized bias of 0.75 posterior SD ...
BIAS_DETECT_POWER = 0.80             # ... with power 0.80 at the Bonferroni level (single-quantity type, SD 1)
BIAS_MATERIALITY_STD = 0.50          # CONVENTION: |mean standardized bias| <= 0.5 is not material for a geometry model
DONOR_SD_FLOOR_FRACTION = 0.10       # CONVENTION: "donor present" means q05(sigma) > 0.1 x smallest realistic donor SD
DONOR_ABSENT_NOMINAL = 0.05          # CONVENTION: reference false-positive rate for the q05 > floor rule
POP_DONOR_RATIO_BOUNDS = (0.80, 1.25)  # CONVENTION: population donor-SD accuracy, +-25% multiplicative
PPC_EXTREME_P = 0.01                 # a two-sided posterior predictive p below this is a PPC failure
TYPE_S_NOMINAL = 0.05                # P(90% interval excludes 0 on the wrong side) <= 5% under calibration
STRUCTURAL_GENE_FRACTION = 59 / 500  # development: genes with any structurally unmeasured cell (exact, matrix level)
DEV_FULLY_UNMEASURED_PAIRS_BY_SOURCE = {"HVS": 38, "NPH52": 20, "SEA_AD": 10}
PLANT_QUANTILE_RANGE = (0.05, 0.95)  # planted values span the development p05-p95 range (Latin hypercube)
SPARSE_PREVALENCE_RANGE = (0.005, 0.05)
WEAK_DONOR_FACTOR, STRONG_DONOR_FACTOR = 0.5, 2.0   # x development p05 / x development p95
TAIL_SIGMA_FACTOR = 2.0                              # x development p95 positive sigma
WEAK_SOURCE_QUANTILE = 0.25                          # |source contrast| fixed at development p25
OPERATOR_SD_FRACTION = 0.5                           # Q11: operator SD = 0.5 x that gene's donor SD (CONVENTION)
FACTOR_LOADING = 0.6                                 # shared donor factor loading for half the genes (second stage)
CHAINS, WARMUP, DRAWS, MAX_TREE_DEPTH = 4, 1000, 1000, 10
TARGET_ACCEPT_PRIMARY, TARGET_ACCEPT_ESCALATION = 0.90, 0.99
RHAT_MAX, ESS_MIN = 1.01, 400
PPC_DRAWS, DONOR_DRAWS_STORED, GH_NODES = 1000, 200, 40
SETTLE_SECONDS = 120
MAX_PROJECTED_HOURS = 72             # engineering benchmark projection above this: stop and report, change nothing

CLASS_LEVELS = ["GABAergic", "Glutamatergic", "NonNeuronal"]
SOURCE_LEVELS = ["HVS", "NPH52", "SEA_AD"]
MATRICES_PER_SOURCE = [24, 7, 11]

PRIORS = {
    "detection": {
        "alpha": {"dist": "Normal", "loc": -1.2, "scale": 2.5},
        "beta_depth1": {"dist": "Normal", "loc": 0.0, "scale": 2.0},
        "beta_depth2": {"dist": "Normal", "loc": 0.0, "scale": 0.5},
        "class_contrasts": {"dist": "Normal", "loc": 0.0, "scale": 1.5},
        "source_contrasts": {"dist": "Normal", "loc": 0.0, "scale": 1.5},
        "donor_sd": {"dist": "HalfNormal", "scale": 1.0},
        "donor_raw": {"dist": "Normal", "loc": 0.0, "scale": 1.0},
    },
    "positive": {
        "alpha": {"dist": "Normal", "loc": 0.5, "scale": 1.0},
        "gamma_depth1": {"dist": "Normal", "loc": 0.0, "scale": 1.0},
        "gamma_depth2": {"dist": "Normal", "loc": 0.0, "scale": 0.5},
        "class_contrasts": {"dist": "Normal", "loc": 0.0, "scale": 0.75},
        "source_contrasts": {"dist": "Normal", "loc": 0.0, "scale": 0.5},
        "donor_sd": {"dist": "HalfNormal", "scale": 0.5},
        "donor_raw": {"dist": "Normal", "loc": 0.0, "scale": 1.0},
        "sigma": {"dist": "HalfNormal", "scale": 1.0},
    },
}
PRIOR_RATIONALE = (
    "Weakly informative and scaled to the masked development ranges (structurally measured cells only; "
    "V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2). Rule: slopes, curvature and contrasts are centred at 0; intercepts are "
    "centred at the development median; each scale puts the development p99 magnitude within about 1.5 prior SD. The "
    "documented exception is the detection |source| p99 tail (about 7.9 logit), which reflects near-separation in about "
    "1% of genes and is not planted. Donor and positive SDs are half-normal with scales above the development p99. The "
    "development donor SDs are ridge-shrunk and so biased low. Priors are frozen here and are never changed after a "
    "qualification outcome.")

# world name -> (design, modifications); every world uses Q00 rules except as modified
WORLDS = [
    ("Q00_BASELINE", "BASE", {}),
    ("Q01_WEAK_DONOR", "BASE", {"donor_sd": "weak"}),
    ("Q02_STRONG_DONOR", "BASE", {"donor_sd": "strong"}),
    ("Q03_WEAK_SOURCE", "BASE", {"source": "weak"}),
    ("Q04_SOURCE_ABSENT", "BASE", {"source": "absent"}),
    ("Q05_CLASS_ABSENT", "BASE", {"class": "absent"}),
    ("Q06_QUADRATIC_DEPTH_ABSENT", "BASE", {"depth2": "absent"}),
    ("Q07_DONOR_ABSENT", "BASE", {"donor_sd": "absent"}),
    ("Q08_SPARSE_DETECTION", "BASE", {"prevalence": "sparse"}),
    ("Q09_POSITIVE_TAIL", "BASE", {"sigma": "tail"}),
    ("Q10_S174_DESIGN_IMBALANCE", "S174", {}),
    ("Q11_OMITTED_OPERATOR", "S174", {"operator": "omitted_perturbation"}),
]
FIXED_TYPES = ["intercept", "depth1", "depth2", "class", "source"]
DESCRIPTIVE_METRICS = [
    "per type: correlation and RMSE of posterior mean vs truth across genes; sign agreement",
    "donor: Spearman rank of donor effects; calibration slope of truth on posterior mean; shrinkage factor",
    "detection held-out (same donors, new donors): mean log loss vs oracle, 10-bin calibration, predicted vs observed prevalence, low-prevalence (planted < 0.05) subset",
    "positive held-out: mean LPD vs oracle (new donors integrated by %d-node Gauss-Hermite)" % GH_NODES,
    "PPC statistics and p-values per gene; Q11 minus Q10 contrasts; second stage",
]
ABSENT_TYPE = {"source": "source", "class": "class", "depth2": "depth2"}
# Worlds that by construction put a donor SD near zero or under weak information. Under a proper half-normal prior,
# the posterior mean there moves away from the boundary, so standardized bias is an expected Bayesian property and
# not a defect. BIAS_DONOR_SD is a LIMIT there; coverage stays FAIL-class.
WEAK_DONOR_IDENTIFICATION = {("Q01_WEAK_DONOR", "detection"), ("Q01_WEAK_DONOR", "positive"),
                             ("Q08_SPARSE_DETECTION", "positive"), ("Q09_POSITIVE_TAIL", "positive")}
WEAK_DONOR_IDENTIFICATION_RATIONALE = (
    "donor SD planted at 0.5 x the smallest realistic value (Q01), or with about 1 positive cell per donor (Q08 "
    "positive), or under a residual SD of about 1.46 (Q09 positive): the posterior mean of a weakly identified SD sits "
    "above a small truth under any proper prior. A failure is reported as a limit on what a small real donor-SD "
    "estimate means; calibration (coverage) remains a FAIL-class gate")
# Population donor-SD ratio is gated only where the donor SD is well identified by construction: the detection part
# (every measured cell informs it) at realistic or strong magnitudes, and the positive part only at strong magnitude
# (at realistic magnitudes the lowest-prevalence genes have about 2 positives per donor).
POP_RATIO_GATED = {("Q00_BASELINE", "detection"), ("Q02_STRONG_DONOR", "detection"),
                   ("Q10_S174_DESIGN_IMBALANCE", "detection"), ("Q02_STRONG_DONOR", "positive")}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _quantile(values, p) -> float:
    return float(np.quantile(np.asarray(values, float), p))


def calibration_magnitudes(cal: dict) -> dict:
    rows = cal["per_gene"]
    def vals(part, key, all_sources=False, absolute=False):
        out = []
        for r in rows:
            if part not in r or (all_sources and not r["all_sources_measured"]) or key not in r[part]:
                continue
            v = r[part][key]
            out.extend([abs(x) for x in v] if absolute else ([v] if not isinstance(v, list) else v))
        return out
    m = {}
    for part, P in (("det", "detection"), ("pos", "positive")):
        m[P] = {
            "depth1": vals(part, "depth"), "depth2": vals(part, "depth2"),
            "abs_class": vals(part, "cls", absolute=True), "abs_source": vals(part, "src", True, True),
            "donor_sd": vals(part, "donor_sd"),
        }
        if part == "pos":
            m[P]["intercept"] = vals(part, "intercept", all_sources=True)
            m[P]["sigma"] = vals(part, "sigma")
    m["detection"]["prevalence"] = [r["prevalence"] for r in rows]
    return m


def planting(mags: dict) -> dict:
    lo, hi = PLANT_QUANTILE_RANGE
    q = lambda part, key, p: _quantile(mags[part][key], p)
    lhs = {part: {k: {"empirical_quantile_range": [q(part, k, lo), q(part, k, hi)]} for k in mags[part]}
           for part in mags}
    fixed = {
        "weak_donor_sd": {P: WEAK_DONOR_FACTOR * q(P, "donor_sd", 0.05) for P in ("detection", "positive")},
        "strong_donor_sd": {P: STRONG_DONOR_FACTOR * q(P, "donor_sd", 0.95) for P in ("detection", "positive")},
        "weak_abs_source": {P: q(P, "abs_source", WEAK_SOURCE_QUANTILE) for P in ("detection", "positive")},
        "tail_sigma": TAIL_SIGMA_FACTOR * q("positive", "sigma", 0.95),
        "donor_absent_floor": {P: DONOR_SD_FLOOR_FRACTION * q(P, "donor_sd", 0.05) for P in ("detection", "positive")},
    }
    return {"latin_hypercube_ranges": lhs, "fixed_magnitudes": fixed}


def world_gates(name: str, mods: dict) -> list[dict]:
    """Every gate for one world, both parts. kind: STAT (statistical) or RULE (deterministic). verdict_class FAIL
    (hard) everywhere, including every Q11 donor and PPC gate (PR #286 ruling B), except the four donor-SD bias gates
    in WEAK_DONOR_IDENTIFICATION, which are LIMIT."""
    gates = []
    for part in ("detection", "positive"):
        absent = {ABSENT_TYPE[k] for k, v in mods.items() if v == "absent" and k in ABSENT_TYPE}
        donor_absent = mods.get("donor_sd") == "absent"
        present_fixed = [t for t in FIXED_TYPES if t not in absent]
        cls = lambda family: "FAIL"
        g = lambda gate, kind, family, **kw: gates.append(dict(world=name, part=part, gate=gate, kind=kind,
                                                               verdict_class=cls(family), **kw))
        g("CONVERGENCE_ALL_FITS_DIAGNOSED", "RULE", "convergence")
        g("COVERAGE_FIXED_POOLED", "STAT", "fixed", test="one_sided_t_lower_across_genes",
          quantity_types=present_fixed, nominal=INTERVAL_MASS)
        for t in present_fixed:
            g(f"BIAS_{t.upper()}", "STAT", "fixed", test="two_sided_t_across_genes_and_materiality",
              quantity_type=t)
        for t in sorted(absent):
            g(f"ABSENT_FALSE_POSITIVE_{t.upper()}", "STAT", "fixed", test="interval_excludes_zero_rate",
              quantity_type=t, nominal=1 - INTERVAL_MASS)
        if mods.get("source") == "weak":
            g("TYPE_S_SOURCE", "STAT", "fixed", test="binomial_upper", quantity_type="source", nominal=TYPE_S_NOMINAL)
        if donor_absent:
            g("ABSENT_FALSE_POSITIVE_DONOR_SD", "STAT", "donor", test="binomial_upper_q05_above_floor",
              quantity_type="donor_sd", nominal=DONOR_ABSENT_NOMINAL)
        else:
            g("COVERAGE_DONOR_SD", "STAT", "donor", test="binomial_lower", quantity_type="donor_sd",
              nominal=INTERVAL_MASS)
            weak_id = (name, part) in WEAK_DONOR_IDENTIFICATION
            gates.append(dict(world=name, part=part, gate="BIAS_DONOR_SD", kind="STAT",
                              verdict_class="LIMIT" if weak_id else cls("donor"),
                              test="two_sided_t_across_genes_and_materiality", quantity_type="donor_sd",
                              **({"limit_rationale": WEAK_DONOR_IDENTIFICATION_RATIONALE} if weak_id else {})))
        g("COVERAGE_DONOR_EFFECTS", "STAT", "donor", test="one_sided_t_lower_across_genes",
          quantity_type="donor_effects", nominal=INTERVAL_MASS)
        if part == "positive":
            g("COVERAGE_SIGMA", "STAT", "fixed", test="binomial_lower", quantity_type="sigma", nominal=INTERVAL_MASS)
            g("BIAS_SIGMA", "STAT", "fixed", test="two_sided_t_across_genes_and_materiality", quantity_type="sigma")
        g("PPC_EXTREME_RATE", "STAT", "ppc", test="binomial_upper", nominal=PPC_EXTREME_P)
        if (name, part) in POP_RATIO_GATED:
            g("POPULATION_DONOR_SD_RATIO", "RULE", "donor", bounds=list(POP_DONOR_RATIO_BOUNDS))
    return gates


def derive_gene_count(alpha_test: float) -> dict:
    """Smallest G whose two-sided bias t-test (df G-1, Bonferroni level) detects BIAS_DETECT_STD with the declared
    power when the per-gene standardized error has SD 1 (single-quantity type, the weakest case)."""
    for G in range(5, 500):
        tc = stats.t.ppf(1 - alpha_test / 2, G - 1)
        ncp = BIAS_DETECT_STD * math.sqrt(G)
        power = stats.nct.sf(tc, G - 1, ncp) + stats.nct.cdf(-tc, G - 1, ncp)
        if power >= BIAS_DETECT_POWER:
            return dict(G=G, t_critical=float(tc), power=float(power),
                        detectable_bias_std=BIAS_DETECT_STD, min_significant_mean_bias_std=float(tc / math.sqrt(G)))
    raise SystemExit("no G found")


def binomial_thresholds(G: int, alpha_test: float) -> dict:
    out = {}
    # coverage lower rule: FAIL iff P(Bin(n, 1-nominal) >= misses) < alpha_test ; report the largest passing misses
    for n in (G, 2 * G):
        k = 0
        while stats.binom.sf(k, n, 1 - INTERVAL_MASS) >= alpha_test:   # sf(k) = P(X > k) = P(X >= k+1)
            k += 1
        out[f"coverage_single_n{n}_max_passing_misses"] = k
    k = 0
    while stats.binom.sf(k, G, DONOR_ABSENT_NOMINAL) >= alpha_test:
        k += 1
    out[f"donor_absent_n{G}_max_passing_false_positives"] = k
    return out


def build(root: Path) -> dict:
    hashes = {k: sha(root / v) for k, v in INPUTS.items()}
    cal = json.loads((root / INPUTS["planting_calibration_masked"]).read_text(encoding="utf-8"))
    design_rec = json.loads((root / INPUTS["s174_design_only_record"]).read_text(encoding="utf-8"))
    if design_rec["npz_sha256"] != hashes["s174_design_only"]:
        raise SystemExit("STOP: design-only npz does not match its record")
    # The masked planting calibration may be used only if its measurement-support join reproduces under the committed,
    # tested builder (PR #286 ruling): the same operator x gene mask hash in all three records.
    support_v1 = json.loads((root / INPUTS["structural_support_v1_record"]).read_text(encoding="utf-8"))
    support_dev = json.loads((root / INPUTS["structural_support_dev"]).read_text(encoding="utf-8"))
    join = {"committed_builder_mask_sha256": support_v1["measured_op_gene_sha256"],
            "development_mask_sha256": support_dev["op_x_gene_sha256"],
            "calibration_mask_sha256": cal["structural_support"]["op_x_gene_sha256"]}
    if len(set(join.values())) != 1 or not support_v1.get("reproduces_development_mask", {}).get("match"):
        raise SystemExit(f"STOP: the masked calibration's support join does not reproduce: {join}")
    audit = json.loads((root / INPUTS["masking_audit"]).read_text(encoding="utf-8"))
    if audit["inputs"]["masked_replay"]["sha256"] != hashes["masked_replay"]:
        raise SystemExit("STOP: the masking audit does not describe the committed masked replay")
    mags = calibration_magnitudes(cal)
    plant = planting(mags)
    gates = [g for name, _, mods in WORLDS for g in world_gates(name, mods)]
    n_stat_hard = sum(g["kind"] == "STAT" and g["verdict_class"] == "FAIL" for g in gates)
    counts = {"total": len(gates),
              "hard_statistical": n_stat_hard,
              "hard_rule": sum(g["kind"] == "RULE" and g["verdict_class"] == "FAIL" for g in gates),
              "limit_statistical": sum(g["kind"] == "STAT" and g["verdict_class"] == "LIMIT" for g in gates),
              "limit_rule": sum(g["kind"] == "RULE" and g["verdict_class"] == "LIMIT" for g in gates),
              "descriptive_metric_families": len(DESCRIPTIVE_METRICS)}
    alpha_test = FAMILYWISE_FALSE_FAIL / n_stat_hard
    gene = derive_gene_count(alpha_test)
    G = gene["G"]
    n_struct = round(STRUCTURAL_GENE_FRACTION * G)
    n_fits = len(WORLDS) * G * 2

    contract = {
        "schema": SCHEMA,
        "name": "V79_V2_CORE_FROZEN_MODEL_AND_PROSPECTIVE_SYNTHETIC_QUALIFICATION_CONTRACT",
        "status": CONTRACT_STATUS,
        "launch_authority": False,
        "launch_condition": ("controller acceptance of the masked exact-S174 replay and of this amended contract; "
                             "until then no world generation, no truth table, no benchmark and no qualification fit"),
        "supersedes": SUPERSEDED,
        "structural_support_join_reproduced": join,
        "authority": {
            "controller_model_freeze": "CANDIDATE_V2_CORE (PR #285 comment 6113335756)",
            "development_evidence": "docs/agent/V79_S174_STRUCTURE_REPLAY_V3_RESULT_20261011.md (replay SHA-256 78db6d31...)",
            "base_commit": "2c230a70d9151e27b14ec2788d1309eb2ac81468",
            "builder": "scripts/v79/build_v79_v2_core_contract.py",
        },
        "boundaries": {
            "training_authorized": False, "real_train_posterior_inference": False, "factorial_science": False,
            "test_split": False, "morabito": False, "pathology": False, "target_discovery": False,
            "scenic_atac_in_truth": False, "operator_in_model": False, "old_18_fit_campaign": False,
            "bernoulli_v2_v3_rescue": False, "stage4_500k": False, "jepa_training_or_checkpoints": False,
        },
        "inputs": {k: {"path": v, "sha256": hashes[k]} for k, v in INPUTS.items()},
        "model": {
            "name": "V2_CORE",
            "unit": "one gene, two independent parts (detection, positive magnitude); genes are fitted separately",
            "observation_support": (
                "The likelihood runs only over STRUCTURALLY MEASURED cell-gene entries: those whose matrix measures "
                "the gene's address. This is the Stage81A2R matrix-level measurement support for real data, and the "
                "world support mask in synthetic worlds. Structurally unmeasured entries enter neither part. A "
                "measured zero is a detection observation y=0. This is the hard invariant MEASURED_SCALAR != "
                "STRUCTURALLY_UNMEASURED, not a model choice."),
            "covariates": {
                "z": "standardized log library over all cells of the design (population SD, ddof=0)",
                "q": "z^2 - 1 (centred quadratic depth)",
                "class": "3 broad classes, normalized Helmert sum-to-zero contrasts (3x2)",
                "source": "3 sources, normalized Helmert sum-to-zero contrasts (3x2)",
                "donor": ("within-source normalized Helmert basis W (block diagonal; columns orthonormal; each "
                          "block sums to zero within source); n_donor - 3 columns"),
            },
            "detection": ("y_ig ~ Bernoulli(p_ig); logit p = alpha + beta1*z + beta2*q + B_class[class].c_class + "
                          "B_source[source].c_source + u[donor]; u = W (sigma_d * eps), eps ~ N(0, I)"),
            "positive": ("for measured y_ig > 0: log y_ig ~ Normal(mu_ig, sigma); mu = alpha+ + gamma1*z + gamma2*q + "
                         "B_class[class].c+_class + B_source[source].c+_source + u+[donor]; u+ = W (tau * eps+)"),
            "excluded_terms": ["operator / matrix", "donor x class", "source x class", "dataset or matrix ID"],
            "positive_family": "lognormal (ZTNB is a separate unadjudicated challenger; no comparison here)",
            "numerics": {"dtype": "float64 (jax_enable_x64)", "matmul_precision": "highest", "backend": "CPU"},
        },
        "parameterization": {
            "contrasts": "constrained normalized Helmert sum-to-zero (class, source, donor-within-source)",
            "donor": "non-centred in every world and both parts; no switching after any outcome",
            "centred_parameterization": "not used anywhere",
        },
        "priors": PRIORS,
        "prior_rationale": PRIOR_RATIONALE,
        "development_reference_quantiles_masked": cal["summary"],
        "second_stage": {
            "status": "DESCRIPTIVE_IN_THIS_QUALIFICATION__NOT_GATED",
            "across_gene_distribution": (
                "Per part and scalar quantity type: posterior means m_g with posterior SDs s_g; m_g ~ N(mu, t^2 + s_g^2). "
                "Priors mu ~ N(prior loc, prior scale) and t ~ HalfNormal(prior scale), from the per-gene prior of "
                "that type. Exact 2-D grid posterior (401 x 401). Reported against the planted across-gene mean and SD."),
            "cross_gene_donor_geometry": (
                "Disattenuated correlation of posterior-mean donor effects between gene pairs: corr(E u_g, E u_h) / "
                "sqrt(rel_g rel_h), with rel_g = var_d(E u_dg) / (var_d(E u_dg) + mean_d var_post(u_dg)). Computed over "
                "shared donors with >=1 informative observation. Reported against the planted realized correlation."),
        },
        "inference": {
            "sampler": "NumPyro NUTS, diagonal mass matrix, default init (uniform radius 2)",
            "chains": CHAINS, "warmup": WARMUP, "draws": DRAWS, "max_tree_depth": MAX_TREE_DEPTH,
            "chain_method": "parallel on 4 host CPU devices (one heavy fit at a time)",
            "diagnostics": {"rhat": "rank-normalized split R-hat (ArviZ) <= %.2f on every site" % RHAT_MAX,
                            "ess": "bulk and tail ESS >= %d on every site" % ESS_MIN,
                            "divergences": "0 in the final attempt",
                            "sites": "every sampled site: alpha, slopes, contrasts, donor SD, every eps, sigma"},
            "diagnostic_rationale": ("R-hat 1.01 and ESS 400 (100 per chain) follow Vehtari et al. 2021, as in the "
                                     "existing V79 rules (v79_sampler_rules.py). With ESS 400 the Monte Carlo SE of a "
                                     "posterior mean is SD/20, negligible against the 0.75 SD bias the gates target."),
            "recovery_path": {
                "version": "V2_CORE_ONE_ESCALATION_ONE_EXTENSION_V1",
                "primary": f"target_accept {TARGET_ACCEPT_PRIMARY}",
                "escalation": (f"any divergence -> refit fresh at target_accept {TARGET_ACCEPT_ESCALATION} with the "
                               "attempt-1 seed. Used at most once per fit"),
                "extension": ("no divergence but R-hat or ESS missed -> continue the same chains once for DRAWS more "
                              "draws, with no new warm-up, and diagnose all draws. Used at most once per fit"),
                "escalation_value_rationale": ("Only one escalation is allowed, so it uses the terminal value of the "
                                               "existing A5_V2 ladder (0.99). A remaining FAIL then reflects the "
                                               "posterior geometry, not too small an escalation."),
                "otherwise": "NOT_DIAGNOSED -> the world fails CONVERGENCE_ALL_FITS_DIAGNOSED",
                "no_other_changes": "no reparameterization, prior, init, tree-depth or warm-up change after any outcome",
            },
            "attempt_record_fields": ["fit_id", "seed", "chains", "warmup", "draws_per_chain", "target_accept",
                                      "extended", "divergences_per_chain", "worst_rhat", "worst_ess_bulk",
                                      "worst_ess_tail", "wall_seconds", "process_cpu_seconds",
                                      "peak_working_set_bytes", "mean_tree_steps", "jax_devices"],
        },
        "seeds": {
            "root": SEED_ROOT,
            "scheme": "numpy.random.SeedSequence(entropy=root, spawn_key=(world_index, gene_index, stream))",
            "binding": "randomness is keyed by scientific identity (world, gene, stream), never by file layout",
            "world_index": {name: i for i, (name, _, _) in enumerate(WORLDS)},
            "shared_base_design_key": [100, 0, 0],
            "world_level_gene_index": 9999,
            "world_streams": {"structural_selection": 1, "donor_factor_fit": 2, "donor_factor_new_donors": 3,
                              "factor_loading_assignment": 4, "lhs_permutations_base": 50},
            "gene_streams": {"lhs_jitter": 10, "contrast_signs": 11, "donor_idiosyncratic_det": 12,
                             "donor_idiosyncratic_pos": 13, "noise_det": 14, "noise_pos": 15,
                             "heldout_same_donor_noise_det": 16, "heldout_same_donor_noise_pos": 17,
                             "new_donor_idiosyncratic_det": 18, "new_donor_idiosyncratic_pos": 19,
                             "new_donor_noise_det": 20, "new_donor_noise_pos": 21, "operator_offsets_det": 22,
                             "operator_offsets_pos": 23, "structural_matrix_choice": 24,
                             "fit_det_primary": 30, "fit_det_escalation": 31, "fit_pos_primary": 40,
                             "fit_pos_escalation": 41},
            "jax_key": "jax.random.PRNGKey(SeedSequence(...).generate_state(1, numpy.uint32)[0])",
            "engineering_benchmark_root": ENGINEERING_SEED_ROOT,
        },
        "worlds": {
            "genes_per_world": G,
            "gene_count_derivation": gene,
            "designs": {
                "BASE": ("Crossed design with S174 sizes. Donors per source (62, 19, 68). Cells per donor are resampled "
                         "with replacement from that source's S174 cells-per-donor values. Each cell's class is drawn "
                         "iid from the S174 class proportions. Each cell's log library is resampled iid from the "
                         "pooled S174 log-library values. Each cell's matrix is drawn uniformly from its source's "
                         "(24, 7, 11) matrices. Seeded once (key [100,0,0]) and shared by Q00-Q09, so between-world "
                         "differences come only from the planted effects."),
                "S174": ("The exact S174 design arrays (V79_S174_DESIGN_ONLY_V1.npz): log library, broad class, "
                         "source, donor, operator=matrix. This design has weak crossing: HVS/NPH52 matrices are "
                         "single-class, NPH52 has 32 GABAergic and 32 Glutamatergic cells, and mean log library by "
                         "class differs by about 1.45 SD."),
            },
            "planting_Q00": {
                "rule": ("Latin hypercube over the development per-gene values. For each world and quantity type, "
                         "level_j = p_lo + (p_hi - p_lo) * (perm_k(j) + U_j) / G, with a seeded permutation per type "
                         "and seeded jitter per gene. The value is the empirical quantile (numpy 'linear') of the "
                         "masked development per-gene values at level_j. Contrast magnitudes come from |contrast| "
                         "values with seeded +-1 signs. The detection intercept is solved by bisection so that the "
                         "mean of expit(linear predictor without donor) over measured cells equals the planted "
                         "prevalence."),
                "detection": ["prevalence", "depth1", "depth2", "abs_class", "abs_source", "donor_sd"],
                "positive": ["intercept", "depth1", "depth2", "abs_class", "abs_source", "donor_sd", "sigma"],
                "donor_effects": ("u = sd * P(lambda_g f + sqrt(1 - lambda_g^2) e_g), where P is within-source "
                                  "centering (equivalent in law to W eps), f is a world donor factor shared across "
                                  "genes and parts, and e_g is idiosyncratic. lambda_g = %.1f for a seeded half of "
                                  "genes and 0 otherwise. Per gene the law is exactly the model's; the factor only "
                                  "exercises the descriptive second stage." % FACTOR_LOADING),
                "positive_values": ("continuous lognormal (correct specification). Real positive counts are integers "
                                    ">= 1; discretization is NOT tested here (ZTNB question)."),
            },
            "planting_magnitudes": plant,
            "structural_support_rule": {
                "genes_with_structural_absence_per_world": n_struct,
                "derivation": "round(%d/500 x G); development fraction of genes with any structurally unmeasured cell" % 59,
                "composition": {
                    "single_source_measured": 1, "one_source_fully_unmeasured": n_struct - 2,
                    "partial_within_source": 1,
                },
                "one_source_absent_probabilities": DEV_FULLY_UNMEASURED_PAIRS_BY_SOURCE,
                "single_source_measured_choice": "measured source drawn uniformly",
                "partial_rule": "a seeded floor(7/2)=3 of the 7 NPH52 matrices are unmeasured (development: partial absence only in NPH52)",
                "poison": "structurally unmeasured entries are written as -1 so any read of them is detectable",
                "world_truth": ("each world's cell x gene support mask is part of its truth, written with the world "
                                "data and hash-bound in the world manifest before any fit"),
                "required_tests_before_generation": [
                    "measured zero enters detection as y=0; an unmeasured entry enters no likelihood, metric or score",
                    "a fully unmeasured source x gene is excluded (no zero prevalence, no source effect from it)",
                    "partial NPH52-style matrix-level support is resolved per matrix x gene, never per source",
                    "a poison value on an entry the mask declares measured is detected and refused",
                    "changing the poison value with the mask fixed changes no fitted or scored output",
                ],
                "partial_count_note": "one partial gene per world exercises the code path; it is not frequency-matched (dev 3/500)",
            },
            "world_list": [
                {"index": i, "name": n, "design": d, "modifications": m, "opaque_id_rule": "sha256('V2CORE|'+name)[:12]"}
                for i, (n, d, m) in enumerate(WORLDS)
            ],
            "modification_semantics": {
                "donor_sd=weak": "sigma_d and tau = %.1f x development p05 for every gene" % WEAK_DONOR_FACTOR,
                "donor_sd=strong": "sigma_d and tau = %.1f x development p95 for every gene" % STRONG_DONOR_FACTOR,
                "donor_sd=absent": "sigma_d = tau = 0; no donor factor",
                "source=weak": "both |source contrasts| = development p25 of |source|, seeded signs",
                "source=absent": "source contrasts = 0 in both parts",
                "class=absent": "class contrasts = 0 in both parts",
                "depth2=absent": "beta2 = gamma2 = 0",
                "prevalence=sparse": "planted detection prevalence log-uniform Latin hypercube on [%.3f, %.2f]" % SPARSE_PREVALENCE_RANGE,
                "sigma=tail": "positive sigma = %.1f x development p95 for every gene" % TAIL_SIGMA_FACTOR,
                "operator=omitted_perturbation": (
                    "per gene and part, matrix offsets o_m ~ N(0, (%.1f x that gene's donor SD)^2), centred within "
                    "source (unweighted), added to the linear predictor; never fitted. On the S174 design matrices are "
                    "single-class in HVS/NPH52, so offsets partly mimic source x class structure. Q11 is a MILD "
                    "omitted-operator stress: a PASS qualifies robustness only to this frozen perturbation magnitude, "
                    "not to stronger operator effects, and it does not qualify an operator-free model universally."
                    % OPERATOR_SD_FRACTION),
            },
            "heldout_replicates": {
                "same_donors": "same design and planted donor effects, new observation noise",
                "new_donors": "same design slots, new donor effects (new f and e), new observation noise",
            },
            "truth_table": ("Rules frozen here. The realized per-gene truth tables, world manifests and file SHA-256 are "
                            "generated deterministically from these seeds and committed BEFORE any qualification fit."),
        },
        "scoring": {
            "interval": "central %.0f%% posterior interval (0.05/0.95 quantiles of all retained draws)" % (100 * INTERVAL_MASS),
            "standardized_error": "z = (posterior mean - truth) / posterior SD",
            "identification": (
                "For a factor (class or source), the scored quantities are the frozen Helmert contrasts when every "
                "level has >=1 informative observation in that part. Otherwise they are the level-effect differences "
                "against the first observed level. Informative means a measured cell for detection, or a positive "
                "measured cell for the positive part. The intercept is scored as alpha plus the mean of the observed "
                "class and source level effects. Donor effects are scored for donors with >=1 informative "
                "observation. Truth and posterior are transformed identically."),
            "quantity_types": FIXED_TYPES + ["donor_sd", "donor_effects", "sigma"],
            "descriptive_metrics": DESCRIPTIVE_METRICS,
            "descriptive_rationale": ("Predictive excess over the oracle has no data-independent acceptance threshold "
                                      "that is not a pure convention. Parameter calibration already gates generative "
                                      "correctness. Predictive metrics serve as implementation cross-checks and as "
                                      "reference values for later real-data held-out work."),
            "ppc": {
                "draws": PPC_DRAWS, "p_value": "two-sided mid-p: 2*min(P(T_rep>T_obs)+P(=)/2, P(T_rep<T_obs)+P(=)/2), capped at 1",
                "detection_statistics": ["zero fraction overall", "zero fraction by world z-decile (10)",
                                         "zero fraction by observed class", "zero fraction by observed source",
                                         "SD across donors (>=5 measured cells) of donor detection fraction"],
                "positive_statistics": ["mean log positive", "mean log positive by z-decile (deciles with >=5 positives)",
                                        "variance of log positive", "0.99 and 0.01 quantiles of log positive",
                                        "SD across donors (>=3 positives) of donor mean log positive"],
                "positive_replication": "conditional on the observed detection pattern (two-part model)",
                "draws_rationale": "1000 replicates give MC SE about 0.003 at p = 0.01",
            },
        },
        "gates": {
            "multiplicity": {
                "familywise_false_fail": FAMILYWISE_FALSE_FAIL, "n_hard_statistical_gates": n_stat_hard,
                "alpha_per_gate": alpha_test, "gate_counts": counts,
                "method": ("Bonferroni over every hard (FAIL-class) statistical gate in all worlds and parts. LIMIT-class "
                           "statistical gates are evaluated at the same alpha but cannot fail qualification, so they "
                           "do not enter the family."),
                "rationale": ("A correctly specified, well-implemented V2_CORE should fail no world by chance with "
                              "probability above 5%. RULE gates are deterministic and carry no alpha."),
            },
            "tests": {
                "one_sided_t_lower_across_genes": ("Per gene, the fraction c_g of its scored quantities whose interval "
                                                   "covers the truth. FAIL iff mean(c) < nominal and "
                                                   "t = (mean(c) - nominal) / (sd(c)/sqrt(n)) < -t_{1-alpha, n-1}. "
                                                   "If sd(c) = 0, FAIL iff mean(c) < nominal - 0.10. Genes are the "
                                                   "independent unit."),
                "two_sided_t_across_genes_and_materiality": ("Per gene, b_g = mean z over its quantities of that "
                                                             "type. FAIL iff |t| > t_{1-alpha/2, n-1} and |mean(b)| > "
                                                             "%.2f." % BIAS_MATERIALITY_STD),
                "binomial_lower": "misses over n single quantities; FAIL iff P(Bin(n, 1-nominal) >= misses) < alpha",
                "interval_excludes_zero_rate": ("truth 0: per gene, the fraction of quantities whose interval excludes "
                                                "0; same as one_sided_t_lower_across_genes applied to coverage of 0. "
                                                "Single-quantity types use binomial_lower. Rates at 95% and 99% are "
                                                "also reported."),
                "binomial_upper": "FAIL iff P(Bin(n, nominal) >= count) < alpha",
                "binomial_upper_q05_above_floor": ("false positive iff the posterior 5%% quantile of the donor SD "
                                                   "exceeds the floor (0.1 x development p05 donor SD). FAIL iff "
                                                   "P(Bin(n, %.2f) >= count) < alpha" % DONOR_ABSENT_NOMINAL),
                "TYPE_S": ("among source quantities whose interval excludes 0, wrong-sign count; binomial_upper with "
                           "nominal %.2f. With none excluded: no sign claims, the gate passes, power is reported as 0." % TYPE_S_NOMINAL),
                "PPC_EXTREME_RATE": ("count of (gene, statistic) with p < %.2f over all genes; binomial_upper with "
                                     "nominal %.2f. Posterior predictive p-values are conservative under correct "
                                     "specification, so this is a false-fail-safe check." % (PPC_EXTREME_P, PPC_EXTREME_P)),
                "POPULATION_DONOR_SD_RATIO": ("mean over genes of posterior-mean donor SD / mean planted donor SD "
                                              "must lie in [%.2f, %.2f] (CONVENTION). Gated only where the donor SD is "
                                              "well identified by construction: detection in Q00, Q02 and Q10, and "
                                              "positive in Q02. Elsewhere it is descriptive, because a weakly "
                                              "identified SD is expected to sit above a small truth under a proper "
                                              "prior." % POP_DONOR_RATIO_BOUNDS),
                "CONVERGENCE_ALL_FITS_DIAGNOSED": "every fit of the world in that part ends diagnosed after the frozen recovery path",
            },
            "binomial_reference_thresholds": binomial_thresholds(G, alpha_test),
            "list": gates,
        },
        "terminal_logic": {
            "world_verdict": ("FAIL if any FAIL-class gate fails. PASS_WITH_LIMITS if only LIMIT-class gates fail; "
                              "the LIMIT class is exactly the four donor-SD bias gates in Q01 (both parts), Q08 "
                              "positive and Q09 positive, whose coverage gates stay hard. PASS otherwise. Every Q11 "
                              "gate (fixed, donor and PPC) is hard: Q11 exists to test whether omitted measurement "
                              "structure is absorbed into donor biology or degrades model adequacy, and it must be able "
                              "to disqualify V2_CORE."),
            "terminal_lock": ("The first FAIL-class gate failure in any world immediately and irreversibly locks the "
                              "combined terminal of this qualification generation to "
                              "V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED. Every world result produced after that "
                              "point is labelled POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION. Such results "
                              "may map failure modes, but they cannot change the combined FAIL, select a model variant, "
                              "relax a gate or authorize downstream work."),
            "post_terminal_label": "POST_TERMINAL_DIAGNOSTIC__CANNOT_RESCUE_QUALIFICATION",
            "combined": {
                "PASS": "V2_CORE_SYNTHETIC_QUALIFICATION_PASS__CONTROLLER_AUDIT_REQUIRED__REAL_TRAIN_POSTERIOR_INFERENCE_STILL_OFF__FACTORIAL_SCIENCE_OFF__TRAINING_OFF",
                "FAIL": "V2_CORE_SYNTHETIC_QUALIFICATION_NOT_QUALIFIED__NO_TUNING__CONTROLLER_REVIEW_REQUIRED__REAL_TRAIN_POSTERIOR_INFERENCE_OFF__TRAINING_OFF",
                "INFRASTRUCTURE": "V2_CORE_SYNTHETIC_QUALIFICATION_INCOMPLETE__INFRASTRUCTURE_STOP__CONTROLLER_REVIEW_REQUIRED",
            },
            "rule": "PASS iff all 12 worlds are PASS or PASS_WITH_LIMITS; FAIL if any world FAILs",
            "run_policy": ("PR #286 ruling A (approved with terminal lock): the precommitted worlds run in the fixed "
                           "order Q00..Q11. After the terminal lock they continue only as post-terminal diagnostics. "
                           "Infrastructure, custody, poison-read and hash failures STOP immediately. No tuning, no "
                           "reruns with changed settings, no adaptive world change after generation, and no "
                           "resurrection of a failed fit."),
            "stopping": "after the combined receipt: STOP for controller audit in every outcome",
        },
        "resources": {
            "environment": "Windows, conda env v79-bayes (Python 3.11.17; see env_lock). No WSL fits and no simultaneous WSL/Windows fits.",
            "concurrency": "one heavy job at a time; a heavy job is one world process fitting its genes serially (det then pos per gene)",
            "settle_seconds_between_worlds": SETTLE_SECONDS,
            "xla_host_devices": CHAINS,
            "checkpoint": "atomic per-fit record (tmp + rename); a world restarts at its first missing or invalid fit record",
            "compact_outputs": ("per fit: JSON summaries (mean, SD, q05, q50, q95 per scalar; per donor) plus a float32 "
                                "npz of %d thinned donor-effect draws. No full chains are stored." % DONOR_DRAWS_STORED),
            "engineering_benchmark": ("Before launch, 2 genes x 2 parts on an engineering world (seed root %d, never "
                                      "scored) measure the time and memory per fit. If the projection exceeds %d h: "
                                      "STOP and report; no setting changes." % (ENGINEERING_SEED_ROOT, MAX_PROJECTED_HOURS)),
            "estimate": {
                "label": "ESTIMATE__TO_BE_REPLACED_BY_ENGINEERING_BENCHMARK",
                "n_fits": n_fits,
                "basis": ("prior V79 CPU fit: 20 genes jointly, 4 chains x 2000 iterations, mean 63 leapfrog steps, "
                          "1,155 s, about 0.46 ms per gene-gradient. V2_CORE single gene, about 45 steps, 4 chains in "
                          "parallel: about 45 s detection and 25 s positive, plus about 10 s JIT"),
                "per_world_hours": round(G * (45 + 25 + 20) / 3600, 2),
                "total_hours_without_retries": round(len(WORLDS) * G * 90 / 3600 + len(WORLDS) * SETTLE_SECONDS / 3600, 1),
                "allowance_for_escalation_extension": "x1.2",
                "peak_memory": "< 2 GB per fit process (4,726 cells, about 155 parameters)",
                "cpu": "4 of 16 logical cores during a fit",
            },
        },
        "result_schemas": {
            "fit_record": "V79_V2_CORE_FIT_RECORD_V1: fit_id, opaque world id, gene index, part, attempts[], final diagnosis, posterior summaries, ppc stats and p-values, input/contract/code hashes",
            "world_result": "V79_V2_CORE_WORLD_RESULT_V1: world manifest hash, truth hash, per-type recovery metrics, every gate (statistic, threshold, pass), verdict, descriptive metrics, second stage, resources",
            "receipt": "V79_V2_CORE_QUALIFICATION_RECEIPT_V1: contract SHA, code commit, environment, every world verdict and result hash, LIMIT list, combined terminal",
        },
        "blinding": ("The fitting stage reads only the world data file (design, observations, support mask) under an "
                     "opaque world ID. It has no path to the truth file and does not import the truth or scoring "
                     "code. Scoring runs only after every fit of a world is complete. The operator knows the mapping, "
                     "and no intervention is permitted between launch and the receipt, so analyst unblinding cannot "
                     "steer an outcome."),
        "ratified_conventions": {
            "ruling": "PR #286 controller ruling 6113874774, part C: ratified for this qualification generation only",
            "bias_materiality_std": {"value": BIAS_MATERIALITY_STD,
                                     "scope": "prospective practical-significance convention, not a universal inferential threshold"},
            "population_donor_sd_ratio": {"value": list(POP_DONOR_RATIO_BOUNDS), "scope": "prospective recovery convention"},
            "donor_absent_floor": {"fraction_of_dev_p05_donor_sd": DONOR_SD_FLOOR_FRACTION,
                                   "scope": "Q07 only; values in worlds.planting_magnitudes.fixed_magnitudes.donor_absent_floor"},
            "q11_operator_sd_fraction": {"value": OPERATOR_SD_FRACTION, "scope": "deliberately mild omitted-operator stress only"},
        },
        "declared_limitations": [
            "Positive values are continuous lognormal; integer discretization of real counts (mass at 1) is not tested (ZTNB question).",
            "Planting magnitudes come from ridge proxies; development donor SDs are shrinkage-biased low.",
            "Truths are fixed values, not prior draws, so coverage is not guaranteed nominal for weakly identified quantities. The gates test for material, significant deviation.",
            "Detection operator remains PRIOR_SENSITIVE__UNRESOLVED (development). Q11 probes one mild omitted-operator rule only.",
            "The second stage (across-gene distributions, cross-gene donor geometry) is descriptive only.",
            "The S174 design (4,726 cells, 149 donors) is smaller than corrected TRAIN; transfer to TRAIN is approximate.",
            "About 1% of development genes show near-separated detection source effects in measured cells (|contrast| about 8). These are not planted, and the N(0,1.5) prior would shrink them.",
        ],
        "development_finding_structural_support": {
            "finding": ("The V3 replay and the V1 planting calibration treated structurally unmeasured entries as "
                        "measured zeros. The corrective masked replay and its old-vs-masked A-H audit are the "
                        "authority; their numbers are not restated here."),
            "masked_replay": {"path": INPUTS["masked_replay"], "sha256": hashes["masked_replay"]},
            "masking_audit": {"path": INPUTS["masking_audit"], "sha256": hashes["masking_audit"],
                              "mechanical_A_to_H_preserved": all(q["mechanical_class_preserved"]
                                                                 for q in audit["questions_A_to_H"].values())},
            "consequence_here": ("V2_CORE enforces the support mask in the likelihood; worlds include structural "
                                 "absence as hash-bound truth; calibration V2 is masked and its join reproduces"),
            "controller_decision": "PENDING: whether V2_CORE remains frozen unchanged after the masked replay",
        },
    }
    return contract


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("root", type=Path)
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    c = build(a.root)
    text = json.dumps(c, indent=1, sort_keys=False) + "\n"
    out = a.root / CONTRACT_REL
    if a.check:
        if out.read_text(encoding="utf-8") != text:
            raise SystemExit("STOP: committed contract differs from a rebuild")
        print("contract rebuild identical:", hashlib.sha256(text.encode()).hexdigest())
        return
    out.write_text(text, encoding="utf-8", newline="\n")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    out.with_suffix(".sha256").write_text(f"{digest}  {out.name}\n", encoding="utf-8", newline="\n")
    print(json.dumps({"sha256": digest, "G": c["worlds"]["genes_per_world"],
                      "gate_counts": c["gates"]["multiplicity"]["gate_counts"],
                      "alpha_per_gate": c["gates"]["multiplicity"]["alpha_per_gate"],
                      "gene_derivation": c["worlds"]["gene_count_derivation"],
                      "binomial": c["gates"]["binomial_reference_thresholds"],
                      "magnitudes": c["worlds"]["planting_magnitudes"]["fixed_magnitudes"],
                      "estimate": c["resources"]["estimate"]}, indent=1))


if __name__ == "__main__":
    main()
