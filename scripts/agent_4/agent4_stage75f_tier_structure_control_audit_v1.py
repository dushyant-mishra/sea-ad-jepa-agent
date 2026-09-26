#!/usr/bin/env python
"""AGENT 4 - Stage75F Tier A/B/C structure: discrimination or annotation artifact?

READ-ONLY. Reruns no motif enrichment. Reads only the per-batch cisTarget
enrichment tables that Stage75F already wrote, plus the motif annotation
columns those tables already carry.

THE QUESTION
------------
Stage75F ran ten per-TF cisTarget analyses and sorted the ten regulators into
three tiers:

    Tier A  direct motif support         STAT1, ELF1, SPI1
    Tier B  extended-only motif support  IRF8, BACH1, CEBPA, RELA
    Tier C  no TF-annotated enriched motif  MITF, NRF1, STAT3

Tier C is treated downstream as a negative-control gate. That reading is only
valid if the tier a TF lands in reflects something about that TF's regulatory
program in the query regions. The companion authentication audit measured that
the ten query region sets share, on average, 93% of the smaller set's regions
and span only 86 distinct regions in total. If the ten analyses are effectively
one analysis of one shared region set, then the enriched motif set is close to
constant across TFs, and the only thing that varies between TFs is how many
motifs in the collection happen to be annotated to that TF.

That is a testable alternative, and it is precisely the shuffled-TF-label
control the project requires. This script runs it.

THE TEST
--------
For each TF:

  E        the set of motifs called enriched in that TF's batch
  A_direct the set of motifs whose Direct_annot names that TF
  A_ext    the set of motifs whose direct/similarity/orthology annotation
           names that TF

Observed support is |E n A|. Under the null that the enriched set carries no
TF-specific information -- i.e. E is just "the motifs enriched in the shared
promoter-proximal pool" -- a set of |E| motifs drawn uniformly from the same
collection should hit A at the hypergeometric rate. We report the exact
hypergeometric expectation and one-sided p-value, and an empirical
label-permutation null over the actual TF annotation vectors.

If observed support is not distinguishable from the annotation-supply
expectation, the tier structure is an ANNOTATION ARTIFACT: Tier C means "few
motifs in this collection are annotated to this TF", not "this TF does not
regulate these genes". A negative-control gate built on it is not a negative
control.

Every biological conclusion here remains NOT_EXECUTED. This audit characterises
a historical analysis; it makes no regulatory claim of its own.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

UNKNOWN = "UNKNOWN"
ANNOT_COLUMNS = [
    "Direct_annot",
    "Motif_similarity_annot",
    "Orthology_annot",
    "Motif_similarity_and_Orthology_annot",
]
TIERS = {
    "STAT1": "Tier A", "ELF1": "Tier A", "SPI1": "Tier A",
    "IRF8": "Tier B", "BACH1": "Tier B", "CEBPA": "Tier B", "RELA": "Tier B",
    "MITF": "Tier C", "NRF1": "Tier C", "STAT3": "Tier C",
}


def tokens(value) -> set[str]:
    """Annotation cells are comma-separated TF symbol lists."""
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return set()
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return set()
    return {x.strip() for x in text.split(",") if x.strip()}


def load_batches(root: Path) -> dict[str, pd.DataFrame]:
    """Load every per-batch enrichment table Stage75F actually wrote.

    Searched by the value being bound -- the batch file glob -- across both
    pilot directories, not by one spelling of a TF name.
    """
    frames: dict[str, pd.DataFrame] = {}
    for sub in ("results/stage75f_motif_pilot",
                "results/stage75f_secondary_motif_pilot"):
        directory = root / sub
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.motif_enrichment_all.csv.gz")):
            frame = pd.read_csv(path, compression="gzip")
            if "batch_tf" in frame.columns:
                tf = str(frame["batch_tf"].iloc[0])
            elif "tf" in frame.columns:
                tf = str(frame["tf"].iloc[0])
            else:
                continue
            frame.attrs["source_path"] = str(path.relative_to(root))
            frames[tf] = frame
    return frames


def hypergeom_sf(k: int, M: int, n: int, N: int) -> float:
    """P(X >= k) for X ~ Hypergeom(M population, n successes, N draws)."""
    if k <= 0:
        return 1.0
    if n == 0 or N == 0:
        return 1.0
    total = 0.0
    upper = min(n, N)
    log_denom = math.lgamma(M + 1) - math.lgamma(N + 1) - math.lgamma(M - N + 1)
    for i in range(k, upper + 1):
        if i > n or (N - i) > (M - n):
            continue
        log_num = (
            math.lgamma(n + 1) - math.lgamma(i + 1) - math.lgamma(n - i + 1)
            + math.lgamma(M - n + 1) - math.lgamma(N - i + 1)
            - math.lgamma(M - n - N + i + 1)
        )
        total += math.exp(log_num - log_denom)
    return min(1.0, total)


def annotation_supply(frame: pd.DataFrame) -> tuple[dict[str, set[str]], dict[str, set[str]]]:
    """Map every TF symbol in the annotation table to its motif sets."""
    motif_ids = frame["MotifID"].astype(str).to_numpy()
    direct: dict[str, set[str]] = {}
    extended: dict[str, set[str]] = {}
    direct_cells = frame["Direct_annot"].to_numpy() if "Direct_annot" in frame else np.array([None] * len(frame))
    ext_cells = [frame[c].to_numpy() if c in frame else np.array([None] * len(frame))
                 for c in ANNOT_COLUMNS]
    for i, motif in enumerate(motif_ids):
        for tf in tokens(direct_cells[i]):
            direct.setdefault(tf, set()).add(motif)
        ext: set[str] = set()
        for col in ext_cells:
            ext |= tokens(col[i])
        for tf in ext:
            extended.setdefault(tf, set()).add(motif)
    return direct, extended


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--permutations", type=int, default=20000)
    ap.add_argument("--seed", type=int, default=75026)
    args = ap.parse_args()

    root = Path(args.data_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    batches = load_batches(root)
    if not batches:
        raise SystemExit("No Stage75F per-batch enrichment tables found.")

    # The annotation table is a property of the motif collection, not of the
    # batch. Verify it is identical across batches before using one copy.
    ref_tf = sorted(batches)[0]
    ref = batches[ref_tf]
    collection = ref["MotifID"].astype(str).tolist()
    # Compare annotation CONTENT, not its string serialisation. The stored
    # cells are comma-joined from Python sets, so the same TF set can be
    # written in a different order by a different process. Ordering differences
    # are a byte-reproducibility note, not an annotation difference, and must
    # not be reported as a content defect.
    annot_identical = True
    annot_mismatch: list[str] = []
    annot_order_only: list[str] = []
    for tf, frame in batches.items():
        if frame["MotifID"].astype(str).tolist() != collection:
            annot_identical = False
            annot_mismatch.append(f"{tf}:motif_order")
            continue
        for col in ANNOT_COLUMNS:
            if col not in ref or col not in frame:
                annot_identical = False
                annot_mismatch.append(f"{tf}:{col}:column_absent")
                continue
            a_raw = ref[col].fillna("").astype(str).to_numpy()
            b_raw = frame[col].fillna("").astype(str).to_numpy()
            a_set = [tokens(x) for x in a_raw]
            b_set = [tokens(x) for x in b_raw]
            if a_set != b_set:
                annot_identical = False
                annot_mismatch.append(f"{tf}:{col}:content_differs")
            elif not np.array_equal(a_raw, b_raw):
                annot_order_only.append(f"{tf}:{col}")

    direct_map, ext_map = annotation_supply(ref)
    M = len(collection)

    # --- enriched-set overlap across the ten batches -----------------------
    enriched = {tf: set(f.loc[f["enriched"].astype(bool), "MotifID"].astype(str))
                for tf, f in batches.items()}
    pairs = []
    for a, b in itertools.combinations(sorted(enriched), 2):
        inter = len(enriched[a] & enriched[b])
        uni = len(enriched[a] | enriched[b])
        pairs.append({
            "tf_a": a, "tf_b": b,
            "n_enriched_a": len(enriched[a]), "n_enriched_b": len(enriched[b]),
            "n_shared_enriched": inter,
            "jaccard": round(inter / uni, 6) if uni else UNKNOWN,
            "frac_of_smaller_shared": round(inter / min(len(enriched[a]), len(enriched[b])), 6)
            if min(len(enriched[a]), len(enriched[b])) else UNKNOWN,
        })
    pair_frame = pd.DataFrame(pairs)
    union_enriched = set().union(*enriched.values())
    core_enriched = set.intersection(*enriched.values()) if enriched else set()

    # --- per-TF support versus annotation supply ---------------------------
    rng = np.random.default_rng(args.seed)
    rows = []
    for tf in sorted(batches):
        E = enriched[tf]
        nE = len(E)
        Ad = direct_map.get(tf, set())
        Ae = ext_map.get(tf, set())
        obs_d = len(E & Ad)
        obs_e = len(E & Ae)

        exp_d = nE * len(Ad) / M if M else UNKNOWN
        exp_e = nE * len(Ae) / M if M else UNKNOWN
        p_d = hypergeom_sf(obs_d, M, len(Ad), nE) if Ad else UNKNOWN
        p_e = hypergeom_sf(obs_e, M, len(Ae), nE) if Ae else UNKNOWN

        # Empirical label-permutation null: hold the enriched set fixed, draw
        # a random motif set of the same size from the same collection.
        idx = np.arange(M)
        ad_mask = np.isin(np.array(collection), list(Ad)) if Ad else np.zeros(M, bool)
        ae_mask = np.isin(np.array(collection), list(Ae)) if Ae else np.zeros(M, bool)
        null_d = np.empty(args.permutations, dtype=np.int32)
        null_e = np.empty(args.permutations, dtype=np.int32)
        for i in range(args.permutations):
            draw = rng.choice(idx, size=nE, replace=False)
            null_d[i] = int(ad_mask[draw].sum())
            null_e[i] = int(ae_mask[draw].sum())
        emp_p_d = float((1 + int((null_d >= obs_d).sum())) / (1 + args.permutations))
        emp_p_e = float((1 + int((null_e >= obs_e).sum())) / (1 + args.permutations))

        # P(a random motif set of this size contains at least one annotated
        # motif). If this is high for Tier A/B and low for Tier C, the tier
        # assignment is fully explained by annotation supply.
        p_any_d = 1.0 - hypergeom_sf(1, M, len(Ad), nE) if Ad else 0.0
        rows.append({
            "tf": tf,
            "frozen_tier": TIERS.get(tf, UNKNOWN),
            "n_enriched_motifs": nE,
            "n_motifs_in_collection": M,
            "n_direct_annotated_motifs_for_tf": len(Ad),
            "n_extended_annotated_motifs_for_tf": len(Ae),
            "observed_direct_support": obs_d,
            "expected_direct_support_if_no_tf_signal": round(exp_d, 4) if exp_d != UNKNOWN else UNKNOWN,
            "hypergeom_p_direct": (round(p_d, 6) if p_d != UNKNOWN else UNKNOWN),
            "permutation_p_direct": round(emp_p_d, 6),
            "observed_extended_support": obs_e,
            "expected_extended_support_if_no_tf_signal": round(exp_e, 4) if exp_e != UNKNOWN else UNKNOWN,
            "hypergeom_p_extended": (round(p_e, 6) if p_e != UNKNOWN else UNKNOWN),
            "permutation_p_extended": round(emp_p_e, 6),
            "prob_random_set_would_show_direct_support": round(1.0 - (1.0 - p_any_d), 6)
            if Ad else 0.0,
            "tier_explained_by_annotation_supply": (
                "YES_no_evidence_beyond_supply" if emp_p_e > 0.05 else
                "NO_support_exceeds_supply_expectation"),
        })
    tf_frame = pd.DataFrame(rows)

    # Does tier track annotation supply?  Rank correlation between the number
    # of motifs annotated to a TF and its tier (A=2, B=1, C=0).
    tier_rank = {"Tier A": 2, "Tier B": 1, "Tier C": 0}
    tf_frame["_tier_num"] = tf_frame["frozen_tier"].map(tier_rank)
    supply_corr = UNKNOWN
    if tf_frame["_tier_num"].notna().all():
        supply_corr = round(float(
            tf_frame["n_extended_annotated_motifs_for_tf"].corr(
                tf_frame["_tier_num"], method="spearman")), 6)
    direct_supply_corr = round(float(
        tf_frame["n_direct_annotated_motifs_for_tf"].corr(
            tf_frame["_tier_num"], method="spearman")), 6)
    tf_frame = tf_frame.drop(columns=["_tier_num"])

    n_no_excess = int((tf_frame["tier_explained_by_annotation_supply"]
                       == "YES_no_evidence_beyond_supply").sum())

    verdict = (
        "TIER_STRUCTURE_IS_AN_ANNOTATION_ARTIFACT"
        if n_no_excess == len(tf_frame)
        else "TIER_STRUCTURE_PARTLY_EXCEEDS_ANNOTATION_SUPPLY"
        if n_no_excess > 0
        else "TIER_STRUCTURE_EXCEEDS_ANNOTATION_SUPPLY_FOR_ALL_TFS"
    )

    report = {
        "audit": "agent4_stage75f_tier_structure_control_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_root": str(root),
        "permutations": args.permutations,
        "seed": args.seed,
        "n_batches_found": len(batches),
        "batch_sources": {tf: f.attrs.get("source_path", UNKNOWN)
                          for tf, f in sorted(batches.items())},
        "annotation_content_identical_across_batches": annot_identical,
        "annotation_content_mismatches": annot_mismatch,
        "annotation_string_order_only_differences": annot_order_only,
        "annotation_order_note": (
            "Annotation cells are comma-joined from Python sets, so the same TF "
            "set can be serialised in a different order by a different process. "
            "Order-only differences are a byte-level reproducibility note: these "
            "tables cannot be reproduced byte-for-byte across runs. They are NOT "
            "an annotation content difference."
        ),
        "motif_collection_size": M,
        "enriched_set_overlap": {
            "n_distinct_enriched_motifs_across_all_tfs": len(union_enriched),
            "n_motifs_enriched_in_every_tf_batch": len(core_enriched),
            "sum_of_per_tf_enriched": int(sum(len(v) for v in enriched.values())),
            "mean_pairwise_jaccard": round(float(pair_frame["jaccard"].mean()), 6),
            "min_pairwise_jaccard": round(float(pair_frame["jaccard"].min()), 6),
            "max_pairwise_jaccard": round(float(pair_frame["jaccard"].max()), 6),
            "mean_frac_of_smaller_shared": round(
                float(pair_frame["frac_of_smaller_shared"].mean()), 6),
        },
        "tier_vs_annotation_supply": {
            "spearman_extended_supply_vs_tier": supply_corr,
            "spearman_direct_supply_vs_tier": direct_supply_corr,
            "n_tfs_with_support_not_exceeding_supply_expectation": n_no_excess,
            "n_tfs_total": int(len(tf_frame)),
        },
        "verdict": verdict,
        "verdict_plain_language": (
            "Tier A/B/C does not measure whether a transcription factor "
            "regulates these genes. It measures how many motifs in the "
            "collection carry that factor's name, combined with an enriched "
            "motif set that is nearly the same for all ten factors because all "
            "ten query region sets are drawn from one 86-region pool. Tier C is "
            "therefore NOT a negative control."
            if verdict == "TIER_STRUCTURE_IS_AN_ANNOTATION_ARTIFACT" else
            "Tier assignment is partly but not wholly explained by how many "
            "motifs carry each factor's name; see the per-TF table for which "
            "factors exceed the annotation-supply expectation."
        ),
        "claim_boundaries": {
            "biological_result": "NOT_EXECUTED",
            "validated_regulation": False,
            "validated_eregulon_set": False,
            "reruns_cistarget": False,
            "statement": (
                "This audit re-reads frozen Stage75F enrichment tables. It "
                "makes no regulatory claim and validates no eRegulon."
            ),
        },
        "governance": ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                       "PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | "
                       "RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF"),
    }

    tf_frame.to_csv(out / "agent4_stage75f_tier_control_by_tf_v1.csv", index=False)
    pair_frame.to_csv(out / "agent4_stage75f_enriched_set_overlap_pairs_v1.csv", index=False)
    (out / "agent4_stage75f_tier_control_report_v1.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8")

    print(json.dumps({k: v for k, v in report.items()
                      if k not in {"batch_sources"}}, indent=2, default=str))
    print("\n--- per TF ---")
    print(tf_frame.to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
