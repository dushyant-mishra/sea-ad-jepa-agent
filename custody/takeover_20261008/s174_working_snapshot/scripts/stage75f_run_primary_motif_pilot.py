#!/usr/bin/env python3
"""Stage75F/F5b bounded primary-regulator cisTarget motif-support pilot.

Runs true cisTarget ranking enrichment for IRF8 and STAT1 using only their
F5a-mapped SCREEN database regions, while retaining the full cisTarget region
universe for AUC/NES normalization.

This is enhancer-informed motif support only. It is not validated regulation,
a validated GRN, causal validation, or a therapeutic claim.
"""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pyarrow.feather as feather
import yaml


INDEX_COLUMN_NAMES = {"motifs", "tracks", "regions", "genes"}


def load_config(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        cfg = yaml.safe_load(handle)
    if not isinstance(cfg, dict):
        raise ValueError(f"Config is not a mapping: {path}")
    return cfg


def atomic_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def atomic_csv(
    frame: pd.DataFrame,
    path: Path,
    *,
    compression: str | None = None,
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = ".tmp.gz" if compression == "gzip" else ".tmp"
    fd, tmp = tempfile.mkstemp(prefix=f".{path.name}.", suffix=suffix, dir=path.parent)
    os.close(fd)
    try:
        frame.to_csv(tmp, index=False, compression=compression)
        Path(tmp).replace(path)
    except Exception:
        Path(tmp).unlink(missing_ok=True)
        raise


def read_region_list(path: Path) -> list[str]:
    regions = [x.strip() for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]
    if not regions:
        raise RuntimeError(f"No cisTarget regions found in {path}")
    if len(regions) != len(set(regions)):
        raise ValueError(f"Duplicate cisTarget regions found in {path}")
    return regions


def load_index_manifest(path: Path) -> dict[str, Any]:
    report = json.loads(path.read_text(encoding="utf-8"))
    required = {"n_columns", "n_parseable_regions", "n_nonregion_columns", "complete"}
    missing = required - set(report)
    if missing:
        raise ValueError(f"Missing index-manifest fields: {sorted(missing)}")
    if report["complete"] is not True:
        raise RuntimeError(f"Region index is incomplete: {path}")
    if int(report["n_nonregion_columns"]) != 1:
        raise RuntimeError(
            f"Expected one non-region index column, found {report['n_nonregion_columns']}"
        )
    return report


def read_motif_ids(
    rankings_path: Path,
    n_columns: int,
) -> tuple[list[str], int, str]:
    motif_column_index = n_columns - 1
    table = feather.read_table(
        str(rankings_path),
        columns=[motif_column_index],
        memory_map=False,
        use_threads=False,
    )
    if table.num_columns != 1:
        raise RuntimeError(f"Expected one motif-index column, got {table.num_columns}")
    column_name = str(table.schema.field(0).name)
    if column_name not in INDEX_COLUMN_NAMES:
        raise RuntimeError(f"Unexpected cisTarget index column {column_name!r}")
    motif_ids = [str(x) for x in table.column(0).to_pylist()]
    if not motif_ids or len(motif_ids) != len(set(motif_ids)):
        raise RuntimeError("Motif index is empty or contains duplicate IDs")
    return motif_ids, motif_column_index, column_name


def resolve_region_indices(
    mapping: pd.DataFrame,
    tf: str,
    expected_regions: list[str],
    motif_column_index: int,
) -> pd.DataFrame:
    required = {
        "tf", "mapped_db_region", "db_column_index", "query_region",
        "overlap_bp", "overlap_fraction_query", "overlap_fraction_db",
    }
    missing = required - set(mapping)
    if missing:
        raise ValueError(f"Missing F5a mapping columns: {sorted(missing)}")

    tf_mapping = mapping.loc[
        mapping["tf"].astype(str).eq(tf)
        & mapping["mapped_db_region"].astype(str).isin(expected_regions)
    ].copy()
    if tf_mapping.empty:
        raise RuntimeError(f"No F5a mappings found for {tf}")

    pairs = (
        tf_mapping[["mapped_db_region", "db_column_index"]]
        .drop_duplicates()
        .copy()
    )
    conflicts = pairs["mapped_db_region"].duplicated(keep=False)
    if conflicts.any():
        raise RuntimeError(
            f"Conflicting database indices for {tf}: "
            f"{pairs.loc[conflicts].head().to_dict(orient='records')}"
        )

    observed = set(pairs["mapped_db_region"].astype(str))
    expected = set(expected_regions)
    if observed != expected:
        raise RuntimeError(
            f"{tf} region/index mismatch: "
            f"missing={sorted(expected-observed)[:5]} "
            f"unexpected={sorted(observed-expected)[:5]}"
        )

    pairs["db_column_index"] = pd.to_numeric(
        pairs["db_column_index"], errors="raise"
    ).astype(np.int64)
    if pairs["db_column_index"].lt(0).any() or pairs["db_column_index"].ge(
        motif_column_index
    ).any():
        raise RuntimeError(f"{tf} has invalid cisTarget region column indices")
    return pairs.sort_values("db_column_index").reset_index(drop=True)


def read_rankings_subset(
    rankings_path: Path,
    pairs: pd.DataFrame,
    motif_ids: list[str],
) -> pd.DataFrame:
    indices = pairs["db_column_index"].astype(int).tolist()
    expected_names = pairs["mapped_db_region"].astype(str).tolist()
    if indices != sorted(indices) or len(indices) != len(set(indices)):
        raise RuntimeError("Bounded Feather indices must be sorted and unique")

    table = feather.read_table(
        str(rankings_path),
        columns=indices,
        memory_map=False,
        use_threads=False,
    )
    actual_names = [str(x) for x in table.schema.names]
    if actual_names != expected_names:
        mismatch = [
            {"position": i, "expected": a, "actual": b}
            for i, (a, b) in enumerate(zip(expected_names, actual_names))
            if a != b
        ]
        raise RuntimeError(
            f"Bounded rankings column verification failed: {mismatch[:3]}"
        )
    if table.num_rows != len(motif_ids):
        raise RuntimeError(
            f"Rankings rows={table.num_rows}, motif IDs={len(motif_ids)}"
        )

    frame = table.to_pandas(split_blocks=True)
    frame.index = pd.Index(motif_ids, name="MotifID")
    if not all(np.issubdtype(dtype, np.integer) for dtype in frame.dtypes):
        raise RuntimeError(
            f"Rankings subset has non-integer dtypes: "
            f"{sorted(set(map(str, frame.dtypes)))}"
        )
    return frame


def load_annotations(path: Path) -> pd.DataFrame:
    from pycistarget.utils import load_motif_annotations

    frame = load_motif_annotations(specie="homo_sapiens", fname=str(path))
    frame.index = frame.index.astype(str)
    frame.index.name = "MotifID"
    return frame


def tokens(value: Any) -> set[str]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return set()
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return set()
    return {x.strip() for x in text.split(",") if x.strip()}


def add_tf_flags(frame: pd.DataFrame, tf: str) -> pd.DataFrame:
    result = frame.copy()
    annotation_columns = [
        "Direct_annot",
        "Motif_similarity_annot",
        "Orthology_annot",
        "Motif_similarity_and_Orthology_annot",
    ]
    for column in annotation_columns:
        if column not in result:
            result[column] = np.nan

    result["batch_tf"] = tf
    result["batch_tf_direct_support"] = result["Direct_annot"].map(
        lambda value: tf in tokens(value)
    )
    result["batch_tf_similarity_support"] = result[
        "Motif_similarity_annot"
    ].map(lambda value: tf in tokens(value))
    result["batch_tf_orthology_support"] = result["Orthology_annot"].map(
        lambda value: tf in tokens(value)
    )
    result["batch_tf_similarity_orthology_support"] = result[
        "Motif_similarity_and_Orthology_annot"
    ].map(lambda value: tf in tokens(value))
    result["batch_tf_extended_support"] = result[
        [
            "batch_tf_direct_support",
            "batch_tf_similarity_support",
            "batch_tf_orthology_support",
            "batch_tf_similarity_orthology_support",
        ]
    ].any(axis=1)
    return result


def bounded_recovery(rankings: np.ndarray, rank_threshold: int) -> np.ndarray:
    """Unweighted recovery curves without allocating to the largest genome rank."""
    rankings = np.asarray(rankings)
    if rankings.ndim != 2:
        raise ValueError("rankings must be a two-dimensional array")
    curves = np.empty((rankings.shape[0], rank_threshold), dtype=np.float64)
    for i, row in enumerate(rankings):
        valid = row[(row >= 0) & (row < rank_threshold)].astype(np.int64, copy=False)
        counts = np.bincount(valid, minlength=rank_threshold)
        curves[i] = np.cumsum(counts[:rank_threshold], dtype=np.float64)
    return curves


def calculate_enrichment(
    rankings: pd.DataFrame,
    total_regions: int,
    auc_threshold: float,
    nes_threshold: float,
    rank_threshold_fraction: float,
    recovery_batch_size: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    from ctxcore.recovery import aucs as ctx_aucs
    from ctxcore.recovery import leading_edge

    n_selected = int(rankings.shape[1])
    weights = np.ones(n_selected, dtype=np.float64)
    auc_values = ctx_aucs(rankings, total_regions, weights, auc_threshold)
    auc_std = float(np.std(auc_values))
    if not np.isfinite(auc_std) or auc_std <= 0:
        raise RuntimeError(f"Invalid motif AUC standard deviation: {auc_std}")
    nes_values = (auc_values - float(np.mean(auc_values))) / auc_std

    enrichment = pd.DataFrame(
        {
            "AUC": auc_values.astype(np.float64),
            "NES": nes_values.astype(np.float64),
            "enriched": nes_values >= nes_threshold,
            "n_selected_db_regions": n_selected,
            "global_total_db_regions": int(total_regions),
            "auc_threshold": float(auc_threshold),
            "nes_threshold": float(nes_threshold),
        },
        index=rankings.index,
    )
    enrichment.index.name = "MotifID"
    enrichment["Rank_at_max"] = pd.Series(
        pd.array([pd.NA] * len(enrichment), dtype="Int64"),
        index=enrichment.index,
    )
    enrichment["n_motif_hit_db_regions"] = 0

    enriched_ids = enrichment.index[
        enrichment["enriched"].astype(bool)
    ].tolist()
    print(f"  enriched motifs={len(enriched_ids)}", flush=True)
    if not enriched_ids:
        return enrichment, pd.DataFrame(
            columns=[
                "MotifID", "mapped_db_region", "database_rank",
                "leading_edge_weight", "Rank_at_max",
            ]
        )

    rank_threshold = int(rank_threshold_fraction * total_regions)
    if not 0 < rank_threshold < total_regions:
        raise ValueError(f"Invalid recovery rank threshold {rank_threshold}")

    values = rankings.to_numpy(copy=False)
    curve_sum = np.zeros(rank_threshold, dtype=np.float64)
    curve_sumsq = np.zeros(rank_threshold, dtype=np.float64)
    n_curves = 0
    print(
        f"  recovery reference motifs={len(rankings)} "
        f"rank_threshold={rank_threshold} batch={recovery_batch_size}",
        flush=True,
    )
    for start in range(0, len(rankings), recovery_batch_size):
        end = min(start + recovery_batch_size, len(rankings))
        curves = bounded_recovery(values[start:end], rank_threshold)
        curve_sum += curves.sum(axis=0)
        curve_sumsq += np.square(curves).sum(axis=0)
        n_curves += curves.shape[0]
        del curves
        if end == len(rankings) or end % (recovery_batch_size * 10) == 0:
            print(f"    recovery reference {end}/{len(rankings)} motifs", flush=True)

    mean_curve = curve_sum / n_curves
    variance = np.maximum(curve_sumsq / n_curves - np.square(mean_curve), 0.0)
    avg2std = mean_curve + 2.0 * np.sqrt(variance)

    hit_rows: list[dict[str, Any]] = []
    for motif_id in enriched_ids:
        pos = rankings.index.get_loc(motif_id)
        motif_ranks = values[pos]
        curve = bounded_recovery(motif_ranks.reshape(1, -1), rank_threshold)[0]
        hits, rank_at_max = leading_edge(
            curve,
            avg2std,
            motif_ranks,
            rankings.columns.to_numpy(dtype=str),
            weights,
        )
        enrichment.loc[motif_id, "Rank_at_max"] = int(rank_at_max)
        enrichment.loc[motif_id, "n_motif_hit_db_regions"] = int(len(hits))
        for db_region, weight in hits:
            region_pos = rankings.columns.get_loc(str(db_region))
            hit_rows.append(
                {
                    "MotifID": str(motif_id),
                    "mapped_db_region": str(db_region),
                    "database_rank": int(motif_ranks[region_pos]),
                    "leading_edge_weight": float(weight),
                    "Rank_at_max": int(rank_at_max),
                }
            )
    return enrichment, pd.DataFrame(hit_rows)


def expand_hits(
    motif_hits: pd.DataFrame,
    tf_mapping: pd.DataFrame,
    tf: str,
    batch_id: int,
) -> pd.DataFrame:
    columns = [
        "batch_id", "tf", "MotifID", "mapped_db_region", "database_rank",
        "leading_edge_weight", "Rank_at_max", "query_region", "query_name",
        "overlap_bp", "overlap_fraction_query", "overlap_fraction_db",
        "exact_match",
    ]
    if motif_hits.empty:
        return pd.DataFrame(columns=columns)
    mapping_columns = [
        "mapped_db_region", "query_region", "query_name", "overlap_bp",
        "overlap_fraction_query", "overlap_fraction_db", "exact_match",
    ]
    available = [x for x in mapping_columns if x in tf_mapping]
    result = motif_hits.merge(
        tf_mapping[available].drop_duplicates(),
        on="mapped_db_region",
        how="left",
        validate="many_to_many",
    )
    result.insert(0, "tf", tf)
    result.insert(0, "batch_id", int(batch_id))
    for column in columns:
        if column not in result:
            result[column] = np.nan
    return result[columns]


def summarize(
    tf: str,
    batch_id: int,
    coverage_row: pd.Series,
    enrichment: pd.DataFrame,
    hits: pd.DataFrame,
) -> dict[str, Any]:
    enriched = enrichment.loc[enrichment["enriched"].astype(bool)]
    direct = enriched.loc[enriched["batch_tf_direct_support"].astype(bool)]
    extended = enriched.loc[enriched["batch_tf_extended_support"].astype(bool)]
    supported_hits = (
        hits.loc[hits["MotifID"].isin(extended.index.astype(str))]
        if not hits.empty
        else hits
    )
    top = extended.sort_values(["NES", "AUC"], ascending=False).head(1)
    return {
        "batch_id": int(batch_id),
        "tf": tf,
        "n_query_regions": int(coverage_row["n_query_regions"]),
        "n_mapped_query_regions": int(coverage_row["n_mapped_query_regions"]),
        "query_coverage_fraction": float(coverage_row["query_coverage_fraction"]),
        "n_selected_db_regions": int(enrichment["n_selected_db_regions"].iloc[0]),
        "n_motifs_tested": int(len(enrichment)),
        "n_enriched_motifs": int(len(enriched)),
        "n_direct_batch_tf_enriched_motifs": int(len(direct)),
        "n_extended_batch_tf_enriched_motifs": int(len(extended)),
        "batch_tf_direct_motif_support": bool(len(direct)),
        "batch_tf_extended_motif_support": bool(len(extended)),
        "top_batch_tf_supported_motif": (
            str(top.index[0]) if not top.empty else ""
        ),
        "top_batch_tf_supported_motif_nes": (
            float(top.iloc[0]["NES"]) if not top.empty else None
        ),
        "n_batch_tf_supported_hit_rows": int(len(supported_hits)),
        "n_batch_tf_supported_unique_db_regions": int(
            supported_hits["mapped_db_region"].nunique()
            if not supported_hits.empty else 0
        ),
        "motif_enrichment_completed": True,
        "validated_regulation": False,
        "validated_grn_claim": False,
        "causal_validation_pass": False,
        "therapeutic_target_claim": False,
    }


def output_paths(output_dir: Path, batch_id: int, tf: str) -> dict[str, Path]:
    stem = f"stage75f_batch_{batch_id:04d}_{tf}"
    return {
        "all": output_dir / f"{stem}.motif_enrichment_all.csv.gz",
        "enriched": output_dir / f"{stem}.motif_enrichment_enriched.csv",
        "hits": output_dir / f"{stem}.motif_hits.csv",
        "summary": output_dir / f"{stem}.summary.json",
    }


def completed(paths: dict[str, Path]) -> bool:
    if not all(path.exists() for path in paths.values()):
        return False
    try:
        return json.loads(paths["summary"].read_text(encoding="utf-8")).get(
            "complete"
        ) is True
    except Exception:
        return False


def process_batch(
    *,
    project: Path,
    tf: str,
    batch_id: int,
    region_list_path: Path,
    rankings_path: Path,
    mapping: pd.DataFrame,
    coverage: pd.DataFrame,
    motif_ids: list[str],
    motif_column_index: int,
    annotations: pd.DataFrame,
    total_regions: int,
    pilot_cfg: dict[str, Any],
    output_dir: Path,
    force: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, Any]]:
    paths = output_paths(output_dir, batch_id, tf)
    if not force and completed(paths):
        print(f"{tf}: reusing completed batch", flush=True)
        return (
            pd.read_csv(paths["all"], compression="gzip"),
            pd.read_csv(paths["enriched"]),
            pd.read_csv(paths["hits"]),
            json.loads(paths["summary"].read_text(encoding="utf-8")),
        )

    print(f"{tf}: starting bounded cisTarget enrichment", flush=True)
    regions = read_region_list(region_list_path)
    pairs = resolve_region_indices(mapping, tf, regions, motif_column_index)
    rankings = read_rankings_subset(rankings_path, pairs, motif_ids)
    print(
        f"{tf}: rankings subset motifs={rankings.shape[0]} "
        f"regions={rankings.shape[1]}",
        flush=True,
    )

    enrichment, motif_hits = calculate_enrichment(
        rankings,
        total_regions,
        float(pilot_cfg.get("auc_threshold", 0.005)),
        float(pilot_cfg.get("nes_threshold", 3.0)),
        float(pilot_cfg.get("rank_threshold_fraction", 0.05)),
        int(pilot_cfg.get("recovery_motif_batch_size", 64)),
    )
    enrichment = add_tf_flags(enrichment.join(annotations, how="left"), tf)
    enrichment.insert(0, "tf", tf)
    enrichment.insert(0, "batch_id", int(batch_id))

    tf_mapping = mapping.loc[
        mapping["tf"].astype(str).eq(tf)
        & mapping["mapped_db_region"].astype(str).isin(regions)
    ].copy()
    expanded_hits = expand_hits(motif_hits, tf_mapping, tf, batch_id)

    coverage_rows = coverage.loc[
        coverage["tf"].astype(str).eq(tf)
        & pd.to_numeric(coverage["batch_id"], errors="coerce").eq(batch_id)
    ]
    if len(coverage_rows) != 1:
        raise RuntimeError(
            f"Expected one coverage row for {tf}/batch {batch_id}, "
            f"found {len(coverage_rows)}"
        )
    summary = summarize(
        tf, batch_id, coverage_rows.iloc[0], enrichment, expanded_hits
    )

    all_output = enrichment.reset_index()
    enriched_output = all_output.loc[all_output["enriched"].astype(bool)].copy()
    report = {
        "stage": "stage75f_primary_motif_pilot_batch_v1",
        "batch_id": int(batch_id),
        "tf": tf,
        "purpose": "bounded cisTarget motif-support pilot",
        "complete": True,
        "inputs": {
            "region_list": str(region_list_path.relative_to(project)),
            "n_selected_db_regions": int(len(regions)),
            "global_total_db_regions": int(total_regions),
        },
        "summary": summary,
        "outputs": {
            key: str(value.relative_to(project)) for key, value in paths.items()
        },
        "claim_boundaries": {
            "enhancer_informed_evidence_only": True,
            "validated_regulation": False,
            "validated_grn_claim": False,
            "causal_validation_pass": False,
            "therapeutic_target_claim": False,
        },
    }

    atomic_csv(all_output, paths["all"], compression="gzip")
    atomic_csv(enriched_output, paths["enriched"])
    atomic_csv(expanded_hits, paths["hits"])
    atomic_text(paths["summary"], json.dumps(report, indent=2))
    print(
        f"{tf}: complete enriched={len(enriched_output)} "
        f"tf_supported={summary['n_extended_batch_tf_enriched_motifs']}",
        flush=True,
    )
    del rankings, enrichment, motif_hits
    gc.collect()
    return all_output, enriched_output, expanded_hits, report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--project-dir", type=Path, default=Path.cwd())
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    project = args.project_dir.resolve()
    cfg = load_config(args.config.resolve())
    pilot_cfg = cfg["cistarget_primary_pilot"]
    mapping_cfg = cfg["cistarget_region_mapping"]

    rankings_path = project / cfg["inputs"]["cistarget_rankings"]
    annotation_path = project / cfg["inputs"]["motif_annotation"]
    mapping = pd.read_csv(project / mapping_cfg["mapping_csv"])
    coverage = pd.read_csv(project / mapping_cfg["coverage_csv"])
    index_manifest = load_index_manifest(
        project / mapping_cfg["index_manifest_json"]
    )
    total_regions = int(index_manifest["n_parseable_regions"])
    motif_ids, motif_column_index, motif_column_name = read_motif_ids(
        rankings_path,
        int(index_manifest["n_columns"]),
    )
    print(
        f"cisTarget motif index PASS column={motif_column_name} "
        f"motifs={len(motif_ids)} total_regions={total_regions}",
        flush=True,
    )
    annotations = load_annotations(annotation_path)
    print(f"motif annotations loaded motifs={len(annotations)}", flush=True)

    batch_manifest = pd.read_csv(project / cfg["outputs"]["batch_manifest_csv"])
    batch_manifest["batch_id"] = pd.to_numeric(
        batch_manifest["batch_id"], errors="raise"
    ).astype(int)
    primary_tfs = list(
        pilot_cfg.get(
            "tfs",
            cfg["regulators"]["primary_passed_all_stage74_gates"],
        )
    )
    output_dir = project / pilot_cfg["output_dir"]
    output_dir.mkdir(parents=True, exist_ok=True)

    all_frames: list[pd.DataFrame] = []
    enriched_frames: list[pd.DataFrame] = []
    hit_frames: list[pd.DataFrame] = []
    reports: list[dict[str, Any]] = []

    for tf in primary_tfs:
        rows = batch_manifest.loc[batch_manifest["tf"].astype(str).eq(tf)]
        if len(rows) != 1:
            raise RuntimeError(f"Expected one F4 batch for {tf}, found {len(rows)}")
        batch = rows.iloc[0]
        batch_id = int(batch["batch_id"])
        bed_path = Path(str(batch["bed_path"]))
        region_name = bed_path.name.replace(
            ".regions.bed", ".cistarget_regions.txt"
        )
        region_list_path = project / bed_path.with_name(region_name)
        if not region_list_path.exists():
            raise FileNotFoundError(region_list_path)

        all_output, enriched_output, hits_output, report = process_batch(
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
        all_frames.append(all_output)
        enriched_frames.append(enriched_output)
        hit_frames.append(hits_output)
        reports.append(report)

    combined_all = pd.concat(all_frames, ignore_index=True)
    combined_enriched = pd.concat(enriched_frames, ignore_index=True)
    combined_hits = pd.concat(hit_frames, ignore_index=True)
    support_summary = pd.DataFrame([x["summary"] for x in reports])

    output_cfg = pilot_cfg["outputs"]
    all_path = project / output_cfg["all_motifs_csv_gz"]
    enriched_path = project / output_cfg["enriched_motifs_csv"]
    hits_path = project / output_cfg["motif_hits_csv"]
    support_path = project / output_cfg["tf_support_summary_csv"]
    report_path = project / output_cfg["report_json"]

    atomic_csv(combined_all, all_path, compression="gzip")
    atomic_csv(combined_enriched, enriched_path)
    atomic_csv(combined_hits, hits_path)
    atomic_csv(support_summary, support_path)

    report = {
        "stage": "stage75f_primary_motif_support_pilot_v1",
        "purpose": "bounded true cisTarget motif enrichment for primary regulators",
        "pilot_pass": bool(
            len(reports) == len(primary_tfs)
            and all(x.get("complete") is True for x in reports)
        ),
        "primary_tfs": primary_tfs,
        "global_total_db_regions": total_regions,
        "n_motifs_tested_per_batch": len(motif_ids),
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
    atomic_text(report_path, json.dumps(report, indent=2))

    for path in [all_path, enriched_path, hits_path, support_path, report_path]:
        print(f"Wrote: {path}", flush=True)
    print(json.dumps(report, indent=2), flush=True)
    return 0 if report["pilot_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
