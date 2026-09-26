#!/usr/bin/env python
"""AGENT 4 - Stage75F authentication and restriction audit (READ-ONLY).

Two jobs, no computation that changes any scientific artifact:

  1. AUTHENTICATE. Recompute SHA-256 for every artifact the Stage75F
     integrated-evidence freeze depends on, compare against the digests the
     frozen manifest records, and report the git tracking status of every
     artifact in the dependency chain. An artifact that is present on disk but
     tracked by no commit is reported as UNTRACKED_NOT_DIGEST_ANCHORED, never
     as authenticated.

  2. TRACE THE RESTRICTIONS. Recompute, from the actual tables, every count
     that narrowed a genome-scale regulatory question down to the frozen
     10-regulator / 96-row panel, and measure the one property the frozen
     summaries structurally cannot show: how much the ten per-TF cisTarget
     query region sets overlap each other.

Nothing here reruns cisTarget, reruns motif enrichment, touches the FULL104
substrate, or reads any protected outcome. Every biological quantity that this
script does not itself measure is emitted as UNKNOWN, never as zero.

Governance: TRAINING=OFF | AUDIT_B_N1=UNOPENED |
PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED |
RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

UNKNOWN = "UNKNOWN"


def sha256_file(path: Path) -> str | None:
    if not path.is_file():
        return None
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True, text=True, timeout=120,
        )
        return out.stdout.strip() if out.returncode == 0 else ""
    except Exception:
        return ""


def tracking_status(repo: Path, rel: str) -> str:
    """TRACKED if some commit reachable from any ref carries this path."""
    listed = git(repo, "ls-files", "--error-unmatch", rel)
    if listed:
        return "TRACKED_AT_HEAD"
    any_commit = git(repo, "log", "--all", "--oneline", "-1", "--", rel)
    if any_commit:
        return "TRACKED_IN_HISTORY_NOT_AT_HEAD"
    return "UNTRACKED_NOT_DIGEST_ANCHORED"


def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.is_file():
        return None
    return pd.read_csv(path)


def authenticate(root: Path, manifest_path: Path) -> tuple[dict, pd.DataFrame]:
    """Recompute digests for the freeze chain and compare to the manifest."""
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    rows: list[dict] = []

    # 1a. The seven source tables the manifest pins by SHA-256.
    for key, spec in manifest["source_tables"].items():
        rel = spec["path"]
        path = root / rel
        actual = sha256_file(path)
        frame = read_csv(path)
        rows.append({
            "role": "manifest_pinned_source",
            "key": key,
            "path": rel,
            "present_on_disk": path.is_file(),
            "recorded_sha256": spec["sha256"],
            "recomputed_sha256": actual or UNKNOWN,
            "digest_match": (actual == spec["sha256"]) if actual else UNKNOWN,
            "recorded_rows": spec["rows"],
            "observed_rows": len(frame) if frame is not None else UNKNOWN,
            "row_match": (len(frame) == spec["rows"]) if frame is not None else UNKNOWN,
            "git_tracking": tracking_status(root, rel),
        })

    # 1b. The freeze outputs. The manifest names them but pins no digest, so
    #     we record the digest here to create the anchor that was missing.
    for key, rel in manifest["outputs"].items():
        path = root / rel
        actual = sha256_file(path)
        frame = read_csv(path) if rel.endswith(".csv") else None
        rows.append({
            "role": "freeze_output_no_recorded_digest",
            "key": key,
            "path": rel,
            "present_on_disk": path.is_file(),
            "recorded_sha256": "NOT_RECORDED_IN_MANIFEST",
            "recomputed_sha256": actual or UNKNOWN,
            "digest_match": "NO_RECORDED_DIGEST_TO_COMPARE",
            "recorded_rows": manifest["output_row_counts"].get(
                key.replace("_csv", ""), UNKNOWN),
            "observed_rows": len(frame) if frame is not None else UNKNOWN,
            "row_match": UNKNOWN,
            "git_tracking": tracking_status(root, rel),
        })

    # 1c. The upstream selection layer. These determine WHAT was tested and are
    #     pinned by no digest anywhere in the freeze.
    selection_layer = {
        "stage72b_candidate_edges": "results/tables/stage72b_tf_target_candidate_edges_v1.csv",
        "stage75c_peak_to_gene_preflight": "results/tables/stage75c_peak_to_gene_preflight_v1.csv",
        "stage75f_candidate_tf_target_edges": "results/tables/stage75f_candidate_tf_target_edges_v1.csv",
        "stage75f_candidate_peak_gene_links": "results/tables/stage75f_candidate_peak_gene_links_v1.csv",
        "stage75f_batch_manifest": "results/tables/stage75f_batch_manifest_v1.csv",
        "stage75f_cistarget_region_mapping": "results/tables/stage75f_cistarget_region_mapping_v1.csv",
        "stage75f_cistarget_region_coverage": "results/tables/stage75f_cistarget_region_coverage_v1.csv",
        "stage75f_primary_motif_hits": "results/tables/stage75f_primary_motif_hits_v1.csv",
        "stage75f_secondary_motif_hits": "results/tables/stage75f_secondary_motif_hits_v1.csv",
        "stage75f_primary_region_gene_evidence": "results/tables/stage75f_primary_tf_region_gene_evidence_v1.csv",
        "stage75f_secondary_region_gene_evidence": "results/tables/stage75f_secondary_tf_region_gene_evidence_v1.csv",
    }
    for key, rel in selection_layer.items():
        path = root / rel
        actual = sha256_file(path)
        frame = read_csv(path)
        rows.append({
            "role": "upstream_selection_layer",
            "key": key,
            "path": rel,
            "present_on_disk": path.is_file(),
            "recorded_sha256": "NOT_RECORDED_IN_MANIFEST",
            "recomputed_sha256": actual or UNKNOWN,
            "digest_match": "NO_RECORDED_DIGEST_TO_COMPARE",
            "recorded_rows": UNKNOWN,
            "observed_rows": len(frame) if frame is not None else UNKNOWN,
            "row_match": UNKNOWN,
            "git_tracking": tracking_status(root, rel),
        })

    # 1d. The external resources the motif analysis actually consumed. These
    #     are multi-GB; record size and mtime, and digest only the small ones.
    resources = {
        "cistarget_rankings_feather": "data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.rankings.feather",
        "cistarget_scores_feather": "data/external_resources/stage75b/hg38_screen_v10_clust.regions_vs_motifs.scores.feather",
        "motif_annotation_tbl": "data/external_resources/stage75b/motifs-v10nr_clust-nr.hgnc-m0.001-o0.0.tbl",
        "gencode_v44_gtf": "data/external_resources/stage75b/gencode.v44.annotation.gtf.gz",
        "hg38_chrom_sizes": "data/external_resources/stage75b/hg38.chrom.sizes",
        "gse174367_snatac_h5": "data/external/gse174367/GSE174367_snATAC-seq_filtered_peak_bc_matrix.h5",
        "gse174367_snrna_h5": "data/external/gse174367/GSE174367_snRNA-seq_filtered_feature_bc_matrix.h5",
        "cistarget_region_index_manifest": "data/processed/stage75f/hg38_screen_v10_clust_scores_region_index_manifest_v2.json",
    }
    resource_rows: list[dict] = []
    for key, rel in resources.items():
        path = root / rel
        size = path.stat().st_size if path.is_file() else None
        small = size is not None and size < 200 * 1024 * 1024
        resource_rows.append({
            "role": "external_resource",
            "key": key,
            "path": rel,
            "present_on_disk": path.is_file(),
            "size_bytes": size if size is not None else UNKNOWN,
            "sha256": (sha256_file(path) if small else
                       "NOT_DIGESTED_SIZE_OVER_200MB_SEE_VENDOR_SHA1"),
            "git_tracking": tracking_status(root, rel),
        })

    return manifest, pd.DataFrame(rows), pd.DataFrame(resource_rows)


def restriction_funnel(root: Path, cfg: dict, manifest: dict) -> tuple[pd.DataFrame, dict]:
    """Recompute every count that narrowed the question, from real tables."""
    p = lambda rel: root / rel  # noqa: E731

    s72b = read_csv(p("results/tables/stage72b_tf_target_candidate_edges_v1.csv"))
    s75c = read_csv(p("results/tables/stage75c_peak_to_gene_preflight_v1.csv"))
    cand_e = read_csv(p("results/tables/stage75f_candidate_tf_target_edges_v1.csv"))
    cand_pg = read_csv(p("results/tables/stage75f_candidate_peak_gene_links_v1.csv"))
    batches = read_csv(p("results/tables/stage75f_batch_manifest_v1.csv"))
    coverage = read_csv(p("results/tables/stage75f_cistarget_region_coverage_v1.csv"))
    mapping = read_csv(p("results/tables/stage75f_cistarget_region_mapping_v1.csv"))
    integ_reg = read_csv(p("results/tables/stage75_integrated_regulator_summary_v1.csv"))
    integ_tt = read_csv(p("results/tables/stage75_integrated_tf_target_summary_v1.csv"))
    integ_neg = read_csv(p("results/tables/stage75_integrated_negative_regulator_gate_v1.csv"))

    tf_cfg = cfg.get("tf_candidates", [])
    tgt_cfg = cfg.get("target_genes", [])

    def n(frame, col=None, unique=False):
        if frame is None:
            return UNKNOWN
        if col is None:
            return int(len(frame))
        if col not in frame.columns:
            return UNKNOWN
        return int(frame[col].nunique()) if unique else int(frame[col].notna().sum())

    def truthy(frame, col):
        if frame is None or col not in frame.columns:
            return UNKNOWN
        return int(frame[col].astype(str).str.lower().isin({"true", "1"}).sum())

    steps = [
        {"step": "S00_human_TF_universe",
         "quantity": "transcription factors in the human genome (external reference, not measured here)",
         "value": UNKNOWN,
         "restriction_kind": "not_measured_by_this_audit"},
        {"step": "S01_stage72b_TF_candidates_declared",
         "quantity": "TFs hand-listed in stage72b config tf_candidates",
         "value": len(tf_cfg), "restriction_kind": "scientific_decision_hand_curated"},
        {"step": "S02_stage72b_target_genes_declared",
         "quantity": "target genes hand-listed in stage72b config target_genes",
         "value": len(tgt_cfg), "restriction_kind": "scientific_decision_hand_curated"},
        {"step": "S03_stage72b_edges_tested",
         "quantity": "TF-target pairs with a coactivity test row",
         "value": n(s72b), "restriction_kind": "consequence_of_S01_x_S02"},
        {"step": "S04_stage72b_edges_passing",
         "quantity": "rows with edge_candidate_pass true",
         "value": truthy(s72b, "edge_candidate_pass"),
         "restriction_kind": "scientific_decision_rho_and_stability_thresholds"},
        {"step": "S05_stage75f_regulators_carried",
         "quantity": "regulators carried into Stage75F batching",
         "value": n(cand_e, "source_tf", unique=True),
         "restriction_kind": "scientific_decision_regulator_shortlist"},
        {"step": "S06_stage75f_candidate_edges",
         "quantity": "TF-target edges after top_targets_per_tf cap",
         "value": n(cand_e), "restriction_kind": "compute_constraint_top_targets_per_tf"},
        {"step": "S07_stage75c_peak_universe",
         "quantity": "GSE174367 ATAC peaks with a nearest-gene annotation",
         "value": n(s75c), "restriction_kind": "measured_peak_universe"},
        {"step": "S08_stage75f_peaks_selected",
         "quantity": "peaks retained as the whole Stage75F query universe",
         "value": n(cand_pg), "restriction_kind": "compute_constraint_nearest_gene_and_top_peaks"},
        {"step": "S09_batches",
         "quantity": "per-TF cisTarget batches executed",
         "value": n(batches), "restriction_kind": "execution_unit"},
        {"step": "S10_query_regions_total_slots",
         "quantity": "sum of n_query_regions over batches (counts shared peaks repeatedly)",
         "value": int(coverage["n_query_regions"].sum()) if coverage is not None else UNKNOWN,
         "restriction_kind": "derived"},
        {"step": "S11_mapped_db_regions_total_slots",
         "quantity": "sum of n_unique_db_regions over batches",
         "value": int(coverage["n_unique_db_regions"].sum()) if coverage is not None else UNKNOWN,
         "restriction_kind": "derived"},
        {"step": "S12_cistarget_global_regions",
         "quantity": "regions in the hg38 SCREEN v10 cisTarget database",
         "value": manifest["parameters"]["cistarget_global_region_count"],
         "restriction_kind": "external_resource_size"},
        {"step": "S13_motifs_tested_per_batch",
         "quantity": "motifs scored per batch (full collection, NOT restricted)",
         "value": manifest["parameters"]["motif_count_per_batch"],
         "restriction_kind": "not_restricted"},
        {"step": "S14_frozen_regulators",
         "quantity": "rows in integrated regulator summary",
         "value": n(integ_reg), "restriction_kind": "freeze_output"},
        {"step": "S15_frozen_tf_target_rows",
         "quantity": "rows in integrated TF-target summary",
         "value": n(integ_tt), "restriction_kind": "freeze_output"},
        {"step": "S16_frozen_negative_gate_rows",
         "quantity": "rows in integrated negative regulator gate",
         "value": n(integ_neg), "restriction_kind": "freeze_output_internal_negative_control"},
        {"step": "S17_distinct_target_genes_in_freeze",
         "quantity": "distinct target genes across the 96 frozen rows",
         "value": n(integ_tt, "target_gene", unique=True), "restriction_kind": "freeze_output"},
        {"step": "S18_distinct_TFs_in_freeze",
         "quantity": "distinct TFs across the 96 frozen rows",
         "value": n(integ_tt, "tf", unique=True), "restriction_kind": "freeze_output"},
    ]

    # The property the frozen summaries cannot show: query-set overlap.
    overlap: dict = {"status": UNKNOWN}
    if mapping is not None and {"tf", "query_region"} <= set(mapping.columns):
        sets = {tf: set(g["query_region"].astype(str))
                for tf, g in mapping.groupby("tf")}
        union = set().union(*sets.values()) if sets else set()
        pairs = []
        for a, b in itertools.combinations(sorted(sets), 2):
            inter = len(sets[a] & sets[b])
            uni = len(sets[a] | sets[b])
            pairs.append({
                "tf_a": a, "tf_b": b,
                "n_a": len(sets[a]), "n_b": len(sets[b]),
                "n_shared": inter,
                "jaccard": round(inter / uni, 6) if uni else UNKNOWN,
                "frac_of_smaller_shared": round(
                    inter / min(len(sets[a]), len(sets[b])), 6)
                if min(len(sets[a]), len(sets[b])) else UNKNOWN,
            })
        pair_frame = pd.DataFrame(pairs)
        overlap = {
            "status": "MEASURED",
            "n_tfs": len(sets),
            "n_distinct_query_regions_across_all_tfs": len(union),
            "sum_of_per_tf_query_regions": sum(len(v) for v in sets.values()),
            "mean_pairwise_jaccard": round(float(pair_frame["jaccard"].mean()), 6),
            "min_pairwise_jaccard": round(float(pair_frame["jaccard"].min()), 6),
            "max_pairwise_jaccard": round(float(pair_frame["jaccard"].max()), 6),
            "mean_frac_of_smaller_shared": round(
                float(pair_frame["frac_of_smaller_shared"].mean()), 6),
            "interpretation": (
                "Each TF's cisTarget query set is drawn from one shared pool of "
                "peaks. High pairwise overlap means the ten motif-enrichment "
                "analyses are not ten independent region sets, so a motif "
                "enriched in the shared pool will appear enriched for every TF. "
                "TF specificity in this design is therefore carried almost "
                "entirely by the motif-to-TF annotation step, not by the "
                "enrichment test. A shuffled-TF-label control is required "
                "before any TF-specific reading of these rows."
            ),
            "pairs": pairs,
        }

    return pd.DataFrame(steps), overlap


def shared_top_motif_check(root: Path) -> dict:
    """Do different TFs share their top supported motif?"""
    frame = read_csv(root / "results/tables/stage75_integrated_regulator_summary_v1.csv")
    if frame is None or "top_batch_tf_supported_motif" not in frame.columns:
        return {"status": UNKNOWN}
    sub = frame.loc[frame["top_batch_tf_supported_motif"].notna()
                    & frame["top_batch_tf_supported_motif"].astype(str).str.len().gt(0)]
    counts = sub.groupby("top_batch_tf_supported_motif")["tf"].apply(
        lambda s: sorted(s.astype(str))).to_dict()
    return {
        "status": "MEASURED",
        "n_regulators_with_a_top_motif": int(len(sub)),
        "n_distinct_top_motifs": int(sub["top_batch_tf_supported_motif"].nunique()),
        "motif_to_regulators": {k: v for k, v in counts.items()},
        "n_motifs_shared_by_more_than_one_regulator": int(
            sum(1 for v in counts.values() if len(v) > 1)),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data-root", required=True,
                    help="Repository whose working tree holds the Stage75F artifacts")
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    root = Path(args.data_root).resolve()
    out = Path(args.out_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    manifest_path = root / "results/reports/stage75_integrated_evidence_manifest_v1.json"
    if not manifest_path.is_file():
        raise SystemExit(f"Frozen manifest not found: {manifest_path}")

    import yaml
    cfg_path = root / "configs/agent/stage72b_external_morabito_micro_pvm_grn_construction_v1.yaml"
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) if cfg_path.is_file() else {}

    manifest, auth, resources = authenticate(root, manifest_path)
    funnel, overlap = restriction_funnel(root, cfg, manifest)
    top_motif = shared_top_motif_check(root)

    auth.to_csv(out / "agent4_stage75f_authentication_v1.csv", index=False)
    resources.to_csv(out / "agent4_stage75f_external_resources_v1.csv", index=False)
    funnel.to_csv(out / "agent4_stage75f_restriction_funnel_v1.csv", index=False)
    if overlap.get("pairs"):
        pd.DataFrame(overlap["pairs"]).to_csv(
            out / "agent4_stage75f_query_region_overlap_pairs_v1.csv", index=False)

    pinned = auth.loc[auth["role"] == "manifest_pinned_source"]
    report = {
        "audit": "agent4_stage75f_authentication_and_restriction_audit_v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "data_root": str(root),
        "audit_code_commit": git(Path(__file__).resolve().parents[2], "rev-parse", "HEAD") or UNKNOWN,
        "data_root_commit": git(root, "rev-parse", "HEAD") or UNKNOWN,
        "data_root_branch": git(root, "rev-parse", "--abbrev-ref", "HEAD") or UNKNOWN,
        "frozen_manifest_declared_git_commit": manifest.get("git_commit", UNKNOWN),
        "authentication": {
            "n_manifest_pinned_sources": int(len(pinned)),
            "n_digest_match": int((pinned["digest_match"] == True).sum()),  # noqa: E712
            "n_digest_mismatch": int((pinned["digest_match"] == False).sum()),  # noqa: E712
            "n_row_match": int((pinned["row_match"] == True).sum()),  # noqa: E712
            "all_pinned_sources_authenticate": bool(
                (pinned["digest_match"] == True).all()  # noqa: E712
                and (pinned["row_match"] == True).all()),  # noqa: E712
            "n_chain_artifacts_untracked": int(
                (auth["git_tracking"] == "UNTRACKED_NOT_DIGEST_ANCHORED").sum()),
            "untracked_chain_artifacts": auth.loc[
                auth["git_tracking"] == "UNTRACKED_NOT_DIGEST_ANCHORED",
                "path"].tolist(),
        },
        "restriction_funnel": funnel.to_dict(orient="records"),
        "query_region_overlap": overlap,
        "shared_top_motif": top_motif,
        "claim_boundaries": {
            "biological_result": "NOT_EXECUTED",
            "validated_regulation": False,
            "validated_eregulon_set": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "independent_validation_of_jepa": False,
            "statement": (
                "The Stage75F freeze is a set of HYPOTHESES: candidate TF-target "
                "pairs with motif-enrichment and proximity evidence. It is not a "
                "validated eRegulon set and contains no experimentally proven "
                "regulation."
            ),
        },
        "governance": ("TRAINING=OFF | AUDIT_B_N1=UNOPENED | "
                       "PROTECTED_FULL104_OUTCOMES=UNOPENED | D_SHARED_G5=UNOPENED | "
                       "RARE_TAIL_MOLECULAR=UNOPENED | THERAPEUTIC_RANKING=OFF"),
    }
    (out / "agent4_stage75f_audit_report_v1.json").write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(json.dumps(report, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
