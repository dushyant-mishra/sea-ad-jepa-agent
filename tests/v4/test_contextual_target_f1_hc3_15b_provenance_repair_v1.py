import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / "scripts/v4/build_contextual_target_f1_hc3_15b_provenance_repair_v1.py"
VALIDATE = ROOT / "scripts/v4/validate_contextual_target_f1_hc3_15b_provenance_repair_v1.py"
FINALIZE = ROOT / "scripts/v4/finalize_contextual_target_f1_hc3_15b_provenance_repair_v1.py"


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_review_sections_are_exact_and_structured_without_prose_reinterpretation():
    # Catches fabricated PASS records or review content that is not an exact source section.
    module = load(BUILD, "build_repair")
    source = "# title\n\n## 1. Historian / Authority\n\nVERDICT: PASS\n\nExact finding.\n\n## 2. Statistical Design\n\nVERDICT: CONCERN\n\nExact concern.\n"
    records = module.extract_review_sections(source, "fixture.md", {"Historian / Authority": "reviewer-a", "Statistical Design": "reviewer-b"})
    assert [r["decision"] for r in records] == ["PASS", "CONCERN"]
    assert records[0]["review_content"] == "## 1. Historian / Authority\n\nVERDICT: PASS\n\nExact finding.\n\n"
    assert records[0]["reviewer_id"] == "reviewer-a"


def test_review_extraction_rejects_non_enum_or_missing_reviewer():
    # Catches truthy/free-text verdicts and anonymous reviews.
    module = load(BUILD, "build_repair_reject")
    with pytest.raises(RuntimeError, match="STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD"):
        module.extract_review_sections("## X\n\nVERDICT: yes\n", "x.md", {"X": "r"})
    with pytest.raises(RuntimeError, match="STOP_F1_HC3_15B_PROVENANCE_REVIEW_RECORD"):
        module.extract_review_sections("## X\n\nVERDICT: PASS\n", "x.md", {})


def test_chronology_claim_is_limited_when_external_pre_result_anchor_is_absent():
    # Catches manufacturing a retroactive timestamp claim from filesystem metadata alone.
    module = load(BUILD, "build_repair_chronology")
    record = module.chronology_record(
        contract_sha="a" * 64,
        creation_utc="2026-09-02T16:51:16Z",
        modified_utc="2026-09-02T16:51:18Z",
        git_blob=None,
        external_pre_result_anchor=None,
    )
    assert record["chronology_claim"] == "EXECUTION_ENFORCED_PROSPECTIVELY__EXTERNAL_TIME_ANCHOR_UNAVAILABLE"
    assert record["filesystem_times_are_independent_proof"] is False


def test_validator_rejects_review_bound_to_wrong_15b_manifest():
    # Catches structured reviews that authenticate a different scientific package.
    module = load(VALIDATE, "validate_repair")
    record = {
        "reviewer_id": "r",
        "lens_id": "L",
        "decision": "PASS",
        "reviewed_artifacts": [{"path": "F1_HC3_15B_MANIFEST.csv", "sha256": "b" * 64}],
        "review_content_sha256": "c" * 64,
        "record_sha256": "d" * 64,
    }
    with pytest.raises(RuntimeError, match="STOP_F1_HC3_15B_PROVENANCE_REVIEW_BINDING"):
        module.require_review_authority(record, "a" * 64)


def test_finalizer_uses_package_relative_source_snapshots_and_external_anchor():
    # Catches staging-absolute source paths and a self-asserted rather than separate root anchor.
    module = load(FINALIZE, "finalize_repair")
    assert module.snapshot_path("build.py") == "source_snapshot/build.py"
    assert module.external_anchor_path().as_posix().endswith("docs/agent/provenance-anchors/F1_HC3_15B_PROVENANCE_REPAIR_ROOT_20260902.json")
