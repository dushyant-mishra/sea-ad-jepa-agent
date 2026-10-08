from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd


def standardize_gene(value: object) -> str:
    return str(value).strip().upper()


def load_feature_order(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(path)
    if path.suffix.lower() in {".txt", ".tsv"}:
        try:
            frame = pd.read_csv(path, sep="\t")
        except pd.errors.ParserError:
            frame = pd.read_csv(path, header=None, names=["gene"])
    else:
        frame = pd.read_csv(path)
    if "gene" in frame.columns:
        values = frame["gene"]
    elif frame.shape[1] == 1:
        values = frame.iloc[:, 0]
    else:
        raise ValueError("Feature-order file must contain one column or a column named gene")
    genes = [standardize_gene(value) for value in values if str(value).strip()]
    if not genes or len(genes) != len(set(genes)):
        raise ValueError("Model feature order must be nonempty and unique after standardization")
    return genes


def load_reference_means(path: Path, model_features: list[str]) -> pd.Series:
    if not path.exists():
        raise FileNotFoundError(path)
    frame = pd.read_csv(path)
    if {"gene", "mean"}.issubset(frame.columns):
        series = pd.Series(
            frame["mean"].to_numpy(dtype=float),
            index=frame["gene"].map(standardize_gene),
        )
    elif len(frame) == 1:
        series = pd.Series(
            frame.iloc[0].to_numpy(dtype=float),
            index=[standardize_gene(column) for column in frame.columns],
        )
    else:
        raise ValueError(
            "Reference mean vector must use gene/mean columns or one row with gene columns"
        )
    if series.index.duplicated().any():
        raise ValueError("Reference mean vector contains duplicate genes")
    missing = [gene for gene in model_features if gene not in series.index]
    if missing:
        raise ValueError(f"Reference mean vector missing model genes: {missing[:10]}")
    return series.reindex(model_features)


def align_dataframe(
    matrix: pd.DataFrame,
    model_features: list[str],
    *,
    missing_strategy: str,
    duplicate_strategy: str,
    feature_coverage_threshold: float,
    reference_means: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict[str, object]]:
    if not 0 <= feature_coverage_threshold <= 1:
        raise ValueError("feature_coverage_threshold must be between 0 and 1")
    if missing_strategy == "reference_mean" and reference_means is None:
        raise ValueError("reference_mean strategy requires an explicit reference mean vector")

    source_columns = [str(column) for column in matrix.columns]
    standardized = [standardize_gene(column) for column in source_columns]
    duplicate_genes = sorted(
        {
            gene
            for gene in standardized
            if standardized.count(gene) > 1
        }
    )
    working = matrix.copy()
    working.columns = standardized
    if duplicate_genes:
        if duplicate_strategy == "error":
            raise ValueError(
                f"Duplicate standardized source genes detected: {duplicate_genes}"
            )
        if duplicate_strategy != "aggregate_mean":
            raise ValueError(f"Unknown duplicate strategy: {duplicate_strategy}")
        working = working.T.groupby(level=0, sort=False).mean().T

    present = [gene for gene in model_features if gene in working.columns]
    missing = [gene for gene in model_features if gene not in working.columns]
    coverage_fraction = len(present) / len(model_features)
    if missing and missing_strategy == "error":
        raise ValueError(f"Missing model features: {missing[:10]}")

    aligned = pd.DataFrame(index=working.index)
    mask = pd.DataFrame(False, index=working.index, columns=model_features)
    for gene in model_features:
        if gene in working.columns:
            aligned[gene] = pd.to_numeric(working[gene], errors="raise")
        elif missing_strategy == "zero":
            aligned[gene] = 0.0
            mask[gene] = True
        elif missing_strategy == "reference_mean":
            aligned[gene] = float(reference_means.loc[gene])
            mask[gene] = True
        else:
            raise ValueError(f"Unknown missing strategy: {missing_strategy}")

    coverage = pd.DataFrame(
        {
            "gene": model_features,
            "present_in_source": [gene in present for gene in model_features],
            "imputed": [gene in missing for gene in model_features],
            "imputation_strategy": [
                missing_strategy if gene in missing else "none"
                for gene in model_features
            ],
        }
    )
    status = (
        "pass"
        if coverage_fraction >= feature_coverage_threshold
        else "insufficient_feature_coverage"
    )
    manifest = {
        "status": status,
        "matrix_orientation": "samples_by_feature_columns",
        "n_samples": int(len(matrix)),
        "n_source_columns": int(len(source_columns)),
        "n_model_features": int(len(model_features)),
        "n_present_model_features": int(len(present)),
        "n_missing_model_features": int(len(missing)),
        "feature_coverage_fraction": float(coverage_fraction),
        "feature_coverage_threshold": float(feature_coverage_threshold),
        "missing_strategy": missing_strategy,
        "duplicate_strategy": duplicate_strategy,
        "duplicated_standardized_source_genes": duplicate_genes,
        "missing_model_genes": missing,
        "source_feature_identifiers": source_columns,
        "standardized_source_feature_identifiers": standardized,
    }
    return aligned, mask, coverage, manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Align a samples-by-feature CSV matrix to an explicit Graph-JEPA "
            "feature order. Features are assumed to be columns."
        )
    )
    parser.add_argument("--input-matrix", type=Path, required=True)
    parser.add_argument("--model-feature-order", type=Path, required=True)
    parser.add_argument("--out-matrix", type=Path, required=True)
    parser.add_argument("--out-mask", type=Path, required=True)
    parser.add_argument("--out-coverage", type=Path, required=True)
    parser.add_argument("--out-manifest", type=Path, required=True)
    parser.add_argument(
        "--missing-strategy",
        choices=["zero", "reference_mean", "error"],
        required=True,
    )
    parser.add_argument("--feature-coverage-threshold", type=float, default=0.80)
    parser.add_argument(
        "--duplicate-strategy",
        choices=["error", "aggregate_mean"],
        default="error",
    )
    parser.add_argument("--reference-mean-vector", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    matrix = pd.read_csv(args.input_matrix)
    features = load_feature_order(args.model_feature_order)
    reference = None
    if args.missing_strategy == "reference_mean":
        if args.reference_mean_vector is None:
            raise ValueError(
                "--reference-mean-vector is required for reference_mean imputation"
            )
        reference = load_reference_means(args.reference_mean_vector, features)
    aligned, mask, coverage, manifest = align_dataframe(
        matrix,
        features,
        missing_strategy=args.missing_strategy,
        duplicate_strategy=args.duplicate_strategy,
        feature_coverage_threshold=args.feature_coverage_threshold,
        reference_means=reference,
    )
    for path in [
        args.out_matrix,
        args.out_mask,
        args.out_coverage,
        args.out_manifest,
    ]:
        path.parent.mkdir(parents=True, exist_ok=True)
    aligned.to_csv(args.out_matrix, index=False)
    mask.to_csv(args.out_mask, index=False)
    coverage.to_csv(args.out_coverage, index=False)
    args.out_manifest.write_text(
        json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8"
    )
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
