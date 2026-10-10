"""The recovery pass rules behave as the contract states, on fabricated fit records (no sampler needed):
coverage is judged against the binomial 1% bound, an invented class fails, removing labels must raise the
residual, and one undiagnosed fit blocks the whole suite."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))
import v79_recovery_rules as R  # noqa: E402


def fit_rec(covered=None, cls_q=(0.01, 0.02, 0.03), res_q=(0.4, 0.5, 0.6), diagnosed=True):
    comp = {"cls": dict(planted_and_scored=covered is not None, covered=covered, across_gene_median_q=list(cls_q)),
            "res": dict(planted_and_scored=False, covered=None, across_gene_median_q=list(res_q))}
    return dict(components_result=comp, diagnostics=dict(diagnosed=diagnosed))


def suite(**over):
    base = {"S1_present": fit_rec(covered=[True] * 18 + [False] * 2, cls_q=(0.20, 0.25, 0.30)),
            "S0_class_absent": fit_rec(), "S2_class_permuted": fit_rec(), "S3_donor_only": fit_rec(),
            "S4_operator_only": fit_rec(), "S5_labels_removed": fit_rec(res_q=(0.7, 0.8, 0.9))}
    base.update(over)
    return base


def test_a_well_behaved_suite_passes_every_rule():
    c = R.criteria(suite())
    assert all(v["pass_"] for v in c.values()), {k: v["pass_"] for k, v in c.items()}


def test_coverage_is_judged_against_the_binomial_bound():
    c = R.criteria(suite(S1_present=fit_rec(covered=[True] * 12 + [False] * 8, cls_q=(0.2, 0.25, 0.3))))
    assert not c["S1_present.coverage"]["pass_"]
    # Binomial(20, 0.9): P(X <= 13) is about 0.002 and P(X <= 14) about 0.011, so the 1% quantile is 14
    assert c["S1_present.coverage"]["bound"] == pytest.approx(14 / 20)


def test_an_invented_class_fails():
    c = R.criteria(suite(S0_class_absent=fit_rec(cls_q=(0.15, 0.22, 0.28))))
    assert not c["S0_class_absent.no_invented_class"]["pass_"]


def test_removing_labels_must_raise_the_residual():
    c = R.criteria(suite(S5_labels_removed=fit_rec(res_q=(0.5, 0.55, 0.6))))
    assert not c["S5_labels_removed.labels_matter"]["pass_"]


def test_one_undiagnosed_fit_blocks_the_suite():
    c = R.criteria(suite(S3_donor_only=fit_rec(diagnosed=False)))
    assert not c["all_fits_diagnosed"]["pass_"]
