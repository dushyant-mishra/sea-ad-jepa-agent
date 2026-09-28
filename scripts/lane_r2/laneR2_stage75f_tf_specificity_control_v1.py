#!/usr/bin/env python
"""LANE R2 - Stage75F TF-specificity: regulatory biology, or annotation supply?

READ-ONLY. Reruns no motif enrichment, no cisTarget scan, no training. Reads
only frozen Stage75F artifacts that already exist on disk and hashes each one.

THE QUESTION
------------
Stage75F ran ten per-TF cisTarget motif-enrichment analyses over ten
target-gene region sets and sorted the ten regulators into tiers by whether an
enriched motif carried that TF name. Downstream the bottom tier has been read
as a negative control. That reading is only valid if the tier a TF lands in
reflects something about that TF in those regions. Two nuisance explanations
must be excluded first:

  (a) ANNOTATION SUPPLY. A TF with many motifs annotated to it in the motif
      collection will collect a "supported" motif by chance alone.
  (b) SHARED QUERY REGIONS. If the ten query region sets are near-identical,
      the enriched motif set is near-constant across the ten analyses, and the
      enrichment test carries no TF-specific information at all. In that case
      TF specificity is not identifiable from this design, whatever the tiers
      look like.

FOUR TESTS, EACH ABLE TO FAIL
-----------------------------
T1 TF-LABEL PERMUTATION. Build S[t][b] = |E_b n A_t|, the support the
   annotation set of TF t receives from the enriched set of batch b. Observed
   statistic = trace(S). Null = permute which batch wears which TF label, i.e.
   sum_t S[t][pi(t)], enumerated EXACTLY over all 10! assignments. This holds
   each TF annotation supply exactly fixed and asks only whether the regions of
   a TF enrich its own motifs more than the regions of another TF do. That is
   the specificity question. PR #179 did not run this test: it drew a random
   motif set of size |E| from the collection, which is the hypergeometric null
   of T2 re-estimated by Monte Carlo, not a TF-label permutation. No numerical
   result from that branch is inherited here.

T2 ANNOTATION-SUPPLY NULL. Exact hypergeometric: does |E_t n A_t| exceed what
   |E_t| draws from the collection would hit given |A_t| annotated motifs?

T3 REGION-SET SPECIFICITY. Pairwise overlap of the ten query region sets, the
   ten mapped cisTarget database region sets, and the ten target-gene sets. If
   these are near-identical, T1 is structurally unable to reject and we say so
   rather than reporting a null result as evidence of absence.

T4 STRUCTURAL DISTINCTNESS. Mandatory and fail-closed. Stage73 once reported
   shuffled-graph controls that were structurally IDENTICAL to the real graph
   because only a mode LABEL changed. Every shuffle built here is therefore
   measured, not named: content digest, element count, changed-element
   fraction, set/rank correlation, and marginal preservation. Two planted
   controls gate the run:
     PLANTED_IDENTICAL - the original data carrying the label SHUFFLED.
                         The harness MUST report it unchanged. This is the
                         Stage73 bug reproduced deliberately.
     PLANTED_VALID     - a verified derangement. The harness MUST report it
                         changed.
   If either planted control returns the wrong answer the process exits
   non-zero and every downstream result is stamped NOT_QUALIFIED.

Governance: TRAINING=OFF | PROTECTED_FULL104_PATHOLOGY=UNOPENED |
RESERVED_RNA_READOUTS=UNOPENED | TD60_OUTCOMES=UNOPENED |
TEACHER_LATENT_OUTCOMES=UNOPENED | NEW_BIOLOGICAL_REGULATORY_CLAIM=NONE
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import hypergeom, spearmanr

UNKNOWN = "UNKNOWN"
ANNOT_COLUMNS = [
    "Direct_annot",
    "Motif_similarity_annot",
    "Orthology_annot",
    "Motif_similarity_and_Orthology_annot",
]
# Historical labels supplied to this lane as EXPOSED HYPOTHESES ONLY. They are
# re-derived below from the frozen tables; a disagreement is itself a finding.
HISTORICAL_TIERS = {
    "STAT1": "Tier A", "ELF1": "Tier A", "SPI1": "Tier A",
    "IRF8": "Tier B", "BACH1": "Tier B", "CEBPA": "Tier B", "RELA": "Tier B",
    "MITF": "Tier C", "NRF1": "Tier C", "STAT3": "Tier C",
}


# --------------------------------------------------------------------------
# hashing / canonical digests
# --------------------------------------------------------------------------
def sha256_file(path: Path) -> str:
    if not path.is_file():
        return "ABSENT"
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def canon_digest(obj) -> str:
    """Digest of a canonical, order-stable serialisation of structure."""
    return hashlib.sha256(
        json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str).encode()
    ).hexdigest()


def tokens(value) -> frozenset:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return frozenset()
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return frozenset()
    return frozenset(x.strip() for x in text.split(",") if x.strip())


# --------------------------------------------------------------------------
# T4 structural distinctness harness  (fail-closed)
# --------------------------------------------------------------------------
def structural_record(name, original, shuffled, kind,
                      orig_marginal=None, new_marginal=None,
                      index_original=None, index_shuffled=None):
    """Measure whether `shuffled` actually differs in CONTENT from `original`.

    A control is distinct only if its content digest differs AND at least one
    element moved. Naming a thing SHUFFLED proves nothing and is ignored here.
    """
    o = [sorted(x) if isinstance(x, (set, frozenset)) else x for x in original]
    s = [sorted(x) if isinstance(x, (set, frozenset)) else x for x in shuffled]
    n = len(o)
    if len(s) != n:
        raise ValueError("%s: length changed %d -> %d" % (name, n, len(s)))
    n_changed = sum(1 for a, b in zip(o, s) if a != b)
    changed_fraction = (n_changed / n) if n else 0.0
    dig_o, dig_s = canon_digest(o), canon_digest(s)

    # element-content multiset preserved?  (a permutation must preserve it)
    multiset_preserved = sorted(map(str, o)) == sorted(map(str, s))

    # rank correlation of the positional mapping, when an index vector is given
    rank_corr = UNKNOWN
    if index_original is not None and index_shuffled is not None and n > 2:
        try:
            rc = spearmanr(np.asarray(index_original),
                           np.asarray(index_shuffled)).statistic
            rank_corr = round(float(rc), 6) if np.isfinite(rc) else UNKNOWN
        except Exception:
            rank_corr = UNKNOWN

    # Jaccard between original and shuffled taken as sets of (position,value)
    pairs_o = set("%d|%s" % (i, v) for i, v in enumerate(map(str, o)))
    pairs_s = set("%d|%s" % (i, v) for i, v in enumerate(map(str, s)))
    inter, uni = len(pairs_o & pairs_s), len(pairs_o | pairs_s)
    positional_jaccard = round(inter / uni, 6) if uni else UNKNOWN

    marg_ok = UNKNOWN
    if orig_marginal is not None and new_marginal is not None:
        marg_ok = bool(orig_marginal == new_marginal)

    is_distinct = bool(dig_o != dig_s and n_changed > 0)
    return {
        "control_name": name,
        "control_kind": kind,
        "n_elements": int(n),
        "content_digest_original": dig_o,
        "content_digest_shuffled": dig_s,
        "digests_differ": bool(dig_o != dig_s),
        "n_changed_elements": int(n_changed),
        "changed_element_fraction": round(float(changed_fraction), 6),
        "positional_jaccard_vs_original": positional_jaccard,
        "rank_correlation_of_index_map": rank_corr,
        "element_multiset_preserved": bool(multiset_preserved),
        "marginals_preserved": marg_ok,
        "is_structurally_distinct": is_distinct,
    }


def run_planted_gate(records_expectations):
    """records_expectations: list of (record, expected_is_distinct)."""
    gate_rows, ok_all = [], True
    for rec, expected in records_expectations:
        passed = bool(rec["is_structurally_distinct"] == expected)
        ok_all = ok_all and passed
        gate_rows.append({
            "control_name": rec["control_name"],
            "expected_is_structurally_distinct": expected,
            "observed_is_structurally_distinct": rec["is_structurally_distinct"],
            "changed_element_fraction": rec["changed_element_fraction"],
            "gate_result": "PASS" if passed else "FAIL",
        })
    return gate_rows, bool(ok_all)


# --------------------------------------------------------------------------
# loading
# --------------------------------------------------------------------------
def load_inputs(pilot_dirs, batch_dir):
    batches, receipts = {}, []
    for d in pilot_dirs:
        if not d.is_dir():
            continue
        for path in sorted(d.glob("*.motif_enrichment_all.csv.gz")):
            frame = pd.read_csv(path, compression="gzip")
            tf = str(frame["batch_tf"].iloc[0])
            frame.attrs["src"] = str(path)
            batches[tf] = frame
            receipts.append({"role": "motif_enrichment_all", "tf": tf,
                             "path": str(path), "bytes": path.stat().st_size,
                             "sha256": sha256_file(path), "n_rows": int(len(frame))})
    # Parse the TF from the filename stem BEFORE the first dot. Splitting the
    # whole filename on "_" is wrong for names such as
    # stage75f_batch_0001_IRF8.cistarget_regions.txt, whose last "_" token is
    # "regions.txt"; that silently collapses all ten files onto one key.
    def tf_of(path: Path) -> str:
        return path.name.split(".")[0].split("_")[-1]

    regions, dbregions, genes = {}, {}, {}
    for path in sorted(batch_dir.glob("*.regions.bed")):
        tf = tf_of(path)
        df = pd.read_csv(path, sep="\t", header=None)
        regions[tf] = set("%s:%s-%s" % (r[0], r[1], r[2]) for r in df.itertuples(index=False))
        receipts.append({"role": "query_regions_bed", "tf": tf, "path": str(path),
                         "bytes": path.stat().st_size, "sha256": sha256_file(path),
                         "n_rows": int(len(df))})
    for path in sorted(batch_dir.glob("*.cistarget_regions.txt")):
        tf = tf_of(path)
        vals = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        dbregions[tf] = set(vals)
        receipts.append({"role": "mapped_cistarget_db_regions", "tf": tf,
                         "path": str(path), "bytes": path.stat().st_size,
                         "sha256": sha256_file(path), "n_rows": len(vals)})
    for path in sorted(batch_dir.glob("*.genes.txt")):
        tf = tf_of(path)
        vals = [l.strip() for l in path.read_text().splitlines() if l.strip()]
        genes[tf] = set(vals)
        receipts.append({"role": "target_genes", "tf": tf, "path": str(path),
                         "bytes": path.stat().st_size, "sha256": sha256_file(path),
                         "n_rows": len(vals)})
    return batches, regions, dbregions, genes, receipts


def pairwise_overlap(sets, label):
    rows = []
    for a, b in itertools.combinations(sorted(sets), 2):
        inter = len(sets[a] & sets[b])
        uni = len(sets[a] | sets[b])
        smaller = min(len(sets[a]), len(sets[b]))
        rows.append({"set_type": label, "tf_a": a, "tf_b": b,
                     "n_a": len(sets[a]), "n_b": len(sets[b]),
                     "n_shared": inter,
                     "jaccard": round(inter / uni, 6) if uni else UNKNOWN,
                     "frac_of_smaller_shared": round(inter / smaller, 6) if smaller else UNKNOWN})
    frame = pd.DataFrame(rows)
    union = set().union(*sets.values()) if sets else set()
    core = set.intersection(*[set(v) for v in sets.values()]) if sets else set()
    summary = {
        "set_type": label,
        "n_tfs": len(sets),
        "sum_of_per_tf_sizes": int(sum(len(v) for v in sets.values())),
        "n_distinct_elements_across_all_tfs": len(union),
        "n_elements_present_in_every_tf": len(core),
        "mean_pairwise_jaccard": round(float(frame["jaccard"].mean()), 6) if len(frame) else UNKNOWN,
        "min_pairwise_jaccard": round(float(frame["jaccard"].min()), 6) if len(frame) else UNKNOWN,
        "max_pairwise_jaccard": round(float(frame["jaccard"].max()), 6) if len(frame) else UNKNOWN,
        "mean_frac_of_smaller_shared": round(float(frame["frac_of_smaller_shared"].mean()), 6) if len(frame) else UNKNOWN,
    }
    return frame, summary


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pilot-dir", action="append", required=True)
    ap.add_argument("--batch-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--annot-permutations", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=750261)
    args = ap.parse_args()

    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(args.seed)

    batches, regions, dbregions, genes, receipts = load_inputs(
        [Path(p) for p in args.pilot_dir], Path(args.batch_dir))
    if not batches:
        raise SystemExit("NOT_EXECUTED: no Stage75F per-batch enrichment tables found.")
    tfs = sorted(batches)

    # FAIL-CLOSED INPUT GUARD. A filename-parsing slip can silently collapse ten
    # per-TF files onto one dictionary key, after which every overlap statistic
    # for that input is computed on a single set and reads as perfect agreement.
    # That failure is invisible downstream, so it is checked here, not assumed.
    key_report = {}
    for label, d in (("query_regions_bed", regions),
                     ("mapped_cistarget_db_regions", dbregions),
                     ("target_genes", genes)):
        key_report[label] = sorted(d)
        if sorted(d) != tfs:
            raise SystemExit(
                "FAIL_CLOSED input guard: %s parsed %d distinct TF keys %r, "
                "expected the %d enrichment-table TFs %r. Refusing to compute "
                "overlap statistics on a collapsed key set."
                % (label, len(d), sorted(d), len(tfs), tfs))

    # ---------------- annotation collection (property of the motif DB) ------
    ref = batches[tfs[0]]
    collection = ref["MotifID"].astype(str).tolist()
    M = len(collection)
    annot_identical, annot_mismatch, annot_order_only = True, [], []
    for tf in tfs:
        f = batches[tf]
        if f["MotifID"].astype(str).tolist() != collection:
            annot_identical = False
            annot_mismatch.append("%s:motif_order_or_content" % tf)
            continue
        for col in ANNOT_COLUMNS:
            if col not in ref.columns or col not in f.columns:
                annot_identical = False
                annot_mismatch.append("%s:%s:column_absent" % (tf, col))
                continue
            a_raw = ref[col].fillna("").astype(str).to_numpy()
            b_raw = f[col].fillna("").astype(str).to_numpy()
            if [tokens(x) for x in a_raw] != [tokens(x) for x in b_raw]:
                annot_identical = False
                annot_mismatch.append("%s:%s:content_differs" % (tf, col))
            elif not np.array_equal(a_raw, b_raw):
                annot_order_only.append("%s:%s" % (tf, col))

    # per-motif annotation token sets (direct, extended)
    direct_rows = [tokens(v) for v in ref["Direct_annot"].to_numpy()]
    ext_rows = []
    for i in range(M):
        acc = set()
        for col in ANNOT_COLUMNS:
            if col in ref.columns:
                acc |= tokens(ref[col].to_numpy()[i])
        ext_rows.append(frozenset(acc))

    def build_map(rowsets):
        m = {}
        for i, s in enumerate(rowsets):
            for tf in s:
                m.setdefault(tf, set()).add(collection[i])
        return m

    direct_map, ext_map = build_map(direct_rows), build_map(ext_rows)

    # ---------------- enriched sets ---------------------------------------
    enriched = {tf: set(batches[tf].loc[batches[tf]["enriched"].astype(bool),
                                        "MotifID"].astype(str)) for tf in tfs}

    # ---------------- independent tier re-derivation ----------------------
    tier_rows = []
    for tf in tfs:
        E = enriched[tf]
        d = len(E & direct_map.get(tf, set()))
        e = len(E & ext_map.get(tf, set()))
        derived = "Tier A" if d > 0 else ("Tier B" if e > 0 else "Tier C")
        tier_rows.append({"tf": tf, "derived_tier": derived,
                          "historical_tier_exposed_hypothesis": HISTORICAL_TIERS.get(tf, UNKNOWN),
                          "agrees_with_historical": bool(derived == HISTORICAL_TIERS.get(tf)),
                          "observed_direct_support": d, "observed_extended_support": e})
    tier_frame = pd.DataFrame(tier_rows)

    # ---------------- T3 region-set specificity ---------------------------
    ov_frames, ov_summaries = [], []
    for sets_, label in ((regions, "query_regions_bed"),
                         (dbregions, "mapped_cistarget_db_regions"),
                         (genes, "target_genes"),
                         (enriched, "enriched_motif_sets")):
        if not sets_:
            ov_summaries.append({"set_type": label, "status": "NOT_EXECUTED_INPUT_ABSENT"})
            continue
        fr, sm = pairwise_overlap(sets_, label)
        sm["status"] = "MEASURED"
        ov_frames.append(fr)
        ov_summaries.append(sm)
    overlap_frame = pd.concat(ov_frames, ignore_index=True) if ov_frames else pd.DataFrame()

    # ---------------- T1 TF-label permutation -----------------------------
    # S[t][b] = |E_b intersect A_t| for direct and extended annotation.
    def support_matrix(amap):
        return np.array([[len(enriched[b] & amap.get(t, set())) for b in tfs]
                         for t in tfs], dtype=float)

    S_direct, S_ext = support_matrix(direct_map), support_matrix(ext_map)
    n = len(tfs)
    n_perm_total = math.factorial(n)

    def perm_test(S):
        """Exact enumeration of all n! batch-label assignments, chunked so the
        permutation list is never materialised in full."""
        obs = float(np.trace(S))
        rows = np.arange(n)
        chunks, gen = [], itertools.permutations(range(n))
        while True:
            block = list(itertools.islice(gen, 200000))
            if not block:
                break
            P = np.asarray(block, dtype=np.int8)
            chunks.append(S[rows[None, :], P].sum(axis=1))
        null = np.concatenate(chunks)
        p = float((null >= obs).sum() / len(null))
        distinct_null_values = int(len(np.unique(null)))
        return {
            "observed_trace": obs,
            "n_permutations_enumerated": len(null),
            "null_mean": round(float(null.mean()), 6),
            "null_sd": round(float(null.std(ddof=0)), 6),
            "null_min": float(null.min()), "null_max": float(null.max()),
            "n_distinct_null_values": distinct_null_values,
            "p_value_one_sided_ge": round(p, 8),
            "null_is_degenerate_constant": bool(distinct_null_values == 1),
        }

    t1_direct, t1_ext = perm_test(S_direct), perm_test(S_ext)

    # per-TF exact batch-label null (10 values, so p floor is 1/10)
    per_tf_rows = []
    for i, t in enumerate(tfs):
        for lab, S in (("direct", S_direct), ("extended", S_ext)):
            row_vals = S[i]
            obs = float(S[i][i])
            p = float((row_vals >= obs).sum() / n)
            per_tf_rows.append({
                "tf": t, "annotation_scope": lab,
                "observed_support_own_batch": obs,
                "mean_support_other_batches": round(float(np.delete(row_vals, i).mean()), 6),
                "max_support_other_batches": float(np.delete(row_vals, i).max()),
                "n_batches": n,
                "exact_batch_label_p": round(p, 6),
                "p_floor_attainable": round(1.0 / n, 6),
                "row_is_constant_across_batches": bool(len(np.unique(row_vals)) == 1),
            })
    per_tf_perm = pd.DataFrame(per_tf_rows)

    # ---------------- T2 annotation-supply null ---------------------------
    supply_rows = []
    for t in tfs:
        E = enriched[t]
        nE = len(E)
        for lab, amap in (("direct", direct_map), ("extended", ext_map)):
            A = amap.get(t, set())
            obs = len(E & A)
            exp = nE * len(A) / M if M else float("nan")
            p = float(hypergeom.sf(obs - 1, M, len(A), nE)) if (A and nE) else UNKNOWN
            supply_rows.append({
                "tf": t, "annotation_scope": lab,
                "n_enriched_motifs": nE,
                "n_motifs_in_collection": M,
                "annotation_supply_n_motifs_naming_this_tf": len(A),
                "observed_support": obs,
                "expected_support_under_supply_only": round(float(exp), 6),
                "hypergeometric_p_one_sided_ge": (round(p, 8) if p != UNKNOWN else UNKNOWN),
                "exceeds_supply_expectation": (bool(p < 0.05) if p != UNKNOWN else UNKNOWN),
            })
    supply_frame = pd.DataFrame(supply_rows)

    # does tier track supply?
    tier_num = {"Tier A": 2, "Tier B": 1, "Tier C": 0}
    tf_supply = supply_frame[supply_frame["annotation_scope"] == "extended"].set_index("tf")
    tnum = pd.Series({t: tier_num[tier_frame.set_index("tf").loc[t, "derived_tier"]] for t in tfs})
    supply_vec = tf_supply["annotation_supply_n_motifs_naming_this_tf"].reindex(tnum.index)
    dsupply_vec = supply_frame[supply_frame["annotation_scope"] == "direct"].set_index(
        "tf")["annotation_supply_n_motifs_naming_this_tf"].reindex(tnum.index)
    sp_ext = spearmanr(supply_vec.to_numpy(), tnum.to_numpy())
    sp_dir = spearmanr(dsupply_vec.to_numpy(), tnum.to_numpy())

    # ---------------- T1b supply-preserving annotation shuffle ------------
    # Permute annotation ROWS. Each TF keeps EXACTLY its annotation supply;
    # the motif-identity linkage is destroyed.
    ext_arr = np.array(ext_rows, dtype=object)
    dir_arr = np.array(direct_rows, dtype=object)
    idx0 = np.arange(M)
    e_index = {mid: i for i, mid in enumerate(collection)}
    enr_idx = {t: np.array([e_index[m] for m in enriched[t]], dtype=int) for t in tfs}

    # Boolean mask per TF over the motif collection: does row i name this TF?
    mask_ext = {t: np.array([t in s for s in ext_rows], dtype=bool) for t in tfs}
    mask_dir = {t: np.array([t in s for s in direct_rows], dtype=bool) for t in tfs}

    shuffle_structural = []
    null_ext = {t: np.empty(args.annot_permutations, dtype=np.int32) for t in tfs}
    null_dir = {t: np.empty(args.annot_permutations, dtype=np.int32) for t in tfs}
    # JOINT statistic: one shared permutation applied to all ten TFs at once.
    # This preserves the co-annotation structure of the motif collection and the
    # heavy overlap between enriched sets, so it is NOT reducible to ten
    # independent hypergeometrics.
    null_joint_ext = np.empty(args.annot_permutations, dtype=np.int64)
    null_joint_dir = np.empty(args.annot_permutations, dtype=np.int64)
    for k in range(args.annot_permutations):
        perm = rng.permutation(M)
        je = jd = 0
        for t in tfs:
            ve = int(mask_ext[t][perm[enr_idx[t]]].sum())
            vd = int(mask_dir[t][perm[enr_idx[t]]].sum())
            null_ext[t][k] = ve
            null_dir[t][k] = vd
            je += ve
            jd += vd
        null_joint_ext[k] = je
        null_joint_dir[k] = jd
        if k < 3:  # structural proof for the first three real shuffles
            shuffle_structural.append(structural_record(
                "REAL_ANNOTATION_SHUFFLE_%d" % k, list(ext_arr), list(ext_arr[perm]),
                "supply_preserving_annotation_row_permutation",
                orig_marginal=sorted(len(v) for v in ext_map.values()),
                new_marginal=sorted(len(v) for v in build_map(list(ext_arr[perm])).values()),
                index_original=idx0, index_shuffled=perm))

    shuffle_rows = []
    for t in tfs:
        for lab, nullv, amap in (("direct", null_dir, direct_map),
                                 ("extended", null_ext, ext_map)):
            obs = len(enriched[t] & amap.get(t, set()))
            p = float((1 + int((nullv[t] >= obs).sum())) / (1 + args.annot_permutations))
            shuffle_rows.append({
                "tf": t, "annotation_scope": lab, "observed_support": obs,
                "shuffle_null_mean": round(float(nullv[t].mean()), 6),
                "shuffle_null_sd": round(float(nullv[t].std(ddof=0)), 6),
                "shuffle_null_max": int(nullv[t].max()),
                "n_shuffles": args.annot_permutations,
                "supply_preserving_shuffle_p": round(p, 8),
                "exceeds_shuffled_annotation": bool(p < 0.05),
            })
    shuffle_frame = pd.DataFrame(shuffle_rows)
    # observed joint statistic == trace of the support matrix, by construction
    obs_joint_ext = int(np.trace(S_ext))
    obs_joint_dir = int(np.trace(S_direct))

    # ---------------- T4 planted structural controls (FAIL-CLOSED) --------
    identity = np.arange(M)
    planted_identical = structural_record(
        "PLANTED_IDENTICAL_annotation_labelled_SHUFFLED", list(ext_arr),
        list(ext_arr[identity]), "planted_identity_masquerading_as_shuffle",
        orig_marginal=sorted(len(v) for v in ext_map.values()),
        new_marginal=sorted(len(v) for v in build_map(list(ext_arr[identity])).values()),
        index_original=idx0, index_shuffled=identity)

    valid_perm = rng.permutation(M)
    guard = 0
    while (valid_perm == identity).mean() > 0.01 and guard < 50:
        valid_perm = rng.permutation(M)
        guard += 1
    planted_valid = structural_record(
        "PLANTED_VALID_annotation_derangement", list(ext_arr),
        list(ext_arr[valid_perm]), "planted_verified_derangement",
        orig_marginal=sorted(len(v) for v in ext_map.values()),
        new_marginal=sorted(len(v) for v in build_map(list(ext_arr[valid_perm])).values()),
        index_original=idx0, index_shuffled=valid_perm)

    bidx = np.arange(n)
    planted_identical_batch = structural_record(
        "PLANTED_IDENTICAL_batch_label_assignment_labelled_SHUFFLED",
        list(tfs), [tfs[i] for i in bidx], "planted_identity_masquerading_as_shuffle",
        index_original=bidx, index_shuffled=bidx)
    bperm = np.array([(i + 1) % n for i in range(n)])  # full cyclic derangement
    planted_valid_batch = structural_record(
        "PLANTED_VALID_batch_label_derangement", list(tfs),
        [tfs[i] for i in bperm], "planted_verified_derangement",
        index_original=bidx, index_shuffled=bperm)

    gate_rows, gate_ok = run_planted_gate([
        (planted_identical, False), (planted_valid, True),
        (planted_identical_batch, False), (planted_valid_batch, True)])
    # every real shuffle must also be measurably distinct
    real_ok = all(r["is_structurally_distinct"] for r in shuffle_structural)
    for r in shuffle_structural:
        gate_rows.append({"control_name": r["control_name"],
                          "expected_is_structurally_distinct": True,
                          "observed_is_structurally_distinct": r["is_structurally_distinct"],
                          "changed_element_fraction": r["changed_element_fraction"],
                          "gate_result": "PASS" if r["is_structurally_distinct"] else "FAIL"})
    gate_ok = bool(gate_ok and real_ok)
    qualification = "QUALIFIED" if gate_ok else "NOT_QUALIFIED_STRUCTURAL_GATE_FAILED"

    # ---------------- identifiability verdict ------------------------------
    enr_sm = [s for s in ov_summaries if s.get("set_type") == "enriched_motif_sets"][0]
    reg_sm = [s for s in ov_summaries if s.get("set_type") == "query_regions_bed"][0]
    identifiable = not (t1_ext["null_is_degenerate_constant"]
                        and t1_direct["null_is_degenerate_constant"])

    all_struct = [planted_identical, planted_valid, planted_identical_batch,
                  planted_valid_batch] + shuffle_structural
    struct_frame = pd.DataFrame(all_struct)
    gate_frame = pd.DataFrame(gate_rows)

    report = {
        "audit": "laneR2_stage75f_tf_specificity_control_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "qualification": qualification,
        "structural_gate_passed": gate_ok,
        "seed": args.seed,
        "n_tfs": n,
        "tfs": tfs,
        "motif_collection_size": M,
        "annotation_content_identical_across_batches": annot_identical,
        "annotation_content_mismatches": annot_mismatch,
        "annotation_string_order_only_differences": sorted(set(annot_order_only)),
        "T3_region_and_set_overlap": ov_summaries,
        "T1_tf_label_permutation_exact": {
            "statistic": "trace(S) where S[t][b]=|E_b intersect A_t|",
            "direct": t1_direct, "extended": t1_ext,
            "note": ("Exact enumeration over all %d batch-label assignments. "
                     "Each TF annotation supply is held exactly fixed, so this "
                     "test isolates region-set specificity." % n_perm_total),
        },
        "T2_annotation_supply": {
            "spearman_extended_supply_vs_derived_tier": round(float(sp_ext.statistic), 6),
            "spearman_extended_supply_vs_derived_tier_p": round(float(sp_ext.pvalue), 6),
            "spearman_direct_supply_vs_derived_tier": round(float(sp_dir.statistic), 6),
            "spearman_direct_supply_vs_derived_tier_p": round(float(sp_dir.pvalue), 6),
            "n_tf_scope_pairs_exceeding_supply_expectation": int(
                (supply_frame["exceeds_supply_expectation"] == True).sum()),
            "n_tf_scope_pairs_tested": int(len(supply_frame)),
        },
        "T1b_supply_preserving_annotation_shuffle": {
            "n_shuffles": args.annot_permutations,
            "n_tf_scope_pairs_exceeding_shuffled_annotation": int(
                (shuffle_frame["exceeds_shuffled_annotation"] == True).sum()),
            "n_tf_scope_pairs_tested": int(len(shuffle_frame)),
            "per_tf_note": ("For a single TF this null is the empirical "
                            "counterpart of the T2 hypergeometric, not an "
                            "independent test; its role is to carry the "
                            "structural-distinctness proofs."),
            "joint_statistic": {
                "definition": "sum over all ten TFs of |E_t intersect A'_t| under ONE shared annotation row permutation",
                "not_reducible_to_independent_hypergeometrics": True,
                "extended": {
                    "observed": int(obs_joint_ext),
                    "null_mean": round(float(null_joint_ext.mean()), 6),
                    "null_sd": round(float(null_joint_ext.std(ddof=0)), 6),
                    "null_max": int(null_joint_ext.max()),
                    "p_value": round(float((1 + int((null_joint_ext >= obs_joint_ext).sum()))
                                           / (1 + args.annot_permutations)), 8),
                },
                "direct": {
                    "observed": int(obs_joint_dir),
                    "null_mean": round(float(null_joint_dir.mean()), 6),
                    "null_sd": round(float(null_joint_dir.std(ddof=0)), 6),
                    "null_max": int(null_joint_dir.max()),
                    "p_value": round(float((1 + int((null_joint_dir >= obs_joint_dir).sum()))
                                           / (1 + args.annot_permutations)), 8),
                },
            },
        },
        "T4_structural_distinctness": {
            "gate": gate_rows,
            "all_gates_passed": gate_ok,
            "planted_identical_detected_as_unchanged": not planted_identical["is_structurally_distinct"],
            "planted_valid_detected_as_changed": planted_valid["is_structurally_distinct"],
        },
        "tier_rederivation_vs_historical": tier_frame.to_dict(orient="records"),
        "identifiability": {
            "tf_label_permutation_null_degenerate": bool(not identifiable),
            "mean_pairwise_jaccard_query_regions": reg_sm.get("mean_pairwise_jaccard", UNKNOWN),
            "mean_pairwise_jaccard_enriched_motif_sets": enr_sm.get("mean_pairwise_jaccard", UNKNOWN),
            "n_motifs_enriched_in_every_batch": enr_sm.get("n_elements_present_in_every_tf", UNKNOWN),
        },
        "claim_boundaries": {
            "biological_regulatory_claim": "NONE",
            "validated_eregulon_network": False,
            "reruns_cistarget_or_motif_enrichment": False,
            "protected_full104_pathology_opened": False,
            "reserved_rna_readouts_opened": False,
            "td60_outcomes_opened": False,
            "teacher_latent_outcomes_opened": False,
            "historical_tiers_treated_as": "EXPOSED_HYPOTHESES_ONLY",
        },
        "governance": ("TRAINING=OFF | PROTECTED_FULL104_PATHOLOGY=UNOPENED | "
                       "RESERVED_RNA_READOUTS=UNOPENED | TD60_OUTCOMES=UNOPENED | "
                       "TEACHER_LATENT_OUTCOMES=UNOPENED | "
                       "NEW_BIOLOGICAL_REGULATORY_CLAIM=NONE"),
    }

    pd.DataFrame(receipts).to_csv(out / "laneR2_input_receipts_v1.csv", index=False)
    overlap_frame.to_csv(out / "laneR2_pairwise_overlap_v1.csv", index=False)
    supply_frame.to_csv(out / "laneR2_annotation_supply_test_v1.csv", index=False)
    per_tf_perm.to_csv(out / "laneR2_tf_label_permutation_per_tf_v1.csv", index=False)
    shuffle_frame.to_csv(out / "laneR2_supply_preserving_shuffle_v1.csv", index=False)
    struct_frame.to_csv(out / "laneR2_structural_distinctness_v1.csv", index=False)
    gate_frame.to_csv(out / "laneR2_structural_gate_v1.csv", index=False)
    tier_frame.to_csv(out / "laneR2_tier_rederivation_v1.csv", index=False)
    pd.DataFrame(S_ext, index=tfs, columns=tfs).to_csv(
        out / "laneR2_support_matrix_extended_v1.csv")
    pd.DataFrame(S_direct, index=tfs, columns=tfs).to_csv(
        out / "laneR2_support_matrix_direct_v1.csv")
    (out / "laneR2_report_v1.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps({k: v for k, v in report.items()
                      if k not in ("tier_rederivation_vs_historical",)},
                     indent=2, default=str))
    print("\n--- STRUCTURAL GATE ---")
    print(gate_frame.to_string(index=False))
    print("\n--- TIER RE-DERIVATION ---")
    print(tier_frame.to_string(index=False))
    if not gate_ok:
        print("\nFAIL-CLOSED: structural distinctness gate failed. "
              "All downstream results are NOT_QUALIFIED.", file=sys.stderr)
        return 3
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
