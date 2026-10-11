from pathlib import Path
import importlib.util
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "src" / "sea_ad_jepa" / "v4" / "foundation_current_transfer_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("foundation_current_transfer_v1", MODULE)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_group_heldout_nearest_centroid_excludes_held_group_and_recovers_classes():
    mod = load_module()
    x = np.array([
        [-3.0, 0.0], [-2.5, 0.1], [3.0, 0.0], [2.5, -0.1],
        [-3.1, 0.2], [-2.6, -0.2], [3.1, 0.2], [2.6, -0.2],
    ])
    y = np.array(["A", "A", "B", "B", "A", "A", "B", "B"])
    groups = np.array(["g1", "g1", "g1", "g1", "g2", "g2", "g2", "g2"])
    rec = mod.group_heldout_nearest_centroid(x, y, groups)
    assert rec["n_scored"] == 8
    assert rec["balanced_accuracy"] == 1.0
    assert rec["accuracy"] == 1.0


def test_conditional_nuisance_decode_retains_nuisance_after_biology_residualization():
    mod = load_module()
    biology = np.array(["A", "A", "B", "B"] * 4)
    nuisance = np.array(["X", "Y", "X", "Y"] * 4)
    groups = np.array(["g1"] * 4 + ["g2"] * 4 + ["g3"] * 4 + ["g4"] * 4)
    biology_effect = np.where(biology == "A", -4.0, 4.0)
    nuisance_effect = np.where(nuisance == "X", -2.0, 2.0)
    x = np.column_stack([biology_effect, nuisance_effect, nuisance_effect * 0.5])
    rec = mod.conditional_nuisance_decode(x, biology, nuisance, groups)
    assert rec["n_scored"] == 16
    assert rec["balanced_accuracy"] == 1.0
    assert rec["accuracy"] == 1.0


def test_identifiability_summary_keeps_unavailable_matrices_out_of_claims():
    mod = load_module()
    rows = [
        {"source": "HVS", "broad_label_identifiability": "AVAILABLE"},
        {"source": "HVS", "broad_label_identifiability": "AVAILABLE"},
        {"source": "NPH52", "broad_label_identifiability": "UNAVAILABLE"},
    ]
    rec = mod.matrix_identifiability_summary(rows)
    assert rec["matrices_total"] == 3
    assert rec["available"] == 2
    assert rec["unavailable"] == 1
    assert rec["by_source"]["NPH52"]["available"] == 0


def test_adjudicator_is_fail_closed_for_bounded_diagnostic():
    mod = load_module()
    rec = mod.adjudicate_bounded_current_diagnostic(
        donor_balanced_accuracy=0.80,
        matrix_balanced_accuracy=0.80,
        conditional_nuisance_balanced_accuracy=0.50,
    )
    assert rec["representation_freeze_authorized"] is False
    assert rec["training_authorized"] is False
    assert rec["factorial_execution_authorized"] is False
    assert rec["status"] == "BOUNDED_DIAGNOSTIC_ONLY__NO_PRODUCTION_AUTHORITY"
