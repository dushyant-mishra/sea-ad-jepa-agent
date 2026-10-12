from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v5"))

import td_corrected_replay_adapter_contract_v1 as A  # noqa: E402


def valid_manifest():
    return {
        "schema": A.SCHEMA,
        "sample_label": "A_NATURAL_MIXTURE",
        "row_count": 25000,
        "global_row_start": 0,
        "global_row_end": 24999,
        "source_counts": {"HVS": 1129, "NPH52": 1310, "SEA_AD": 22561},
        "replay_address_count": 9216,
        "metadata_fields": list(A.REQUIRED_METADATA_FIELDS),
        "executor_sha256": dict(A.EXECUTOR_SHA256),
        "td59_original_executor_sha256": A.TD59_ORIGINAL_EXECUTOR_SHA256,
        "td59_original_executor_bytes_recovered": False,
        "historical_fixture_equivalence": {stage: "PASS" for stage in A.STAGES},
        "g7_terminal": "PASS_TD_G7_S174_EXACT_OVERLAP",
        "g7_externally_accepted": True,
        **dict(A.NO_AUTHORITY),
    }


def test_valid_contract_is_ready_only_for_separate_owner_authorization():
    out = A.validate_and_classify(valid_manifest())
    assert out["terminal"] == "READY_FOR_SEPARATE_OWNER_CORRECTED_REPLAY_AUTHORIZATION__NO_REPLAY_AUTHORITY"
    assert out["adapter_contract_valid"] is True
    assert out["replay_package_ready_for_owner_authorization"] is True
    for key in A.NO_AUTHORITY:
        assert out[key] is False


def test_g7_must_be_pass_and_externally_accepted():
    for terminal, accepted in [
        ("PASS_TD_G7_S174_EXACT_OVERLAP", False),
        ("NOT_ESTIMABLE_NO_NATURAL_S174_CELL_OVERLAP", True),
        ("STOP_TD_G7_S174_CROSSCHECK_MISMATCH", True),
    ]:
        manifest = valid_manifest()
        manifest["g7_terminal"] = terminal
        manifest["g7_externally_accepted"] = accepted
        out = A.validate_and_classify(manifest)
        assert out["terminal"] == "BLOCKED_G7_NOT_EXTERNALLY_ACCEPTED__NO_REPLAY_AUTHORITY"
        assert out["replay_package_ready_for_owner_authorization"] is False


def test_all_stage_historical_fixture_equivalence_must_pass():
    manifest = valid_manifest()
    manifest["historical_fixture_equivalence"]["TD57C"] = "PENDING"
    out = A.validate_and_classify(manifest)
    assert out["terminal"] == "BLOCKED_ADAPTER_EQUIVALENCE_INCOMPLETE__NO_REPLAY_AUTHORITY"
    assert out["replay_package_ready_for_owner_authorization"] is False


def test_executor_substitution_is_rejected():
    manifest = valid_manifest()
    manifest["executor_sha256"]["TD57C"] = "0" * 64
    with pytest.raises(A.ReplayAdapterContractError, match="executor_sha256"):
        A.validate_and_classify(manifest)


def test_td59_original_executor_must_remain_unrecovered():
    manifest = valid_manifest()
    manifest["td59_original_executor_bytes_recovered"] = True
    with pytest.raises(A.ReplayAdapterContractError, match="TD59 original executor"):
        A.validate_and_classify(manifest)


def test_contract_refuses_forbidden_or_missing_metadata_fields():
    manifest = valid_manifest()
    manifest["metadata_fields"].append("pathology")
    with pytest.raises(A.ReplayAdapterContractError, match="metadata_fields"):
        A.validate_and_classify(manifest)

    manifest = valid_manifest()
    manifest["metadata_fields"].remove("donor_id")
    with pytest.raises(A.ReplayAdapterContractError, match="metadata_fields"):
        A.validate_and_classify(manifest)


def test_authority_flags_must_remain_false_even_in_ready_state():
    manifest = valid_manifest()
    manifest["training_authorized"] = True
    with pytest.raises(A.ReplayAdapterContractError, match="authority"):
        A.validate_and_classify(manifest)
