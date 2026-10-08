import csv
import importlib.util
from pathlib import Path

import numpy as np
import pytest


ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/v4/derive_contextual_target_f1_hc3_nuisance_design_freeze_v1.py"
VALIDATOR = ROOT / "scripts/v4/validate_contextual_target_f1_hc3_nuisance_design_freeze_v1.py"
FINALIZER = ROOT / "scripts/v4/finalize_contextual_target_f1_hc3_nuisance_design_freeze_v1.py"
FRONTIER = ROOT / "outputs/contextual_teacher_target_v1_f1_hc3_replication_frontier_complete_20260902/F1_HC3_REPLICATION_FRONTIER_COMPLETE.csv"


def load_module():
    spec = importlib.util.spec_from_file_location("freeze15b", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_validator():
    spec = importlib.util.spec_from_file_location("validate15b", VALIDATOR)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_finalizer():
    spec = importlib.util.spec_from_file_location("finalize15b", FINALIZER)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_current_frontier_has_one_universal_componentwise_maximum():
    # Catches selector reintroduction of inadmissible NPH or nonreplicated HVS prefixes.
    module = load_module()
    with FRONTIER.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    audit = module.select_unique_componentwise_maximum(rows)
    assert audit["admissible_count"] == 30
    assert audit["maximal_triples"] == [(5, 0, 4)]
    assert audit["universal_maximum_triples"] == [(5, 0, 4)]
    assert audit["selected_triple"] == (5, 0, 4)


def test_incomparable_maxima_fail_closed_without_tiebreak():
    # Catches addition of leverage, variance, or lexical tie-breaking.
    module = load_module()
    rows = [
        {"r_HVS": "1", "r_NPH52": "0", "r_SEAAD": "0", "donor_replicated_hc3_admissible": "True"},
        {"r_HVS": "0", "r_NPH52": "0", "r_SEAAD": "1", "donor_replicated_hc3_admissible": "True"},
    ]
    with pytest.raises(RuntimeError, match="STOP_F1_HC3_15B_SELECTION_UNRESOLVED"):
        module.select_unique_componentwise_maximum(rows)


def test_inadmissible_dominating_row_cannot_enter_selection():
    # Catches filtering after, instead of before, the dominance calculation.
    module = load_module()
    rows = [
        {"r_HVS": "1", "r_NPH52": "0", "r_SEAAD": "1", "donor_replicated_hc3_admissible": "True"},
        {"r_HVS": "6", "r_NPH52": "1", "r_SEAAD": "4", "donor_replicated_hc3_admissible": "False"},
    ]
    assert module.select_unique_componentwise_maximum(rows)["selected_triple"] == (1, 0, 1)


def test_hc3_engine_is_invariant_to_invertible_optional_reparameterization():
    # Catches basis-dependent hat geometry or covariance implementation.
    module = load_module()
    rng = np.random.default_rng(1502)
    base = np.column_stack((np.ones(32), rng.normal(size=(32, 3))))
    optional = rng.normal(size=(32, 2))
    y = rng.normal(size=32)
    transform = np.array([[2.0, 0.3], [-0.4, 1.5]], dtype=np.float64)
    first = module.hc3_fit(np.column_stack((base, optional)), y)
    second = module.hc3_fit(np.column_stack((base, optional @ transform)), y)
    assert np.array_equal(first["leverage"], second["leverage"]) or np.allclose(first["leverage"], second["leverage"], rtol=0, atol=1e-13)
    assert np.allclose(first["fitted"], second["fitted"], rtol=0, atol=1e-12)


def test_known_donor_indispensable_direction_fails_hc3_gate():
    # Catches leverage clamping or deletion of a singleton donor direction.
    module = load_module()
    x = np.column_stack((np.ones(12), np.arange(12, dtype=np.float64), np.eye(12)[:, 0]))
    geometry = module.selected_geometry(x, np.array([f"D{i}" for i in range(12)]), np.array(["HVS"] * 12))
    assert geometry["hc3_estimable"] is False
    assert geometry["loo_rank_stable"] is False
    assert "D0" in geometry["loo_critical_donors"]


def test_independent_selector_rejects_incomparable_frontier():
    # Catches an independent validator that merely trusts the production selection.
    module = load_validator()
    rows = [
        {"r_HVS": "2", "r_NPH52": "0", "r_SEAAD": "0", "donor_replicated_hc3_admissible": "True"},
        {"r_HVS": "0", "r_NPH52": "0", "r_SEAAD": "2", "donor_replicated_hc3_admissible": "True"},
    ]
    with pytest.raises(RuntimeError, match="STOP_F1_HC3_15B_SELECTION_UNRESOLVED"):
        module.independent_selection(rows)


def test_independent_reconstruction_consumes_selection_instead_of_hardcoding_it():
    # Catches a validator that bakes the observed winning triple into reconstruction.
    module = load_validator()
    x, identities, _, _, _ = module.rebuild((0, 0, 0))
    assert x.shape == (104, 7)
    assert len(identities) == 7


def test_finalizer_requires_all_14_outputs_and_package_relative_snapshots():
    # Catches incomplete packages and staging-absolute snapshot paths.
    module = load_finalizer()
    assert len(module.REQUIRED_ARTIFACTS) == 14
    assert "F1_HC3_15B_MANIFEST.csv" in module.REQUIRED_ARTIFACTS
    assert module.snapshot_manifest_path("derive.py") == "source_snapshot/derive.py"
