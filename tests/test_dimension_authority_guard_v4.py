import pytest

from sea_ad_jepa.v5.dimension_authority_guard_v3 import DimensionAuthorityGuardV3
from sea_ad_jepa.v5.dimension_authority_guard_v4 import DimensionAuthorityV4
from sea_ad_jepa.v5.prospective_precision_authority_v1 import FROZEN_PRECISION_AUTHORITY_SHA256


def receipt():
    g = DimensionAuthorityGuardV3(metadata_sha256="a" * 64)
    return {
        "expression_binding_terminal": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "metadata_sqlite_sha256": "a" * 64,
        "block_manifest_sha256": g.block_manifest_sha256,
        "materialization_contract_sha256": g.materialization_contract_sha256,
        "materialization_audit_sha256": g.materialization_audit_sha256,
        "cells": 4_553_407, "donors": 104, "operators": 42, "matrices": 42,
        "blocks": 8_915, "addresses": 41_238,
        "cross_ledger_identity_mismatches": 0, "cross_ledger_missing_cells": 0,
        "test_fixture_mode": False, "synthetic_data_used": False,
        "pathology_used": False, "checkpoint_outcomes_used": False,
        "population_mode": "FULL_READER_FIT_STREAM",
        "estimand": "EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR",
        "null_geometry": "FULL_REFIT_EVERY_REPLICATE",
        "sampled_stratum_cap": None,
        "precision_authority_sha256": FROZEN_PRECISION_AUTHORITY_SHA256,
        "precision_authority_terminal": "PASS_V5_PROSPECTIVE_PRECISION_AUTHORITY_V1",
        "precision_authority_frozen_before_dimension_outcomes": True,
        "D_shared": 96, "D_private": 64, "D_total": 160, "D_obs": 32,
    }


def authority(closure="b" * 64, frozen=True, precision=FROZEN_PRECISION_AUTHORITY_SHA256):
    return DimensionAuthorityV4(
        authority_id="dimension-v4",
        expression_closure_artifact_sha256=closure,
        guard_v3=DimensionAuthorityGuardV3(metadata_sha256="a" * 64),
        authority_frozen_before_optimizer_start=frozen,
        precision_authority_sha256=precision,
    )


def test_dimension_report_binds_exact_full104_and_precision_artifacts():
    out = authority().validate(receipt())
    assert out["expression_closure_artifact_sha256"] == "b" * 64
    assert out["precision_authority_sha256"] == FROZEN_PRECISION_AUTHORITY_SHA256
    assert out["D_total"] == out["D_shared"] + out["D_private"]
    assert out["training_authorized"] is False


def test_missing_or_substituted_precision_parent_stops():
    r = receipt(); del r["precision_authority_sha256"]
    with pytest.raises(RuntimeError, match="PRECISION_AUTHORITY_MISMATCH"):
        authority().validate(r)

    with pytest.raises(RuntimeError, match="PRECISION_AUTHORITY_SUBSTITUTION"):
        authority(precision="0" * 64).validate(receipt())


def test_precision_must_have_been_frozen_before_dimension_outcomes():
    r = receipt(); r["precision_authority_frozen_before_dimension_outcomes"] = False
    with pytest.raises(RuntimeError, match="NOT_PROSPECTIVE"):
        authority().validate(r)


def test_invalid_full104_receipt_still_stops_through_v3():
    r = receipt(); r["synthetic_data_used"] = True
    with pytest.raises(RuntimeError, match="SYNTHETIC"):
        authority().validate(r)


def test_closure_artifact_identity_must_be_sha256():
    with pytest.raises(ValueError, match="SHA-256"):
        authority("not-a-sha").validate(receipt())


def test_dimension_authority_must_precede_optimizer():
    with pytest.raises(ValueError, match="frozen before optimizer start"):
        authority(frozen=False).validate(receipt())
