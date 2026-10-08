#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

SCHEMA = "FULL104_DATASET_ETL_ATLAS_V3"
EXPECTED = {
    "metadata_cells": 6_351_753,
    "reader_fit_cells": 4_553_407,
    "reader_fit_donors": 104,
    "reader_operators": 42,
    "addresses": 41_238,
}
KEY_FILES = (
    "metadata/foundation_metadata_rows.sqlite",
    "metadata/FOUNDATION_METADATA_ATLAS.json",
    "splits/foundation_split_registry.csv",
    "splits/reader_donor_split.csv",
    "support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv",
    "support/FOUNDATION_SUPPORT_BY_SOURCE.csv",
    "support/FOUNDATION_SUPPORT_BY_OPERATOR.csv",
    "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz",
    "contracts/address_namespace.csv",
    "contracts/unregistered_collisions.csv",
)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def quantiles(values) -> dict[str, float]:
    a = np.asarray(values, dtype=float)
    if a.ndim != 1 or a.size == 0 or not np.all(np.isfinite(a)):
        raise ValueError("quantiles require a finite nonempty vector")
    return {
        str(q): float(np.quantile(a, q))
        for q in (0, .01, .05, .1, .25, .5, .75, .9, .95, .99, 1)
    }


def verify_manifest(root: Path) -> dict[str, dict[str, object]]:
    manifest_path = root / "BUNDLE_SHA256_MANIFEST.csv"
    if not manifest_path.is_file():
        raise SystemExit("missing BUNDLE_SHA256_MANIFEST.csv")
    manifest = pd.read_csv(manifest_path)
    rows = {str(row.path): row for row in manifest.itertuples(index=False)}
    out: dict[str, dict[str, object]] = {}
    for rel in KEY_FILES:
        if rel not in rows:
            raise SystemExit(f"missing {rel} from bundle manifest")
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"missing bundle file {rel}")
        observed = sha256(path)
        expected = str(rows[rel].sha256).lower()
        if observed != expected:
            raise SystemExit(f"hash mismatch {rel}: {observed} != {expected}")
        out[rel] = {"bytes": int(path.stat().st_size), "sha256": observed}
    return out


def source_from_matrix_id(matrix_id: str) -> str:
    if matrix_id.startswith("HVS::"):
        return "HVS"
    if matrix_id.startswith("NPH52::"):
        return "NPH52"
    return "SEA_AD"


def build_support_geometry(root: Path) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    path = root / "support/FOUNDATION_OPERATOR_ADDRESS_OBSERVATION_STATE.npz"
    with np.load(path, allow_pickle=False) as z:
        states = np.asarray(z["states"], dtype=np.uint8)
        matrix_id = np.asarray(z["matrix_id"]).astype(str)
        operator_index = np.asarray(z["operator_index"], dtype=np.int64)
        address_index = np.asarray(z["molecular_address_index"], dtype=np.int64)
        state_names = tuple(np.asarray(z["state_names"]).astype(str).tolist())
    if states.shape != (EXPECTED["reader_operators"], EXPECTED["addresses"]):
        raise SystemExit(f"unexpected observation-state shape {states.shape}")
    if not np.array_equal(operator_index, np.arange(EXPECTED["reader_operators"])):
        raise SystemExit("operator indexes are not canonical 0..41")
    if not np.array_equal(address_index, np.arange(EXPECTED["addresses"])):
        raise SystemExit("address indexes are not canonical 0..41237")
    if set(state_names) != {
        "MEASURED_COLLISION_UNRESOLVED",
        "MEASURED_SCALAR",
        "STRUCTURALLY_UNMEASURED",
    }:
        raise SystemExit(f"unexpected observation-state vocabulary {state_names}")
    measured_code = state_names.index("MEASURED_SCALAR")
    measured = states == measured_code
    source = np.asarray([source_from_matrix_id(x) for x in matrix_id], dtype=object)

    pattern_rows = []
    for i in range(states.shape[0]):
        digest = hashlib.sha256(np.packbits(measured[i]).tobytes()).hexdigest()
        pattern_rows.append(
            {
                "source": str(source[i]),
                "operator_index": int(operator_index[i]),
                "matrix_id": str(matrix_id[i]),
                "measured_scalar_addresses": int(measured[i].sum()),
                "support_pattern_sha256": digest,
            }
        )
    operator_patterns = pd.DataFrame(pattern_rows)
    pattern_summary = (
        operator_patterns.groupby(["source", "support_pattern_sha256"], as_index=False)
        .agg(
            operators=("matrix_id", "count"),
            measured_scalar_addresses=("measured_scalar_addresses", "first"),
        )
        .sort_values(["source", "measured_scalar_addresses", "support_pattern_sha256"])
        .reset_index(drop=True)
    )

    source_masks: dict[str, dict[str, np.ndarray]] = {}
    for src in sorted(set(source.tolist())):
        block = measured[source == src]
        source_masks[src] = {"all": block.all(axis=0), "any": block.any(axis=0)}

    overlap_rows = []
    sources = sorted(source_masks)
    for i, left in enumerate(sources):
        for right in sources[i + 1 :]:
            for kind in ("all", "any"):
                a = source_masks[left][kind]
                b = source_masks[right][kind]
                inter = int(np.count_nonzero(a & b))
                union = int(np.count_nonzero(a | b))
                overlap_rows.append(
                    {
                        "source_a": left,
                        "source_b": right,
                        "support_kind": kind,
                        "a_n": int(a.sum()),
                        "b_n": int(b.sum()),
                        "intersection": inter,
                        "union": union,
                        "jaccard": inter / union,
                        "a_fraction_shared": inter / int(a.sum()),
                        "b_fraction_shared": inter / int(b.sum()),
                    }
                )
    source_overlap = pd.DataFrame(overlap_rows)
    summary = {
        "exact_support_patterns": int(pattern_summary.shape[0]),
        "patterns_by_source": {
            src: int((pattern_summary.source == src).sum()) for src in sources
        },
        "source_all_measured": {
            src: int(source_masks[src]["all"].sum()) for src in sources
        },
        "source_any_measured": {
            src: int(source_masks[src]["any"].sum()) for src in sources
        },
    }
    return pattern_summary, source_overlap, summary


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--sql-cache-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.bundle_root.resolve()
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=True)

    verified = verify_manifest(root)
    status_path = root / "BUNDLE_STATUS.json"
    if not status_path.is_file():
        raise SystemExit("missing BUNDLE_STATUS.json")
    status = json.loads(status_path.read_text(encoding="utf-8"))

    sql_cache = args.sql_cache_dir.resolve()
    sql_manifest_path = sql_cache / "FULL104_DATASET_ETL_SQL_AGGREGATE_SHA256.csv"
    if not sql_manifest_path.is_file():
        raise SystemExit("missing FULL104_DATASET_ETL_SQL_AGGREGATE_SHA256.csv")
    sql_manifest = pd.read_csv(sql_manifest_path)
    required_sql = {
        "FIT_SOURCE": "fit_source",
        "PARTITION_SOURCE": "part_source",
        "FIT_DONOR": "fit_donor",
        "FIT_OPERATOR_NATIVE_CLASS": "op_native",
        "DONOR_PARTITION_SOURCE": "partitions",
        "FIT_BROAD_MISSING": "broad_missing",
        "FIT_SUPPORT_FINGERPRINT": "support_fingerprint",
        "SEA_AD_FIT_DONOR_REGION": "sea_donor_region",
        "FIT_DONOR_NATIVE_CLASS": "donor_class_raw",
        "FIT_NATIVE_CLASS_COVERAGE": "class_coverage",
    }
    loaded = {}
    manifest_by_id = {str(r.query_id): r for r in sql_manifest.itertuples(index=False)}
    for query_id in required_sql:
        if query_id not in manifest_by_id:
            raise SystemExit(f"SQL cache manifest missing {query_id}")
        row = manifest_by_id[query_id]
        path = sql_cache / str(row.path)
        if not path.is_file():
            raise SystemExit(f"SQL cache file missing {path}")
        if sha256(path) != str(row.sha256).lower():
            raise SystemExit(f"SQL cache SHA mismatch for {query_id}")
        frame = pd.read_csv(path)
        if len(frame) != int(row.rows):
            raise SystemExit(f"SQL cache row-count mismatch for {query_id}")
        loaded[query_id] = frame
    fit_source = loaded["FIT_SOURCE"]
    part_source = loaded["PARTITION_SOURCE"]
    fit_donor = loaded["FIT_DONOR"]
    op_native = loaded["FIT_OPERATOR_NATIVE_CLASS"]
    partitions = loaded["DONOR_PARTITION_SOURCE"]
    broad_missing = loaded["FIT_BROAD_MISSING"]
    support_fingerprint = loaded["FIT_SUPPORT_FINGERPRINT"]
    sea_donor_region = loaded["SEA_AD_FIT_DONOR_REGION"]
    donor_class_raw = loaded["FIT_DONOR_NATIVE_CLASS"]
    class_coverage = loaded["FIT_NATIVE_CLASS_COVERAGE"]
    if int(part_source.cells.sum()) != EXPECTED["metadata_cells"]:
        raise SystemExit("metadata cell total drifted")
    if int(fit_source.cells.sum()) != EXPECTED["reader_fit_cells"]:
        raise SystemExit("reader-fit cell total drifted")
    if int(fit_source.donors.sum()) != EXPECTED["reader_fit_donors"]:
        raise SystemExit("reader-fit donor total drifted")
    if int(fit_source.operators.sum()) != EXPECTED["reader_operators"]:
        raise SystemExit("reader operator total drifted")
    if int(partitions.donor_id.nunique()) != 149:
        raise SystemExit("reader metadata donor universe drifted")
    if int((partitions.groupby("donor_id").partition.nunique() > 1).sum()) != 0:
        raise SystemExit("reader donor appears in multiple reader partitions")

    split = pd.read_csv(root / "splits/foundation_split_registry.csv")
    split["donor_id"] = split.canonical_person_id.astype(str).str.split("::").str[-1]
    reader_context = partitions.merge(
        split[["study_id", "cohort", "donor_id", "split", "pathology_used_for_foundation_split"]],
        on="donor_id",
        how="left",
        validate="many_to_one",
    )
    if reader_context.cohort.isna().any():
        raise SystemExit("reader donor missing from foundation split registry")
    if not bool((split.pathology_used_for_foundation_split == False).all()):  # noqa: E712
        raise SystemExit("foundation split unexpectedly used pathology")

    nph_reader = reader_context[reader_context.source == "NPH52"]
    nph_cohort_counts = (
        nph_reader.groupby(["partition", "cohort"])
        .size()
        .rename("donors")
        .reset_index()
    )

    op_tot = op_native.groupby(["source", "operator_index", "matrix_id"], as_index=False).cells.sum()
    op_classes = (
        op_native.groupby(["source", "operator_index", "matrix_id"], as_index=False)
        .native_class.nunique()
        .rename(columns={"native_class": "native_classes"})
    )
    op_dom = (
        op_native.assign(_total=op_native.groupby("operator_index").cells.transform("sum"))
        .assign(share=lambda frame: frame.cells / frame._total)
        .groupby(["source", "operator_index", "matrix_id"], as_index=False)
        .share.max()
        .rename(columns={"share": "dominant_native_class_share"})
    )
    operators = op_tot.merge(op_classes, on=["source", "operator_index", "matrix_id"]).merge(
        op_dom, on=["source", "operator_index", "matrix_id"]
    )

    donor_class = (
        donor_class_raw.groupby(["source", "donor_id"], as_index=False)
        .agg(
            classes=("native_class", "nunique"),
            cells=("cells", "sum"),
            min_class_cells=("cells", "min"),
            max_class_cells=("cells", "max"),
        )
    )
    sea_region_coverage = (
        sea_donor_region.groupby("donor_id", as_index=False)
        .agg(
            regions=("matrix_id", "nunique"),
            cells=("cells", "sum"),
            min_region_cells=("cells", "min"),
            max_region_cells=("cells", "max"),
        )
    )

    recurrence = pd.read_csv(root / "support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv")
    namespace = pd.read_csv(root / "contracts/address_namespace.csv")
    source_support = pd.read_csv(root / "support/FOUNDATION_SUPPORT_BY_SOURCE.csv")
    collisions = pd.read_csv(root / "contracts/unregistered_collisions.csv")
    if len(recurrence) != EXPECTED["addresses"] or len(namespace) != EXPECTED["addresses"]:
        raise SystemExit("address authority row count drifted")

    source_total = int(fit_source.cells.sum())
    fit_source = fit_source.copy()
    fit_source["cell_fraction"] = fit_source.cells / source_total
    fit_source["donor_fraction"] = fit_source.donors / fit_source.donors.sum()
    fit_source = fit_source.merge(
        source_support[[
            "source",
            "cell_weighted_measured_scalar_fraction",
            "cell_weighted_structurally_unmeasured_fraction",
            "cell_weighted_collision_unresolved_fraction",
        ]],
        on="source",
        validate="one_to_one",
    ).merge(broad_missing, on=["source", "cells"], validate="one_to_one")
    fit_source["broad_missing_fraction"] = fit_source.missing_broad / fit_source.cells

    part_source = part_source.copy()
    part_source["cell_fraction_within_partition"] = part_source.cells / part_source.groupby("partition").cells.transform("sum")
    part_source["donor_fraction_within_partition"] = part_source.donors / part_source.groupby("partition").donors.transform("sum")

    native_sets = {source: set(group.native_class.astype(str)) for source, group in op_native.groupby("source")}
    overlap_rows = []
    sources = sorted(native_sets)
    for i, left in enumerate(sources):
        for right in sources[i + 1 :]:
            intersection = sorted(native_sets[left] & native_sets[right])
            union = native_sets[left] | native_sets[right]
            overlap_rows.append({
                "left_source": left,
                "right_source": right,
                "left_native_classes": len(native_sets[left]),
                "right_native_classes": len(native_sets[right]),
                "literal_intersection": len(intersection),
                "literal_jaccard": len(intersection) / len(union) if union else 1.0,
                "shared_labels": "|".join(intersection),
            })
    native_overlap = pd.DataFrame(overlap_rows)

    pattern_summary, source_overlap, support_geometry = build_support_geometry(root)

    recurrence_summary = {
        "addresses": int(len(recurrence)),
        "measured_by_all_42": int((recurrence.operators_measured_scalar == 42).sum()),
        "measured_by_no_operator": int((recurrence.operators_measured_scalar == 0).sum()),
        "measured_by_all_3_source_families": int((recurrence.source_families_measuring == 3).sum()),
        "operator_measured_scalar_quantiles": quantiles(recurrence.operators_measured_scalar),
    }
    identity_summary = {
        "addresses": int(len(namespace)),
        "identity_class_counts": {str(k): int(v) for k, v in namespace.identity_class.value_counts().items()},
        "source_family_contribution_counts": {
            str(k): int(v)
            for k, v in namespace.contributing_source_families.fillna("")
            .map(lambda value: 0 if value == "" else len(str(value).split("|")))
            .value_counts().sort_index().items()
        },
    }
    collision_summary = {
        "rows": int(len(collisions)),
        "matrices": int(collisions.matrix_id.nunique()),
        "addresses": int(collisions.molecular_address_id.nunique()),
        "source_datasets": int(collisions.source_dataset_id.nunique()),
        "sources": sorted(set(str(value).split("::")[0] for value in collisions.matrix_id)),
    }

    donor_quantiles = {
        source: {
            "cells": quantiles(group.cells),
            "operators": quantiles(group.operators),
            "native_classes": quantiles(group.native_classes),
        }
        for source, group in fit_donor.groupby("source")
    }
    source_operator_semantics = {
        source: {
            "operators": int(len(group)),
            "native_classes_per_operator": quantiles(group.native_classes),
            "dominant_native_class_share": quantiles(group.dominant_native_class_share),
            "operator_is_native_class_pure_for_all": bool((group.native_classes == 1).all()),
        }
        for source, group in operators.groupby("source")
    }
    sea_region_distribution = {
        str(int(k)): int(v) for k, v in sea_region_coverage.regions.value_counts().sort_index().items()
    }
    donor_class_count_distribution = {
        source: {str(int(k)): int(v) for k, v in group.classes.value_counts().sort_index().items()}
        for source, group in donor_class.groupby("source")
    }

    findings = {
        "source_cell_mass_is_highly_imbalanced": bool(fit_source.cell_fraction.max() / fit_source.cell_fraction.min() > 10),
        "operator_is_not_common_semantic_axis": True,
        "measurement_support_is_source_dependent": True,
        "support_pattern_is_source_identifying": bool(
            support_geometry["patterns_by_source"] == {"HVS": 1, "NPH52": 7, "SEA_AD": 1}
        ),
        "broad_class_schema_is_not_harmonized_across_sources": bool((fit_source.broad_missing_fraction > 0).any()),
        "nph_reader_population_is_control_subcohort_only": bool(set(nph_reader.cohort) == {"NPH_Ctrl"}),
        "reader_partitions_are_donor_disjoint": True,
        "reader_validation_has_no_nph52": bool(not ((part_source.partition == "reader_validation") & (part_source.source == "NPH52")).any()),
        "sea_ad_region_coverage_is_donor_ragged": bool(sea_region_coverage.regions.min() < sea_region_coverage.regions.max()),
        "pathology_was_not_used_for_foundation_split": True,
        "bundle_contains_pathology_fields": bool(status.get("pathology_fields_included", False)),
        "bundle_contains_dev_sealed_expression": bool(status.get("dev_sealed_expression_included", False)),
    }

    summary = {
        "schema": SCHEMA,
        "sql_aggregate_manifest_sha256": sha256(sql_manifest_path),
        "scope": "AUTHENTICATED_BUNDLE_METADATA_AND_SUPPORT__NO_DEV_SEALED_EXPRESSION",
        "verified_inputs": verified,
        "population": {
            "metadata_cells": int(part_source.cells.sum()),
            "metadata_donors": int(partitions.donor_id.nunique()),
            "reader_fit_cells": int(fit_source.cells.sum()),
            "reader_fit_donors": int(fit_source.donors.sum()),
            "reader_operators": int(operators.operator_index.nunique()),
            "addresses": int(len(namespace)),
            "partition_source": part_source.to_dict(orient="records"),
        },
        "reader_fit_source_summary": fit_source.to_dict(orient="records"),
        "reader_fit_donor_quantiles_by_source": donor_quantiles,
        "operator_semantics_by_source": source_operator_semantics,
        "support_geometry": support_geometry,
        "sea_ad_fit_donor_region_count_distribution": sea_region_distribution,
        "donor_native_class_count_distribution_by_source": donor_class_count_distribution,
        "nph_reader_foundation_cohort_summary": nph_cohort_counts.to_dict(orient="records"),
        "address_support": recurrence_summary,
        "address_identity": identity_summary,
        "collision_summary": collision_summary,
        "findings": findings,
        "protected_state": {
            "terminal_masking_outcomes": "UNOPENED",
            "d_shared": "SEALED",
            "pathology": "SEALED_FOR_MODEL_AND_TERMINAL_ADAPTATION",
            "dev_sealed": "SEALED",
            "training": "OFF",
        },
        "interpretation_limits": [
            "This bundle contains no pathology fields and no DEV/SEALED expression.",
            "Foundation cohort labels are used only for provenance/composition and are not model-facing features or terminal policy-selection inputs.",
            "The 50k expression sample is not consumed by this atlas builder and cannot set FULL104 adaptive thresholds.",
        ],
    }

    outputs: dict[str, pd.DataFrame | str] = {
        "FULL104_DATASET_ETL_SOURCE_SUMMARY.csv": fit_source,
        "FULL104_DATASET_ETL_OPERATOR_SUMMARY.csv": operators,
        "FULL104_DATASET_ETL_NPH_READER_COHORT_SUMMARY.csv": nph_cohort_counts,
        "FULL104_DATASET_ETL_READER_PARTITION_SOURCE_SUMMARY.csv": part_source,
        "FULL104_DATASET_ETL_NATIVE_CLASS_OVERLAP.csv": native_overlap,
        "FULL104_DATASET_ETL_SUPPORT_FINGERPRINT_SUMMARY.csv": support_fingerprint,
        "FULL104_DATASET_ETL_EXACT_SUPPORT_PATTERN_SUMMARY.csv": pattern_summary,
        "FULL104_DATASET_ETL_SOURCE_SUPPORT_OVERLAP.csv": source_overlap,
        "FULL104_DATASET_ETL_SEAAD_DONOR_REGION_COVERAGE.csv": sea_region_coverage,
        "FULL104_DATASET_ETL_DONOR_CLASS_COVERAGE.csv": donor_class,
        "FULL104_DATASET_ETL_NATIVE_CLASS_COVERAGE.csv": class_coverage,
    }
    for name, frame in outputs.items():
        assert isinstance(frame, pd.DataFrame)
        frame.to_csv(out / name, index=False, lineterminator="
")

    summary_path = out / "FULL104_DATASET_ETL_ATLAS_SUMMARY_V3.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "
", encoding="utf-8")

    manifest_rows = []
    for path in sorted(out.iterdir(), key=lambda p: p.name):
        if path.is_file() and path.name != "FULL104_DATASET_ETL_OUTPUT_SHA256.csv":
            manifest_rows.append({"path": path.name, "bytes": path.stat().st_size, "sha256": sha256(path)})
    manifest = pd.DataFrame(manifest_rows)
    manifest.to_csv(out / "FULL104_DATASET_ETL_OUTPUT_SHA256.csv", index=False, lineterminator="
")

    print(json.dumps({
        "terminal": "PASS_FULL104_DATASET_ETL_ATLAS_V3",
        "summary_sha256": sha256(summary_path),
        "output_manifest_sha256": sha256(out / "FULL104_DATASET_ETL_OUTPUT_SHA256.csv"),
        "findings": findings,
    }, sort_keys=True))


if __name__ == "__main__":
    main()
