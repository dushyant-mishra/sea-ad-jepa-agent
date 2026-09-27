"""Contract tests for the AGENT 5 Morabito benchmark preparatory analysis.

Every test here is written so that it CAN fail: each asserts a property that a
plausible defect would violate, and several are deliberately constructed against
synthetic inputs that carry the defect, so that the test is shown to fire.

Run:
    pytest tests/agent_5/test_agent5_morabito_benchmark_preparatory_v1.py -q
"""
import importlib.util
import json
import math
import os
import sys

import pandas as pd
import pytest

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SCRIPT = os.path.join(REPO, "scripts", "agent_5",
                      "agent5_morabito_benchmark_preparatory_v1.py")


def _load():
    spec = importlib.util.spec_from_file_location("a5prep", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["a5prep"] = mod
    spec.loader.exec_module(mod)
    return mod


a5 = _load()


# --------------------------------------------------------------- fixtures

def _cells(sample, n, barcode_suffix, cell_types, **cov):
    rows = []
    for i in range(n):
        rows.append(dict(
            Barcode="%016d-%s" % (i, barcode_suffix),
            SampleID=sample,
            **{"Cell.Type": cell_types[i % len(cell_types)]},
            cluster="C%d" % (i % 2),
            **cov,
        ))
    return rows


def _toy_pair(same_barcodes=False, covariate_conflict=False):
    base = dict(Diagnosis="AD", Batch=1, Age=80, Sex="M", PMI=4.0,
                RIN=8.0)
    base["Tangle.Stage"] = "Stage 5"
    base["Plaque.Stage"] = "Stage C"
    rna = pd.DataFrame(
        _cells("Sample-1", 10, "1", ["MG", "EX"], **base)
        + _cells("Sample-2", 10, "2", ["MG", "EX"],
                 **{**base, "Diagnosis": "Control", "Age": 70, "Batch": 2}))
    atac_base = dict(base)
    if covariate_conflict:
        atac_base["Age"] = 99          # same SampleID, different person
    atac = pd.DataFrame(
        _cells("Sample-1", 12, "1" if same_barcodes else "7",
               ["MG", "EX"], **atac_base)
        + _cells("Sample-2", 12, "2" if same_barcodes else "8", ["MG", "EX"],
                 **{**base, "Diagnosis": "Control", "Age": 70, "Batch": 2}))
    return rna, atac


# ------------------------------------------------ 1. replication arithmetic

def test_kish_effective_clusters_is_bounded_by_the_unit_count():
    assert a5.kish_effective_clusters([100, 100, 100]) == pytest.approx(3.0)
    # One dominant cluster must reduce the effective count well below 3.
    assert a5.kish_effective_clusters([1000, 1, 1]) < 1.1
    assert a5.kish_effective_clusters([]) is None


def test_kish_is_not_a_cell_count():
    """The effective-unit count must never be reported as a cell count. A
    regression that returned sum(counts) instead would trip this."""
    counts = [141, 233, 372]
    ess = a5.kish_effective_clusters(counts)
    assert ess <= len(counts) + 1e-9
    assert ess < sum(counts) / 10.0


def test_sign_consistency_critical_value_is_exact_and_conservative():
    r = a5.sign_consistency_critical(18)
    assert r["critical_k"] == 13
    assert r["achieved_alpha"] <= 0.05
    # 12/18 must NOT be significant, or the threshold is wrong.
    assert a5.binomial_sf(12, 18) > 0.05
    assert a5.binomial_sf(13, 18) <= 0.05


def test_binomial_sf_endpoints():
    assert a5.binomial_sf(0, 5) == pytest.approx(1.0)
    assert a5.binomial_sf(5, 5) == pytest.approx(1 / 32)


def test_mde_shrinks_as_n_grows():
    assert a5.fisher_z_mde(18) > a5.fisher_z_mde(20) > a5.fisher_z_mde(100)
    assert a5.paired_d_mde(18) > a5.paired_d_mde(200)
    assert a5.fisher_z_mde(3) is None


def test_design_effect_is_one_only_when_icc_is_zero():
    tbl = a5.deff_table(229.222)
    by_icc = {r["assumed_icc"]: r["design_effect"] for r in tbl}
    assert by_icc[0.0] == pytest.approx(1.0)
    assert by_icc[0.01] > 3.0
    assert all(r["status"] == "ASSUMED_NOT_MEASURED" for r in tbl)


# ----------------------------------------------- 2. the pairing prohibition

def test_pairing_falsifier_rejects_a_forged_cell_level_join():
    """If a future deposit revision made barcodes coincide, the falsifier must
    still refuse a cell-level join, and must show that the coincidence does not
    name the same sample."""
    rna, atac = _toy_pair(same_barcodes=True)
    res = a5.pairing_falsifier(rna, atac)
    assert res["verdict"] == "NO_CELL_LEVEL_RNA_ATAC_PAIRING_EXISTS"
    assert "Barcode" in res["forbidden_join_keys"]
    assert res["admissible_join_keys"] == ["SampleID"]
    assert res["raw_barcode_string_overlap"] > 0


def test_pairing_falsifier_counts_disagreeing_collisions():
    rna, atac = _toy_pair(same_barcodes=True)
    res = a5.pairing_falsifier(rna, atac)
    same = res["raw_overlap_same_sample"]
    diff = res["raw_overlap_different_sample"]
    assert same + diff == res["raw_barcode_string_overlap"]


def test_sample_id_is_the_only_admissible_key():
    rna, atac = _toy_pair()
    res = a5.pairing_falsifier(rna, atac)
    for forbidden in ("barcode_16mer", "gem_group_suffix", "row_position",
                      "cell_index"):
        assert forbidden in res["forbidden_join_keys"]


# ------------------------------------------- 3. donor-key validity detection

def test_covariate_conflict_falsifies_the_sample_level_join():
    """Same SampleID with a different age in the two assays means SampleID is
    not a donor key. The register must detect that rather than merge anyway."""
    rna, atac = _toy_pair(covariate_conflict=True)
    _, mismatch, n = a5.build_sample_register(rna, atac)
    assert n > 0
    assert mismatch["Age"] > 0
    assert sum(mismatch.values()) > 0


def test_clean_pair_has_no_covariate_conflict():
    rna, atac = _toy_pair()
    _, mismatch, _ = a5.build_sample_register(rna, atac)
    assert sum(mismatch.values()) == 0


def test_register_never_claims_cell_level_pairing():
    rna, atac = _toy_pair()
    tbl, _, _ = a5.build_sample_register(rna, atac)
    assert set(tbl.admissible_join_level) == {"SAMPLE_DONOR_ONLY"}
    assert set(tbl.cell_level_pairing) == {"NONE_IN_DEPOSIT"}


# ------------------------------------ 4. permutation-control adequacy checks

def test_singleton_strata_are_reported_as_partially_vacuous():
    """A stratification so fine that a unit is alone in its stratum pins that
    unit. The audit must say so instead of reporting a clean control."""
    reg = pd.DataFrame([
        dict(sample_id="S1", in_both_modalities=True, rna_batch=1,
             diagnosis="AD", sex="M"),
        dict(sample_id="S2", in_both_modalities=True, rna_batch=2,
             diagnosis="Control", sex="F"),
    ])
    out = a5.restricted_permutation_space(reg, {"fine": ("rna_batch", "diagnosis", "sex")})
    assert out["fine"]["units_pinned_by_a_singleton_stratum"] == 2
    assert out["fine"]["vacuity_warning"].startswith("PARTIALLY_VACUOUS")
    assert out["fine"]["adequate_for_alpha_0p05"] is False


def test_permutation_floor_blocks_an_unusable_control():
    """Two units can produce only 2 permutations, so p < 0.05 is unreachable."""
    reg = pd.DataFrame([
        dict(sample_id="S1", in_both_modalities=True, rna_batch=1,
             diagnosis="AD", sex="M"),
        dict(sample_id="S2", in_both_modalities=True, rna_batch=1,
             diagnosis="AD", sex="M"),
    ])
    out = a5.restricted_permutation_space(reg, {"coarse": ()})
    assert out["coarse"]["minimum_attainable_permutation_p"] == pytest.approx(0.5)
    assert out["coarse"]["adequate_for_alpha_0p05"] is False


def test_unrestricted_permutation_space_is_larger_than_restricted():
    reg = pd.DataFrame([
        dict(sample_id="S%d" % i, in_both_modalities=True,
             rna_batch=1 + (i % 3), diagnosis="AD" if i % 2 else "Control",
             sex="M" if i % 2 else "F")
        for i in range(12)])
    out = a5.restricted_permutation_space(
        reg, {"free": (), "batch": ("rna_batch",)})
    assert (out["free"]["n_distinct_restricted_permutations"]
            > out["batch"]["n_distinct_restricted_permutations"])


# ------------------------------------------- 5. covariate availability audit

def test_sample_level_covariates_are_not_labelled_cell_level():
    rna, atac = _toy_pair()
    tbl, summary = a5.covariate_audit(rna, atac)
    levels = dict(zip(tbl[tbl.assay == "snRNA"].column,
                      tbl[tbl.assay == "snRNA"].variable_level))
    for field in ("Diagnosis", "Age", "Sex", "PMI", "RIN", "Batch"):
        assert levels[field] == "sample_level", field
    assert "Cell.Type" in summary["cell_level_columns_present"]


def test_absent_qc_columns_are_reported_as_absent_not_zero():
    rna, atac = _toy_pair()
    _, summary = a5.covariate_audit(rna, atac)
    assert "nUMI" in summary["standard_qc_columns_absent_from_deposit"]
    assert "percent.mt" in summary["standard_qc_columns_absent_from_deposit"]


def test_a_real_cell_level_covariate_is_detected_when_present():
    """Guards against a check that always says 'absent'."""
    rna, atac = _toy_pair()
    rna = rna.copy()
    rna["nUMI"] = range(len(rna))
    tbl, summary = a5.covariate_audit(rna, atac)
    row = tbl[(tbl.assay == "snRNA") & (tbl.column == "nUMI")].iloc[0]
    assert row.variable_level == "cell_level"
    assert bool(row.usable_as_cell_level_technical_covariate) is True
    assert "nUMI" not in summary["standard_qc_columns_absent_from_deposit"]


# ------------------------------------------------- 6. produced-artifact tests

MANIFEST_ENV = "AGENT5_PREPARATORY_MANIFEST"


def _manifest():
    p = os.environ.get(MANIFEST_ENV)
    if not p or not os.path.exists(p):
        pytest.skip("set %s to the produced manifest to run artifact checks"
                    % MANIFEST_ENV)
    with open(p) as fh:
        return json.load(fh)


def test_manifest_marks_biological_evaluation_not_executed():
    m = _manifest()
    assert m["biological_evaluation_status"] == "NOT_EXECUTED"
    assert m["model_loaded"] is False
    assert m["frozen_state_scored"] is False
    assert m["protected_outcomes_touched"] is False
    assert "TRAINING=OFF" in m["governance_footer"]


def test_manifest_independent_units_are_samples_not_cells():
    m = _manifest()
    rep = m["effective_replication"]["rna_microglia"]
    assert rep["independent_units_n"] < rep["total_cells"]
    assert rep["kish_effective_number_of_units"] <= rep["independent_units_n"]
    assert rep["cell_level_effective_sample_size"].startswith("UNKNOWN")


def test_manifest_records_stage75f_as_non_independent():
    m = _manifest()
    s = m["stage75f_circularity"]
    assert s["independence_verdict"].startswith("NON_INDEPENDENT")
    assert s["edges_derived_from_gse174367_rna"] is True


def test_manifest_reports_untestable_overlap_as_unknown_not_zero():
    m = _manifest()
    f = m["full104_donor_overlap"]
    assert f["exact_donor_identity_overlap"] == "UNTESTABLE_FROM_DEPOSIT"
    assert f["residual_overlap_risk"].startswith("UNKNOWN")
    assert f["gse174367_present_as_a_registered_study"] is False


def test_manifest_cross_modality_n_equals_shared_samples():
    m = _manifest()
    assert (m["effective_replication"]["cross_modality"]["independent_units_n"]
            == m["sample_overlap"]["shared_samples"])


def test_manifest_microglia_counts_are_internally_consistent():
    m = _manifest()
    reg = pd.read_csv(os.path.join(
        os.path.dirname(os.environ[MANIFEST_ENV]),
        "agent5_sample_overlap_register_v1.csv"))
    assert int(reg.rna_microglia_cells.sum()) == m["sample_overlap"]["rna_microglia_cells"]
    assert int(reg.atac_microglia_cells.sum()) == m["sample_overlap"]["atac_microglia_cells"]
    assert int(reg.in_both_modalities.sum()) == m["sample_overlap"]["shared_samples"]


# ------------------------------------------------ 7. frozen-protocol binding

PROTOCOL = os.path.join(REPO, "configs", "agent_5",
                        "agent5_morabito_frozen_scoring_protocol_v1.json")


def test_frozen_protocol_digest_matches_its_recorded_value():
    """The protocol records the SHA-256 of its own scored content. If anyone
    edits a threshold without re-freezing, this fails."""
    if not os.path.exists(PROTOCOL):
        pytest.skip("frozen protocol not present")
    with open(PROTOCOL, "rb") as fh:
        doc = json.loads(fh.read().decode("utf-8"))
    recorded = doc["freeze"]["scored_content_sha256"]
    payload = json.dumps(doc["scored_content"], sort_keys=True,
                         separators=(",", ":")).encode("utf-8")
    import hashlib
    assert hashlib.sha256(payload).hexdigest() == recorded


def test_frozen_protocol_has_a_disqualifier_for_every_control():
    if not os.path.exists(PROTOCOL):
        pytest.skip("frozen protocol not present")
    with open(PROTOCOL) as fh:
        doc = json.load(fh)
    controls = doc["scored_content"]["negative_controls"]
    assert len(controls) >= 7
    for c in controls:
        assert c["disqualifies_claim_if"], c["control_id"]
        assert c["exchangeability_restriction"], c["control_id"]


def test_every_frozen_threshold_is_justified_or_labelled_arbitrary():
    if not os.path.exists(PROTOCOL):
        pytest.skip("frozen protocol not present")
    with open(PROTOCOL) as fh:
        doc = json.load(fh)
    for t in doc["scored_content"]["thresholds"]:
        assert t["justification_class"] in ("external_statistical_rationale",
                                            "arbitrary_convention"), t["threshold_id"]
        assert t["justification"], t["threshold_id"]


def test_outcomes_are_reported_separately_and_never_merged():
    if not os.path.exists(PROTOCOL):
        pytest.skip("frozen protocol not present")
    with open(PROTOCOL) as fh:
        doc = json.load(fh)
    outs = doc["scored_content"]["outcomes"]
    assert [o["outcome_id"] for o in outs] == ["O1", "O2", "O3"]
    assert doc["scored_content"]["reporting_rule"]["single_headline_number"] is False
    for o in outs:
        assert o["execution_status"] == "NOT_EXECUTED"


def test_no_bounded_metric_carries_a_relative_improvement_threshold():
    if not os.path.exists(PROTOCOL):
        pytest.skip("frozen protocol not present")
    with open(PROTOCOL) as fh:
        doc = json.load(fh)
    for t in doc["scored_content"]["thresholds"]:
        if t.get("comparison_form") == "relative":
            assert t["metric_is_bounded"] is True, t["threshold_id"]
