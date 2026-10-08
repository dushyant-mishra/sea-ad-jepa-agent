from __future__ import annotations

import csv
from pathlib import Path

import pytest

from sea_ad_jepa.v5.dataset_etl_guardrails_v1 import (
    strict_source_from_matrix_id,
    validate_operator_source_rows,
    validate_support_pattern_source_identity,
)

ROOT = Path(__file__).resolve().parents[1]
ETL = ROOT / "analysis/v5_full104_dataset_etl_20260921/evidence"


def rows(path: Path):
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_current_operator_summary_passes_strict_source_guard() -> None:
    observed = validate_operator_source_rows(
        rows(ETL / "FULL104_DATASET_ETL_OPERATOR_SUMMARY.csv")
    )
    assert observed == {"HVS": 24, "NPH52": 7, "SEA_AD": 11}


def test_unknown_matrix_id_is_not_silently_relabelled_sea_ad() -> None:
    with pytest.raises(ValueError, match="unrecognized"):
        strict_source_from_matrix_id("totally_new_dataset_matrix")
    with pytest.raises(ValueError, match="unrecognized"):
        strict_source_from_matrix_id("sea_ad_unregistered_future_matrix")


def test_known_matrix_names_map_only_to_their_current_source() -> None:
    assert strict_source_from_matrix_id(
        "HVS::19cd530b-622c-4bd8-b738-dbf169412cb0"
    ) == "HVS"
    assert strict_source_from_matrix_id(
        "NPH52::matrix::OPC_data_arranged_updatedId_final_batches.qs"
    ) == "NPH52"
    assert strict_source_from_matrix_id("sea_ad_v1c_rna_final_2026") == "SEA_AD"


def test_current_support_patterns_directly_prove_source_identity() -> None:
    out = validate_support_pattern_source_identity(
        rows(ETL / "FULL104_DATASET_ETL_EXACT_SUPPORT_PATTERN_SUMMARY.csv")
    )
    assert out["support_pattern_is_source_identifying"] is True
    assert out["distinct_pattern_hashes"] == 9
    assert out["cross_source_hash_collisions"] == 0
    assert out["patterns_by_source"] == {"HVS": 1, "NPH52": 7, "SEA_AD": 1}


def test_same_support_hash_in_two_sources_fails_even_if_counts_look_plausible() -> None:
    digest = "a" * 64
    synthetic = [
        {"source": "HVS", "support_pattern_sha256": digest, "operators": 24},
        {"source": "NPH52", "support_pattern_sha256": digest, "operators": 1},
    ] + [
        {
            "source": "NPH52",
            "support_pattern_sha256": f"{i:064x}",
            "operators": 1,
        }
        for i in range(1, 7)
    ] + [
        {"source": "SEA_AD", "support_pattern_sha256": "f" * 64, "operators": 11}
    ]
    with pytest.raises(ValueError, match="shared across sources"):
        validate_support_pattern_source_identity(synthetic)


def test_declared_source_must_match_matrix_identity() -> None:
    current = rows(ETL / "FULL104_DATASET_ETL_OPERATOR_SUMMARY.csv")
    current[0] = dict(current[0])
    current[0]["source"] = "SEA_AD"
    with pytest.raises(ValueError, match="matrix/source mismatch"):
        validate_operator_source_rows(current)
