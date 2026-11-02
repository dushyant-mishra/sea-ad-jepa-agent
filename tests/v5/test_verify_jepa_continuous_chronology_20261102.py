"""Hostile static checks: extra history is not new scientific authority."""
import json
import shutil
from pathlib import Path

import pytest

from scripts.v5 import verify_jepa_continuous_chronology_20261102 as C


def _isolated(tmp_path: Path):
    for p in (C.LEDGER, C.INDEX, C.CHRONOLOGY, C.PROTOCOL, C.ADDITIONAL):
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
    assert receipt["historical_sources"] >= 27


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
