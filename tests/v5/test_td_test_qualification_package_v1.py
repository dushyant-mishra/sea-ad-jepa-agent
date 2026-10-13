from __future__ import annotations

import importlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "v5"
sys.path.insert(0, str(SCRIPTS))


def _complete_binding() -> dict:
    return {
        "schema": "JEPA_TD_EXTERNAL_SYNTHETIC_PACKAGE_BINDING_V1",
        "package_id": "external-relational-known-truth-v1",
        "package_sha256": "a" * 64,
        "fit_views": [
            {"challenge_id": "opaque-01", "sha256": "1" * 64},
            {"challenge_id": "opaque-02", "sha256": "2" * 64},
        ],
        "controller_truth_sha256": "b" * 64,
        "capabilities": [
            {
                "capability_id": "REL_FINE_RECURRENT_POSITIVE",
                "challenge_id": "opaque-01",
                "semantic_class": "POSITIVE_TRUTH",
            },
            {
                "capability_id": "REL_NULL_NEGATIVE",
                "challenge_id": "opaque-02",
                "semantic_class": "NEGATIVE_TRUTH",
            },
        ],
        "fit_view_fields": [
            "observations",
            "donor_id",
            "source",
            "operator",
            "support",
            "entity_id",
        ],
        "authority": {
            "synthetic_world_generation_authorized": False,
            "synthetic_world_regeneration_authorized": False,
            "qualification_model_fitting_authorized": False,
            "target_selection_authorized": False,
            "td60_authorized": False,
            "stage4_authorized": False,
            "training_authorized": False,
        },
    }


def test_external_package_validator_accepts_complete_read_only_binding():
    module_path = SCRIPTS / "td_test_qualification_package_v1.py"
    assert module_path.is_file(), "TD external-package validator has not been implemented yet"
    Q = importlib.import_module("td_test_qualification_package_v1")
    binding = _complete_binding()
    result = Q.validate_external_package_binding(
        binding,
        authenticated_package_sha256="a" * 64,
    )
    assert result.package_id == binding["package_id"]
    assert result.package_sha256 == "a" * 64
    assert result.fit_views == {"opaque-01": "1" * 64, "opaque-02": "2" * 64}
    assert set(result.capabilities) == {"REL_FINE_RECURRENT_POSITIVE", "REL_NULL_NEGATIVE"}
