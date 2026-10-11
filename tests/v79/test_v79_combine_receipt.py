"""The suite receipt: built only from schema-V2 parts sharing one likelihood, frozen sampler configuration, sampler
rules and code snapshot; mixed or live-tree parts and duplicated worlds are refused; a world with no part file is
reported MISSING (a launch failure is never a statistical failure); every fit's diagnostics, A5 use and coverage
are carried. Fabricated parts only (no sampler)."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_recovery_rules as R  # noqa: E402

CFG = dict(name="DETECTION_V2_NC_ALL", sha256="c" * 64)
RULES = dict(version="A5_V2_DIVERGENT_EXTENSION_ESCALATES", sha256="r" * 64)


def fit(name, cls_q=(0.01, 0.02, 0.03), res_q=(0.4, 0.5, 0.6), covered=None, diagnosed=True, extended=False):
    comp = {"cls": dict(planted_and_scored=covered is not None, covered=covered, across_gene_median_q=list(cls_q)),
            "res": dict(planted_and_scored=False, covered=None, across_gene_median_q=list(res_q))}
    diag = dict(diagnosed=diagnosed, worst_rhat=1.004, worst_ess=700, divergences=[0, 0, 0, 0],
                per_site={"mu": dict(max_rhat=1.004, min_ess_bulk=700, min_ess_tail=900)},
                attempts=[dict(target_accept=0.9, extended=False)] + ([dict(target_accept=0.9, extended=True)]
                                                                       if extended else []))
    return {name: dict(scenario=name, modification=None, components_result=comp, diagnostics=diag)}


def part(name, **over):
    kw = {k: over.pop(k) for k in list(over) if k in ("cls_q", "res_q", "covered", "diagnosed", "extended")}
    base = dict(schema="V79_SIMULATION_RECOVERY_V2", likelihood="bernoulli", code_snapshot="abc123",
                sampler_config=dict(CFG), sampler_rules=dict(RULES), counts_loaded=False, fits=fit(name, **kw))
    base.update(over)
    return base


def suite(**over):
    p = {"S1_present": part("S1_present", covered=[True] * 18 + [False] * 2, cls_q=(0.2, 0.25, 0.3), extended=True),
         "S0_class_absent": part("S0_class_absent"), "S2_class_permuted": part("S2_class_permuted"),
         "S3_donor_only": part("S3_donor_only"), "S4_operator_only": part("S4_operator_only"),
         "S5_labels_removed": part("S5_labels_removed", res_q=(0.7, 0.8, 0.9))}
    p.update(over)
    return [v for v in p.values() if v is not None]


def test_a_clean_suite_passes_and_carries_every_fit():
    rec = R.combine_parts(suite())
    assert rec["terminal"] == "PASS" and rec["missing_worlds"] == []
    assert rec["sampler_config"]["name"] == "DETECTION_V2_NC_ALL" and rec["code_snapshot"] == "abc123"
    assert rec["per_fit"]["S1_present"]["a5_extension_used"] is True
    assert rec["per_fit"]["S1_present"]["coverage"] == {"cls": "18/20"}
    assert rec["per_fit"]["S0_class_absent"]["worst_tail_ess"] == 900 and rec["counts_loaded"] is False


@pytest.mark.parametrize("field,value", [("sampler_config", dict(name="DETECTION_V1", sha256="v" * 64)),
                                         ("code_snapshot", "other"), ("likelihood", "gaussian"),
                                         ("sampler_rules", dict(version="old", sha256="o" * 64)),
                                         ("schema", "V79_SIMULATION_RECOVERY_V1")])
def test_mixed_parts_are_refused(field, value):
    with pytest.raises(ValueError):
        R.combine_parts(suite(S4_operator_only=part("S4_operator_only", **{field: value})))


def test_live_tree_and_duplicates_are_refused():
    with pytest.raises(ValueError):
        R.combine_parts([part(n, code_snapshot="LIVE_TREE_NOT_A_SNAPSHOT") for n in R.SCENARIOS_REQUIRED])
    with pytest.raises(ValueError):
        R.combine_parts(suite() + [part("S0_class_absent")])


def test_a_missing_world_is_reported_missing_not_failed():
    rec = R.combine_parts(suite(S3_donor_only=None))
    assert rec["terminal"] == "MISSING_WORLDS" and rec["missing_worlds"] == ["S3_donor_only"] and rec["criteria"] is None


def test_an_undiagnosed_world_fails_the_suite():
    rec = R.combine_parts(suite(S4_operator_only=part("S4_operator_only", diagnosed=False)))
    assert rec["terminal"] == "FAIL" and rec["criteria"]["all_fits_diagnosed"]["pass_"] is False
