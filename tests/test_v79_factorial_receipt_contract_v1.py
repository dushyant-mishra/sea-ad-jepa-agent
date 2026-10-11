import json
from pathlib import Path

import pytest

from scripts.v79.build_v79_factorial_worlds import validate_arm_manifest
from scripts.v79.run_v79_factorial_tournament import (
    MAX_RECEIPT_JSON_BYTES,
    _atomic_json,
    make_receipt,
    validate_receipt_payload,
)
from tests.test_v79_factorial_gate_v1 import good_contract, manifest_dict


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
