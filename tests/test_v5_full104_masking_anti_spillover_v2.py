"""Second-generation anti-spillover firewall for the FULL104 masking freeze."""
from __future__ import annotations

import inspect
import re
from pathlib import Path

from sea_ad_jepa.v5 import (
    full104_census_receipt_v2,
    masking_burden_ladder_authority_v2,
    masking_donor_evidence_v1,
    masking_control_executor_v1,
    masking_nonlinear_challenge_authority_v2,
    masking_nonlinear_challenge_executor_v1,
    masking_nonlinear_challenge_receipt_v1,
    masking_qualification_decision_v3,
    masking_qualification_execution_authority_v5,
    masking_qualification_parameters_authority_v2,
    masking_qualification_run_contract_v3,
    precision_authority_v4,
    target_panel_selector_v2,
    target_panel_sizing_authority_v1,
    target_panel_authority_v2,
    masking_rng_replay_authority_v2,
)

CURRENT_PRODUCTION_MODULES = (
    full104_census_receipt_v2,
    masking_burden_ladder_authority_v2,
    masking_donor_evidence_v1,
    masking_control_executor_v1,
    masking_nonlinear_challenge_authority_v2,
    masking_nonlinear_challenge_executor_v1,
    masking_nonlinear_challenge_receipt_v1,
    masking_qualification_decision_v3,
    masking_qualification_execution_authority_v5,
    masking_qualification_parameters_authority_v2,
    masking_qualification_run_contract_v3,
    precision_authority_v4,
    target_panel_selector_v2,
    target_panel_sizing_authority_v1,
    target_panel_authority_v2,
    masking_rng_replay_authority_v2,
)

FORBIDDEN_CURRENT_PATTERNS = {
    "placeholder": re.compile(r"(?i)PLACEHOLDER_|UNRESOLVED_BIND|UNRESOLVED_PROSPECTIVE"),
    "stage81a3": re.compile(r"(?i)stage81a3"),
    "t1_checkpoint": re.compile(r"(?i)t1_checkpoint|post_u0_t1"),
    "historical_ema": re.compile(r"(?<![\w.])0?\.996(?![\w])"),
    "historical_geometry": re.compile(r"(?<![\w.])160(?![\w.])"),
    "analysis_import": re.compile(r"(?m)^\s*(?:from|import)\s+analysis(?:\.|\s)"),
}


def test_no_placeholder_or_historical_artifact_spillover_in_current_successors() -> None:
    violations: list[str] = []
    for module in CURRENT_PRODUCTION_MODULES:
        source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
        for label, pattern in FORBIDDEN_CURRENT_PATTERNS.items():
            match = pattern.search(source)
            if match:
                line = source[: match.start()].count("\n") + 1
                violations.append(f"{module.__name__}:{line}:{label}")
    assert violations == [], violations


def test_parameter_reuse_is_explicitly_provenanced_not_defaulted() -> None:
    module = masking_qualification_parameters_authority_v2
    source = Path(inspect.getfile(module)).read_text(encoding="utf-8")
    assert "DISCOVERY_DEFINED_CANDIDATE_FROZEN_FOR_INDEPENDENT_FULL104_CONFIRMATION_V1" in source
    assert "FULL104_CONFIRMATION_WITHOUT_PARAMETER_RETUNING_V1" in source
    assert "BURDEN_OWNED_BY_FULL104_CENSUS_LADDER_V1" in source
    for field in (
        "discovery_expanded_validation_report_sha256",
        "discovery_universe_scale_script_sha256",
        "discovery_outside800_unified_script_sha256",
        "discovery_provenance_note_sha256",
    ):
        assert field in source


def test_current_checkpoint_state_does_not_point_back_to_v1_masking_sources() -> None:
    import json

    state = json.loads(Path("docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json").read_text(encoding="utf-8"))
    sources = state["assets"]["current_sources"]
    assert sources["masking_run_contract"].endswith("masking_qualification_run_contract_v2.py") or sources["masking_run_contract"].endswith("masking_qualification_run_contract_v3.py")
    assert sources["target_evidence_budget"].endswith("target_evidence_budget_authority_v2.py")
    assert "target_evidence_budget_authority_v1.py" not in str(sources)
    assert "masking_qualification_run_contract_v1.py" not in str(sources)


def test_historical_tmp_evidence_trend_artifacts_are_not_tracked_in_successor_tree() -> None:
    assert not Path(".tmp/evidence_trend_4iu5q3yi").exists()


def test_existing_support_authority_is_present_and_not_replaced_by_placeholder() -> None:
    import json

    path = Path("docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json")
    assert path.is_file()
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"] == "V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1"
    assert payload["full104_substrate_sha256"] == "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
    assert payload["training_authorized"] is False
