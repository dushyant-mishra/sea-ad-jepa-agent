from __future__ import annotations

import json
from pathlib import Path

from scripts.agent.validate_d1a_synthetic_contract_v2 import validate_contract

CONTRACT = Path("docs/agent/D1A_SYNTHETIC_ESTIMATION_ATLAS_CONTRACT_V2_20260907.json")


def _base() -> dict:
    return json.loads(CONTRACT.read_text(encoding="utf-8"))


def _assert_invalid(contract: dict, fragment: str) -> None:
    result = validate_contract(contract)
    assert result["terminal"] == "D1A_CONTRACT_INVALID"
    assert any(fragment in failure for failure in result["failures"]), result


def test_current_contract_is_valid_and_nonconfirmatory() -> None:
    result = validate_contract(_base())
    assert result["terminal"] == "D1A_CONTRACT_VALID"
    assert result["failures"] == []


def test_v2_is_bound_to_preserved_v1_preimplementation_freeze() -> None:
    contract = _base()
    contract["supersedes"]["package_root_sha256"] = "0" * 64
    _assert_invalid(contract, "V1 package-root binding mismatch")


def test_v2_requires_pre_outcome_chronology_statement() -> None:
    contract = _base()
    contract["supersedes"]["reason"] = "fixed after implementation"
    _assert_invalid(contract, "pre-outcome chronology statement missing")


def test_state_loading_table_cannot_be_removed() -> None:
    contract = _base()
    del contract["required_outputs"]["state_loading_table"]
    _assert_invalid(contract, "required output missing: state_loading_table")


def test_operator_table_cannot_be_removed() -> None:
    contract = _base()
    del contract["required_outputs"]["operator_table"]
    _assert_invalid(contract, "required output missing: operator_table")


def test_state_direction_must_cover_all_160_coordinates() -> None:
    contract = _base()
    contract["estimation"]["state_direction_identity"]["relationship_to_frozen_160d_basis"] = "top loadings only"
    _assert_invalid(contract, "160-D basis completeness rule missing")


def test_program_table_must_bind_direction_and_known_reference() -> None:
    contract = _base()
    contract["required_outputs"]["program_table"].remove("state_direction_sha256")
    _assert_invalid(contract, "V2 program output missing: state_direction_sha256")


def test_real_trained_teacher_mode_cannot_be_allowed() -> None:
    contract = _base()
    contract["governance"]["allowed_modes"].append("trained_teacher")
    _assert_invalid(contract, "allowed modes mismatch")


def test_protected_metadata_firewall_cannot_shrink() -> None:
    contract = _base()
    contract["inputs"]["metadata"]["forbidden_column_tokens"].remove("pathology")
    _assert_invalid(contract, "metadata forbidden-token firewall incomplete")


def test_metadata_cannot_enter_pca_fit() -> None:
    contract = _base()
    contract["decomposition"]["metadata_used_in_fit"] = True
    _assert_invalid(contract, "fit leakage flag must be false")


def test_molecular_values_cannot_define_pca_directions() -> None:
    contract = _base()
    contract["decomposition"]["molecular_values_used_in_fit"] = True
    _assert_invalid(contract, "fit leakage flag must be false")


def test_bootstrap_count_cannot_be_tuned_after_known_answer() -> None:
    contract = _base()
    contract["fixed_prototype_parameters"]["bootstrap_resamples"] = 512
    _assert_invalid(contract, "prototype parameter mismatch: bootstrap_resamples")


def test_tail_fraction_cannot_be_tuned_after_known_answer() -> None:
    contract = _base()
    contract["fixed_prototype_parameters"]["tail_fraction"] = 0.01
    _assert_invalid(contract, "prototype parameter mismatch: tail_fraction")


def test_measurement_support_definition_cannot_change() -> None:
    contract = _base()
    contract["estimation"]["measurement_support_score"] = "absolute correlation"
    _assert_invalid(contract, "measurement-support definition mismatch")


def test_missing_known_reference_cannot_be_called_maximally_novel() -> None:
    contract = _base()
    contract["estimation"]["novelty"]["when_no_reference"] = "1.0"
    _assert_invalid(contract, "novelty missing-reference rule mismatch")


def test_priority_formula_cannot_be_changed_to_ignore_measurement_support() -> None:
    contract = _base()
    contract["ranked_hypothesis_catalog"]["priority_score"] = (
        "explained_variance_ratio * axis_stability"
    )
    _assert_invalid(contract, "priority formula mismatch")


def test_no_confirmatory_threshold_can_be_introduced() -> None:
    contract = _base()
    contract["ranked_hypothesis_catalog"]["confirmatory_threshold"] = 0.5
    _assert_invalid(contract, "must not define a confirmatory threshold")


def test_final_real_d1_algorithm_cannot_be_smuggled_in() -> None:
    contract = _base()
    contract["real_d1_transition"]["this_contract_does_not_freeze_final_real_algorithm"] = False
    _assert_invalid(contract, "must not silently become final real-D1 algorithm")


def test_output_provenance_root_cannot_be_removed() -> None:
    contract = _base()
    contract["provenance"]["output_rows_must_carry_input_root"] = False
    _assert_invalid(contract, "output provenance-root requirement missing")


def test_terminal_cannot_be_promoted_to_pass() -> None:
    contract = _base()
    contract["terminal"] = "PASS_D1A"
    _assert_invalid(contract, "terminal")
