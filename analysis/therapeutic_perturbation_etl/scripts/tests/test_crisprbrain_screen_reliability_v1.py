"""Adversarial suite for assess_crisprbrain_screen_reliability_v1.

Each test attacks a way the reliability verdict could be wrong or could be
made to look right.  The suite deliberately includes both a POSITIVE control
(two identical screens must score as perfect agreement, and the verdict must be
able to say YES) and a NEGATIVE control (two independent random screens must
score as chance, and must not be called agreement).

Run:
    python -m pytest analysis/therapeutic_perturbation_etl/scripts/tests/ -q
"""
from __future__ import annotations

import gzip
import importlib.util
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

HERE = Path(__file__).resolve()
SCRIPTS = HERE.parent.parent
REPO = SCRIPTS.parent.parent.parent
PRODUCER = SCRIPTS / "assess_crisprbrain_screen_reliability_v1.py"
RECEIPT = (
    REPO
    / "analysis/therapeutic_perturbation_etl/evidence/crisprbrain_reliability"
    / "CRISPRBRAIN_SCREEN_RELIABILITY_RECEIPT_V1.json"
)


def _load_module():
    spec = importlib.util.spec_from_file_location("crb_rel", PRODUCER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


MOD = _load_module()


@pytest.fixture(scope="module")
def receipt():
    if not RECEIPT.is_file():
        pytest.skip("receipt not produced yet; run the producer first")
    return json.loads(RECEIPT.read_text(encoding="utf-8"))


def _synth(seed, n_targets=6, n_genes=400, copy_of=None, noise=0.0):
    """Build a CRISPRbrain-shaped table.

    copy_of=None            -> an independent random screen
    copy_of=<frame>         -> the same effects, optionally with added noise
    """
    rng = np.random.default_rng(seed)
    targets = ["T%02d" % i for i in range(n_targets)]
    genes = ["G%04d" % i for i in range(n_genes)]
    rows = []
    for t in targets:
        if copy_of is None:
            fc = rng.normal(0, 0.6, n_genes)
        else:
            base = copy_of[copy_of["name"] == t].set_index("Gene").loc[genes, "Log2FC"]
            fc = base.values + rng.normal(0, noise, n_genes)
        z = np.abs(fc) / 0.2
        p = 2.0 * (1.0 - 0.5 * (1.0 + np.math.erf(0)) - 0)  # placeholder, replaced below
        from scipy import stats as _st

        p = 2.0 * _st.norm.sf(np.abs(z))
        rows.append(
            pd.DataFrame(
                {
                    "Gene": genes,
                    "Log2CPM": rng.uniform(0, 6, n_genes),
                    "Log2FC": fc,
                    "P Value": np.clip(p, 1e-300, 1.0),
                    "FDR": np.clip(p * n_genes / np.arange(1, n_genes + 1).max(), 0, 1),
                    "name": t,
                }
            )
        )
    df = pd.concat(rows, ignore_index=True)
    # make each target's own symbol a measurable readout, knocked down hard
    for t in targets:
        df.loc[len(df)] = {
            "Gene": t,
            "Log2CPM": 3.0,
            "Log2FC": -2.0,
            "P Value": 1e-20,
            "FDR": 1e-18,
            "name": t,
        }
    return df


# --------------------------------------------------------------------------
# 1-3: input authentication must fail closed
# --------------------------------------------------------------------------
def test_01_digest_mismatch_fails_closed(tmp_path):
    """A single altered byte in a screen table must stop the run, not warn."""
    fake = tmp_path / "repo"
    src = REPO / "analysis/therapeutic_perturbation_etl"
    for rel in [
        "outputs/crisprbrain",
        "reference/gse335887",
        "evidence/crisprbrain",
    ]:
        shutil.copytree(src / rel, fake / "analysis/therapeutic_perturbation_etl" / rel)
    tgt = (
        fake
        / "analysis/therapeutic_perturbation_etl/outputs/crisprbrain"
        / "iTF-Microglia-CROP-seq-CRISPRi.csv.gz"
    )
    with gzip.open(tgt, "rt", encoding="utf-8") as fh:
        text = fh.read()
    text = text.replace("MARCKS", "MARCK5", 1) if "MARCKS" in text else text[:-2]
    with gzip.open(tgt, "wt", encoding="utf-8") as fh:
        fh.write(text)
    proc = subprocess.run(
        [sys.executable, str(PRODUCER), "--repo", str(fake), "--out", str(tmp_path / "o")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, "corrupted input did not fail the run"
    assert "FAIL-CLOSED" in (proc.stderr + proc.stdout)


def test_02_missing_input_fails_closed(tmp_path):
    """A deleted input must stop the run rather than silently reduce scope."""
    fake = tmp_path / "repo"
    src = REPO / "analysis/therapeutic_perturbation_etl"
    for rel in ["outputs/crisprbrain", "reference/gse335887", "evidence/crisprbrain"]:
        shutil.copytree(src / rel, fake / "analysis/therapeutic_perturbation_etl" / rel)
    (
        fake
        / "analysis/therapeutic_perturbation_etl/reference/gse335887"
        / "GSE335887_img_feature_reference.csv.gz"
    ).unlink()
    proc = subprocess.run(
        [sys.executable, str(PRODUCER), "--repo", str(fake), "--out", str(tmp_path / "o")],
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0
    assert "MISSING_INPUT" in (proc.stderr + proc.stdout)


def test_03_regzip_of_identical_content_still_authenticates(tmp_path):
    """The contract pins DECOMPRESSED bytes, so a recompression at a different
    level must still pass.  A container-only digest would wrongly reject it."""
    p = (
        REPO
        / "analysis/therapeutic_perturbation_etl/outputs/crisprbrain"
        / "iPSC-Microglia-CITE-seq-CRISPRi.csv.gz"
    )
    with gzip.open(p, "rb") as fh:
        raw = fh.read()
    out = tmp_path / "re.csv.gz"
    with gzip.open(out, "wb", compresslevel=1) as fh:
        fh.write(raw)
    assert MOD.sha256_file(out) != MOD.sha256_file(p), "recompression did not change bytes"
    assert MOD.sha256_gz_inner(out) == MOD.sha256_gz_inner(p)


# --------------------------------------------------------------------------
# 4-5: controls
# --------------------------------------------------------------------------
def test_04_positive_control_identical_screens_score_as_perfect():
    """POSITIVE CONTROL.  Two identical screens must give Pearson 1, Spearman 1,
    sign agreement 1 and full significant-hit overlap.  If the concordance code
    cannot detect perfect agreement it cannot be trusted to report its absence."""
    a = _synth(11)
    b = a.copy()
    screens = {"iTF_CROPseq": a, "iPSC_CROPseq": b}
    shared_t = sorted(set(a["name"]))
    shared_g = sorted(set(a["Gene"]) & set(b["Gene"]))
    m = MOD.build_merged(screens, shared_t, shared_g)
    pr, sr, _ = MOD.corr_pair(m["Log2FC_itf"], m["Log2FC_ipsc"])
    assert pr == pytest.approx(1.0, abs=1e-12)
    assert sr == pytest.approx(1.0, abs=1e-12)
    assert MOD.sign_agreement(m["Log2FC_itf"].values, m["Log2FC_ipsc"].values) == 1.0
    sig_a = m["sig_itf"].sum()
    assert sig_a > 0, "fixture produced no significant rows; control is vacuous"
    assert int((m["sig_itf"] & m["sig_ipsc"]).sum()) == int(sig_a)


def test_05_negative_control_independent_screens_score_as_chance():
    """NEGATIVE CONTROL.  Two independent random screens must give ~0
    correlation and ~0.5 sign agreement, and must not be reported as agreeing."""
    a = _synth(21)
    b = _synth(22)
    screens = {"iTF_CROPseq": a, "iPSC_CROPseq": b}
    shared_t = sorted(set(a["name"]) & set(b["name"]))
    shared_g = sorted(set(a["Gene"]) & set(b["Gene"]))
    m = MOD.build_merged(screens, shared_t, shared_g)
    # drop the planted self-rows, which agree by construction
    m = m[m["name"] != m["Gene"]]
    pr, _, _ = MOD.corr_pair(m["Log2FC_itf"], m["Log2FC_ipsc"])
    sa = MOD.sign_agreement(m["Log2FC_itf"].values, m["Log2FC_ipsc"].values)
    assert abs(pr) < 0.10, "independent screens correlated at %.3f" % pr
    assert abs(sa - 0.5) < 0.05, "independent screens agreed in sign at %.3f" % sa


# --------------------------------------------------------------------------
# 6-9: estimator correctness
# --------------------------------------------------------------------------
def test_06_wald_se_matches_hand_computation():
    """SE = |beta|/z.  For beta=1.959963985 and p=0.05 the SE is exactly 1."""
    se = MOD.wald_se(np.array([1.959963984540054]), np.array([0.05]))
    assert se[0] == pytest.approx(1.0, rel=1e-9)
    se2 = MOD.wald_se(np.array([-2.5758293035489004]), np.array([0.01]))
    assert se2[0] == pytest.approx(1.0, rel=1e-9)


def test_07_wald_se_is_infinite_not_small_when_p_is_one():
    """An uninformative row must produce an INFINITE standard error.  If it
    produced a small one, the heterogeneity test would call an uninformative
    screen a disagreement, manufacturing irreproducibility that is not there."""
    se = MOD.wald_se(np.array([0.8]), np.array([1.0]))
    assert not np.isfinite(se[0])
    d = 0.8
    z = d / math.sqrt(0.2 ** 2 + float(se[0]) ** 2)
    assert z == 0.0


def test_08_heterogeneity_never_calls_disagreement_on_an_uninformative_row():
    """End-to-end guard on the same failure: a row where one screen carries no
    information must classify as underpowered, never as disagreement."""
    a = pd.DataFrame(
        {
            "Gene": ["G1"],
            "Log2CPM": [3.0],
            "Log2FC": [3.0],
            "P Value": [1e-40],
            "FDR": [1e-38],
            "name": ["T00"],
        }
    )
    b = pd.DataFrame(
        {
            "Gene": ["G1"],
            "Log2CPM": [3.0],
            "Log2FC": [0.9],
            "P Value": [1.0],
            "FDR": [1.0],
            "name": ["T00"],
        }
    )
    m = MOD.build_merged({"iTF_CROPseq": a, "iPSC_CROPseq": b}, ["T00"], ["G1"])
    d = m["Log2FC_ipsc"].values - m["Log2FC_itf"].values
    sd = np.sqrt(m["se_itf"].values ** 2 + m["se_ipsc"].values ** 2)
    z = d / sd
    assert abs(float(z[0])) <= MOD.Z_CRIT


def test_09_sign_agreement_ignores_zeros_and_survives_degenerate_input():
    assert MOD.sign_agreement([1.0, -1.0, 0.0], [1.0, -1.0, 5.0]) == 1.0
    assert MOD.sign_agreement([1.0, -1.0], [-1.0, 1.0]) == 0.0
    assert math.isnan(MOD.sign_agreement([0.0, 0.0], [0.0, 0.0]))


# --------------------------------------------------------------------------
# 10-13: definitional integrity
# --------------------------------------------------------------------------
def test_10_engagement_requires_knockdown_not_merely_significance():
    """A CRISPRi target whose own transcript goes significantly UP is not
    engaged.  Counting it would inflate the engagement rate, which is the single
    number that decides whether the screens can be truth for anything."""
    df = pd.DataFrame(
        {
            "Gene": ["T00", "T01"],
            "Log2CPM": [3.0, 3.0],
            "Log2FC": [+2.0, -2.0],
            "P Value": [1e-30, 1e-30],
            "FDR": [1e-28, 1e-28],
            "name": ["T00", "T01"],
        }
    )
    sr = MOD._self_rows(df)
    eng = sr[(sr["self_log2fc"] < 0) & (sr["self_fdr"] < MOD.FDR_ALPHA)]
    assert sorted(eng["name"]) == ["T01"]


def test_11_self_row_match_is_exact_not_substring():
    """STAT2P1 is a pseudogene, not STAT2.  A substring or prefix match would
    silently fabricate engagement evidence."""
    df = pd.DataFrame(
        {
            "Gene": ["STAT2P1", "STAT2"],
            "Log2CPM": [1.0, 1.0],
            "Log2FC": [-3.0, -0.01],
            "P Value": [1e-40, 0.9],
            "FDR": [1e-38, 1.0],
            "name": ["STAT2", "STAT2"],
        }
    )
    sr = MOD._self_rows(df)
    assert len(sr) == 1
    assert float(sr.iloc[0]["self_log2fc"]) == pytest.approx(-0.01)


def test_12_jnum_refuses_to_write_a_number_it_does_not_have():
    """Provenance rule: an unmeasured quantity is recorded as null, never as a
    plausible-looking value."""
    assert MOD.jnum(float("nan")) is None
    assert MOD.jnum(float("inf")) is None
    assert MOD.jnum(float("-inf")) is None
    assert MOD.jnum(None) is None
    assert MOD.jnum(np.float64(2.5)) == 2.5
    assert MOD.jnum(np.int64(3)) == 3


def test_13_build_merged_refuses_a_duplicated_key():
    """The paired analysis assumes one row per (target, readout gene).  A
    duplicate would silently fan out the join and inflate every count."""
    a = _synth(31, n_targets=2, n_genes=10)
    b = a.copy()
    b = pd.concat([b, b.iloc[[0]]], ignore_index=True)
    with pytest.raises(Exception):
        MOD.build_merged(
            {"iTF_CROPseq": a, "iPSC_CROPseq": b},
            sorted(set(a["name"])),
            sorted(set(a["Gene"])),
        )


# --------------------------------------------------------------------------
# 14-16: the verdict must be earned, not hard-coded
# --------------------------------------------------------------------------
def _verdict_from(receipt_like, per_target):
    MOD.verdict(receipt_like, per_target)
    return receipt_like["VERDICT"]


def _skeleton(n_engaged, med_pearson, sign_agr, n_targets_joint, independent, n_shared=31):
    return {
        "S1_identity": {
            "shared_targets_by_display_name": n_shared,
            "shared_targets_by_ensembl_id": n_shared - 1,
        },
        "S2_engagement": {
            "iTF_CROPseq": {"engaged_fdr_lt_0.05_and_down": 3, "n_targets": n_shared},
            "iPSC_CROPseq": {"engaged_fdr_lt_0.05_and_down": 3, "n_targets": n_shared},
            "JOINT_CROPseq": {
                "n_jointly_engaged": n_engaged,
                "jointly_engaged_targets": ["T%02d" % i for i in range(n_engaged)],
                "engaged_in_exactly_one": [],
                "not_measurable_in_at_least_one": [],
            },
        },
        "S3_concordance": {
            "pooled_pearson_log2fc": med_pearson,
            "pooled_spearman_log2fc": med_pearson,
            "per_target_pearson_median": med_pearson,
            "per_target_pearson_max": max(med_pearson, 0.0),
            "pooled_sign_agreement_all_rows": sign_agr,
            "n_sig_both": 100,
            "jointly_significant_rows_by_target": {"T00": 100},
            "n_targets_with_any_jointly_significant_row": n_targets_joint,
            "n_targets_with_zero_jointly_significant_rows": n_shared - n_targets_joint,
            "largest_target_share_of_jointly_significant_rows": 1.0,
        },
        "S4_power": {
            "non_replication_itf_sig_not_ipsc_sig": 10,
            "non_replication_classification": {"DISAGREEMENT": 1},
            "jointly_significant_classification": {"CONSISTENT": 100},
            "z_crit": MOD.Z_CRIT,
        },
        "S6_independence": {
            "independent_replication": independent,
            "independence_verdict": "fixture",
        },
    }


def test_14_verdict_says_yes_when_the_evidence_supports_it():
    """POSITIVE CONTROL on the decision rule itself.  A verdict function that
    always returns NO is not a verdict.  Fed screens that agree, are engaged and
    are independent, it must return YES."""
    pt = pd.DataFrame({"target": ["T%02d" % i for i in range(31)], "pearson": [0.8] * 31})
    v = _verdict_from(_skeleton(25, 0.80, 0.90, 25, True), pt)
    assert v["answer"] == "YES"
    assert v["criteria_passed"] == v["criteria_total"]


def test_15_verdict_can_return_the_subset_answer():
    """The middle answer must be reachable, otherwise 'only for this subset' was
    never actually on the table."""
    pt = pd.DataFrame(
        {
            "target": ["T%02d" % i for i in range(31)],
            "pearson": [0.8] * 8 + [0.01] * 23,
        }
    )
    v = _verdict_from(_skeleton(8, 0.05, 0.52, 3, False), pt)
    assert v["answer"] == "ONLY_FOR_THIS_SUBSET"
    assert v["qualifying_subset_size"] == 8


def test_16_verdict_says_no_on_the_real_data(receipt):
    v = receipt["VERDICT"]
    assert v["answer"] == "NO"
    assert v["criteria_passed"] == 0
    assert v["qualifying_subset_size"] == 0


# --------------------------------------------------------------------------
# 17-21: the executed receipt must describe what actually ran
# --------------------------------------------------------------------------
def test_17_receipt_records_every_input_digest_and_all_match(receipt):
    assert receipt["status"] == "COMPLETE"
    keys = {i["key"] for i in receipt["inputs"]}
    assert keys == set(MOD.FROZEN_INPUTS) | set(MOD.FROZEN_REFS) | {"crisprbrain_catalog"}
    assert all(i["digest_match"] for i in receipt["inputs"])
    for i in receipt["inputs"]:
        assert len(i.get("sha256_decompressed", i.get("sha256", ""))) == 64


def test_18_receipt_declares_unmeasured_quantities_as_unmeasured(receipt):
    """Cell counts and preparation counts are not in the deposit.  They must be
    recorded as UNMEASURED, never estimated."""
    s4 = receipt["S4_power"]
    s6 = receipt["S6_independence"]
    assert s4["cell_and_guide_counts_per_target"] == "NOT_DEPOSITED"
    assert s6["differentiation_preparations_per_model"].startswith("UNMEASURED")
    assert s6["cells_per_target"].startswith("UNMEASURED")
    blob = json.dumps(receipt)
    assert "ESTIMATED" not in blob.upper().replace("UNDERESTIMATED", "")


def test_19_depositor_prose_is_labelled_as_prose_not_measurement(receipt):
    """The only cell counts that exist are the depositors' own claims.  They must
    be labelled so they cannot be read as this run's measurements."""
    s4 = receipt["S4_power"]
    assert "depositor_stated_counts_NOT_MEASURED_HERE" in s4
    assert "DEPOSITOR_PROSE_READ_VERBATIM" in s4["depositor_stated_counts_status"]
    vals = s4["depositor_stated_counts_NOT_MEASURED_HERE"]
    assert vals["iTF-Microglia-CROP-seq-CRISPRi"]["single_sgrna_cells"] != "NOT_STATED"


def test_20_preliminary_claims_are_checked_not_inherited(receipt):
    chk = receipt["PRELIMINARY_CLAIMS_CHECK"]["checks"]
    assert len(chk) >= 7
    for c in chk:
        assert c["recomputed_here"] is not None
        assert c["verdict"] in {
            "CONFIRMED",
            "CONFIRMED_WITH_CORRECTION",
            "DISCREPANCY_EXPLAINED",
            "DISCREPANCY_EXPLAINED_WORSE_THAN_REPORTED",
            "DISCREPANCY_UNEXPLAINED",
        }
    # the discrepancies must be explained by the FDR cut, reproducibly
    sens = {
        round(s["fdr_alpha"], 4): s
        for s in receipt["S3_concordance"]["fdr_threshold_sensitivity"]
    }
    assert sens[0.1]["n_sig_both"] == 72
    assert sens[0.1]["overlap_itf_to_ipsc"] == pytest.approx(0.072, abs=5e-4)
    assert sens[0.05]["n_sig_both"] == 54


def test_21_permutation_control_is_seeded_and_beats_nothing_by_much(receipt):
    """The pooled correlation is partly shared gene-level structure.  The
    permutation null must be recorded, seeded, and the observed value must be
    reported against it rather than on its own."""
    s3 = receipt["S3_concordance"]
    assert s3["permutation_seed"] == MOD.PERM_SEED
    assert s3["n_permutations"] >= 100
    obs = s3["mean_per_target_pearson_observed"]
    null = s3["mean_per_target_pearson_permuted_mean"]
    assert obs is not None and null is not None
    # the target-specific increment over permuted labels must be reported and,
    # on this data, must be small in absolute terms
    assert obs - null < 0.10


def test_22_positive_control_self_concordance_is_recorded_as_one(receipt):
    pc = receipt["POSITIVE_CONTROLS"]
    assert pc["self_concordance_pearson_must_be_1"] == pytest.approx(1.0, abs=1e-9)
    assert pc["self_concordance_spearman_must_be_1"] == pytest.approx(1.0, abs=1e-12)
    assert pc["self_concordance_sign_agreement_must_be_1"] == 1.0
    # and the format control must show engagement IS detectable in this schema
    assert pc["day8_format_control_engaged"] > receipt["S2_engagement"]["iTF_CROPseq"][
        "engaged_fdr_lt_0.05_and_down"
    ]


def test_23_identity_rule_does_not_rely_on_display_names_alone(receipt):
    s1 = receipt["S1_identity"]
    assert s1["shared_targets_by_ensembl_id"] <= s1["shared_targets_by_display_name"]
    assert s1["symbols_mapping_to_multiple_ensembl_ids"] == {}
    assert "ARID5B" in s1["targets_without_deposited_guide_evidence_iTF"]
    # readout identity limitation must be stated, not glossed
    assert "NOT UPGRADEABLE" in s1["readout_identity_rule"]
    assert s1["readout_universe_iTF"]["n_case_insensitive"] == s1["readout_universe_iTF"]["n"]


def test_24_independence_claim_is_negative_and_justified(receipt):
    s6 = receipt["S6_independence"]
    assert s6["independent_replication"] is False
    assert s6["shared_guide_library_row_for_row_identical"] is True
    assert s6["n_targeting_genes_in_library"] == 30
    assert s6["non_targeting_guides"] == 5
    assert set(s6["guides_per_target_distribution"]) == {"2"}
    # and the cited-not-measured statement must be marked as such
    assert "NOT recomputed here" in s6["shared_vector_and_parental_line"]
