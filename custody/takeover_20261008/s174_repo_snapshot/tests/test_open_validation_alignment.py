from __future__ import annotations

from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from open_validation.align_to_graph_jepa import align_dataframe


FEATURES = ["A", "B", "C", "D"]


def test_perfect_gene_overlap():
    matrix = pd.DataFrame({"a": [1, 2], " B ": [3, 4], "c": [5, 6], "D": [7, 8]})
    aligned, mask, _, manifest = align_dataframe(
        matrix,
        FEATURES,
        missing_strategy="error",
        duplicate_strategy="error",
        feature_coverage_threshold=0.8,
    )
    assert aligned.columns.tolist() == FEATURES
    assert not mask.to_numpy().any()
    assert manifest["status"] == "pass"
    assert manifest["feature_coverage_fraction"] == 1.0


def test_missing_genes_zero_imputation():
    matrix = pd.DataFrame({"A": [1, 2], "C": [5, 6], "D": [7, 8]})
    aligned, mask, coverage, manifest = align_dataframe(
        matrix,
        FEATURES,
        missing_strategy="zero",
        duplicate_strategy="error",
        feature_coverage_threshold=0.7,
    )
    assert aligned["B"].eq(0).all()
    assert mask["B"].all()
    assert coverage.set_index("gene").loc["B", "imputed"]
    assert manifest["status"] == "pass"


def test_missing_genes_error_strategy_raises():
    matrix = pd.DataFrame({"A": [1], "B": [2]})
    try:
        align_dataframe(
            matrix,
            FEATURES,
            missing_strategy="error",
            duplicate_strategy="error",
            feature_coverage_threshold=0.8,
        )
    except ValueError as exc:
        assert "Missing model features" in str(exc)
    else:
        raise AssertionError("Missing-feature error strategy did not raise")


def test_reference_mean_imputation_requires_and_uses_vector():
    matrix = pd.DataFrame({"A": [1], "B": [2], "C": [3]})
    reference = pd.Series({"A": 10.0, "B": 20.0, "C": 30.0, "D": 40.0})
    aligned, mask, _, _ = align_dataframe(
        matrix,
        FEATURES,
        missing_strategy="reference_mean",
        duplicate_strategy="error",
        feature_coverage_threshold=0.7,
        reference_means=reference,
    )
    assert aligned.loc[0, "D"] == 40.0
    assert mask.loc[0, "D"]


def test_reference_mean_without_vector_raises():
    matrix = pd.DataFrame({"A": [1], "B": [2]})
    try:
        align_dataframe(
            matrix,
            FEATURES,
            missing_strategy="reference_mean",
            duplicate_strategy="error",
            feature_coverage_threshold=0.8,
        )
    except ValueError as exc:
        assert "reference mean vector" in str(exc)
    else:
        raise AssertionError("Missing reference mean vector did not raise")


def test_duplicate_source_gene_error_raises():
    matrix = pd.DataFrame({"GeneA": [1], " genea ": [3], "B": [2]})
    try:
        align_dataframe(
            matrix,
            ["GENEA", "B"],
            missing_strategy="error",
            duplicate_strategy="error",
            feature_coverage_threshold=0.8,
        )
    except ValueError as exc:
        assert "Duplicate standardized source genes" in str(exc)
    else:
        raise AssertionError("Duplicate source gene did not raise")


def test_duplicate_source_gene_aggregate_mean():
    matrix = pd.DataFrame({"GeneA": [1, 3], " genea ": [3, 5], "B": [2, 4]})
    aligned, _, _, manifest = align_dataframe(
        matrix,
        ["GENEA", "B"],
        missing_strategy="error",
        duplicate_strategy="aggregate_mean",
        feature_coverage_threshold=0.8,
    )
    assert aligned["GENEA"].tolist() == [2.0, 4.0]
    assert manifest["duplicated_standardized_source_genes"] == ["GENEA"]


def test_low_feature_coverage_status():
    matrix = pd.DataFrame({"A": [1]})
    _, _, _, manifest = align_dataframe(
        matrix,
        FEATURES,
        missing_strategy="zero",
        duplicate_strategy="error",
        feature_coverage_threshold=0.8,
    )
    assert manifest["status"] == "insufficient_feature_coverage"


def run_all_tests() -> None:
    tests = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    for test in tests:
        test()
    print(f"{len(tests)} open-validation alignment tests passed")


if __name__ == "__main__":
    run_all_tests()
