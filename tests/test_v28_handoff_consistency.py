"""Adversarial test of the V28 documentary guard; NEVER a training permission test."""
import copy
import importlib.util
import json
from pathlib import Path
import shutil
import pytest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts/agent/verify_v28_handoff_consistency_v1.py"
SPEC = importlib.util.spec_from_file_location("v28_handoff_check", MODULE_PATH)
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)

@pytest.fixture
def dossier(tmp_path):
    for name in (CHECK.POINTER, CHECK.STATE, CHECK.ASSETS):
        src, dst = ROOT / name, tmp_path / name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    p = json.loads((tmp_path / CHECK.POINTER).read_text())
    for field in CHECK.REQUIRED:
        src, dst = ROOT / p[field], tmp_path / p[field]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
    return tmp_path

def change(root, name, fn):
    p = root / name
    data = json.loads(p.read_text())
    fn(data)
    p.write_text(json.dumps(data))

def refused(dossier, scope):
    with pytest.raises(ValueError, match="STOP_V28_HANDOFF_" + scope):
        CHECK.verify(dossier)

def test_original_dossier_positive_control(dossier):
    r = CHECK.verify(dossier)
    assert r["status"] == "PASS_V28_HANDOFF_CONSISTENCY_ONLY"
    assert not r["training_authorized"] and r["closed_root_count"] == 0

def test_retracted_s9_must_never_reappear_as_defect(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["evidence"]["environment"].update(S9="OPEN_DEFECT"))
    refused(dossier, "S9_RETRACTION_LOST")

def test_six_self_validations_do_not_become_six_closed_roots(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["evidence"]["authority"].update(full_closure_roots=6))
    refused(dossier, "FALSE_AUTHORITY_CLOSURE")

def test_hardcoded_gradient_counter_cannot_be_repromoted(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["evidence"]["synthetic_mechanics"].update(
               success_counter_40of40_claim="INDEPENDENTLY_MEASURED"))
    refused(dossier, "VACUOUS_GRADIENT_OR_GPU_PROMOTION")

def test_nine_archive_members_are_not_ten_public_individual_files(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["evidence"]["fit_metadata"].update(
               original_local_archive_members=10))
    refused(dossier, "HISTORICAL_POPULATION_OR_ZIP_SPILLOVER")

def test_incomplete_raw_l4_scan_cannot_become_a_pass(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["evidence"]["raw_level4"].update(all104_verdict="PASS"))
    refused(dossier, "RAW_COUNT_FALSE_GREEN")

def test_no_protected_access_from_document_edits(dossier):
    change(dossier, CHECK.STATE,
           lambda s: s["protected"].update(training="ON"))
    refused(dossier, "PROTECTED_ACCESS_INFLATION")

def test_known_provenance_mismatch_npz_must_remain_quarantined(dossier):
    def promote(m):
        for x in m["assets"]:
            if x["filename"].startswith("66e64913"):
                x["role"] = "FULL104_CURRENT_INPUT"
    change(dossier, CHECK.ASSETS, promote)
    refused(dossier, "MISMATCHED_NPZ_PROMOTED")

def test_local_asset_count_cannot_silently_shrink(dossier):
    change(dossier, CHECK.ASSETS, lambda m: m["assets"].pop())
    refused(dossier, "LOCAL_ASSET_CENSUS")

def test_pointer_must_not_mix_up_data_and_handoff_roles(dossier):
    change(dossier, CHECK.POINTER,
           lambda p: p.update(state_path=CHECK.ASSETS))
    refused(dossier, "POINTER_ROLE_CROSSING")

def test_missing_handoff_file_is_not_a_successful_recovery(dossier):
    (dossier / "docs/agent/JEPA_NEW_CHAT_HANDOFF_20260926_V28_VERIFIED_GITHUB_PUBLICATION.md").unlink()
    refused(dossier, "MISSING_REFERENCED_FILE")
