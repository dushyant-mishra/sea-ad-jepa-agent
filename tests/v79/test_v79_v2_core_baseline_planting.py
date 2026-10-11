from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import generate_v79_v2_core_worlds as G  # noqa: E402

PAYLOAD = json.loads((ROOT / "results/v79/v2_core_qualification/V79_V2_CORE_QUALIFICATION_CONTRACT_V2_DRAFT.json").read_text())
CAL = json.loads((ROOT / "results/v79/development/v2_core_planting_calibration/V79_V2_CORE_PLANTING_CALIBRATION_MASKED_V2.json").read_text())


def _authority_fixture():
    # Three sources, two donors/source, donor cell-count supports [2,3] by source.
    src = np.array([0,0, 0,0,0, 1,1, 1,1,1, 2,2, 2,2,2], dtype=np.int64)
    donor = np.array([0,0, 1,1,1, 2,2, 3,3,3, 4,4, 5,5,5], dtype=np.int64)
    cls = np.array([0,1, 2,0,1, 0,2, 1,1,2, 0,0, 1,2,2], dtype=np.int64)
    op = np.array([0,1, 0,1,0, 2,3, 2,3,2, 4,5, 4,5,4], dtype=np.int64)
    log_lib = np.linspace(-1.4, 1.3, len(src))
    return {"src":src,"donor":donor,"cls":cls,"op":op,"log_lib":log_lib}


def test_base_design_is_deterministic_and_uses_frozen_sampling_sources():
    auth = _authority_fixture()
    a = G.build_base_design(auth, donors_per_source=(3,2,4), root=31000000)
    b = G.build_base_design(auth, donors_per_source=(3,2,4), root=31000000)
    for k in a: assert np.array_equal(a[k], b[k])
    # Requested donor counts per source are exact.
    assert [len(np.unique(a["donor"][a["src"] == s])) for s in range(3)] == [3,2,4]
    # Every generated donor cell count is drawn from that source's empirical donor-count support.
    for s in range(3):
        empirical = {int((auth["donor"] == d).sum()) for d in np.unique(auth["donor"][auth["src"] == s])}
        generated = {int((a["donor"] == d).sum()) for d in np.unique(a["donor"][a["src"] == s])}
        assert generated <= empirical
    # Class, log library and operators are sampled only from allowed authority support.
    assert set(np.unique(a["cls"])) <= set(np.unique(auth["cls"]))
    assert set(a["log_lib"].tolist()) <= set(auth["log_lib"].tolist())
    for s in range(3):
        assert set(np.unique(a["op"][a["src"] == s])) <= set(np.unique(auth["op"][auth["src"] == s]))


def test_base_design_seed_is_world_independent_shared_key():
    auth = _authority_fixture()
    a = G.build_base_design(auth, donors_per_source=(3,2,4), root=31000000)
    # No world_index argument exists: Q00-Q09 must consume the same design bytes.
    assert G.array_bundle_sha(a) == G.array_bundle_sha(G.build_base_design(auth, donors_per_source=(3,2,4), root=31000000))


def test_latin_hypercube_is_deterministic_stratified_and_within_p5_p95():
    values = np.arange(100, dtype=float)
    a, levels = G.latin_hypercube_empirical(values, G=10, world_index=0, quantity_index=7,
                                             root=31000000, p_lo=0.05, p_hi=0.95)
    b, levels2 = G.latin_hypercube_empirical(values, G=10, world_index=0, quantity_index=7,
                                              root=31000000, p_lo=0.05, p_hi=0.95)
    assert np.array_equal(a, b) and np.array_equal(levels, levels2)
    assert np.all(levels >= 0.05) and np.all(levels < 0.95)
    # Transform back to p5-p95 strata; each of ten strata appears once.
    strata = np.floor((levels - 0.05) / 0.90 * 10).astype(int)
    assert sorted(strata.tolist()) == list(range(10))
    assert np.all(a >= np.quantile(values, 0.05, method="linear"))
    assert np.all(a <= np.quantile(values, 0.95, method="linear"))


def test_baseline_plant_uses_masked_calibration_and_frozen_ranges():
    plant = G.build_q00_planting(CAL, PAYLOAD, world_index=0, G=44)
    assert set(plant) >= {"detection","positive","lhs_levels","contrast_signs"}
    ranges = PAYLOAD["worlds"]["planting_magnitudes"]["latin_hypercube_ranges"]
    for key, cal_key in [("depth1","depth"),("depth2","depth2"),("donor_sd","donor_sd")]:
        lo, hi = ranges["detection"][key]["empirical_quantile_range"]
        assert np.min(plant["detection"][key]) >= lo - 1e-12
        assert np.max(plant["detection"][key]) <= hi + 1e-12
    for key in ("depth1","depth2","donor_sd","sigma","intercept"):
        lo, hi = ranges["positive"][key]["empirical_quantile_range"]
        assert np.min(plant["positive"][key]) >= lo - 1e-12
        assert np.max(plant["positive"][key]) <= hi + 1e-12
    assert np.all((plant["detection"]["prevalence"] >= ranges["detection"]["prevalence"]["empirical_quantile_range"][0]) &
                  (plant["detection"]["prevalence"] <= ranges["detection"]["prevalence"]["empirical_quantile_range"][1]))


def test_detection_intercept_bisection_hits_measured_target():
    non_intercept = np.array([-2., -1., 0., 1., 2.])
    measured = np.array([True, True, False, True, True])
    alpha = G.solve_detection_intercept(non_intercept, measured, target_prevalence=0.35)
    p = 1.0 / (1.0 + np.exp(-(alpha + non_intercept[measured])))
    assert float(np.mean(p)) == pytest.approx(0.35, abs=1e-10)


def test_donor_factor_effects_are_within_source_centered_and_lambda_assignment_half():
    src_by_donor = np.array([0,0,0,1,1,2,2,2], dtype=np.int64)
    sd = np.linspace(0.2, 0.5, 6)
    out = G.build_donor_effects(src_by_donor, sd, world_index=0, part="detection", root=31000000)
    assert out["effects"].shape == (len(src_by_donor), 6)
    assert out["lambda"].shape == (6,)
    assert int(np.sum(out["lambda"] == 0.6)) == 3
    assert int(np.sum(out["lambda"] == 0.0)) == 3
    for g in range(6):
        for s in np.unique(src_by_donor):
            assert float(out["effects"][src_by_donor == s, g].mean()) == pytest.approx(0.0, abs=1e-12)
