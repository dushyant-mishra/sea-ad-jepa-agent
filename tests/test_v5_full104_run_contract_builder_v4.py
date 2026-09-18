from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import re

from scripts.agent.work_checkpoint import semantic_sha256 as checkpoint_semantic_sha256


BUILDER = Path("scripts/agent/build_full104_masking_run_contract_v4_20260918.py")


def load_builder_module():
    spec = importlib.util.spec_from_file_location("full104_run_contract_builder_v4", BUILDER)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_final_run_contract_builder_accepts_paths_not_role_digests():
    source = BUILDER.read_text(encoding="utf-8")
    compile(source, str(BUILDER), "exec")
    cli_flags = re.findall(r'add_argument\("([^"]+)"', source)
    assert cli_flags
    assert not [flag for flag in cli_flags if "sha256" in flag.lower()]
    assert "PATH_ONLY_INPUTS__NO_CALLER_ENTERED_ROLE_DIGESTS__CURRENT_FULL104_ROOT_CLOSURE_V1" in source


def test_final_run_contract_builder_invokes_every_v4_binding_gate():
    source = BUILDER.read_text(encoding="utf-8")
    required = (
        "bind_machine_checkpoint_semantic",
        "bind_parameters",
        "bind_evidence_budget_template",
        "bind_burden_ladder",
        "bind_rng_replay",
        "bind_design",
        "bind_control_calibration_provenance",
        "bind_control_calibration_precision_plan",
        "bind_target_panel",
        "bind_precision",
        "bind_nonlinear",
        "bind_execution_sources",
        "assert_terminal_execution_input_role",
    )
    for method in required:
        assert f"contract.{method}(" in source, method


def test_final_run_contract_builder_uses_only_current_final_roles():
    source = BUILDER.read_text(encoding="utf-8")
    assert "MaskingQualificationDesignAuthorityV2" in source
    assert "ControlCalibrationPrecisionPlanV2" in source
    assert "TargetPanelAuthorityV3" in source
    assert "QualificationPrecisionAuthorityV4" in source
    assert "NonlinearSamplingCalibrationPlanV2" in source
    assert "NonlinearMaskingChallengeAuthorityV3" in source
    assert "MaskingRngReplayAuthorityV2" in source
    assert "TargetEvidenceBudgetTemplateAuthorityV1" in source
    assert "AddressUniverseLadder" not in source
    assert "control_calibration_precision_authority_v1.py" not in source
    assert "masking_nonlinear_challenge_authority_v2.py" not in source
    assert "v5_full104_masking_gpu_preflight_20260917" not in source
    assert "PLACEHOLDER" not in source


def test_final_run_contract_builder_pins_current_support_semantics_and_full104_roots():
    source = BUILDER.read_text(encoding="utf-8")
    assert "cab2cecdd5ff31c2fbcaff408e1b1b7548eb2f72c1d3213931f1ce39188b6e08" in source
    assert "66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29" in source
    assert "852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537" in source
    assert "support authority is not the exact current semantic authority" in source


def test_builder_checkpoint_semantic_digest_matches_checkpoint_tool():
    module = load_builder_module()
    payload = {
        "schema": "JEPA_WORK_CHECKPOINT_V1",
        "head": "abc",
        "nested": {"b": 2, "a": 1},
        "checkpoint_semantic_sha256": "0" * 64,
    }
    assert module.semantic_sha256(payload) == checkpoint_semantic_sha256(payload)


def test_live_source_roles_are_explicit_current_files_and_include_spillover_firewall():
    module = load_builder_module()
    roles = module.SOURCE_ROLES
    assert roles["control_calibration_precision_live_sha256"].endswith(
        "control_calibration_precision_authority_v2.py"
    )
    assert roles["nonlinear_sampling_calibration_live_sha256"].endswith(
        "nonlinear_sampling_calibration_authority_v2.py"
    )
    assert roles["nonlinear_authority_live_sha256"].endswith(
        "masking_nonlinear_challenge_authority_v3.py"
    )
    assert roles["anti_spillover_test_live_sha256"] == "tests/test_v5_full104_masking_anti_spillover_v2.py"
    for relative in roles.values():
        assert Path(relative).is_file(), relative
