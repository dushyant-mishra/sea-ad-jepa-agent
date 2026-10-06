#!/usr/bin/env python
"""AGENT 5 - control firing proofs for the Morabito (GSE174367) benchmark.

WHY THIS EXISTS
    Lane A planted each of its controls' failures and found that
    GLOBAL_CONTEXT_ONLY did not fire on the exact failure it was written to
    catch: a query-conditioned predictor combined with a pooled cell summary
    already suffices to emit a query-local answer, so the "no query" comparator
    was never actually query-free. A control that cannot fail is not a control.

    This module therefore does not merely declare a negative-control suite. For
    every control it constructs two synthetic worlds with the real GSE174367
    geometry:

        DEFECT  - the exact artifact the control was written to catch is
                  planted. The control MUST refuse.
        GENUINE - a real effect of the kind the benchmark is trying to detect
                  is planted instead. The control MUST NOT refuse.

    A control passes its proof only if it fires in the first world and stays
    silent in the second. Either failure means the control is unusable and the
    protocol says so.

WHAT THIS IS NOT
    No JEPA model is loaded. No frozen representation is scored. No real
    expression or accessibility value is read. Every array here is synthetic and
    generated from a seed derived from the control's identity. This is a proof
    about the CONTROLS, not a biological result.

GOVERNANCE
    TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED |
    D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
import argparse
import hashlib
import json
import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

FOOTER = ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | PROTECTED_FULL104_OUTCOMES=UNOPENED | "
          "D_SHARED_G5=UNOPENED | RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF")

# Real geometry, transcribed from agent5_preparatory_manifest_v1.json.
# Synthetic fixtures must reproduce the dataset's geometry or they prove
# nothing about the real design.
N_SHARED_SAMPLES = 18
BATCH_SIZES = (4, 6, 8)            # samples per RNA batch on the shared 18
RNA_MG_CELLS_PER_SAMPLE = 229      # mean, real range 141-372
ATAC_MG_CELLS_PER_SAMPLE = 608     # mean on shared samples, real range 256-1284
N_PERMUTATIONS = 10000
ALPHA = 0.05


def seed_for(control_id, arm):
    """Seed from scientific identity (control + arm), never from array order or
    file layout."""
    h = hashlib.sha256(("agent5::%s::%s" % (control_id, arm)).encode()).digest()
    return int.from_bytes(h[:4], "big")


def spearman(x, y):
    xr = pd.Series(x).rank().values
    yr = pd.Series(y).rank().values
    xr = xr - xr.mean()
    yr = yr - yr.mean()
    denom = np.sqrt((xr ** 2).sum() * (yr ** 2).sum())
    return 0.0 if denom == 0 else float((xr * yr).sum() / denom)


def batch_vector():
    v = []
    for b, n in enumerate(BATCH_SIZES, start=1):
        v.extend([b] * n)
    assert len(v) == N_SHARED_SAMPLES
    return np.array(v)


def permutation_p(observed, null_draws, higher_is_better=True):
    null = np.asarray(null_draws, dtype=float)
    if higher_is_better:
        k = int((null >= observed).sum())
    else:
        k = int((null <= observed).sum())
    return (k + 1) / (null.size + 1)


def restricted_permute(rng, strata):
    """Permute indices within each stratum only."""
    idx = np.arange(len(strata))
    out = idx.copy()
    for s in np.unique(strata):
        m = np.where(strata == s)[0]
        out[m] = rng.permutation(m)
    return out


# ============================================================ N1

def n1_sample_label_permutation(arm):
    """Shuffled donor/sample assignment for the cross-modality outcome.

    Exchangeability restriction: permute the ATAC-side sample label WITHIN its
    RNA batch. Without the restriction the control would also destroy batch
    structure, so a purely technical batch association would look like a donor
    association and the control would wrongly pass it.
    """
    rng = np.random.default_rng(seed_for("N1", arm))
    batch = batch_vector()

    if arm == "DEFECT":
        # Planted artifact: BOTH modalities are driven only by batch. There is
        # no donor-specific correspondence at all.
        beff = rng.normal(0, 1, size=len(BATCH_SIZES) + 1)
        x = beff[batch] + rng.normal(0, 0.25, N_SHARED_SAMPLES)
        y = beff[batch] * 1.3 + rng.normal(0, 0.25, N_SHARED_SAMPLES)
    else:
        # Planted genuine effect: a donor-specific latent shared by both assays,
        # with batch deliberately uninformative.
        donor = rng.normal(0, 1, N_SHARED_SAMPLES)
        x = donor + rng.normal(0, 0.35, N_SHARED_SAMPLES)
        y = donor * 1.1 + rng.normal(0, 0.35, N_SHARED_SAMPLES)

    obs = spearman(x, y)
    restricted_null = [spearman(x, y[restricted_permute(rng, batch)])
                       for _ in range(N_PERMUTATIONS)]
    free_null = [spearman(x, rng.permutation(y)) for _ in range(N_PERMUTATIONS)]
    p_restricted = permutation_p(obs, restricted_null)
    p_free = permutation_p(obs, free_null)

    return dict(
        observed_statistic=round(obs, 5),
        p_restricted_within_batch=round(p_restricted, 5),
        p_unrestricted=round(p_free, 5),
        decision="REFUSE" if p_restricted > ALPHA else "ALLOW",
        note=("The unrestricted p is the one a careless design would quote."
              if arm == "DEFECT" else ""),
    )


# ============================================================ N2

def n2_peak_to_gene_link_shuffle(arm):
    """Shuffled regulatory links.

    Exchangeability restriction: reassign peaks to genes preserving chromosome,
    distance-to-TSS stratum, and the number of peaks per gene. An unrestricted
    shuffle is vacuous because promoter-proximal peaks track expression for
    reasons that have nothing to do with the specific link.
    """
    rng = np.random.default_rng(seed_for("N2", arm))
    n_genes, peaks_per_gene = 60, 6
    n_peaks = n_genes * peaks_per_gene
    gene_of_peak = np.repeat(np.arange(n_genes), peaks_per_gene)
    # Distance stratum 0 = promoter-proximal, 1 = distal.
    dist_stratum = np.tile(np.array([0, 0, 1, 1, 1, 1]), n_genes)
    chrom = np.repeat(rng.integers(1, 23, n_genes), peaks_per_gene)

    gene_expr = rng.normal(0, 1, n_genes)

    if arm == "DEFECT":
        # Planted artifact: accessibility depends only on the distance stratum
        # and on a gene-level abundance term that ANY promoter-proximal peak
        # would carry. The specific peak-gene link carries nothing.
        strat_effect = np.where(dist_stratum == 0, 1.0, 0.0)
        acc = strat_effect * gene_expr[gene_of_peak] + rng.normal(0, 0.4, n_peaks)
        # Break the link-specific component explicitly.
        acc = strat_effect * rng.normal(0, 1, n_peaks) * 0 + acc
    else:
        # Planted genuine effect: a link-specific component that only the TRUE
        # peak-gene assignment can recover.
        link_effect = rng.normal(0, 1, n_peaks)
        acc = (link_effect + 1.5 * gene_expr[gene_of_peak]
               + rng.normal(0, 0.4, n_peaks))
        gene_expr = gene_expr + 0.0

    def score(assignment):
        agg = np.zeros(n_genes)
        cnt = np.zeros(n_genes)
        np.add.at(agg, assignment, acc)
        np.add.at(cnt, assignment, 1.0)
        return spearman(agg / np.maximum(cnt, 1), gene_expr)

    obs = score(gene_of_peak)

    def matched_shuffle():
        out = gene_of_peak.copy()
        for c in np.unique(chrom):
            for d in np.unique(dist_stratum):
                m = np.where((chrom == c) & (dist_stratum == d))[0]
                out[m] = gene_of_peak[rng.permutation(m)]
        return out

    matched_null = [score(matched_shuffle()) for _ in range(1000)]
    free_null = [score(rng.permutation(gene_of_peak)) for _ in range(1000)]
    p_matched = permutation_p(obs, matched_null)
    p_free = permutation_p(obs, free_null)
    return dict(
        observed_statistic=round(obs, 5),
        p_distance_and_chromosome_matched=round(p_matched, 5),
        p_unrestricted=round(p_free, 5),
        decision="REFUSE" if p_matched > ALPHA else "ALLOW",
    )


# ============================================================ N3

def n3_tf_label_shuffle(arm):
    """Shuffled TF labels.

    Exchangeability restriction: permute the motif -> TF annotation within
    (GC-content decile x number-of-peaks-hit decile). A TF whose motif simply
    hits more peaks will otherwise always win, and an unrestricted shuffle
    would never notice.
    """
    rng = np.random.default_rng(seed_for("N3", arm))
    n_motifs, n_samples = 200, N_SHARED_SAMPLES
    n_hits = rng.integers(5, 500, n_motifs)
    gc = rng.uniform(0.2, 0.8, n_motifs)
    hit_decile = pd.qcut(n_hits, 5, labels=False, duplicates="drop")
    gc_decile = pd.qcut(gc, 5, labels=False, duplicates="drop")
    stratum = np.asarray(hit_decile) * 10 + np.asarray(gc_decile)

    target = rng.normal(0, 1, n_samples)

    if arm == "DEFECT":
        # Planted artifact: a motif's apparent association is a deterministic
        # function of how many peaks it hits. TF identity contributes nothing.
        base = np.log1p(n_hits)
        dev = np.outer(base / base.max(), target) + rng.normal(0, 0.3,
                                                               (n_motifs, n_samples))
    else:
        # Planted genuine effect: one specific motif, of middling hit count,
        # tracks the target; the rest do not.
        dev = rng.normal(0, 1, (n_motifs, n_samples))
        chosen = int(np.argsort(n_hits)[n_motifs // 2])
        dev[chosen] = 2.0 * target + rng.normal(0, 0.3, n_samples)

    tf_of_motif = np.arange(n_motifs) % 20   # 20 TFs, 10 motifs each

    # Motif-level association with the target is a property of the DATA, not of
    # the annotation, so it is computed once. Only the motif -> TF mapping is
    # permuted.
    abs_rho = np.array([abs(spearman(dev[i], target)) for i in range(n_motifs)])

    def score_by_annotation(annotation):
        """Statistic: the best mean association over the motifs carrying one TF
        label. A TF whose motifs simply hit more peaks will score high for
        reasons unrelated to TF identity."""
        n_tf = int(annotation.max()) + 1
        tot = np.zeros(n_tf)
        cnt = np.zeros(n_tf)
        np.add.at(tot, annotation, abs_rho)
        np.add.at(cnt, annotation, 1.0)
        return float(np.max(tot / np.maximum(cnt, 1)))

    obs = score_by_annotation(tf_of_motif)

    def matched_shuffle():
        out = tf_of_motif.copy()
        for s in np.unique(stratum):
            m = np.where(stratum == s)[0]
            out[m] = tf_of_motif[rng.permutation(m)]
        return out

    matched_null = [score_by_annotation(matched_shuffle()) for _ in range(300)]
    free_null = [score_by_annotation(rng.permutation(tf_of_motif))
                 for _ in range(300)]
    p_matched = permutation_p(obs, matched_null)
    p_free = permutation_p(obs, free_null)
    return dict(
        observed_statistic=round(obs, 5),
        p_gc_and_hitcount_matched=round(p_matched, 5),
        p_unrestricted=round(p_free, 5),
        decision="REFUSE" if p_matched > ALPHA else "ALLOW",

    )


# ============================================================ N4

def n4_matched_random_feature_sets(arm):
    """Matched random features.

    Exchangeability restriction: control gene sets drawn to match the real set
    on mean-abundance decile and detection-rate decile. Unmatched control sets
    are vacuous because abundant, widely detected genes are easier to predict
    for purely statistical reasons.
    """
    rng = np.random.default_rng(seed_for("N4", arm))
    n_genes = 2000
    abundance = rng.lognormal(0, 1, n_genes)
    detection = np.clip(abundance / (abundance + 2), 0.01, 0.99)
    ab_dec = pd.qcut(abundance, 10, labels=False, duplicates="drop")
    det_dec = pd.qcut(detection, 10, labels=False, duplicates="drop")
    stratum = np.asarray(ab_dec) * 10 + np.asarray(det_dec)

    # Per-gene predictability. Under DEFECT it is a pure function of abundance.
    if arm == "DEFECT":
        skill = np.log1p(abundance) / np.log1p(abundance).max()
        skill = skill + rng.normal(0, 0.02, n_genes)
        real_set = np.argsort(-abundance)[:50]      # the "interesting" set is
        #                                             just the abundant genes
    else:
        skill = rng.normal(0.2, 0.05, n_genes)
        real_set = rng.choice(n_genes, 50, replace=False)
        skill[real_set] += 0.35                     # genuine set-specific skill

    obs = float(skill[real_set].mean())

    def matched_draw():
        out = []
        for g in real_set:
            pool = np.where(stratum == stratum[g])[0]
            out.append(int(rng.choice(pool)))
        return np.array(out)

    matched_null = [float(skill[matched_draw()].mean()) for _ in range(2000)]
    free_null = [float(skill[rng.choice(n_genes, 50, replace=False)].mean())
                 for _ in range(2000)]
    p_matched = permutation_p(obs, matched_null)
    p_free = permutation_p(obs, free_null)
    return dict(
        observed_statistic=round(obs, 5),
        p_abundance_and_detection_matched=round(p_matched, 5),
        p_unrestricted=round(p_free, 5),
        decision="REFUSE" if p_matched > ALPHA else "ALLOW",
    )


# ============================================================ N5

def n5_query_address_channel(arm):
    """Query-address control for Outcome 2, written against the Lane A failure.

    Lane A's finding: a query-conditioned predictor plus a pooled cell summary
    already emits a query-local answer, so a comparator that lacks per-gene
    parameters is not a query-agnostic comparator - it is a weaker model, and
    the "increment" it produces is capacity, not query conditioning.

    The corrected comparator B4 therefore keeps the SAME per-gene readout
    capacity (including a per-gene intercept and a per-gene slope on the
    query-agnostic state) and differs from the query-conditional model in one
    respect only: whether the queried address is supplied.

    Three arms are evaluated:
      DEFECT_QUERY_BLIND   - predictor ignores the query entirely.
      DEFECT_GLOBAL_MEAN   - predictor uses the query only to look up a global
                             per-gene mean (the Lane A trap).
      GENUINE              - predictor modulates the answer by cell state in a
                             gene-specific way.
    """
    rng = np.random.default_rng(seed_for("N5", arm))
    n_cells, n_genes, d = 400, 60, 8
    state = rng.normal(0, 1, (n_cells, d))          # query-agnostic cell state
    gene_mean = rng.normal(0, 1, n_genes)
    gene_load = rng.normal(0, 1, (n_genes, d))

    if arm == "GENUINE":
        truth = gene_mean[None, :] + state @ gene_load.T
    else:
        truth = np.tile(gene_mean, (n_cells, 1))
    truth = truth + rng.normal(0, 0.3, (n_cells, n_genes))

    def predictor(kind, gene_idx):
        if kind == "query_blind":
            return np.repeat(state.mean(axis=1, keepdims=True), 1, axis=1).ravel()
        if kind == "global_mean":
            return np.full(n_cells, gene_mean[gene_idx])
        return gene_mean[gene_idx] + state @ gene_load[gene_idx]

    kind = {"DEFECT_QUERY_BLIND": "query_blind",
            "DEFECT_GLOBAL_MEAN": "global_mean",
            "GENUINE": "query_local"}[arm]

    def skill(pred, gene_idx):
        y = truth[:, gene_idx]
        resid = y - pred
        var = y.var()
        return 0.0 if var == 0 else float(1 - resid.var() / var)

    def comparator(gene_idx, with_per_gene_intercept):
        """B4: query-agnostic state read out per gene, same capacity."""
        y = truth[:, gene_idx]
        X = state
        if with_per_gene_intercept:
            X = np.hstack([np.ones((n_cells, 1)), state])
        beta, *_ = np.linalg.lstsq(X, y, rcond=None)
        return skill(X @ beta, gene_idx)

    deltas_correct, deltas_naive = [], []
    for g in range(n_genes):
        s_model = skill(predictor(kind, g), g)
        deltas_correct.append(s_model - comparator(g, True))
        deltas_naive.append(s_model - comparator(g, False))

    # Query-address shuffle: answer gene g while being handed address g'.
    shuffled = rng.permutation(n_genes)
    deltas_shuffled = []
    for g in range(n_genes):
        s_model = skill(predictor(kind, int(shuffled[g])), g)
        deltas_shuffled.append(s_model - comparator(g, True))

    med_correct = float(np.median(deltas_correct))
    med_naive = float(np.median(deltas_naive))
    med_shuffled = float(np.median(deltas_shuffled))
    fires = med_correct <= 0 or med_correct <= med_shuffled
    return dict(
        median_delta_vs_corrected_comparator=round(med_correct, 5),
        median_delta_vs_naive_comparator_no_per_gene_intercept=round(med_naive, 5),
        median_delta_under_shuffled_query_address=round(med_shuffled, 5),
        decision="REFUSE" if fires else "ALLOW",
        lane_a_trap_reproduced=bool(arm == "DEFECT_GLOBAL_MEAN"
                                    and med_naive > 0 >= med_correct),
    )


# ============================================================ N6

def n6_random_encoder(arm):
    """Untrained-encoder control.

    If a randomly initialised encoder of the same width, read out with the same
    fitting budget, scores as well as the frozen state, the benchmark is
    measuring the readout, not the model.
    """
    rng = np.random.default_rng(seed_for("N6", arm))
    n_cells, d_in, d_out = 300, 200, 64
    x = rng.normal(0, 1, (n_cells, d_in))
    w_true = rng.normal(0, 1, (d_in, 4))
    y = x @ w_true[:, 0] + rng.normal(0, 0.5, n_cells)

    if arm == "DEFECT":
        # Planted artifact: the "trained" encoder is a random projection too,
        # and the readout is so wide it fits anything.
        enc_trained = rng.normal(0, 1, (d_in, d_out))
    else:
        # Planted genuine effect: the trained encoder actually aligns with the
        # signal direction.
        enc_trained = np.zeros((d_in, d_out))
        enc_trained[:, 0] = w_true[:, 0]
        enc_trained[:, 1:] = rng.normal(0, 0.05, (d_in, d_out - 1))
    enc_random = rng.normal(0, 1, (d_in, d_out))

    def cv_r2(enc):
        z = x @ enc
        folds = np.arange(n_cells) % 5
        preds = np.zeros(n_cells)
        for f in range(5):
            tr, te = folds != f, folds == f
            A = np.hstack([np.ones((tr.sum(), 1)), z[tr]])
            beta, *_ = np.linalg.lstsq(A, y[tr], rcond=None)
            preds[te] = np.hstack([np.ones((te.sum(), 1)), z[te]]) @ beta
        return float(1 - ((y - preds) ** 2).sum() / ((y - y.mean()) ** 2).sum())

    r_trained, r_random = cv_r2(enc_trained), cv_r2(enc_random)
    fires = (r_trained - r_random) <= 0.02
    return dict(
        cv_r2_frozen_state=round(r_trained, 5),
        cv_r2_random_encoder=round(r_random, 5),
        margin=round(r_trained - r_random, 5),
        decision="REFUSE" if fires else "ALLOW",
    )


# ============================================================ N7

ADMISSIBLE_JOIN_KEYS = {"SampleID", "sample_id", "Sample.ID"}


def assert_no_cell_level_cross_modality_join(join_keys):
    """Runtime guard. Any cross-modality merge must key on the sample."""
    bad = [k for k in join_keys if k not in ADMISSIBLE_JOIN_KEYS]
    return dict(join_keys=list(join_keys), forbidden_keys_used=bad,
                decision="REFUSE" if bad else "ALLOW")


def n7_pairing_forgery(arm):
    if arm == "DEFECT":
        keys = ["Barcode"]
    elif arm == "DEFECT_SUBTLE":
        keys = ["SampleID", "cell_index"]
    else:
        keys = ["SampleID"]
    return assert_no_cell_level_cross_modality_join(keys)


# ============================================================ N8

def n8_stage75f_independence_guard(arm):
    """Stage75F may be a prior. It may not also be the outcome."""
    if arm == "DEFECT":
        cfg = dict(prior_source="stage75f", outcome_source="stage75f")
    elif arm == "DEFECT_RENAMED":
        cfg = dict(prior_source="stage75f",
                   outcome_source="stage75f_tf_target_summary_v1")
    else:
        cfg = dict(prior_source="stage75f",
                   outcome_source="external_distance_rule_peak_to_gene")
    prior_is_75f = "stage75f" in cfg["prior_source"]
    outcome_is_75f = "stage75f" in cfg["outcome_source"]
    circular = prior_is_75f and outcome_is_75f
    return dict(
        config=cfg,
        independence_label=("NON_INDEPENDENT" if (prior_is_75f or outcome_is_75f)
                            else "INDEPENDENT"),
        circular_prior_and_outcome=circular,
        may_contribute_to_pass=bool(not (prior_is_75f or outcome_is_75f)),
        decision="REFUSE" if circular else "ALLOW",
    )


# ============================================================ registry

CONTROLS = [
    dict(control_id="N1", name="sample_label_permutation",
         targets="Outcome 3", fn=n1_sample_label_permutation,
         defect_arms=["DEFECT"], genuine_arms=["GENUINE"]),
    dict(control_id="N2", name="peak_to_gene_link_shuffle",
         targets="Outcome 3a", fn=n2_peak_to_gene_link_shuffle,
         defect_arms=["DEFECT"], genuine_arms=["GENUINE"]),
    dict(control_id="N3", name="tf_label_shuffle",
         targets="Outcome 3b", fn=n3_tf_label_shuffle,
         defect_arms=["DEFECT"], genuine_arms=["GENUINE"]),
    dict(control_id="N4", name="matched_random_feature_sets",
         targets="Outcomes 1-3", fn=n4_matched_random_feature_sets,
         defect_arms=["DEFECT"], genuine_arms=["GENUINE"]),
    dict(control_id="N5", name="query_address_shuffle_and_capacity_matched_comparator",
         targets="Outcome 2", fn=n5_query_address_channel,
         defect_arms=["DEFECT_QUERY_BLIND", "DEFECT_GLOBAL_MEAN"],
         genuine_arms=["GENUINE"]),
    dict(control_id="N6", name="random_encoder",
         targets="Outcomes 1-3", fn=n6_random_encoder,
         defect_arms=["DEFECT"], genuine_arms=["GENUINE"]),
    dict(control_id="N7", name="cell_level_pairing_forgery_detector",
         targets="Outcome 3", fn=n7_pairing_forgery,
         defect_arms=["DEFECT", "DEFECT_SUBTLE"], genuine_arms=["GENUINE"]),
    dict(control_id="N8", name="stage75f_independence_guard",
         targets="Outcomes 2-3", fn=n8_stage75f_independence_guard,
         defect_arms=["DEFECT", "DEFECT_RENAMED"], genuine_arms=["GENUINE"]),
]


def run_proofs():
    rows, detail = [], {}
    for c in CONTROLS:
        arms = {}
        for arm in c["defect_arms"] + c["genuine_arms"]:
            arms[arm] = c["fn"](arm)
        fired_on_all_defects = all(arms[a]["decision"] == "REFUSE"
                                   for a in c["defect_arms"])
        silent_on_genuine = all(arms[a]["decision"] == "ALLOW"
                                for a in c["genuine_arms"])
        verdict = ("CONTROL_PROVEN_ABLE_TO_FIRE" if fired_on_all_defects and silent_on_genuine
                   else ("CONTROL_DOES_NOT_FIRE_ON_ITS_OWN_TARGET_DEFECT"
                         if not fired_on_all_defects
                         else "CONTROL_ALWAYS_REFUSES__NOT_A_CONTROL"))
        rows.append(dict(
            control_id=c["control_id"], control_name=c["name"],
            targets_outcome=c["targets"],
            defect_arms=";".join(c["defect_arms"]),
            fired_on_every_planted_defect=bool(fired_on_all_defects),
            silent_on_planted_genuine_effect=bool(silent_on_genuine),
            proof_verdict=verdict))
        detail[c["control_id"]] = arms
    return pd.DataFrame(rows), detail


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    tbl, detail = run_proofs()
    tbl.to_csv(os.path.join(args.out_dir,
                            "agent5_control_firing_proof_v1.csv"), index=False)

    manifest = dict(
        agent="AGENT_5_biological_validation_and_jepa_comparison_design",
        artifact="control_firing_proof_v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        governance_footer=FOOTER,
        execution_class="SYNTHETIC_FIXTURE_PROOF_ABOUT_CONTROLS",
        biological_evaluation_status="NOT_EXECUTED",
        model_loaded=False,
        real_expression_or_accessibility_values_read=False,
        motivation=("Lane A planted each control's failure and found "
                    "GLOBAL_CONTEXT_ONLY did not fire on the defect it targeted, "
                    "because a query-conditioned predictor plus a pooled cell "
                    "summary already emits a query-local answer. Every control "
                    "here is therefore proven against a planted instance of its "
                    "own target defect AND against a planted genuine effect."),
        fixture_geometry=dict(
            shared_samples=N_SHARED_SAMPLES, batch_sizes=list(BATCH_SIZES),
            rna_microglia_cells_per_sample_mean=RNA_MG_CELLS_PER_SAMPLE,
            atac_microglia_cells_per_sample_mean=ATAC_MG_CELLS_PER_SAMPLE,
            source="agent5_preparatory_manifest_v1.json"),
        alpha=ALPHA, n_permutations=N_PERMUTATIONS,
        summary=json.loads(tbl.to_json(orient="records")),
        arm_detail=detail,
        all_controls_proven=bool((tbl.proof_verdict
                                  == "CONTROL_PROVEN_ABLE_TO_FIRE").all()),
    )
    mp = os.path.join(args.out_dir, "agent5_control_firing_proof_v1.json")
    with open(mp, "w") as fh:
        json.dump(manifest, fh, indent=2)
    print(tbl.to_string(index=False))
    print("\nall_controls_proven:", manifest["all_controls_proven"])
    print("wrote:", mp)


if __name__ == "__main__":
    main()
