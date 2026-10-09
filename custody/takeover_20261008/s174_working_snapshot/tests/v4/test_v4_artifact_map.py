from __future__ import annotations

import json
from pathlib import Path

import yaml


PROJECT = Path(__file__).resolve().parents[2]
MAP = PROJECT / "configs/v4/v4_artifact_map.yaml"


def test_artifact_map_points_to_existing_files() -> None:
    registry = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    paths = (
        registry["human_entry_points"]
        + registry["canonical_current_outputs"]
        + registry["supporting_current_outputs"]
        + registry["reproducibility_builders"]["current"]
        + registry["reproducibility_builders"]["acquisition_provenance"]
        + registry["reproducibility_builders"]["inventory_and_history"]
    )
    missing = [path for path in paths if not (PROJECT / path).is_file()]
    assert missing == []


def test_canonical_and_supporting_outputs_do_not_overlap() -> None:
    registry = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    canonical = set(registry["canonical_current_outputs"])
    supporting = set(registry["supporting_current_outputs"])
    assert canonical
    assert canonical.isdisjoint(supporting)
    assert registry["model_training_started"] is False


def test_artifact_map_matches_current_report() -> None:
    registry = yaml.safe_load(MAP.read_text(encoding="utf-8"))
    report = json.loads(
        (PROJECT / "results/v4/pre_stage81a2_readiness_report.json").read_text(
            encoding="utf-8"
        )
    )
    assert registry["current_stage"] == report["stage_id"]
    assert report["model_trained"] is False
    assert report["ready_for_stage81a2_foundation_review"] is False
    assert report["readiness_blockers"] == [
        "gse97930_cerebellar_umi:donor_grouping",
        "gse97930_frontal_cortex_umi:donor_grouping",
        "gse97930_visual_cortex_umi:donor_grouping",
    ]
