import json
from pathlib import Path

import pytest

from scripts.v79.build_v79_factorial_worlds import manifest_hash, validate_arm_manifest
from scripts.v79.run_v79_factorial_tournament import (
    FROZEN_V78_BASE_SHA,
    MAX_RECEIPT_JSON_BYTES,
    _atomic_json,
    make_receipt,
    validate_receipt_payload,
)


def manifest_dict():
    return {
        "arm_names": ["H0", "H1", "H2", "H3", "C_OBS", "C_BIO"],
        "biology_seed": 101,
        "observation_seed": 202,
        "counterfactual_biology_seed": 303,
        "crossing_seed": 404,
        "cell_count": 2400,
        "donor_count": 12,
        "balancing_rule": "BALANCED_WITHIN_BROAD_CLASS",
        "h2_realization_family": "independent_thinning",
        "h3_realization_family": "independent_thinning",
        "endpoint_version": "V79_FACTORIAL_ENDPOINTS_V1",
        "training_authorized": False,
    }


def good_contract():
    m = validate_arm_manifest(manifest_dict())
    return {
        "v78_base_sha": FROZEN_V78_BASE_SHA,
        "authority_hashes": {
            "biology": {"expected": "bio123", "actual": "bio123"},
            "observation": {"expected": "obs123", "actual": "obs123"},
        },
        "preregistered_manifest_hash": manifest_hash(m),
        "test_or_morabito_accessed": False,
        "pathology_accessed": False,
        "target_discovery_modified": False,
        "post_outcome_arm_mutation": False,
        "training_authorized": False,
    }


def test_receipt_rejects_internal_correlation_matrix_payload():
    with pytest.raises(ValueError, match="forbidden receipt key"):
        validate_receipt_payload({"L0": {"corr": [[1.0, 0.2], [0.2, 1.0]]}})


def test_receipt_rejects_internal_gene_address_identity_payload():
    with pytest.raises(ValueError, match="forbidden receipt key"):
        make_receipt(
            "SCORE",
            good_contract(),
            validate_arm_manifest(manifest_dict()),
            {"selection": {"selected_universe_ids": [1, 7, 11]}},
        )


def test_receipt_rejects_payload_over_hard_json_bound():
    huge = {"summary": "x" * (MAX_RECEIPT_JSON_BYTES + 1)}
    with pytest.raises(ValueError, match="receipt payload exceeds"):
        validate_receipt_payload(huge)


def test_atomic_json_writes_complete_bounded_receipt_without_temp_files(tmp_path: Path):
    out = tmp_path / "receipt.json"
    obj = {"schema": "V79_TEST", "payload": {"summary": [1, 2, 3]}}
    _atomic_json(out, obj)
    assert json.loads(out.read_text()) == obj
    assert [p for p in tmp_path.iterdir() if p.name != out.name] == []
