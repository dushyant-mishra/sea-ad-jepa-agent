from __future__ import annotations

import importlib.util
import json
from pathlib import Path


PROJECT = Path(__file__).resolve().parents[2]
SCRIPT = PROJECT / "scripts/v4/stage81_reconsider_storage_policy.py"


def load_script():
    spec = importlib.util.spec_from_file_location("stage81_storage", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_decision_vocabulary_and_revoked_statuses() -> None:
    module = load_script()
    assert module.ALLOWED == {
        "download_required", "download_useful", "metadata_only", "duplicate_excluded",
        "raw_data_excluded", "scientifically_incompatible", "controlled_access_blocked",
        "source_unverified",
    }
    assert "deferred_oversized" in module.REVOKED
    assert module.classify("skip", "consolidated object is sufficient duplicate", "x") == "duplicate_excluded"
    assert module.classify("skip", "controlled access requires terms acceptance", "x") == "controlled_access_blocked"


def test_frozen_audit_when_present() -> None:
    path = PROJECT / "results/v4/stage81_storage_policy_reconsideration.json"
    if not path.exists():
        return
    report = json.loads(path.read_text(encoding="utf-8"))
    assert report["storage_policy_audit_pass"] is True
    assert report["no_fixed_stage_download_cap"] is True
    assert report["surviving_revoked_statuses"] == []
    assert report["prior_size_based_exclusion_count"] == 0
    assert len(report["source_commit"]) == 40
