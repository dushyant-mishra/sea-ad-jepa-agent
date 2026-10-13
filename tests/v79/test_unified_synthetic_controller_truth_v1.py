from __future__ import annotations
import inspect
from scripts.v79.unified_synthetic_integration_v1 import PERTURBATION_ARM_SEMANTICS, UnifiedBiologyConfig, build_unified_biology
from scripts.v79.unified_synthetic_fit_view_v1 import UnifiedObservationConfig, observe_unified_world, serialize_fit_view
from scripts.v79.unified_synthetic_controller_truth_v1 import derive_controller_truth, controller_truth_sha256, assert_fit_view_is_controller_free

def test_controller_truth_is_deterministic_and_posthoc():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=360,n_genes=40,n_donors=12),seed=5)
    a=derive_controller_truth(w); b=derive_controller_truth(w)
    assert controller_truth_sha256(a)==controller_truth_sha256(b)
    assert {"C1","C2","C3","C4","C5","C6"} <= set(a.candidate_mapping)

def test_controller_truth_binds_exact_perturbation_arm_semantics():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=360,n_genes=40,n_donors=12),seed=5)
    truth=derive_controller_truth(w)
    assert truth.counterfactual_truth["perturbation_arm_semantics"] == PERTURBATION_ARM_SEMANTICS
    assert truth.counterfactual_truth["perturbation_arm_semantics"]["2"] == "MATCHED_PERTURB_NULL"

def test_controller_truth_does_not_preassign_recoverability_outcomes():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=360,n_genes=40,n_donors=12),seed=5)
    truth=derive_controller_truth(w)
    assert set(truth.recoverability) == {"C1","C2","C3","C4","C5","C6"}
    assert set(truth.recoverability.values()) == {"UNASSESSED_PENDING_RECOVERABILITY_QUALIFICATION"}

def test_fit_view_firewall_rejects_injected_controller_fields():
    w=build_unified_biology(UnifiedBiologyConfig(n_cells=240,n_genes=32,n_donors=12),seed=8)
    payload=serialize_fit_view(observe_unified_world(w,UnifiedObservationConfig(),seed=3))
    assert_fit_view_is_controller_free(payload)
    payload["candidate_mapping"]={"C1":1}
    try:
        assert_fit_view_is_controller_free(payload)
    except ValueError:
        pass
    else:
        raise AssertionError("controller leak not rejected")

def test_fit_view_module_does_not_import_controller_module():
    import scripts.v79.unified_synthetic_fit_view_v1 as fit
    src=inspect.getsource(fit)
    assert "unified_synthetic_controller_truth_v1" not in src
