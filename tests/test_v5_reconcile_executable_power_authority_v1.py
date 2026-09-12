from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_executable_power_successor_authority_is_present():
    dependency_guard = ROOT / "src" / "sea_ad_jepa" / "v5" / "postqualification_dependency_guard_v2.py"
    phase_contract = ROOT / "src" / "sea_ad_jepa" / "v5" / "qualification_phase_contract_v3.py"
    assert dependency_guard.is_file(), "postqualification V2 executable-power dependency guard is missing"
    assert phase_contract.is_file(), "postqualification V3 phase contract is missing"

    guard_source = dependency_guard.read_text(encoding="utf-8")
    contract_source = phase_contract.read_text(encoding="utf-8")
    assert "validate_executable_power_receipt_v4" in guard_source
    assert "ACTUAL_FROZEN_GATE_EXECUTION" in guard_source
    assert "executable_power_calibration_required" in contract_source
    assert "legacy_v3_power_report_disallowed" in contract_source
