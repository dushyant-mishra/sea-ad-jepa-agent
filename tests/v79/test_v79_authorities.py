"""The posterior-generative authorities: built only from complete internal records, both pass the firewall, carry
no gene address (only the internal realism diagnostic does), are byte-reproducible, keep within-gene couplings
under the anonymous order, export only a status for a phase that did not converge, and refuse missing inputs.
Fabricated records and draws only."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import build_v79_authorities as BA  # noqa: E402
import v79_firewall as FW  # noqa: E402

G, D = 12, 50
COMPS = ("cls", "src", "op", "donor", "dk", "res")


def fractions(n):
    return {c: dict(across_gene_median_q=[0.1, 0.2, 0.3], per_gene_median=[0.2] * n, per_gene_q05=[0.1] * n,
                    per_gene_q95=[0.3] * n, variance_per_gene_median=[0.5] * n) for c in COMPS}


def write_world(tmp: Path, converged=None):
    converged = converged or {}
    rng = np.random.default_rng(0)
    genes = sorted(rng.choice(41238, G, replace=False).tolist())
    for ph, (j, n) in BA.PHASES.items():
        ng = 2 if ph == "B0" else G
        rec = dict(diagnosed=converged.get(ph, True), fractions=fractions(ng),
                   gene_sample=dict(n=G, internal_address_indices=genes),
                   design_levels=dict(class_levels=["GABAergic", "Glutamatergic", "NonNeuronal"],
                                      source_levels=["HVS", "NPH52", "SEA_AD"]),
                   responses=["log_source_library", "log_detected_features"] if ph == "B0" else None)
        (tmp / j).parent.mkdir(parents=True, exist_ok=True)
        (tmp / j).write_text(json.dumps(rec), encoding="utf-8")
        arr = dict(mu=rng.normal(0, 1, (D, ng)), b_depth=rng.normal(0.5, 0.2, (D, ng)),
                   a_cls=rng.normal(0, 0.5, (D, 3, ng)), a_src=rng.normal(0, 0.3, (D, 3, ng)),
                   a_op=rng.normal(0, 0.3, (D, 6, ng)), a_donor=rng.normal(0, 0.4, (D, 9, ng)),
                   a_dk=rng.normal(0, 0.2, (D, 20, ng)), **{f"{p}_{x}": rng.normal(0, 0.1, D)
                                                          for p in ("m", "s") for x in ("op", "donor", "dk")})
        if ph in ("A", "B0"):
            arr.update(logsd_res=rng.normal(-0.2, 0.1, (D, ng)), m_res=rng.normal(0, .1, D), s_res=rng.normal(0, .1, D))
        if ph == "C":
            arr.update(logphi=rng.normal(0.7, 0.3, (D, ng)), m_phi=rng.normal(0.7, .1, D), s_phi=rng.normal(.3, .05, D))
        np.savez_compressed(tmp / n, **arr)
    other = dict(C_choice=dict(decision="ztnb (frozen rule)", comparison=dict(winner="ztnb")),
                 D1=dict(statistics={"expression_cp10k_log1p.median_abs_corr": dict(point=.2, q05=.18, median=.2, q95=.22)}),
                 support_A=dict(comparison=dict(mean_difference_per_observation=.01, donor_clustered_se=.002, supported=True)),
                 support_B=dict(comparison=dict(mean_difference_per_observation=.0, donor_clustered_se=.002, supported=False)),
                 **{f"ppc_{p}": dict(pooled_share_inside={"gene_mean": dict(share_inside=.9),
                                                         "pooled_median_abs_corr": dict(share_inside=.1)})
                    for p in ("A", "B", "B0")})
    for k, v in other.items():
        (tmp / BA.OTHER[k]).parent.mkdir(parents=True, exist_ok=True)
        (tmp / BA.OTHER[k]).write_text(json.dumps(v), encoding="utf-8")
    return genes


def strings(obj):
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)
    elif isinstance(obj, str):
        yield obj


def test_authorities_pass_the_firewall_and_carry_no_addresses(tmp_path):
    genes = write_world(tmp_path)
    bio, obs, realism = BA.build(tmp_path)
    for art in (bio, obs):
        assert FW.scrub(art) is art and art["training_authorized"] is False
        assert "gene_address_indices" not in json.dumps(art) and "internal_address" not in json.dumps(art)
    assert realism["gene_address_indices"] == genes and realism["status"].startswith("INTERNAL__REALISM")
    assert set(obs["phases"]["detection_logit"]["source_effect_by_source"]) == {"HVS", "NPH52", "SEA_AD"}
    shares = bio["phases"]["expression_log1p_cp10k"]["class_effects"]["share_of_genes_highest_in_class"]
    assert set(shares) == {"GABAergic", "Glutamatergic", "NonNeuronal"} and abs(sum(shares.values()) - 1) < 1e-12
    assert "pooled_median_abs_corr" in bio["ppc_limitations"]["A"]          # a failed PPC is carried forward


def test_builds_are_reproducible_and_keep_within_gene_coupling(tmp_path):
    write_world(tmp_path)
    a, b = BA.build(tmp_path), BA.build(tmp_path)
    assert json.dumps(a[1], sort_keys=True) == json.dumps(b[1], sort_keys=True)
    joint = a[1]["joint_depth_slopes_per_gene"]
    triples = set(zip(*(np.round(joint[p], 9) for p in ("A", "B", "C"))))
    orig = {}
    for ph in ("A", "B", "C"):
        with np.load(tmp_path / BA.PHASES[ph][1]) as z:
            orig[ph] = np.median(z["b_depth"], 0)
    assert triples == set(zip(*(np.round(orig[p], 9) for p in ("A", "B", "C"))))
    assert [round(x, 9) for x in joint["A"]] != [round(x, 9) for x in orig["A"]]   # order is not the internal one


def test_a_phase_that_did_not_converge_exports_only_its_status(tmp_path):
    write_world(tmp_path, converged={"B": False})
    bio, obs, _ = BA.build(tmp_path)
    assert bio["phases"]["detection_logit"] == BA.NOT_CONVERGED == obs["phases"]["detection_logit"]
    assert "joint_depth_slopes_per_gene" not in obs and bio["variance_fractions"]["B"] == "NOT_CONVERGED"


def test_missing_inputs_refuse(tmp_path):
    write_world(tmp_path)
    (tmp_path / BA.OTHER["D1"]).unlink()
    with pytest.raises(SystemExit):
        BA.build(tmp_path)
