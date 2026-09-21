from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest


ROOT = Path("analysis/v5_full104_dataset_etl_atlas_20260921/evidence")


def test_reader_population_geometry_is_pinned() -> None:
    source = pd.read_csv(ROOT / "FULL104_DATASET_ETL_SOURCE_SUMMARY.csv")
    assert int(source["cells"].sum()) == 4_553_407
    assert int(source["donors"].sum()) == 104
    assert int(source["operators"].sum()) == 42
    assert source.set_index("source").loc["SEA_AD", "cell_fraction"] == pytest.approx(
        4_118_213 / 4_553_407
    )
    assert source.set_index("source").loc["HVS", "donor_fraction"] == pytest.approx(
        41 / 104
    )


def test_reader_partitions_are_the_expected_149_donor_metadata_universe() -> None:
    part = pd.read_csv(
        ROOT / "FULL104_DATASET_ETL_READER_PARTITION_SOURCE_SUMMARY.csv"
    )
    assert int(part["cells"].sum()) == 6_351_753
    assert int(part["donors"].sum()) == 149
    assert set(part["partition"]) == {
        "reader_fit",
        "reader_validation",
        "reader_oracle",
    }


def test_nph_reader_population_is_control_subcohort_only() -> None:
    nph = pd.read_csv(ROOT / "FULL104_DATASET_ETL_NPH_READER_COHORT_SUMMARY.csv")
    assert set(nph["cohort"]) == {"NPH_Ctrl"}
    assert int(nph.loc[nph.partition == "reader_fit", "donors"].iloc[0]) == 17
    assert int(nph.loc[nph.partition == "reader_oracle", "donors"].iloc[0]) == 2


def test_nph_broad_class_is_missing_not_silently_harmonized() -> None:
    source = pd.read_csv(ROOT / "FULL104_DATASET_ETL_SOURCE_SUMMARY.csv").set_index(
        "source"
    )
    assert int(source.loc["NPH52", "missing_broad"]) == 236_476
    assert float(source.loc["NPH52", "broad_missing_fraction"]) == pytest.approx(1.0)


def test_operator_semantics_are_source_specific_not_generic_batch() -> None:
    op = pd.read_csv(ROOT / "FULL104_DATASET_ETL_OPERATOR_SUMMARY.csv")
    hvs = op[op.source == "HVS"]
    nph = op[op.source == "NPH52"]
    sea = op[op.source == "SEA_AD"]
    assert len(hvs) == 24 and (hvs.native_classes == 1).all()
    assert len(nph) == 7 and (nph.native_classes == 1).all()
    assert len(sea) == 11
    assert sea.native_classes.min() >= 17
    assert sea.native_classes.max() <= 26
    assert sea.dominant_native_class_share.max() < 0.30


def test_literal_taxonomy_overlap_is_not_mistaken_for_harmonization() -> None:
    overlap = pd.read_csv(ROOT / "FULL104_DATASET_ETL_NATIVE_CLASS_OVERLAP.csv")
    by_pair = {
        (row.left_source, row.right_source): row
        for row in overlap.itertuples(index=False)
    }
    assert by_pair[("HVS", "SEA_AD")].literal_intersection == 22
    assert by_pair[("HVS", "NPH52")].literal_intersection == 1
    assert by_pair[("NPH52", "SEA_AD")].literal_intersection == 1
    assert by_pair[("HVS", "NPH52")].shared_labels == "OPC"


def test_measurement_support_asymmetry_remains_visible() -> None:
    source = pd.read_csv(ROOT / "FULL104_DATASET_ETL_SOURCE_SUMMARY.csv").set_index(
        "source"
    )
    assert source.loc["HVS", "cell_weighted_measured_scalar_fraction"] == pytest.approx(
        0.4543382317280179
    )
    assert source.loc["SEA_AD", "cell_weighted_measured_scalar_fraction"] == pytest.approx(
        0.8505747126436781
    )
    assert source.loc["HVS", "cell_weighted_collision_unresolved_fraction"] == 0.0
    assert source.loc["NPH52", "cell_weighted_collision_unresolved_fraction"] > 0.0
