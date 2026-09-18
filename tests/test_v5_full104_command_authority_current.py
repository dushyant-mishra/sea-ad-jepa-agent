from __future__ import annotations

import ast
from pathlib import Path
import re


COMMANDS = Path("docs/agent/JEPA_NEW_CHAT_COMMANDS_20260918_V5_FULL104_MASKING_CURRENT.md")

CURRENT_PIPELINE_SCRIPTS = (
    Path("scripts/agent/build_full104_masking_parameters_authority_v2_20260918.py"),
    Path("analysis/v5_full104_census_20260918/full104_readonly_census_receipts_v2.py"),
    Path("scripts/agent/build_full104_census_authority_v2_20260918.py"),
    Path("scripts/agent/build_full104_control_calibration_cache_v1.py"),
    Path("scripts/agent/evaluate_full104_target_panel_capacity_from_cache_v1.py"),
    Path("scripts/agent/build_full104_target_panel_selection_v2_20260918.py"),
    Path("scripts/agent/build_full104_target_panel_authority_v3_20260918.py"),
    Path("scripts/agent/build_full104_outer_split_authority_v1_20260918.py"),
    Path("scripts/agent/build_full104_precision_authority_v4_20260918.py"),
    Path("scripts/agent/build_full104_nonlinear_capacity_model_authority_v1_20260918.py"),
    Path("scripts/agent/evaluate_full104_nonlinear_capacity_from_cache_v1.py"),
    Path("scripts/agent/build_full104_target_evidence_budget_template_authority_v1_20260918.py"),
    Path("scripts/agent/build_full104_burden_ladder_authority_v2_20260918.py"),
    Path("scripts/agent/build_full104_rng_replay_authority_v2_20260918.py"),
    Path("scripts/agent/build_full104_nonlinear_challenge_authority_v3_20260918.py"),
    Path("scripts/agent/build_full104_masking_design_authority_v2_20260918.py"),
    Path("scripts/agent/build_full104_masking_run_contract_v4_20260918.py"),
)


def required_cli_flags(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    flags: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if not isinstance(func, ast.Attribute) or func.attr != "add_argument":
            continue
        if not node.args or not isinstance(node.args[0], ast.Constant):
            continue
        flag = node.args[0].value
        if not isinstance(flag, str) or not flag.startswith("--"):
            continue
        required = any(
            keyword.arg == "required"
            and isinstance(keyword.value, ast.Constant)
            and keyword.value.value is True
            for keyword in node.keywords
        )
        if required:
            flags.append(flag)
    return tuple(flags)


def powershell_fences(text: str) -> tuple[str, ...]:
    return tuple(
        match.group(1)
        for match in re.finditer(r"\x60\x60\x60powershell\s*\n(.*?)\x60\x60\x60", text, flags=re.DOTALL)
    )


def test_canonical_gpu_command_authority_covers_every_required_current_cli_flag():
    text = COMMANDS.read_text(encoding="utf-8")
    fences = powershell_fences(text)
    assert fences, "canonical GPU command authority contains no PowerShell blocks"

    for script in CURRENT_PIPELINE_SCRIPTS:
        assert script.is_file(), script
        required = required_cli_flags(script)
        assert required, f"{script}: expected at least one required CLI flag"
        matching = tuple(block for block in fences if script.name in block)
        assert matching, f"{script}: missing from canonical GPU command authority"
        command_context = "\n".join(matching)
        missing = [flag for flag in required if flag not in command_context]
        assert not missing, (
            f"{script}: canonical GPU command authority is stale; "
            f"missing required CLI flags {missing}"
        )


def test_current_command_authority_keeps_historical_and_terminal_boundaries_explicit():
    text = COMMANDS.read_text(encoding="utf-8")
    required_phrases = (
        "Historical/smaller-run artifacts may motivate",
        "v5_full104_masking_gpu_preflight_20260917.ps1",
        "CONTROL_CALIBRATION_ONLY__FORBIDDEN_FOR_TERMINAL_MASKING_QUALIFICATION_V1",
        "AUTHENTICATED_FULL104_LEVEL4_BLOCK_STREAM_V1",
        "AddressUniverseLadderAuthorityV1",
        "no caller-entered role SHA",
        "stop at the first fully qualifying rung",
    )
    for phrase in required_phrases:
        assert phrase in text, phrase


def test_current_command_authority_requires_exact_replay_status_not_exit_code_alone():
    text = COMMANDS.read_text(encoding="utf-8")
    assert "REPLAY_REQUIRED_BEFORE_CAPACITY_VERDICT" in text
    assert "REPLAY_REQUIRED_BEFORE_NONLINEAR_CAPACITY_VERDICT" in text
    assert 'STOP: target-panel Run B failed' in text
    assert 'STOP: nonlinear Run B failed' in text

def test_current_pipeline_historical_ingress_is_narrow_explicit_allowlist():
    historical_root = "analysis/v5_masking_successor_spike_20260917"
    allowed = {
        "build_full104_masking_parameters_authority_v2_20260918.py",
        "build_full104_nonlinear_capacity_model_authority_v1_20260918.py",
    }
    observed = set()
    forbidden_tokens = (
        "stage81a3",
        "corrected_real_train",
        "v2_full104_corrected_ladder_results",
        "FULL104_MASKING_PROSPECTIVE_FREEZE_STATUS_20260917",
        "QUALIFICATION_800_V1",
        "QUALIFICATION_6000_V1",
        "PLACEHOLDER_SUPPORT_ESTIMABILITY_AUTHORITY",
    )
    for script in CURRENT_PIPELINE_SCRIPTS:
        source = script.read_text(encoding="utf-8")
        if historical_root in source:
            observed.add(script.name)
        for token in forbidden_tokens:
            assert token not in source, f"{script}: forbidden historical/placeholder ingress token {token}"
    assert observed == allowed, (
        "current pipeline historical ingress changed; historical evidence may motivate only, "
        f"and intentional reauthorization is restricted to {sorted(allowed)}; observed {sorted(observed)}"
    )



def test_superseded_20260917_freeze_builder_is_a_fail_closed_tombstone():
    path = Path("scripts/agent/build_full104_masking_freeze_status_20260917.py")
    source = path.read_text(encoding="utf-8")
    assert "SUPERSEDED_FAIL_CLOSED" in source
    assert "MaskingBurdenLadderAuthorityV1" not in source
    assert "PLACEHOLDER_SUPPORT_ESTIMABILITY_AUTHORITY" not in source
    assert "build_full104_masking_run_contract_v4_20260918.py" in source
