#!/usr/bin/env python3
"""BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1: the single source of the V79 lane's frozen contract.

`build()` returns the contract as a dict; `main()` writes the JSON and renders the Markdown from it, so the two
cannot drift. Firewall lists, the class map and gene-sampling constants are read from the code that enforces
them; a test checks they agree. Settings that depend on the compute benchmark are frozen here as RULES, and the
benchmark record supplies only the value, before any real-data inference.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import v79_data as DA  # noqa: E402
import v79_firewall as FW  # noqa: E402

NL = chr(10)
JSON_OUT = ROOT / "docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json"
MD_OUT = ROOT / "docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.md"
CUSTODY = ROOT / "results/v79/V79_CORRECTED_TRAIN_CUSTODY_RECEIPT_V1.json"


def sha_file(p) -> str:
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def build() -> dict:
    return dict(
        schema="BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1",
        status="FROZEN_BEFORE_ANY_REAL_DATA_INFERENCE",
        lane_terminal=FW.LANE_TERMINAL,
        lineage=dict(
            branch="analysis/v79-bayesian-synthetic-geometry-20261009",
            base_branch="impl/v78-signed-detection-marginals-20261009 (PR #242)",
            handoff_head="ce0ccc6d528a4c892d2afd50dd7ba9cd65a551e2",
            branched_from="e959d9a732698ae9a41e8cb1f6c10052d7390326",
            why_different=("PR #242 moved after the handoff: V78's frozen F0-F3 execution, tournament receipt and "
                           "no-promotion scientific ruling were committed. This lane changes nothing in V78")),
        purpose=("Estimate the population geometry and uncertainty structure of corrected S174 TRAIN data, so future "
                 "synthetic worlds can be judged against posterior distributions rather than brittle point estimates "
                 "or underpowered bootstrap bands. Not optimization of a generator; not target discovery"),
        questions={
            "Q1": "variation attributable to broad cell class",
            "Q2": "variation attributable to donor",
            "Q3": "variation attributable to source/cohort",
            "Q4": "variation attributable to observation operator",
            "Q5": "whether donor x class interaction is materially supported",
            "Q6": "residual within-class variation",
            "Q7": "dependence in detection versus positive expression",
            "Q8": "uncertainty of pooled-versus-within-class geometry such as T5",
            "Q9": "uncertainty of abundance and depth distributions across donors and operators",
            "Q10": "which corrected real statistics are stable population quantities versus noisy finite-sample realizations"},
        data=dict(
            substrate="corrected S174 TRAIN cache only; the pre-repair scrambled cache is never read",
            custody_receipt=dict(path=CUSTODY.relative_to(ROOT).as_posix(),
                                 sha256=sha_file(CUSTODY) if CUSTODY.exists() else None,
                                 required_terminal="PASS_V79_CORRECTED_TRAIN_CUSTODY_AUTHENTICATED"),
            design="4,726 cells; 149 donors (HVS 62, SEA_AD 68, NPH52 19); 42 operators; 3 sources; 426 donor-class "
                   "groups; 148 of 149 donors appear in two or more operators",
            gene_population=dict(universe=f"addresses detected in more than {DA.PREVALENCE_FLOOR:.0%} of TRAIN cells "
                                          "(14,417; equal to the frozen corrected evaluation universe)",
                                 sample="equal numbers per prevalence decile, without identity, frozen seed",
                                 seed=DA.GENE_SAMPLE_SEED, deciles=DA.N_DECILES,
                                 same_genes_for_phases="A, B and C use one gene sample so detection and positive "
                                                       "expression are compared on the same genes")),
        firewall=dict(
            allowed_meta_fields=list(FW.ALLOWED_META_FIELDS), allowed_bridge_fields=list(FW.ALLOWED_BRIDGE_FIELDS),
            allowed_split_columns=list(FW.ALLOWED_SPLIT_COLUMNS), denied_field_patterns=list(FW.DENY_FIELD_PATTERNS),
            denied_path_patterns=list(FW.DENY_PATH_PATTERNS),
            never_consumed=["TD panel membership", "TD56-TD60 outcomes", "target rankings", "disease-target priors",
                            "SCENIC+ edges", "Nott/ATAC evidence", "NIH-CARD outcomes", "pathology labels",
                            "TEST/Morabito/DEV/SEALED data", "named disease marker programs"],
            gene_identity="never read; cache columns are address indices used internally for alignment only"),
        broad_class=dict(
            primary_map=FW.CLASS_MAP, broad_classes=list(FW.BROAD_CLASSES),
            why=("the corrected TRAIN meta carries source-specific vocabularies (canonical three-way labels, SEA-AD "
                 "subclass labels, NPH52 short codes); the existing V77 class-composition authority keeps all 24 raw "
                 "labels and defines no three-way map, so this standard-taxonomy map is frozen here before any fit"),
            sensitivity=["canonical-label cells only (4,352)", "the 24 raw labels as classes (Phase D, where the T5 "
                         "reference itself uses raw labels with a 200-cell floor)"]),
        models=dict(
            linear_predictor=("eta[c,g] = mu[g] + class[k,g] + source[s,g] + operator[o,g] + donor[d,g] "
                              "+ donor_class[j,g] + b[g] * log_library_centered[c]"),
            parameterization=("class and source: fixed effects, exchangeable sum-to-zero N(0, 1.5) prior on K-1 "
                              "orthonormal contrasts. operator and donor: random effects within source; donor_class: "
                              "random effect within class; each on a block-orthonormal within-parent sum-to-zero "
                              "basis, coefficients ~ N(0, sd_x[g]). Per-gene log sd_x[g] ~ N(m_x, s_x) shared across "
                              "genes; m_x ~ N(log 0.3, 1), s_x ~ HalfNormal(0.5); mu ~ N(data centre, 2.5); "
                              "b ~ N(0, 1). Sampler parameterization (centring changes the sampler's geometry, not "
                              "the posterior; chosen on simulations only): per-gene log sds centred; effects centred, "
                              "except donor_class effects non-centred for detection and for both Phase C families "
                              "(amendment A1)"),
            interpretation={"class": "between-class differences", "source": "between-source differences",
                            "operator": "operator variation within a source", "donor": "donor variation within a source",
                            "donor_class": "donor-specific class deviation within a class",
                            "residual": "cell-level variation within donor, class and operator (biology and "
                                        "measurement noise together)"},
            observation_not_biology="operator and source are observation effects, never latent biological classes",
            variance_definition=("realized (finite-population) variance of each component's effects over the observed "
                                 "cells; fractions = component / (sum of components + residual)"),
            phases={
                "A": "Gaussian on log1p(count / library * 1e4) (library = sum over cached columns, as the corrected "
                     "reference builders); model and computational qualification",
                "B0": "cell-level Gaussian models of log library size (source_library) and log detected features, "
                      "same components, no depth covariate (Q9)",
                "B": "Bernoulli-logit detection, residual pi^2/3 on the logit scale",
                "C": "positive magnitude conditional on detection; candidate families log-normal on log count and "
                     "zero-truncated negative binomial with log-depth offset; family chosen by held-out-donor log "
                     "predictive density per positive observation (rule frozen here)",
                "C_detail": ("amendment A2. Offset: log of the cached-address library (the Phase A library); the "
                             "depth covariate is as in A and B. Log-normal: Gaussian on log count minus the offset over "
                             "detected cells. Zero-truncated NB: NB2(mean exp(eta + offset), dispersion phi[g]) "
                             "conditioned on a positive count; log phi[g] ~ N(m_phi, s_phi), m_phi ~ N(log 2, 1.5), "
                             "s_phi ~ HalfNormal(0.5). Both families are scored on the count scale, because a density "
                             "on log count and a probability on count are not comparable: the log-normal as the "
                             "probability it puts on [k - 1/2, k + 1/2) renormalised above 1/2. Pointwise lpd = log "
                             "mean over 1,000 thinned draws with new donor and donor-class effects; family score = "
                             "mean over every held-out positive observation; the higher score wins; the paired "
                             "difference's donor-clustered standard error is a diagnostic only. Variance fractions of "
                             "the NB family use the Nakagawa, Johnson & Schielzeth (2017) log-normal approximation "
                             "ln(1 + 1/lambda + 1/phi), lambda = exp(mu + mean offset over the gene's detected cells "
                             "+ total component variance / 2): a labelled convention for the truncated model. Counts "
                             "that are not non-negative integers stop Phase C"),
                "D1": "nested donor-then-cell Bayesian bootstrap (Dirichlet(1) weights) of the geometry statistics "
                      "exactly as the corrected reference builders define them (both layers, pooled and within-class, "
                      "T5, signed, eigenspectrum, abundance, depth); 1,000 draws (quantile Monte Carlo error about "
                      "0.7 percentile points at the 5th and 95th)",
                "D2": "model-based residual dependence (low-rank factor layer): specified in a V2 contract after "
                      "Phases A-C qualify; not part of V1 real inference"},
            donor_class_support=("reported as the posterior of the across-gene median donor-class fraction and the "
                                 "held-out-donor log predictive density difference between models with and without "
                                 "donor-class; 'supported' is used only when the difference exceeds two standard errors "
                                 "(a labelled convention)")),
        inference=dict(
            framework="NumPyro NUTS on JAX (a Pyro port was abandoned on measured speed; see the self-audit log)",
            chains=4, warmup=1000, draws=1000, target_accept=0.9, max_tree_depth=10,
            retry="any divergence: refit once at target_accept 0.95, then 0.99; still divergent: NOT_DIAGNOSED",
            seed_base=20261009,
            gene_count_rule=("the largest multiple of 10, at most 60, for which one 4-chain fit on the qualified "
                             "hardware completes within 2 hours in the compute benchmark; set before real inference"),
            fold_rule="5 held-out-donor folds if one fit takes at most 30 minutes, otherwise 2; set from the benchmark",
            variational_inference="allowed for exploration only; never reported as a diagnosed posterior"),
        diagnostics=dict(
            rhat="rank-normalized split R-hat at most 1.01 on every hyperparameter, per-gene log sd, intercept, depth "
                 "slope and contrast (Vehtari et al. 2021)",
            ess="bulk and tail ESS at least 400 on the same sites (Vehtari et al. 2021)",
            divergences="zero after the retry rule",
            tree_depth="fraction of iterations at maximum depth reported",
            failing_fit="a fit that misses any criterion is reported as NOT_DIAGNOSED and its estimates are not interpreted"),
        simulation_recovery=dict(
            design=("planted worlds on the real grouping structure (identity-free), Gaussian and Bernoulli; and "
                    "(amendment A3) the zero-truncated NB, new in Phase C, which must pass the same suite before Phase "
                    "C real inference. The inference retry rule applies to every recovery fit"),
            scenarios={"S1_present": "every component present at known magnitude",
                       "S0_class_absent": "class variance zero, others present",
                       "S2_class_permuted": "S1 data fitted with class labels permuted within source",
                       "S3_donor_only": "only donor variance (class and others zero)",
                       "S4_operator_only": "only operator variance",
                       "S5_labels_removed": "S1 data fitted without donor and donor-class components"},
            criteria={
                "coverage": ("per scenario, the share of planted per-gene fractions inside their 90% posterior interval "
                             "is at least the binomial 1% lower quantile of Binomial(n, 0.9) / n (derived, not chosen)"),
                "no_invented_class": ("in S0, S2, S3 and S4 the 95th percentile of the across-gene median class fraction "
                                      "is below the 5th percentile of the same quantity in S1"),
                "confounding": "in S3 and S4 the planted component is recovered under the coverage rule",
                "labels_matter": ("in S5 the residual fraction's 5th percentile exceeds its 95th percentile in S1"),
                "diagnostics": "every recovery fit meets the diagnostics section"},
            must_pass_before_real_inference=True),
        validation=dict(
            frozen_before_real_posteriors=True,
            posterior_predictive=["per-gene detection rate", "per-gene positive-count quantiles",
                                  "library-depth distribution", "detected-feature distribution", "class composition",
                                  "pooled and within-class correlation distributions among the sampled genes",
                                  "signed positive and negative dependence", "eigenspectrum summaries",
                                  "between-class versus within-class dispersion", "donor-level heterogeneity",
                                  "operator and source heterogeneity"],
            held_out_donors=("folds by donor, stratified by source, frozen seed; fit on the remaining donors; held-out "
                             "donors predicted with new donor and donor-class effects drawn from the fitted spreads"),
            reporting=("for every statistic, the observed value's position in its 90% predictive interval; a model "
                       "failing a check is reported as inadequate for that statistic, never tuned to pass it"),
            expected_failure=("the variance-component models carry no gene-gene residual dependence, so the correlation "
                              "checks are expected to fail for A-C; that failure motivates D2 and is reported as such")),
        s159=dict(treatment=("not repaired by decree: no widening, no larger bootstrap declared sufficient, no "
                             "re-centring. D1 reports each statistic's nested-Bayesian-bootstrap posterior beside the "
                             "full-data point and the historical with-replacement band, and measures the resampling "
                             "shift; existing points stay descriptive and existing bands stay diagnostics")),
        outputs=dict(
            scientific_internal="results/v79/internal/: gene-address-level analysis for validation; never consumed by "
                                "the synthetic generator",
            synthetic_consumable=("results/v79/V79_SYNTHETIC_GEOMETRY_ARTIFACT_V1.json: identity-scrubbed posterior "
                                  "summaries only (variance fractions, T5-like ratio, detection dependence, abundance "
                                  "and depth predictive summaries, eigenspectrum summaries); passes v79_firewall.scrub"),
            first_real_result="an estimation result, not synthetic authorization"),
        v78=("V78 F0-F3 is untouched: seeds, definitions, effect sizes, scoring, evaluation universe and pass/fail "
             "criteria are not changed, and no synthetic arm is tuned to these posteriors"),
        non_goals=["TD56/TD57B/TD59 replay or any target discovery", "target Bayesian modelling",
                   "353 historical ID remediation", "E4 donor x class synthetic implementation", "JEPA training",
                   "optimizer, EMA or runtime changes", "TEST/Morabito", "Stage 4", "500K",
                   "production target or representation selection"],
        amendments=[
            dict(id="A1", date="2026-10-10", before_real_data=True,
                 change=("parameterization text corrected: per-gene log sds are centred (the V1 text said non-centred; "
                         "self-audit entry 10), and donor_class effects are non-centred for detection (self-audit "
                         "entry 16) and for the Phase C families"),
                 why=("centring is a sampler setting; the model and its posterior are unchanged; the text must state "
                      "what runs")),
            dict(id="A2", date="2026-10-10", before_real_data=True,
                 change="Phase C details: offset, dispersion prior, count-scale scoring, residual convention",
                 why=("the frozen family rule compares a log-count density with a count probability unless both are "
                      "evaluated on counts; this fixes the only valid evaluation without changing the rule")),
            dict(id="A3", date="2026-10-10", before_real_data=True,
                 change="the zero-truncated NB must pass the recovery suite; the retry rule applies to recovery fits",
                 why="a likelihood new in Phase C gets the same simulation qualification as A and B (stricter)"),
            dict(id="A4", date="2026-10-10", before_real_data=True,
                 change=("Output B also exports magnitudes: the across-gene spread of each component's absolute "
                         "realized variance, the population hyperparameters (typical per-gene log sd and its "
                         "spread across genes), and B0's absolute depth and detected-feature variances by component"),
                 why=("the consumer (PR #253 sections 8.1, 8.2 and 15) needs anonymous effect-magnitude and "
                      "capture-spread distributions, not only shares; no estimand or rule changes"))],
        amended_from_sha256="1807ddb1b9071f5465873e076ebd6a1fbab6b5fcc14e7ec87bd505525144833b",
        terminal_authority=[FW.LANE_TERMINAL, "no target winner", "no representation winner",
                            "no JEPA training authority", "no E4 authority", "no protected-data authority",
                            "no production synthetic arm authority"])


def render(c: dict) -> str:
    L = ["# Bayesian synthetic-geometry contract V1", "", f"**Status:** `{c['status']}`. **Lane:** `{c['lane_terminal']}`.",
         "", "Generated from `scripts/v79/v79_contract.py`; the JSON twin is "
         "`docs/agent/BAYESIAN_SYNTHETIC_GEOMETRY_CONTRACT_V1.json`.", ""]

    def section(title, obj, level=2):
        L.append("#" * level + " " + title)
        L.append("")
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (dict, list)):
                    L.append(f"**{k.replace('_', ' ')}:**")
                    L.append("")
                    items = v.items() if isinstance(v, dict) else enumerate(v)
                    for kk, vv in items:
                        L.append(f"- {kk}: {vv}" if isinstance(v, dict) else f"- {vv}")
                    L.append("")
                else:
                    L.append(f"**{k.replace('_', ' ')}:** {v}")
                    L.append("")
        elif isinstance(obj, list):
            for x in obj:
                if isinstance(x, dict) and "id" in x:
                    L.append(f"- **{x['id']}** ({x['date']}; before real data: {x['before_real_data']}): "
                             f"{x['change']}. Why: {x['why']}.")
                else:
                    L.append(f"- {x}")
            L.append("")
        else:
            L.extend([str(obj), ""])
    for key, title in [("lineage", "Lineage"), ("purpose", "Purpose"), ("questions", "Questions"), ("data", "Data"),
                       ("firewall", "Information firewall"), ("broad_class", "Broad cell class"),
                       ("models", "Models"), ("inference", "Inference"), ("diagnostics", "Diagnostics"),
                       ("simulation_recovery", "Simulation recovery"), ("validation", "Validation plan"),
                       ("s159", "S159"), ("outputs", "Outputs"), ("v78", "Relationship to V78"),
                       ("non_goals", "Non-goals"),
                       ("amendments", f"Amendments before real-data inference (from {c['amended_from_sha256'][:12]})"),
                       ("terminal_authority", "Terminal authority")]:
        section(title, c[key])
    return NL.join(L) + NL


def main() -> None:
    c = build()
    # explicit LF: Path.write_text writes CRLF on Windows (the defect that stopped the TD preflight)
    with open(JSON_OUT, "w", encoding="utf-8", newline=NL) as fh:
        fh.write(json.dumps(c, indent=1, ensure_ascii=False) + NL)
    with open(MD_OUT, "w", encoding="utf-8", newline=NL) as fh:
        fh.write(render(c))
    print("contract written", JSON_OUT.name, sha_file(JSON_OUT))


if __name__ == "__main__":
    main()
