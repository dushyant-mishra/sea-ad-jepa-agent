from __future__ import annotations

from pathlib import Path

import pytest

from scripts.v5 import jepa_post_td_harness_contract_v1 as legacy
from scripts.v5.td_unified import downstream_preflight_v1 as p

ROOT = Path(__file__).resolve().parents[3]
TASK3_CANDIDATE = "d9e58a18da5bcfc95d9b9e7484e5686d403c55d4"


def test_pinned_downstream_design_and_plan_are_reachable_from_git_history():
    report = p.audit_downstream_preflight(ROOT, task3_candidate_sha=TASK3_CANDIDATE)
    assert report["design_custody"]["architecture_v1_1_reachable"] is True
    assert report["design_custody"]["implementation_plan_reachable"] is True


def test_task4_production_surface_remains_absent_before_task3_acceptance():
    report = p.audit_downstream_preflight(ROOT, task3_candidate_sha=TASK3_CANDIDATE)
    assert report["task4_production_paths_present"] == []
    assert report["task4_authorized"] is False
    assert report["status"] == "DOWNSTREAM_STAGED__TASK3_ACCEPTANCE_REQUIRED__TASK4_BLOCKED"


def test_legacy_post_td_harness_is_explicitly_non_authorizing_and_not_unified_authority():
    report = p.audit_downstream_preflight(ROOT, task3_candidate_sha=TASK3_CANDIDATE)
    assert report["legacy_post_td_harness"]["classification"] == "LEGACY_NON_AUTHORIZING_MECHANICS_ONLY"
    assert report["legacy_post_td_harness"]["authority_all_false"] is True
    assert report["legacy_post_td_harness"]["uses_unified_registry_evidence"] is False


def test_legacy_pass_label_path_executes_but_cannot_authorize_anything():
    portfolio = legacy.build_target_portfolio(
        selected_candidate="C1",
        qualifications={"C1": "PASS"},
    )
    assert portfolio["schema"] == legacy.PORTFOLIO_SCHEMA
    assert portfolio["authority"]
    assert all(value is False for value in portfolio["authority"].values())
    assert portfolio["schema"] != "JEPA_UNIFIED_TARGET_QUALIFICATION_BUNDLE_V1"


def test_unified_package_does_not_import_legacy_post_td_harness():
    report = p.audit_downstream_preflight(ROOT, task3_candidate_sha=TASK3_CANDIDATE)
    assert report["legacy_post_td_harness"]["imported_by_unified_package"] is False


def test_caller_boolean_cannot_turn_task3_into_downstream_authority():
    with pytest.raises(p.DownstreamPreflightError, match="caller assertion.*authority"):
        p.audit_downstream_preflight(
            ROOT,
            task3_candidate_sha=TASK3_CANDIDATE,
            claimed_task3_accepted=True,
        )


def test_global_stop_state_is_preserved_verbatim():
    report = p.audit_downstream_preflight(ROOT, task3_candidate_sha=TASK3_CANDIDATE)
    assert report["global_authority"] == (
        "TARGET_WINNER_NONE__REPRESENTATION_WINNER_NONE__REAL_TRAINING_OFF__STAGE4_NOT_AUTHORIZED"
    )
    assert report["real_training_authorized"] is False
    assert report["stage4_authorized"] is False


def test_premature_task4_file_fails_closed(tmp_path: Path):
    (tmp_path / "scripts/v5/td_unified").mkdir(parents=True)
    (tmp_path / "scripts/v5/jepa_post_td_harness_contract_v1.py").parent.mkdir(parents=True, exist_ok=True)
    (tmp_path / "scripts/v5/jepa_post_td_harness_contract_v1.py").write_text(
        '_AUTHORITY_OFF = {"training_authorized": False, "stage4_authorized": False}\n',
        encoding="utf-8",
    )
    (tmp_path / "scripts/v5/td_unified/target_bundle_v1.py").write_text("# premature\n", encoding="utf-8")
    with pytest.raises(p.DownstreamPreflightError, match="premature Task 4"):
        p.audit_downstream_preflight(
            tmp_path,
            task3_candidate_sha=TASK3_CANDIDATE,
            verify_git_custody=False,
        )
