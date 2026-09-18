"""Second-generation anti-spillover firewall for the FULL104 masking freeze."""
from __future__ import annotations
import inspect,re
from pathlib import Path

from sea_ad_jepa.v5 import (
    full104_census_receipt_v2,
    control_calibration_interval_receipt_v1,
    control_capacity_calibration_receipt_v1,
    control_calibration_precision_authority_v1,
    full104_control_calibration_cache_v1,
    full104_control_calibration_cache_evaluator_v1,
    full104_nonlinear_capacity_cache_evaluator_v1,
    nonlinear_capacity_model_authority_v1,
    nonlinear_sampling_calibration_authority_v2,
    masking_burden_ladder_authority_v2,
    masking_control_executor_v1,
    masking_donor_evidence_v1,
    masking_nonlinear_challenge_authority_v3,
    masking_nonlinear_challenge_executor_v1,
    masking_qualification_decision_v2,
    masking_qualification_execution_authority_v4,
    masking_qualification_parameters_authority_v2,
    masking_qualification_run_contract_v4,
    masking_rng_replay_authority_v2,
    precision_authority_v4,
    target_panel_authority_v3,
    target_panel_selector_v2,
    target_panel_sizing_authority_v2,
)

CURRENT_PRODUCTION_MODULES=(
    full104_census_receipt_v2,
    control_calibration_interval_receipt_v1,
    control_capacity_calibration_receipt_v1,
    control_calibration_precision_authority_v1,
    full104_control_calibration_cache_v1,
    full104_control_calibration_cache_evaluator_v1,
    masking_burden_ladder_authority_v2,
    masking_control_executor_v1,
    masking_donor_evidence_v1,
    masking_nonlinear_challenge_authority_v3,
    masking_nonlinear_challenge_executor_v1,
    masking_qualification_decision_v2,
    masking_qualification_execution_authority_v4,
    masking_qualification_parameters_authority_v2,
    masking_qualification_run_contract_v4,
    masking_rng_replay_authority_v2,
    nonlinear_sampling_calibration_authority_v1,
    precision_authority_v4,
    target_panel_authority_v3,
    target_panel_selector_v2,
    target_panel_sizing_authority_v2,
)

FORBIDDEN_CURRENT_PATTERNS={
    "placeholder":re.compile(r"(?i)PLACEHOLDER_|UNRESOLVED_BIND|UNRESOLVED_PROSPECTIVE"),
    "stage81a3":re.compile(r"(?i)stage81a3"),
    "t1_checkpoint":re.compile(r"(?i)t1_checkpoint|post_u0_t1"),
    "historical_ema":re.compile(r"(?<![\w.])0?\.996(?![\w])"),
    "historical_geometry":re.compile(r"(?<![\w.])160(?![\w.])"),
    "analysis_import":re.compile(r"(?m)^\s*(?:from|import)\s+analysis(?:\.|\s)"),
}

def test_no_placeholder_or_historical_artifact_spillover_in_current_successors():
    violations=[]
    for module in CURRENT_PRODUCTION_MODULES:
        source=Path(inspect.getfile(module)).read_text(encoding="utf-8")
        for label,pattern in FORBIDDEN_CURRENT_PATTERNS.items():
            m=pattern.search(source)
            if m:
                line=source[:m.start()].count("\n")+1
                violations.append(f"{module.__name__}:{line}:{label}")
    assert violations==[],violations

def test_parameter_reuse_is_explicitly_provenanced_not_defaulted():
    from sea_ad_jepa.v5 import masking_qualification_parameters_authority_v2 as module
    source=Path(inspect.getfile(module)).read_text(encoding="utf-8")
    assert "DISCOVERY_DEFINED_CANDIDATE_FROZEN_FOR_INDEPENDENT_FULL104_CONFIRMATION_V1" in source
    assert "FULL104_CONFIRMATION_WITHOUT_PARAMETER_RETUNING_V1" in source
    assert "BURDEN_OWNED_BY_FULL104_CENSUS_LADDER_V1" in source

def test_provisional_128_and_256_authorities_are_not_current_production_modules():
    names={m.__name__.split(".")[-1] for m in CURRENT_PRODUCTION_MODULES}
    assert "target_panel_sizing_authority_v1" not in names
    assert "target_panel_authority_v2" not in names
    assert "precision_authority_v3" not in names
    assert "masking_nonlinear_challenge_authority_v2" not in names
    assert "masking_qualification_run_contract_v3" not in names

def test_historical_tmp_evidence_trend_artifacts_are_absent():
    assert not Path(".tmp/evidence_trend_4iu5q3yi").exists()

def test_existing_support_authority_is_present_and_real():
    import json
    path=Path("docs/agent/V5_SUPPORT_ESTIMABILITY_AUTHORITY_20260915.json")
    assert path.is_file()
    payload=json.loads(path.read_text(encoding="utf-8"))
    assert payload["schema"]=="V5_SUPPORT_ESTIMABILITY_AUTHORITY_V1"
    assert payload["full104_substrate_sha256"]=="66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29"
    assert payload["training_authorized"] is False

def test_current_checkpoint_state_names_redteam2_successors():
    import json
    state=json.loads(Path("docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json").read_text(encoding="utf-8"))
    assert state["assets"]["repository"]["working_branch"]=="impl/v5-full104-masking-redteam2-20260918"
    sources=state["assets"]["current_sources"]
    assert sources["masking_run_contract"].endswith("masking_qualification_run_contract_v4.py")
    assert sources["target_panel_sizing"].endswith("target_panel_sizing_authority_v2.py")
    assert sources["target_panel_authority"].endswith("target_panel_authority_v3.py")
    assert sources["precision_authority"].endswith("precision_authority_v4.py")
    assert sources["nonlinear_sampling_calibration"].endswith("nonlinear_sampling_calibration_authority_v1.py")
    assert sources["nonlinear_challenge_authority"].endswith("masking_nonlinear_challenge_authority_v3.py")


def test_calibration_cache_and_scripts_cannot_spill_historical_substrates_into_full104():
    script_paths = (
        Path("scripts/agent/build_full104_control_calibration_cache_v1.py"),
        Path("scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py"),
        Path("scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py"),
        Path("scripts/agent/build_full104_outer_split_authority_v1_20260918.py"),
        Path("scripts/agent/build_full104_precision_authority_v4_20260918.py"),
    )
    forbidden = {
        "historical_analysis_path": re.compile(r"(?i)(?:^|[\\/])analysis[\\/]"),
        "history_path": re.compile(r"(?i)docs[\\/]history"),
        "stage81": re.compile(r"(?i)stage81"),
        "t1_checkpoint": re.compile(r"(?i)t1_checkpoint|post_u0_t1"),
        "historical_ema": re.compile(r"(?<![\w.])0?\.996(?![\w])"),
        "old_800_universe": re.compile(r"(?<!\d)800(?!\d)"),
        "old_6000_universe": re.compile(r"(?<!\d)6000(?!\d)"),
    }
    violations=[]
    for path in script_paths:
        source=path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        for label,pattern in forbidden.items():
            m=pattern.search(source)
            if m:
                line=source[:m.start()].count("\n")+1
                violations.append(f"{path}:{line}:{label}")
    assert violations==[],violations


def test_direct_stream_capacity_driver_remains_fail_closed_tombstone():
    path=Path("scripts/agent/run_full104_target_panel_capacity_calibration_v1.py")
    source=path.read_text(encoding="utf-8")
    compile(source, str(path), "exec")
    assert "SUPERSEDED_FAIL_CLOSED" in source
    assert "build_full104_control_calibration_cache_v1.py" in source
    assert "evaluate_full104_target_panel_capacity_from_cache_v1.py" in source


def test_current_state_binds_calibration_cache_sources_and_explicitly_forbids_terminal_use():
    import json
    state=json.loads(Path("docs/agent/CURRENT_WORK_CHECKPOINT_STATE.json").read_text(encoding="utf-8"))
    sources=state["assets"]["current_sources"]
    assert sources["control_calibration_cache"].endswith("full104_control_calibration_cache_v1.py")
    assert sources["control_calibration_cache_evaluator"].endswith("full104_control_calibration_cache_evaluator_v1.py")
    assert sources["control_calibration_cache_builder"].endswith("build_full104_control_calibration_cache_v1.py")
    assert sources["target_panel_capacity_evaluator"].endswith("evaluate_full104_target_panel_capacity_from_cache_v1.py")
    assert "CALIBRATION_CACHE_FORBIDDEN_AS_TERMINAL_FULL104_INPUT" in state["forbidden_actions"]


def test_nonlinear_model_capacity_builder_has_narrow_historical_role_only():
    path=Path("scripts/agent/build_full104_nonlinear_capacity_model_authority_v1_20260918.py")
    source=path.read_text(encoding="utf-8")
    compile(source,str(path),"exec")
    assert "HISTORICAL_SCRIPT" in source and "HISTORICAL_SUMMARY" in source
    assert "NonlinearCapacityModelAuthorityV1" in source
    assert "MODEL_CAPACITY_PROVENANCE_ONLY__NO_DATA_TARGET_BURDEN_FOLD_SEED_OR_ROW_CAP_AUTHORITY" in source
    for forbidden in ("X_common6000.npz","outer5200_targets32_cols.npy","JEPA_SCALE_MASK","JEPA_SCALE_FOLD","random_state=20260917"):
        assert forbidden not in source
