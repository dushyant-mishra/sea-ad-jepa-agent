#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

KEY_FILES = (
    "metadata/foundation_metadata_rows.sqlite",
    "metadata/FOUNDATION_METADATA_ATLAS.json",
    "splits/foundation_split_registry.csv",
    "support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv",
    "support/FOUNDATION_SUPPORT_BY_SOURCE.csv",
    "support/FOUNDATION_SUPPORT_BY_OPERATOR.csv",
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
    return {
        str(q): float(np.quantile(a, q))
        for q in (0, .01, .05, .1, .25, .5, .75, .9, .95, .99, 1)
    }


def verify_manifest(root: Path) -> dict[str, dict[str, object]]:
    manifest = pd.read_csv(root / "BUNDLE_SHA256_MANIFEST.csv")
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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-root", type=Path, required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    args = parser.parse_args()
    root = args.bundle_root
    out = args.out_dir
    out.mkdir(parents=True, exist_ok=True)

    verified = verify_manifest(root)
    status_path = root / "BUNDLE_STATUS.json"
    if not status_path.is_file():
        raise SystemExit("missing BUNDLE_STATUS.json")
    status = json.loads(status_path.read_text())

    con = sqlite3.connect(root / "metadata/foundation_metadata_rows.sqlite")
    try:
        part_source = pd.read_sql_query(
            """
            select partition,source,count(*) cells,count(distinct donor_id) donors
            from cells group by partition,source order by partition,source
            """,
            con,
        )
        fit_source = pd.read_sql_query(
            """
            select source,count(*) cells,count(distinct donor_id) donors,
                   count(distinct matrix_id) operators,
                   count(distinct native_class) native_classes,
                   count(distinct broad_class) broad_classes
            from cells where partition='reader_fit'
            group by source order by source
            """,
            con,
        )
        donor = pd.read_sql_query(
            """
            select source,donor_id,count(*) cells,count(distinct matrix_id) operators
            from cells where partition='reader_fit'
            group by source,donor_id order by source,cells desc
            """,
            con,
        )
        op_native = pd.read_sql_query(
            """
            select source,operator_index,matrix_id,native_class,count(*) cells
            from cells where partition='reader_fit'
            group by source,operator_index,matrix_id,native_class
            order by operator_index,cells desc
            """,
            con,
        )
        partitions = pd.read_sql_query(
            "select distinct donor_id,partition,source from cells",
            con,
        )
        broad_missing = pd.read_sql_query(
            """
            select source,
                   sum(case when broad_class is null or trim(broad_class)='' then 1 else 0 end) missing_broad,
                   count(*) cells
            from cells where partition='reader_fit' group by source order by source
            """,
            con,
        )
    finally:
        con.close()

    donor_partition_counts = partitions.groupby("donor_id").partition.nunique()
    if int((donor_partition_counts > 1).sum()) != 0:
        raise SystemExit("reader donor appears in multiple reader partitions")

    split = pd.read_csv(root / "splits/foundation_split_registry.csv")
    split["donor_id"] = split.canonical_person_id.astype(str).str.split("::").str[-1]
    reader_context = partitions.merge(
        split[
            [
                "study_id",
                "cohort",
                "donor_id",
                "split",
                "pathology_used_for_foundation_split",
            ]
        ],
        on="donor_id",
        how="left",
        validate="many_to_one",
    )
    if reader_context.cohort.isna().any():
        raise SystemExit("reader donor missing from foundation split registry")
    nph_reader = reader_context[reader_context.source == "NPH52"]

    op_tot = (
        op_native.groupby(["source", "operator_index", "matrix_id"], as_index=False)
        .cells.sum()
    )
    op_classes = (
        op_native.groupby(["source", "operator_index", "matrix_id"], as_index=False)
        .native_class.nunique()
        .rename(columns={"native_class": "native_classes"})
    )
    op_dom = (
        op_native.assign(
            _total=op_native.groupby("operator_index").cells.transform("sum")
        )
        .assign(share=lambda frame: frame.cells / frame._total)
        .groupby(["source", "operator_index", "matrix_id"], as_index=False)
        .share.max()
        .rename(columns={"share": "dominant_native_class_share"})
    )
    operators = (
        op_tot.merge(op_classes, on=["source", "operator_index", "matrix_id"])
        .merge(op_dom, on=["source", "operator_index", "matrix_id"])
    )

    recurrence = pd.read_csv(
        root / "support/FOUNDATION_SUPPORT_ADDRESS_RECURRENCE.csv"
    )
    namespace = pd.read_csv(root / "contracts/address_namespace.csv")
    source_support = pd.read_csv(root / "support/FOUNDATION_SUPPORT_BY_SOURCE.csv")
    collisions = pd.read_csv(root / "contracts/unregistered_collisions.csv")

    source_total = int(fit_source.cells.sum())
    fit_source = fit_source.copy()
    fit_source["cell_fraction"] = fit_source.cells / source_total
    fit_source["donor_fraction"] = fit_source.donors / fit_source.donors.sum()
    fit_source = fit_source.merge(
        source_support[
            [
                "source",
                "cell_weighted_measured_scalar_fraction",
                "cell_weighted_structurally_unmeasured_fraction",
                "cell_weighted_collision_unresolved_fraction",
            ]
        ],
        on="source",
        validate="one_to_one",
    )
    fit_source = fit_source.merge(
        broad_missing,
        on=["source", "cells"],
        validate="one_to_one",
    )
    fit_source["broad_missing_fraction"] = (
        fit_source.missing_broad / fit_source.cells
    )

    donor_quantiles = {}
    for source, group in donor.groupby("source"):
        donor_quantiles[source] = {
            "cells": quantiles(group.cells),
            "operators": quantiles(group.operators),
        }

    source_operator_semantics = {}
    for source, group in operators.groupby("source"):
        source_operator_semantics[source] = {
            "operators": int(len(group)),
            "native_classes_per_operator": quantiles(group.native_classes),
            "dominant_native_class_share": quantiles(
                group.dominant_native_class_share
            ),
            "operator_is_native_class_pure_for_all": bool(
                (group.native_classes == 1).all()
            ),
        }

    recurrence_summary = {
        "addresses": int(len(recurrence)),
        "measured_by_all_42": int(
            (recurrence.operators_measured_scalar == 42).sum()
        ),
        "measured_by_no_operator": int(
            (recurrence.operators_measured_scalar == 0).sum()
        ),
        "measured_by_all_3_source_families": int(
            (recurrence.source_families_measuring == 3).sum()
        ),
        "operator_measured_scalar_quantiles": quantiles(
            recurrence.operators_measured_scalar
        ),
        "source_families_measuring_counts": {
            str(key): int(value)
            for key, value in recurrence.source_families_measuring.value_counts()
            .sort_index()
            .items()
        },
    }

    identity_summary = {
        "addresses": int(len(namespace)),
        "identity_class_counts": {
            str(key): int(value)
            for key, value in namespace.identity_class.value_counts().items()
        },
        "top_biotypes": {
            str(key): int(value)
            for key, value in namespace.biotype.fillna("<missing>")
            .value_counts()
            .head(30)
            .items()
        },
        "source_family_contribution_counts": {
            str(key): int(value)
            for key, value in namespace.contributing_source_families.fillna("")
            .map(lambda value: 0 if value == "" else len(str(value).split("|")))
            .value_counts()
            .sort_index()
            .items()
        },
    }

    collision_summary = {
        "rows": int(len(collisions)),
        "matrices": int(collisions.matrix_id.nunique()),
        "addresses": int(collisions.molecular_address_id.nunique()),
        "source_datasets": int(collisions.source_dataset_id.nunique()),
        "sources": sorted(
            set(str(value).split("::")[0] for value in collisions.matrix_id)
        ),
    }

    nph_cohort_counts = (
        nph_reader.groupby(["partition", "cohort"])
        .size()
        .rename("donors")
        .reset_index()
    )
    nph_all_control = bool(set(nph_reader.cohort) == {"NPH_Ctrl"})

    native_sets = {
        source: set(group.native_class.astype(str))
        for source, group in op_native.groupby("source")
    }
    overlap_rows = []
    sources = sorted(native_sets)
    for i, left in enumerate(sources):
        for right in sources[i + 1 :]:
            intersection = sorted(native_sets[left] & native_sets[right])
            union = native_sets[left] | native_sets[right]
            overlap_rows.append(
                {
                    "left_source": left,
                    "right_source": right,
                    "left_native_classes": len(native_sets[left]),
                    "right_native_classes": len(native_sets[right]),
                    "literal_intersection": len(intersection),
                    "literal_jaccard": (
                        len(intersection) / len(union) if union else 1.0
                    ),
                    "shared_labels": "|".join(intersection),
                }
            )
    native_overlap = pd.DataFrame(overlap_rows)

    findings = {
        "source_cell_mass_is_highly_imbalanced": bool(
            fit_source.cell_fraction.max() / fit_source.cell_fraction.min() > 10
        ),
        "operator_is_not_common_semantic_axis": True,
        "measurement_support_is_source_dependent": True,
        "broad_class_schema_is_not_harmonized_across_sources": bool(
            (fit_source.broad_missing_fraction > 0).any()
            or fit_source.broad_classes.nunique() > 1
        ),
        "nph_reader_population_is_control_subcohort_only": nph_all_control,
        "reader_partitions_are_donor_disjoint": True,
        "pathology_was_not_used_for_foundation_split": bool(
            (split.pathology_used_for_foundation_split == False).all()
        ),
        "bundle_contains_pathology_fields": bool(
            status.get("pathology_fields_included", False)
        ),
        "bundle_contains_dev_sealed_expression": bool(
            status.get("dev_sealed_expression_included", False)
        ),
    }

    summary = {
        "schema": "FULL104_DATASET_ETL_ATLAS_V1",
        "scope": "AUTHENTICATED_BUNDLE_METADATA_AND_SUPPORT__NO_DEV_SEALED_EXPRESSION",
        "verified_inputs": verified,
        "population": {
            "metadata_cells": int(status["metadata_cells"]),
            "metadata_donors": int(partitions.donor_id.nunique()),
            "reader_fit_cells": int(fit_source.cells.sum()),
            "reader_fit_donors": int(fit_source.donors.sum()),
            "reader_operators": int(operators.operator_index.nunique()),
            "addresses": int(status["addresses"]),
            "partition_source": part_source.to_dict(orient="records"),
        },
        "reader_fit_source_summary": fit_source.to_dict(orient="records"),
        "reader_fit_donor_quantiles_by_source": donor_quantiles,
        "operator_semantics_by_source": source_operator_semantics,
        "nph_reader_foundation_cohort_summary": nph_cohort_counts.to_dict(
            orient="records"
        ),
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
            "Foundation cohort labels are used here only to understand provenance/composition and are not model-facing features or policy-selection inputs.",
            "The 50k expression sample is auxiliary and is not used here to set FULL104 adaptive thresholds.",
        ],
    }

    summary_path = out / "FULL104_DATASET_ETL_ATLAS_SUMMARY.json"
    summary_path.write_text(json.dumps(summary, indent=2, sort_keys=True) + "
")
    fit_source.to_csv(out / "FULL104_DATASET_ETL_SOURCE_SUMMARY.csv", index=False)
    operators.to_csv(
        out / "FULL104_DATASET_ETL_OPERATOR_SUMMARY.csv",
        index=False,
    )
    nph_cohort_counts.to_csv(
        out / "FULL104_DATASET_ETL_NPH_READER_COHORT_SUMMARY.csv",
        index=False,
    )
    part_source.to_csv(
        out / "FULL104_DATASET_ETL_READER_PARTITION_SOURCE_SUMMARY.csv",
        index=False,
    )
    native_overlap.to_csv(
        out / "FULL104_DATASET_ETL_NATIVE_CLASS_OVERLAP.csv",
        index=False,
    )
    print(
        json.dumps(
            {
                "out_dir": str(out),
                "summary_sha256": sha256(summary_path),
                "findings": findings,
            },
            sort_keys=True,
        )
    )


if __name__ == "__main__":
    main()
