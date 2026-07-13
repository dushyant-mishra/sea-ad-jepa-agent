#!/usr/bin/env python3
"""Stage75F/F6 bounded secondary-regulator cisTarget motif-support expansion.

Reuses the validated F5b bounded cisTarget engine for the eight descriptive
secondary TF hypotheses. Each TF is processed sequentially and checkpointed in
its own output directory. Successful computation does not require positive
motif support for any TF.

These results remain enhancer-informed candidate evidence only. They are not
validated regulation, a validated GRN, causal validation, or therapeutic
claims.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import pandas as pd

import stage75f_run_primary_motif_pilot as engine


def parse_tf_filter(value: str | None) -> list[str] | None:
    if value is None:
        return None
    tfs = [item.strip() for item in value.split(",") if item.strip()]
    if not tfs:
        raise ValueError("--tfs was provided but contained no TF names")
    if len(tfs) != len(set(tfs)):
        raise ValueError(f"--tfs contains duplicates: {tfs}")
    return tfs


def secondary_batches(
    batch_manifest: pd.DataFrame,
    configured_tfs: list[str],
    tf_filter: list[str] | None,
) -> pd.DataFrame:
    configured_set = set(configured_tfs)
    requested = configured_tfs if tf_filter is None else tf_filter
    unknown = sorted(set(requested) - configured_set)
    if unknown:
        raise ValueError(
            f"Requested TFs are not configured secondary hypotheses: {unknown}"
        )

    selected = batch_manifest.loc[
        batch_manifest["tf"].astype(str).isin(requested)
    ].copy()
    if selected.empty:
        raise RuntimeError("No secondary-regulator batches were selected")

    counts = selected.groupby("tf").size()
    bad_counts = counts.loc[counts.ne(1)]
    missing = sorted(set(requested) - set(counts.index.astype(str)))
    if len(bad_counts) or missing:
        raise RuntimeError(
            "Expected exactly one F4 batch per requested secondary TF; "
            f"bad_counts={bad_counts.to_dict()} missing={missing}"
        )

    selected["batch_id"] = pd.to_numeric(
        selected["batch_id"], errors="raise"
    ).astype(int)
    return selected.sort_values("batch_id").reset_index(drop=True)


def update_batch_report(
    report: dict[str, Any],
    report_path: Path,
) -> dict[str, Any]:
    revised = dict(report)
    revised["stage"] = "stage75f_secondary_motif_pilot_batch_v1"
    revised["purpose"] = (
        "bounded cisTarget motif-support expansion for a descriptive "
        "secondary regulator hypothesis"
    )
    revised["regulator_role"] = "descriptive_secondary_hypothesis"
    revised["claim_boundaries"] = {
        "motif_enrichment_completed": True,
        "enhancer_informed_evidence_only": True,
        "secondary_hypothesis_only": True,
        "validated_regulation": False,
        "validated_grn_claim": False,
        "causal_validation_pass": False,
        "therapeutic_target_claim": False,
    }
    engine.atomic_text(report_path, json.dumps(revised, indent=2))
    return revised


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--force", action="store_true")
    parser.add_argument(
        "--tfs",
        type=str,
        default=None,
        help="Optional comma-separated subset of configured secondary TFs",
    )
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = engine.load_config(args.config.resolve())
    pilot_cfg = cfg["cistarget_secondary_pilot"]
    mapping_cfg = cfg["cistarget_region_mapping"]

    configured_tfs = list(
        pilot_cfg.get(
            "tfs",
            cfg["regulators"]["descriptive_secondary_hypotheses"],
        )
    )
    tf_filter = parse_tf_filter(args.tfs)

    rankings_path = project / cfg["inputs"]["cistarget_rankings"]
    annotation_path = project / cfg["inputs"]["motif_annotation"]
    mapping = pd.read_csv(project / mapping_cfg["mapping_csv"])
    coverage = pd.read_csv(project / mapping_cfg["coverage_csv"])
    index_manifest = engine.load_index_manifest(
        project / mapping_cfg["index_manifest_json"]
    )
    total_regions = int(index_manifest["n_parseable_regions"])
    motif_ids, motif_column_index, motif_column_name = engine.read_motif_ids(
        rankings_path,
        int(index_manifest["n_columns"]),
    )
    print(
        f"cisTarget motif index PASS column={motif_column_name} "
        f"motifs={len(motif_ids)} total_regions={total_regions}",
        flush=True,
    )

    annotations = engine.load_annotations(annotation_path)
    print(f"motif annotations loaded motifs={len(annotations)}", flush=True)

    batch_manifest = pd.read_csv(project / cfg["outputs"]["batch_manifest_csv"])
    batches = secondary_batches(batch_manifest, configured_tfs, tf_filter)
    selected_tfs = batches["tf"].astype(str).tolist()
    print(
        "secondary TF batches: "
        + ", ".join(
            f"{row.tf}(batch={int(row.batch_id)})"
            for row in batches.itertuples(index=False)
        ),
        flush=True,
    )

    output_dir = project / pilot_cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    all_frames: list[pd.DataFrame] = []
    enriched_frames: list[pd.DataFrame] = []
    hit_frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []

    for batch in batches.itertuples(index=False):
        tf = str(batch.tf)
        batch_id = int(batch.batch_id)
        bed_path = Path(str(batch.bed_path))
        region_list_path = project / bed_path.with_name(
            bed_path.name.replace(".regions.bed", ".cistarget_regions.txt")
        )
        if not region_list_path.exists():
            raise FileNotFoundError(region_list_path)

        all_output, enriched_output, hits_output, report = engine.process_batch(
            project=project,
            tf=tf,
            batch_id=batch_id,
            region_list_path=region_list_path,
            rankings_path=rankings_path,
            mapping=mapping,
            coverage=coverage,
            motif_ids=motif_ids,
            motif_column_index=motif_column_index,
            annotations=annotations,
            total_regions=total_regions,
            pilot_cfg=pilot_cfg,
            output_dir=output_dir,
            force=args.force,
        )

        batch_paths = engine.output_paths(output_dir, batch_id, tf)
        report = update_batch_report(report, batch_paths["summary"])
        all_frames.append(all_output)
        enriched_frames.append(enriched_output)
        hit_frames.append(hits_output)
        reports.append(report)

    combined_all = pd.concat(all_frames, ignore_index=True)
    combined_enriched = pd.concat(enriched_frames, ignore_index=True)
    combined_hits = pd.concat(hit_frames, ignore_index=True)
    support_summary = pd.DataFrame([item["summary"] for item in reports])
    support_summary.insert(
        support_summary.columns.get_loc("tf") + 1,
        "regulator_role",
        "descriptive_secondary_hypothesis",
    )

    output_cfg = pilot_cfg["outputs"]
    all_path = project / output_cfg["all_motifs_csv_gz"]
    enriched_path = project / output_cfg["enriched_motifs_csv"]
    hits_path = project / output_cfg["motif_hits_csv"]
    support_path = project / output_cfg["tf_support_summary_csv"]
    report_path = project / output_cfg["report_json"]

    engine.atomic_csv(combined_all, all_path, compression="gzip")
    engine.atomic_csv(combined_enriched, enriched_path)
    engine.atomic_csv(combined_hits, hits_path)
    engine.atomic_csv(support_summary, support_path)

    n_direct = int(support_summary["batch_tf_direct_motif_support"].sum())
    n_extended = int(support_summary["batch_tf_extended_motif_support"].sum())
    n_without_support = int(
        (~support_summary["batch_tf_extended_motif_support"].astype(bool)).sum()
    )

    report = {
        "stage": "stage75f_secondary_motif_support_expansion_v1",
        "purpose": (
            "bounded true cisTarget motif enrichment for descriptive "
            "secondary regulator hypotheses"
        ),
        "expansion_pass": bool(
            len(reports) == len(selected_tfs)
            and all(item.get("complete") is True for item in reports)
        ),
        "secondary_tfs": selected_tfs,
        "global_total_db_regions": total_regions,
        "n_motifs_tested_per_batch": len(motif_ids),
        "n_secondary_tfs_with_direct_support": n_direct,
        "n_secondary_tfs_with_extended_support": n_extended,
        "n_secondary_tfs_without_tf_annotated_motif_support": n_without_support,
        "n_combined_enriched_motif_rows": int(len(combined_enriched)),
        "n_combined_motif_hit_rows": int(len(combined_hits)),
        "batch_summaries": support_summary.to_dict(orient="records"),
        "outputs": {
            key: str((project / value).relative_to(project))
            for key, value in output_cfg.items()
        },
        "claim_boundaries": {
            "motif_enrichment_completed": True,
            "enhancer_informed_evidence_only": True,
            "secondary_hypothesis_only": True,
            "prediction_benchmark_updated": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
            "validated_grn_claim": False,
            "approved_wording": cfg.get("safety", {}).get(
                "approved_wording",
                "Model-based, enhancer-informed perturbation hypotheses "
                "requiring experimental validation.",
            ),
        },
    }
    engine.atomic_text(report_path, json.dumps(report, indent=2))

    for path in [all_path, enriched_path, hits_path, support_path, report_path]:
        print(f"Wrote: {path}", flush=True)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if report["expansion_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
