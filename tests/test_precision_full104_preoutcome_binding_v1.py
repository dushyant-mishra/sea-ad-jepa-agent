import json
from pathlib import Path

import pytest

from sea_ad_jepa.v5 import full104_dimension_interface_v1 as full104
from sea_ad_jepa.v5.prospective_precision_authority_v1 import (
    FROZEN_PRECISION_AUTHORITY_SHA256,
    PrecisionAuthorityStop,
    bind_full104_precision_execution_plan_v1,
)

AUTH_PATH = Path(__file__).resolve().parents[1] / "docs" / "agent" / "V5_PROSPECTIVE_DIMENSION_PRECISION_AUTHORITY_V1.json"
DIMENSION_INTERFACE_SHA256 = "dcc8c95ef8ed4b8106ee3b8f1536aa6fac6b338cafd3057b9f567a5336c673df"


def receipt():
    return {
        "schema": "JEPA_V5_FULL104_EXPRESSION_BLOCK_BINDING_V4",
        "status": "PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE",
        "block_manifest_sha256": full104.EXPECTED_BLOCK_MANIFEST_SHA256,
        "materialization_contract_sha256": full104.EXPECTED_CONTRACT_SHA256,
        "materialization_audit_sha256": full104.EXPECTED_AUDIT_SHA256,
        "metadata_sqlite_sha256": full104.EXPECTED_METADATA_SQLITE_SHA256,
        "selection_sha256": full104.EXPECTED_SELECTION_SHA256,
        "selection_manifest_sha256": full104.EXPECTED_SELECTION_MANIFEST_SHA256,
        "cells": 4_553_407,
        "donors": 104,
        "operators": 42,
        "matrices": 42,
        "blocks": 8_915,
        "addresses": 41_238,
        "cross_ledger_identity_mismatches": 0,
        "cross_ledger_missing_cells": 0,
        "test_fixture_mode": False,
        "synthetic_data_used": False,
        "pathology_used": False,
        "checkpoint_outcomes_used": False,
        "training_authorized": False,
    }


def test_preoutcome_bridge_binds_exact_full104_artifact_to_frozen_precision_parent():
    authority = json.loads(AUTH_PATH.read_bytes())
    envelope = full104.seal_full104_dimension_input(receipt())
    plan = bind_full104_precision_execution_plan_v1(
        authority,
        authority_sha256=FROZEN_PRECISION_AUTHORITY_SHA256,
        full104_dimension_envelope=envelope,
        full104_artifact_sha256=envelope["artifact_sha256"],
        dimension_interface_sha256=DIMENSION_INTERFACE_SHA256,
    )
    assert plan["schema"] == "JEPA_V5_FULL104_PRECISION_PREOUTCOME_BINDING_V1"
    assert plan["full104_dimension_input_artifact_sha256"] == envelope["artifact_sha256"]
    assert plan["precision_authority_sha256"] == FROZEN_PRECISION_AUTHORITY_SHA256
    assert plan["all_full104_parents_match_precision_authority"] is True
    assert plan["dimension_outcomes_authorized"] is True
    assert plan["training_authorized"] is False


def test_preoutcome_bridge_rejects_artifact_or_interface_substitution():
    authority = json.loads(AUTH_PATH.read_bytes())
    envelope = full104.seal_full104_dimension_input(receipt())
    with pytest.raises(PrecisionAuthorityStop, match="FULL104_ARTIFACT_SHA_MISMATCH"):
        bind_full104_precision_execution_plan_v1(
            authority,
            authority_sha256=FROZEN_PRECISION_AUTHORITY_SHA256,
            full104_dimension_envelope=envelope,
            full104_artifact_sha256="0" * 64,
            dimension_interface_sha256=DIMENSION_INTERFACE_SHA256,
        )
    with pytest.raises(PrecisionAuthorityStop, match="DIMENSION_INTERFACE_SHA_MISMATCH"):
        bind_full104_precision_execution_plan_v1(
            authority,
            authority_sha256=FROZEN_PRECISION_AUTHORITY_SHA256,
            full104_dimension_envelope=envelope,
            full104_artifact_sha256=envelope["artifact_sha256"],
            dimension_interface_sha256="0" * 64,
        )
