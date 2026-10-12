from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import v79_rare_biology_input_authority as A  # noqa: E402

AUTH = ROOT / "results" / "v79" / "rare_biology_integration" / "V79_RARE_BIOLOGY_INPUT_AUTHORITY_V1.json"


def load():
    return json.loads(AUTH.read_text(encoding="utf-8"))


def test_frozen_authority_validates_and_keeps_training_off():
    doc = load()
    A.validate(doc)
    assert doc["schema"] == "v79-rare-biology-input-authority-v1"
    assert doc["training_authorized"] is False
    assert doc["q00_q11_mutation_authorized"] is False
    assert doc["pathology_used"] is False


def test_missing_required_hash_fails_closed():
    doc = load()
    broken = copy.deepcopy(doc)
    broken["assets"]["v6r5a_program_weights"]["sha256"] = ""
    with pytest.raises(ValueError, match="sha256"):
        A.validate(broken)


def test_morabito_cannot_be_promoted_to_same_cell_or_target_selection():
    doc = load()
    broken = copy.deepcopy(doc)
    broken["assets"]["gse174367_morabito"]["pairing"] = "same_nucleus"
    with pytest.raises(ValueError, match="Morabito"):
        A.validate(broken)

    broken = copy.deepcopy(doc)
    broken["assets"]["gse174367_morabito"]["allowed_roles"].append("target_selection")
    with pytest.raises(ValueError, match="target_selection"):
        A.validate(broken)


def test_q00_q11_can_only_be_reused_as_measurement_layer():
    doc = load()
    assert doc["assets"]["v79_q00_q11"]["allowed_roles"] == ["measurement_statistical_qualification"]
    broken = copy.deepcopy(doc)
    broken["assets"]["v79_q00_q11"]["allowed_roles"].append("rare_biology_truth")
    with pytest.raises(ValueError, match="Q00-Q11"):
        A.validate(broken)


def test_regulatory_assets_cannot_claim_causal_truth():
    doc = load()
    broken = copy.deepcopy(doc)
    broken["assets"]["stage75_79_regulatory"]["allowed_roles"].append("causal_grn_truth")
    with pytest.raises(ValueError, match="causal"):
        A.validate(broken)
