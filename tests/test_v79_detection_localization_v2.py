import json
import sys
from pathlib import Path

import numpy as np
import pytest
from scipy import sparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "v77"))
sys.path.insert(0, str(ROOT / "scripts" / "v79"))


def make_localization_fixture():
    rng = np.random.default_rng(19)
    n, g = 800, 90
    cls = np.array(["A"] * 400 + ["B"] * 400)
    base = np.linspace(.2, 5.0, g)
    lam = np.tile(base, (n, 1))
    lam[cls == "A", :20] *= 2.0
    lam[cls == "B", 20:40] *= 2.0
    depth = np.concatenate([np.linspace(.5, 1.5, 400), np.linspace(.6, 1.6, 400)])
    lam *= depth[:, None]
    x = rng.poisson(lam).astype(float)
    x[:, 0] = 1.0
    x[:, 1] = 0.0
    return x, np.arange(g), cls


def make_nested_detection_fixture():
    rng = np.random.default_rng(23)
    n, g = 500, 70
    H = (rng.random((n, g)) < np.linspace(.15, .85, g)).astype(float)
    base = np.array(["A|d0"] * 300 + ["A|d1"] * 200)
    op = np.array(["op_big"] * 150 + ["op_small1"] * 75 + ["op_small2"] * 75 +
                  ["op_b2"] * 120 + ["op_bsmall"] * 80)
    src = np.array(["S1"] * 300 + ["S2"] * 200)
    donor = np.array(["D1"] * 100 + ["D2"] * 100 + ["D3"] * 100 + ["D1"] * 100 + ["D2"] * 100)
    return H, base, op, src, donor


def test_support_status_thresholds():
    import v79_detection_localization as V
    assert V.support_status(100, 50)["supported"] is True
    assert V.support_status(99, 50)["reason"] == "n_cells_lt_100"
    assert V.support_status(100, 49)["reason"] == "n_variable_genes_lt_50"


def test_depth_bins_deterministic_coarsening_and_ties():
    import v79_detection_localization as V
    for n, expected in [(500, 5), (400, 4), (200, 2)]:
        got = V.quantile_depth_bins(np.linspace(1, 100, n))
        assert got["supported"] is True and got["n_bins"] == expected
        assert np.bincount(got["labels"]).min() >= 100
    bad = V.quantile_depth_bins(np.linspace(1, 100, 199))
    assert bad["supported"] is False and bad["reason"] == "no_supported_partition_5_to_2"
    vals = np.repeat([1., 2., 3., 4.], 100)
    assert np.array_equal(V.quantile_depth_bins(vals)["labels"], V.quantile_depth_bins(vals)["labels"])


def test_l0_l2_and_sparse_equivalence():
    import v79_detection_localization as V
    import v78_signed_scoring as V78S
    x, u, cls = make_localization_fixture()
    dense = V.build_l0_l2(x, u, cls, n_hvg=70)
    got = V.build_l0_l2(sparse.csr_matrix(x), u, cls, n_hvg=70)
    assert np.array_equal(dense["selection"]["selected_positions"], got["selection"]["selected_positions"])
    assert np.allclose(dense["L0"]["corr"], got["L0"]["corr"])
    assert got["L0"]["summary"]["canonical"] == V78S.signed_diagnostics_from_corr(got["L0"]["corr"], strong_threshold=.30)
    assert got["L2"]["primary"]["depth_variable"] == "detected_feature_count"
    assert got["L2"]["primary"]["canonical"] is True
    assert got["L2"]["sensitivity"]["depth_variable"] == "library_size"
    assert got["L2"]["sensitivity"]["canonical"] is False


def test_streaming_mode_omits_stratum_corr_without_changing_combined():
    import v79_detection_localization as V
    H, base, _, _, _ = make_nested_detection_fixture()
    keep = V.localize_by_labels(H, base, np.arange(H.shape[1]), retain_stratum_corr=True)
    drop = V.localize_by_labels(H, base, np.arange(H.shape[1]), retain_stratum_corr=False)
    assert np.allclose(keep["combined_corr"], drop["combined_corr"])
    assert all("corr" not in r for r in drop["strata"])


def test_operator_source_fallback_without_pseudo_pooling():
    import v79_detection_localization as V
    H, base, op, src, _ = make_nested_detection_fixture()
    got = V.localize_operator_source(H, base, op, src)
    realized = [r for r in got["strata"] if r["support"]["supported"]]
    assert any(r["kind"] == "operator" and r["label"] == "op_big" and r["n_cells"] == 150 for r in realized)
    assert any(r["kind"] == "source_fallback" and r["label"] == "S1" and r["n_cells"] == 150 for r in realized)
    assert any(r["kind"] == "operator" and r["label"] == "op_b2" and r["n_cells"] == 120 for r in realized)
    assert not any(r["kind"] == "source_fallback" and r["label"] == "S2" for r in realized)


def test_donor_localization_is_biological_or_ambiguous():
    import v79_detection_localization as V
    H, base, _, _, donor = make_nested_detection_fixture()
    got = V.localize_donor(H, base, donor)
    assert got["interpretation"] == "BIOLOGICAL_OR_AMBIGUOUS"
    assert all(r.get("interpretation") != "TECHNICAL" for r in got["strata"])
    assert got["n_supported_strata"] >= 4


def test_residual_persistence_is_identity_scrubbed():
    import v79_detection_localization as V
    A = np.array([[1,.5,-.5,.05],[.5,1,-.4,.2],[-.5,-.4,1,-.2],[.05,.2,-.2,1]], float)
    B = np.array([[1,.6,-.45,-.05],[.6,1,-.35,.1],[-.45,-.35,1,.15],[-.05,.1,.15,1]], float)
    C = np.array([[1,.4,-.6,.02],[.4,1,-.5,.25],[-.6,-.5,1,-.1],[.02,.25,-.1,1]], float)
    got = V.aggregate_residual_persistence({"L1":{"combined_corr":A},"L2":{"combined_corr":B},"L3":{"combined_corr":C}})
    can = got["thresholds"]["0.30"]
    assert can["persistent_positive_count"] >= 1 and can["persistent_negative_count"] >= 2
    text = json.dumps(got).lower()
    for forbidden in ["selected_positions", "gene_id", "gene_name", "edge_pairs", "registry_id"]:
        assert forbidden not in text


def test_v79_gate_ready_and_fail_closed(monkeypatch):
    import run_v79_detection_localization as D
    ready = D.preexecution_gate("e2", "bridge", "authority", "cache")
    assert ready["status"] == "READY" and ready["training_authorized"] is False
    base = D.V78.preexecution_gate("e2", "bridge", "authority", "cache")
    base["status"] = "BLOCKED"
    base["blockers"] = ["corrected_count_digest_mismatch"]
    monkeypatch.setattr(D.V78, "preexecution_gate", lambda *a, **k: base)
    blocked = D.preexecution_gate("e2", "bridge", "authority", "cache")
    assert "v78_custody_gate" in blocked["blockers"]
    with pytest.raises(PermissionError):
        D.require_execution_authority(blocked)


def test_v79_gate_blocks_hash_mismatch_and_training_contamination(monkeypatch):
    import run_v79_detection_localization as D
    base = D.V78.preexecution_gate("e2", "bridge", "authority", "cache")
    base["details"]["e2_reference"]["evaluation_universe_sha256"] = "wrong"
    base["details"]["e2_reference"]["class_authority_sha256"] = "wrong"
    base["details"]["marginal_authority"]["training_authorized"] = True
    monkeypatch.setattr(D.V78, "preexecution_gate", lambda *a, **k: base)
    got = D.preexecution_gate("e2", "bridge", "authority", "cache")
    assert "evaluation_universe_mismatch" in got["blockers"]
    assert "class_authority_mismatch" in got["blockers"]
    assert "training_authorization_contamination" in got["blockers"]


def test_run_localization_writes_non_authorizing_receipts(tmp_path):
    import run_v79_detection_localization as D
    x, u, cls = make_localization_fixture()
    source = np.array(["S1"] * 400 + ["S2"] * 400)
    operator = np.array(["op1"] * 200 + ["op2"] * 200 + ["op3"] * 200 + ["op4"] * 200)
    donor = np.array(["D1"] * 100 + ["D2"] * 100 + ["D3"] * 100 + ["D4"] * 100 +
                     ["D1"] * 100 + ["D2"] * 100 + ["D3"] * 100 + ["D4"] * 100)
    gate = {"status":"READY", "blockers":[], "training_authorized":False}
    rec = D.run_localization(sparse.csr_matrix(x), u, cls, source, operator, donor, gate,
                             n_hvg=70, output_dir=tmp_path)
    assert rec["ruling"]["training_authorized"] is False
    assert rec["ruling"]["v78_retuning_authorized"] is False
    assert rec["ruling"]["synthetic_arm_promoted"] is None
    assert set(rec["ruling"]["candidate_mechanism_families"]).issubset(D.ALLOWED_MECHANISM_FAMILIES)
    for name in D.RECEIPT_FILENAMES.values():
        assert (tmp_path / name).is_file()
    l5_text = json.dumps(rec["canonical"]["L5"]).lower()
    for forbidden in ["gene_id", "gene_name", "edge_pairs", "selected_positions", "registry_id"]:
        assert forbidden not in l5_text


def test_mechanism_ruling_never_promotes_or_claims_unique_cause():
    import run_v79_detection_localization as D
    loc = {
        "L0":{"summary":{"canonical":{"pos_over_neg_ratio":59.0}}},
        "L1":{"summary":{"canonical":{"pos_over_neg_ratio":80.0}}},
        "L2":{"primary":{"summary":{"canonical":{"pos_over_neg_ratio":120.0}}}},
        "L3":{"summary":{"canonical":{"pos_over_neg_ratio":150.0}}},
        "L4":{"summary":{"canonical":{"pos_over_neg_ratio":160.0}}},
    }
    r = D.mechanism_ruling(loc)
    assert r["synthetic_arm_promoted"] is None
    assert r["training_authorized"] is False
    assert r["unique_causal_winner_claimed"] is False
    assert "FACTORIAL_BIOLOGY_X_OBSERVATION_TOURNAMENT" in r["candidate_mechanism_families"]
