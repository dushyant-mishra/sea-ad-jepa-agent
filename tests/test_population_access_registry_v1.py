from __future__ import annotations

import csv
from pathlib import Path

from scripts.agent.validate_population_access_registry_v1 import validate


def _write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _fixture(tmp_path: Path) -> tuple[Path, Path]:
    foundation_rows: list[dict[str, str]] = []

    def add(domain: str, split: str, n: int, study: str, prefix: str) -> None:
        for i in range(n):
            donor = f"{prefix}{i:03d}"
            foundation_rows.append({
                "split_domain": domain,
                "cohort": "fixture",
                "study_id": study,
                "canonical_person_id": f"{study}::{donor}" if study in {"HVS", "NPH52", "SEA_AD"} else donor,
                "split_group_id": f"{study}::{donor}",
                "split": split,
                "assignment_method": "fixture",
                "freeze_seed": "8102",
                "pathology_used_for_foundation_split": "False",
            })

    add("foundation", "train", 149, "HVS", "F")
    add("foundation", "development", 19, "HVS", "D")
    add("foundation", "sealed_holdout", 19, "HVS", "S")
    add("continuation", "train", 17, "NPH52", "C")
    add("continuation", "development", 5, "NPH52", "CD")
    add("continuation", "sealed_holdout", 5, "NPH52", "CS")
    foundation_rows.append({
        "split_domain": "whole_study_external_holdout",
        "cohort": "Siletti",
        "study_id": "siletti_human_brain_cell_atlas_v1",
        "canonical_person_id": "whole_study",
        "split_group_id": "SILETTI::WHOLE_STUDY",
        "split": "whole_study_external_holdout",
        "assignment_method": "fixture",
        "freeze_seed": "8102",
        "pathology_used_for_foundation_split": "False",
    })

    reader_ids = [f"F{i:03d}" for i in range(149)]
    reader_rows = (
        [{"donor_id": x, "reader_partition": "reader_fit"} for x in reader_ids[:104]]
        + [{"donor_id": x, "reader_partition": "reader_validation"} for x in reader_ids[104:126]]
        + [{"donor_id": x, "reader_partition": "reader_oracle"} for x in reader_ids[126:]]
    )

    foundation_path = tmp_path / "foundation.csv"
    reader_path = tmp_path / "reader.csv"
    _write_csv(foundation_path, list(foundation_rows[0]), foundation_rows)
    _write_csv(reader_path, ["donor_id", "reader_partition"], reader_rows)
    return foundation_path, reader_path


def test_valid_geometry_and_nesting_passes_without_hash_check(tmp_path: Path) -> None:
    foundation_path, reader_path = _fixture(tmp_path)
    report = validate(foundation_path, reader_path, require_hashes=False)
    assert report["terminal"] == "PASS_POPULATION_ACCESS_REGISTRY_INPUTS"
    assert report["reader_nested_in_foundation_train"] is True
    assert report["continuation_reader_overlap"] == []


def test_reader_oracle_cannot_be_outside_foundation_train(tmp_path: Path) -> None:
    foundation_path, reader_path = _fixture(tmp_path)
    rows = list(csv.DictReader(reader_path.open(encoding="utf-8")))
    rows[-1]["donor_id"] = "S000"
    _write_csv(reader_path, ["donor_id", "reader_partition"], rows)
    report = validate(foundation_path, reader_path, require_hashes=False)
    assert report["terminal"] == "STOP_POPULATION_ACCESS_REGISTRY_INPUTS"
    assert any("not in foundation train" in failure for failure in report["failures"])


def test_continuation_train_cannot_silently_enter_reader_split(tmp_path: Path) -> None:
    foundation_path, reader_path = _fixture(tmp_path)
    rows = list(csv.DictReader(reader_path.open(encoding="utf-8")))
    rows[0]["donor_id"] = "C000"
    _write_csv(reader_path, ["donor_id", "reader_partition"], rows)
    report = validate(foundation_path, reader_path, require_hashes=False)
    assert report["terminal"] == "STOP_POPULATION_ACCESS_REGISTRY_INPUTS"
    assert report["continuation_reader_overlap"] == ["C000"]


def test_pathology_based_split_is_rejected(tmp_path: Path) -> None:
    foundation_path, reader_path = _fixture(tmp_path)
    rows = list(csv.DictReader(foundation_path.open(encoding="utf-8")))
    rows[0]["pathology_used_for_foundation_split"] = "True"
    _write_csv(foundation_path, list(rows[0]), rows)
    report = validate(foundation_path, reader_path, require_hashes=False)
    assert report["terminal"] == "STOP_POPULATION_ACCESS_REGISTRY_INPUTS"
    assert any("pathology flag" in failure for failure in report["failures"])


def test_hash_mismatch_fails_closed(tmp_path: Path) -> None:
    foundation_path, reader_path = _fixture(tmp_path)
    report = validate(foundation_path, reader_path, require_hashes=True)
    assert report["terminal"] == "STOP_POPULATION_ACCESS_REGISTRY_INPUTS"
    assert "foundation split SHA-256 mismatch" in report["failures"]
    assert "reader split SHA-256 mismatch" in report["failures"]
