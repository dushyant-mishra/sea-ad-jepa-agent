import copy
import pytest

from sea_ad_jepa.v5 import full104_dimension_interface_v1 as m


def receipt(*, fixture=False):
    return {
        "schema": "JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4",
        "status": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "block_manifest_sha256": m.EXPECTED_BLOCK_MANIFEST_SHA256,
        "materialization_contract_sha256": m.EXPECTED_CONTRACT_SHA256,
        "materialization_audit_sha256": m.EXPECTED_AUDIT_SHA256,
        "metadata_sqlite_sha256": m.EXPECTED_METADATA_SQLITE_SHA256,
        "selection_sha256": m.EXPECTED_SELECTION_SHA256,
        "selection_manifest_sha256": m.EXPECTED_SELECTION_MANIFEST_SHA256,
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "matrices": 42,
        "blocks": 8_915,
        "addresses": 41_238,
        "cross_ledger_identity_mismatches": 0,
        "cross_ledger_missing_cells": 0,
        "test_fixture_mode": fixture,
        "synthetic_data_used": fixture,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }


def test_real_full104_receipt_projects_exact_dimension_authority_fields():
    out = m.project_full104_receipt_for_dimension_authority(receipt())
    assert out["expression_binding_terminal"] == "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE"
    assert out["population_mode"] == "FULL_READER_FIT_STREAM"
    assert out["estimand"] == "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR"
    assert out["null_geometry"] == "FULL_REFIT_EVERY_REPLICATE"
    assert out["sampled_stratum_cap"] is None
    assert out["test_fixture_mode"] is False
    assert out["synthetic_data_used"] is False


def test_wrong_metadata_sqlite_digest_cannot_enter_dimension_authority():
    r = receipt()
    r["metadata_sqlite_sha256"] = "b" * 64
    with pytest.raises(RuntimeError, match="METADATA_SQLITE_SHA256_MISMATCH"):
        m.project_full104_receipt_for_dimension_authority(r)


def test_fixture_receipt_cannot_project_to_production_dimension_authority():
    with pytest.raises(RuntimeError, match="FIXTURE_OR_SYNTHETIC"):
        m.project_full104_receipt_for_dimension_authority(receipt(fixture=True))


def test_wrong_full104_terminal_cannot_project():
    r = receipt()
    r["status"] = "PASS_SOMETHING_ELSE"
    with pytest.raises(RuntimeError, match="TERMINAL"):
        m.project_full104_receipt_for_dimension_authority(r)


def test_sealed_dimension_input_binds_exact_full104_parent_bytes():
    envelope = m.seal_full104_dimension_input(receipt())
    assert envelope["schema"] == "JEPA_V5_FULL104_DIMENSION_INPUT_ARTIFACT_V1"
    assert len(envelope["artifact_sha256"]) == 64
    out = m.validate_full104_dimension_input(envelope)
    assert out["population_mode"] == "FULL_READER_FIT_STREAM"
    assert out["training_authorized"] is False


def test_sealed_dimension_input_rejects_parent_and_payload_tamper():
    envelope = m.seal_full104_dimension_input(receipt())
    bad_parent = copy.deepcopy(envelope)
    bad_parent["parent_sha256"]["metadata_sqlite"] = "b" * 64
    with pytest.raises(RuntimeError, match="PARENT_MISMATCH|DIGEST_MISMATCH"):
        m.validate_full104_dimension_input(bad_parent)

    bad_payload = copy.deepcopy(envelope)
    bad_payload["payload"]["cells"] = 4_553_406
    with pytest.raises(RuntimeError, match="DIGEST_MISMATCH"):
        m.validate_full104_dimension_input(bad_payload)
