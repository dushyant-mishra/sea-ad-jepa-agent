from __future__ import annotations

import ast
from pathlib import Path
import sys

import numpy as np
import pytest
import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from sea_ad_jepa.v4.foundation_observation import (
    ConditioningMetadata,
    FoundationObservation,
    ProvenanceMetadata,
    audit_metadata_schema,
)


CONFIG = ROOT / "configs/v4/stage81a3_foundation_heterogeneity_reality_audit.yaml"
SCRIPT = ROOT / "scripts/v4/stage81a3_foundation_heterogeneity_reality_audit.py"


def observation() -> FoundationObservation:
    return FoundationObservation(
        expression=np.asarray([0.0, 1.0, 0.0], dtype=np.float32),
        gene_ids=np.asarray([0, 1, 2]),
        measurement_mask=np.asarray([True, True, False]),
        provenance=ProvenanceMetadata("dataset", "matrix", "donor"),
        conditioning=ConditioningMetadata(assay_type="nucleus"),
    )


def test_observation_validates() -> None:
    observation().validate()


def test_measured_zero_remains_measured() -> None:
    assert observation().measured_zero_mask.tolist() == [True, False, False]


def test_structural_unmeasurement_is_explicit() -> None:
    assert observation().structural_unmeasured_mask.tolist() == [False, False, True]


def test_unmeasured_nonzero_placeholder_rejected() -> None:
    item = observation()
    item.expression[2] = 1.0
    with pytest.raises(ValueError, match="unmeasured"):
        item.validate()


def test_provenance_is_separate_from_model_inputs() -> None:
    item = observation()
    assert not {"dataset_id", "matrix_id", "donor_id"} & set(item.model_inputs())
    assert {"dataset_id", "matrix_id", "donor_id"} <= set(item.provenance_record())


def test_schema_audit_never_returns_forbidden_values() -> None:
    result = audit_metadata_schema(["donor", "Braak", "unused"], {"donor": "donor"}, {"Braak"})
    assert result["forbidden_fields_present_values_not_read"] == ["Braak"]
    assert "forbidden_field_values" not in result


def test_config_is_pathology_blind_train_only() -> None:
    config = yaml.safe_load(CONFIG.read_text(encoding="utf-8"))
    assert config["governance"]["pathology_blind"] is True
    assert config["governance"]["train_expression_only"] is True
    assert config["governance"]["development_expression_forbidden"] is True
    assert config["governance"]["sealed_expression_forbidden"] is True


def test_identifiers_are_not_conditioning_fields() -> None:
    fields = set(ConditioningMetadata.__dataclass_fields__)
    assert not {"dataset_id", "matrix_id", "donor_id"} & fields


def test_script_has_no_optimizer_or_backward_call() -> None:
    tree = ast.parse(SCRIPT.read_text(encoding="utf-8"))
    calls = [node.func.attr for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)]
    assert "backward" not in calls
    assert "step" not in calls


def test_script_does_not_open_pathology_sidecar() -> None:
    text = SCRIPT.read_text(encoding="utf-8").lower()
    assert "nph52_pathology_sidecar" not in text
