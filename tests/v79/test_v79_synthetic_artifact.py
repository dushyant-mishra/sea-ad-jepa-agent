"""Output B is built only from complete internal records, exports population summaries without per-gene values,
withholds numbers of undiagnosed fits, and is refused by the firewall when an identity reaches it. Fabricated
internal records only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import build_v79_synthetic_artifact as B  # noqa: E402
import v79_firewall as FW  # noqa: E402

COMPS = ("cls", "src", "op", "donor", "dk", "res")


def phase(diagnosed=True, n=20, responses=None):
    rng = np.random.default_rng(n)
    fr = {c: dict(across_gene_median_q=[0.1, 0.2, 0.3], per_gene_median=rng.random(n).tolist(),
                  per_gene_q05=rng.random(n).tolist(), per_gene_q95=rng.random(n).tolist(),
                  variance_per_gene_median=rng.random(n).tolist(), variance_per_gene_q05=rng.random(n).tolist(),
                  variance_per_gene_q95=rng.random(n).tolist()) for c in COMPS}
    hyper = {k: [0.1, 0.2, 0.3] for k in ("m_op", "s_op", "m_donor", "s_donor", "m_dk", "s_dk")}
    return dict(diagnosed=diagnosed, fractions=fr, responses=responses, hyperparameters=hyper)


def ppc(diag=True):
    return dict(all_folds_diagnosed=diag, pooled_share_inside={"gene_mean": dict(share_inside=0.9),
                                                               "pooled_median_abs_corr": dict(share_inside=0.0)})


def support():
    return dict(comparison=dict(mean_difference_per_observation=0.01, donor_clustered_se=0.002, supported=True,
                                both_runs_diagnosed=True, rule="two standard errors"))


def write_all(tmp: Path, **over):
    recs = {"A": phase(), "B": phase(), "B0": phase(n=2, responses=["log_source_library", "log_detected_features"]),
            "C": phase(), "C_choice": dict(decision="ztnb (frozen rule)", comparison=dict(winner="ztnb")),
            "D1": dict(method="nested", draws=1000, statistics={
                "expression_cp10k_log1p.median_abs_corr": dict(point=0.1, q05=0.09, median=0.1, q95=0.11,
                                                               resampling_shift=0.0, point_inside_bb90=True)}),
            "ppc_A": ppc(), "ppc_B": ppc(), "ppc_B0": ppc(), "support_A": support(), "support_B": support()}
    recs.update(over)
    for k, v in recs.items():
        p = tmp / B.INPUTS[k]
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(v), encoding="utf-8")


def all_lists(obj):
    if isinstance(obj, dict):
        for v in obj.values():
            yield from all_lists(v)
    elif isinstance(obj, list):
        yield obj
        for v in obj:
            yield from all_lists(v)


def test_builds_population_summaries_only(tmp_path):
    write_all(tmp_path)
    art = B.build(tmp_path)
    assert FW.scrub(art) is art
    assert max(len(x) for x in all_lists(art)) <= 5                 # no per-gene vectors
    a = art["variance_fractions"]["A_log1p_cp10k"]
    assert a["status"] == "CONVERGED" and set(a["fractions"]) == set(B.LABEL.values())
    assert set(a["population_hyperparameters_posterior_q05_q50_q95"]) >= {"m_donor", "s_donor"}
    assert len(a["fractions"]["donor"]["absolute_variance_spread_q10_q25_q50_q75_q90"]) == 5
    b0 = art["variance_fractions"]["B0_depth_and_detected_features"]["fractions"]
    assert set(b0) == {"log_source_library", "log_detected_features"}
    assert "absolute_variance_median" in b0["log_source_library"]["operator"]
    assert art["variance_fractions"]["C_positive_magnitude"]["family"] == "ztnb"
    json.dumps(art)


def test_refuses_missing_inputs(tmp_path):
    write_all(tmp_path)
    (tmp_path / B.INPUTS["D1"]).unlink()
    with pytest.raises(SystemExit):
        B.build(tmp_path)


def test_undiagnosed_fits_export_no_numbers(tmp_path):
    write_all(tmp_path, B=phase(diagnosed=False), ppc_A=ppc(diag=False))
    art = B.build(tmp_path)
    assert art["variance_fractions"]["B_detection_logit"] == dict(
        status="NOT_CONVERGED", note="estimates exist internally but are not interpreted or exported")
    assert art["heldout_posterior_predictive"]["A"]["share_inside_90"] == "NOT_CONVERGED"


def test_an_identity_in_an_input_is_refused(tmp_path):
    d1 = dict(method="nested", draws=1000, statistics={"ENSG00000123456.median": dict(
        point=0.1, q05=0.09, median=0.1, q95=0.11, resampling_shift=0.0, point_inside_bb90=True)})
    write_all(tmp_path, D1=d1)
    with pytest.raises(FW.FirewallError):
        B.build(tmp_path)
