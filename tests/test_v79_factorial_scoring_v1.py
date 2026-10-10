from types import SimpleNamespace
import numpy as np
import pytest
from scipy import sparse

from scripts.v79.v79_hierarchical_biology import generate_latent_biology
from scripts.v79.v79_observation_operator import observe_latent_biology
from scripts.v79.build_v79_factorial_worlds import WorldArm, FactorialWorlds, validate_arm_manifest
from scripts.v79.score_v79_factorial_worlds import (
    CANONICAL_THRESHOLD,
    SENSITIVITY_THRESHOLDS,
    score_world,
    score_factorial_tournament,
    compare_factorial_mechanisms,
)


def bio_authority():
    return {
        "class_frequencies": [0.5, 0.5], "substates_per_class": [2, 2],
        "substate_prevalence": [1.0, 1.0], "module_size_distribution": [5, 8],
        "n_modules_per_substate": 2, "n_continuous_factors": 2,
        "substate_effect_scale": 0.8, "continuous_factor_scale": 0.05,
        "donor_effect_scale": 0.04, "baseline_log_mean": -0.2, "baseline_log_sd": 0.2,
    }


def obs_authority(n_genes=64):
    return {
        "regime_ids": ["OBS_A", "OBS_B"],
        "structural_support": np.ones((2, n_genes), dtype=bool).tolist(),
        "capture_log_mean": [-0.2, -0.4], "capture_log_sd": [0.1, 0.1],
        "gene_propensity": np.ones(n_genes).tolist(),
        "realization_family": "independent_thinning", "molecule_scale": 4.0,
    }


def arm(n_cells=240, n_genes=64, n_donors=2):
    z = generate_latent_biology(bio_authority(), n_cells, n_genes, n_donors, seed=3)
    labels = np.resize(np.array(["OBS_A", "OBS_B"]), n_cells)
    x = observe_latent_biology(z, obs_authority(n_genes), labels, seed=4)
    return WorldArm("H3", "HIERARCHICAL", "EXPLICIT", z, x, x.latent_truth_hash, "independent_thinning")


class FakeLoc:
    CANONICAL_THRESHOLD = 0.30
    SENSITIVITY_THRESHOLDS = (0.10, 0.20, 0.30, 0.40)
    def __init__(self): self.calls = []
    def build_l0_l2(self, counts, universe, broad_class, n_hvg=3000, retain_stratum_corr=True):
        self.calls.append(("l0_l2", n_hvg, tuple(universe)))
        n = min(n_hvg, len(universe))
        det = (sparse.csr_matrix(counts)[:, universe] > 0).astype(float).toarray()[:, :n]
        C = np.corrcoef(det, rowvar=False) if n > 1 else np.ones((1, 1))
        C = np.nan_to_num(C); np.fill_diagonal(C, 1)
        return {
            "selection": {"selected_positions": np.arange(n), "n_selected": n, "selection_rule": "FROZEN"},
            "L0": {"corr": C, "summary": {"canonical_threshold": 0.3}},
            "L1": {"combined_corr": C, "summary": {"ok": True}},
            "L2": {"primary": {"combined_corr": C, "summary": {"ok": True}}},
        }
    def quantile_depth_bins(self, values, min_cells=100):
        n = len(values)
        if n < 200: return {"supported": False, "labels": None, "n_bins": None}
        labels = np.arange(n) % 2
        return {"supported": True, "labels": labels, "n_bins": 2}
    def localize_operator_source(self, det, base, operator, source, retain_stratum_corr=True):
        self.calls.append(("l3", len(det)))
        return {"combined_corr": np.eye(det.shape[1]), "summary": {"supported": True}, "n_supported_strata": 2}
    def localize_donor(self, det, base, donor, retain_stratum_corr=True):
        self.calls.append(("l4", len(det)))
        return {"combined_corr": np.eye(det.shape[1]), "summary": {"supported": True}, "n_supported_strata": len(np.unique(donor))}


def fake_legacy(counts, universe, cls, n_hvg=3000):
    return {"rule": "FROZEN_V77", "n_hvg": n_hvg, "cells": counts.shape[0]}


def test_continuity_delegates_frozen_selection_and_thresholds():
    loc = FakeLoc(); w = arm()
    out = score_world(w, np.arange(64), legacy_score_fn=fake_legacy, localization_backend=loc, n_hvg=32)
    assert out["legacy"]["rule"] == "FROZEN_V77"
    assert loc.calls[0] == ("l0_l2", 32, tuple(range(64)))
    assert CANONICAL_THRESHOLD == 0.30
    assert SENSITIVITY_THRESHOLDS == (0.10, 0.20, 0.30, 0.40)


def test_localization_reports_pooled_class_depth_source_and_donor_views():
    loc = FakeLoc(); w = arm(n_cells=400, n_donors=2)
    out = score_world(w, np.arange(64), legacy_score_fn=fake_legacy, localization_backend=loc, n_hvg=32)
    assert set(out["localization"]) >= {"L0", "L1", "L2", "L3", "L4"}
    assert out["localization"]["L4"]["n_supported_strata"] == 2
    assert out["localization"]["L4"]["synthetic_donor_view"] == "BALANCED_CROSS_SOURCE_BY_DESIGN"
    assert any(c[0] == "l3" for c in loc.calls)
    assert any(c[0] == "l4" for c in loc.calls)


def test_distributional_endpoints_include_class_and_observation_marginal_views():
    w = arm(n_cells=400, n_donors=2)
    out = score_world(w, np.arange(64), legacy_score_fn=fake_legacy, localization_backend=FakeLoc(), n_hvg=32)
    views = out["marginal_views"]
    assert set(views) == {"by_broad_class", "by_observation_regime"}
    assert sum(v["n_cells"] for v in views["by_broad_class"].values()) == 400
    assert sum(v["n_cells"] for v in views["by_observation_regime"].values()) == 400
    for groups in views.values():
        for rec in groups.values():
            assert rec["quantile_probs"] == [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]
            assert len(rec["library_size_quantiles"]) == 7
            assert len(rec["detected_feature_quantiles"]) == 7
            assert len(rec["positive_count_quantiles"]) == 7
            assert rec["positive_count_n"] > 0


def manifest():
    return validate_arm_manifest({
        "arm_names": ["H0","H1","H2","H3","C_OBS","C_BIO"],
        "biology_seed": 1, "observation_seed": 2, "counterfactual_biology_seed": 3,
        "crossing_seed": 4, "cell_count": 240, "donor_count": 2,
        "balancing_rule": "BALANCED_WITHIN_BROAD_CLASS",
        "h2_realization_family": "independent_thinning", "h3_realization_family": "independent_thinning",
        "endpoint_version": "V79_FACTORIAL_ENDPOINTS_V1", "training_authorized": False,
    })


def test_counterfactual_metrics_are_latent_and_observed_only_no_jepa():
    a = arm(); b = arm();
    xb = observe_latent_biology(a.latent, obs_authority(64), np.array(["OBS_B"]*240), seed=99)
    b = WorldArm("B", "HIERARCHICAL", "EXPLICIT", a.latent, xb, xb.latent_truth_hash, "independent_thinning")
    worlds = FactorialWorlds(manifest(), {"H0": a, "H1": a, "H2": a, "H3": a}, (a,b), (a,arm()))
    out = score_factorial_tournament(worlds, np.arange(64), legacy_score_fn=fake_legacy, localization_backend=FakeLoc(), n_hvg=32)
    assert out["counterfactuals"]["C_OBS"]["latent_distance"] == 0.0
    assert out["counterfactuals"]["C_OBS"]["observed_distance"] > 0
    assert "jepa" not in str(out).lower()


@pytest.mark.parametrize("evidence,expected", [
    ({"H1":{"biology_endpoint_pass":True,"observer_endpoint_pass":False,"joint_adequate":False},"H2":{"biology_endpoint_pass":False,"observer_endpoint_pass":False,"joint_adequate":False},"H3":{"joint_adequate":False}}, "BIOLOGY_NECESSARY"),
    ({"H1":{"biology_endpoint_pass":False,"observer_endpoint_pass":False,"joint_adequate":False},"H2":{"biology_endpoint_pass":False,"observer_endpoint_pass":True,"joint_adequate":False},"H3":{"joint_adequate":False}}, "OBSERVER_NECESSARY"),
    ({"H1":{"biology_endpoint_pass":True,"observer_endpoint_pass":False,"joint_adequate":False},"H2":{"biology_endpoint_pass":False,"observer_endpoint_pass":True,"joint_adequate":False},"H3":{"joint_adequate":True}}, "BOTH_AND_INTERACTION"),
    ({"H1":{"biology_endpoint_pass":True,"observer_endpoint_pass":True,"joint_adequate":True},"H2":{"biology_endpoint_pass":False,"observer_endpoint_pass":False,"joint_adequate":False},"H3":{"joint_adequate":True}}, "BIOLOGY_ONLY_SUFFICIENT"),
    ({"H1":{"biology_endpoint_pass":False,"observer_endpoint_pass":False,"joint_adequate":False},"H2":{"biology_endpoint_pass":True,"observer_endpoint_pass":True,"joint_adequate":True},"H3":{"joint_adequate":True}}, "OBSERVER_ONLY_SUFFICIENT"),
    ({"H1":{"biology_endpoint_pass":True,"observer_endpoint_pass":False,"joint_adequate":False},"H2":{"biology_endpoint_pass":False,"observer_endpoint_pass":True,"joint_adequate":False},"H3":{"joint_adequate":False}}, "COUPLING_FALSIFIED"),
])
def test_mechanism_comparison_requires_causal_endpoint_evidence(evidence, expected):
    assert compare_factorial_mechanisms(evidence) == expected


def test_mechanism_comparison_rejects_aggregate_distance_only():
    with pytest.raises(ValueError, match="causal endpoint"):
        compare_factorial_mechanisms({"H1":{"distance":1},"H2":{"distance":2},"H3":{"distance":0.5}})
