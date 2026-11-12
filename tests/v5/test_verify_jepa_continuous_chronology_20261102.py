"""Hostile static checks: extra history is not new scientific authority."""
import json
import shutil
from pathlib import Path

import pytest

from scripts.v5 import verify_jepa_continuous_chronology_20261102 as C


def _isolated(tmp_path: Path):
    for p in (C.LEDGER, C.INDEX, C.CHRONOLOGY, C.PROTOCOL, C.ADDITIONAL, C.LATER, C.NEWER):
        dst = tmp_path / p
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(C.ROOT / p, dst)
    data = json.loads((tmp_path / C.LEDGER).read_text())
    for e in data["records"]:
        for source in e["source_inputs"]:
            p = tmp_path / source["path"]
            p.parent.mkdir(parents=True, exist_ok=True)
            p.touch()
    return tmp_path, data


def _save(root, data):
    (root / C.LEDGER).write_text(json.dumps(data), encoding="utf-8")


def test_current_tree_is_structurally_valid():
    receipt = C.check()
    assert receipt["events"] >= 3
    assert receipt["historical_sources"] >= 41


def test_refuse_claimed_training_authority(tmp_path):
    root, data = _isolated(tmp_path)
    data["records"][0]["authority_after"] = "TRAINING_ALLOWED"
    _save(root, data)
    with pytest.raises(ValueError, match="authority promotion"):
        C.check(root)


def test_refuse_duplicate_history_event(tmp_path):
    root, data = _isolated(tmp_path)
    data["records"].append(dict(data["records"][0]))
    _save(root, data)
    with pytest.raises(ValueError, match="duplicate events"):
        C.check(root)


def test_refuse_missing_early_graph_jepa_source(tmp_path):
    root, data = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["source_evidence"] = [x for x in idx["source_evidence"] if x["id"] != "stage35c"]
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="historical source coverage|missing historical evidence"):
        C.check(root)


def test_refuse_fabricated_source_path(tmp_path):
    root, data = _isolated(tmp_path)
    data["records"][0]["source_inputs"][0]["path"] = "invented/nonexistent_source.json"
    _save(root, data)
    with pytest.raises(ValueError, match="source file identity"):
        C.check(root)


def test_refuse_wrong_current_branch_ownership(tmp_path):
    root, data = _isolated(tmp_path)
    data["active_handoff_pr"] = 323
    _save(root, data)
    with pytest.raises(ValueError, match="PR322/460"):
        C.check(root)


def test_refuse_missing_stage81a3_qualification_source(tmp_path):
    root, data = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["source_evidence"] = [x for x in idx["source_evidence"]
                              if x["id"] != "stage81a3_complete_qualification_record"]
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="historical source coverage|missing historical evidence"):
        C.check(root)


def test_refuse_erased_v2_graph_detail(tmp_path):
    root, data = _isolated(tmp_path)
    (root / C.ADDITIONAL).write_text("Stage81A3 only", encoding="utf-8")
    with pytest.raises(ValueError, match="additional chronology omission"):
        C.check(root)


def test_refuse_erasure_of_historical_freeze1(tmp_path):
    root, data = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["milestones"]["historical_stage81a3r_freeze1"]["declared"] = False
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="historical Freeze1 declaration missing"):
        C.check(root)


def test_refuse_promoting_historical_freeze1_to_current_winner(tmp_path):
    root, data = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["milestones"]["historical_stage81a3r_freeze1"]["current_representation_winner"] = True
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="must not promote current dimension"):
        C.check(root)


def test_refuse_dropped_depth_null_and_x4_redteam(tmp_path):
    root, data = _isolated(tmp_path)
    (root / C.LATER).write_text("Stage81A3R Freeze1 d_global=224", encoding="utf-8")
    with pytest.raises(ValueError, match="later chronology omission"):
        C.check(root)


def test_refuse_erasing_recovered_morabito_primary_source(tmp_path):
    root, _ = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["source_evidence"] = [x for x in idx["source_evidence"]
                              if x["id"] != "v21_morabito_frozen_encoder_external_projection"]
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="missing round25-29 primary sources"):
        C.check(root)


def test_refuse_promoting_stage72b_coactivity_to_validated_regulation(tmp_path):
    root, _ = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["milestones"]["round28_morabito_regulatory_ancestry"]["validated_regulation"] = True
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="stage72 coactivity silently promoted"):
        C.check(root)


def test_refuse_claiming_older_external_projection_as_clean_current_benchmark(tmp_path):
    root, _ = _isolated(tmp_path)
    idx = json.loads((root / C.INDEX).read_text())
    idx["milestones"]["round25_early_external_cohort_tests"]["current_clean_benchmark_authority"] = True
    (root / C.INDEX).write_text(json.dumps(idx), encoding="utf-8")
    with pytest.raises(ValueError, match="old external cohort silently promoted"):
        C.check(root)


@pytest.mark.parametrize("event_number", [105, 106, 107])
def test_new_historical_repair_categories_are_explicitly_reviewed(event_number):
    data = json.loads((C.ROOT / C.LEDGER).read_text(encoding="utf-8"))
    assert data["records"][event_number - 1]["change_type"] in C.TYPES


def test_refuse_unapproved_new_chronology_category(tmp_path):
    root, data = _isolated(tmp_path)
    data["records"][-1]["change_type"] = "UNAPPROVED_NEW_SCIENCE_AUTHORITY"
    _save(root, data)
    with pytest.raises(ValueError, match="unrecognized change type"):
        C.check(root)
