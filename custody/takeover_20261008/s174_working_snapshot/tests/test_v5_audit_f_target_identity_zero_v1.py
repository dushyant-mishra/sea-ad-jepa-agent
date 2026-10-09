"""Tests for the Audit F target-identity / zero-stratified decomposition.

The decomposition is only useful if it attributes variance to the RIGHT source.
So each test builds a representation whose composition is known by construction
and requires the decomposition to recover it -- including, critically, the
negative cases where a share must come back at zero.

The sharpest of these is ``detection_only``: a representation that responds to
whether the target is on or off, but not at all to how much. If the
decomposition credited that to ``quantitative``, it would report target-specific
quantitative information that does not exist, which is precisely the error this
audit is built to detect in a real teacher.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import importlib.util
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/scripts/audit_f_target_identity_zero_decomposition_20260920.py"
_spec = importlib.util.spec_from_file_location("audit_f", SCRIPT)
audit_f = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(audit_f)


def _decompose(kind: str) -> dict:
    fx = audit_f.make_fixture(kind)
    return audit_f.decompose_stratified(
        representation=fx["representation"], address_code=fx["address_code"],
        context=fx["context"], target_value=fx["target_value"])


def test_fixtures_reproduce_the_authoritative_sparsity():
    """A fixture at the wrong sparsity would not exercise the real problem."""
    fx = audit_f.make_fixture("identity_only")
    assert fx["observed_zero_fraction"] == pytest.approx(
        audit_f.CORE_MEASURED_ZERO_FREQUENCY, abs=0.02), (
        "fixture sparsity must track core_measured_zero_frequency = "
        f"{audit_f.CORE_MEASURED_ZERO_FREQUENCY}")


def test_pure_noise_attributes_essentially_nothing():
    p = _decompose("pure_noise")["pooled"]
    for share in ("share_identity", "share_context", "share_detection", "share_quantitative"):
        assert p[share] < 0.02, f"{share} = {p[share]:.4f} on pure noise"


def test_identity_only_is_attributed_to_identity():
    p = _decompose("identity_only")["pooled"]
    assert p["share_identity"] > 0.95
    assert p["share_context"] < 0.02
    assert p["share_detection"] < 0.02
    assert p["share_quantitative"] < 0.02


def test_context_contribution_is_separated_from_identity():
    p = _decompose("identity_plus_context")["pooled"]
    assert p["share_context"] > 0.5, "context contribution was not recovered"
    assert p["share_identity"] > 0.05, "identity contribution was absorbed"
    assert p["share_detection"] < 0.02 and p["share_quantitative"] < 0.02


def test_detection_only_credits_nothing_to_quantitative():
    """The load-bearing negative case.

    A representation carrying ONLY on/off information must not be reported as
    carrying quantitative target information. Failing this would let a teacher
    that merely memorises detection state look like it had learned expression.
    """
    p = _decompose("detection_only")["pooled"]
    assert p["share_detection"] > 0.1, "detection contribution was not recovered"
    assert p["share_quantitative"] < 0.02, (
        f"quantitative share {p['share_quantitative']:.4f} on a detection-only "
        "representation -- the decomposition is crediting information that does not exist")


def test_quantitative_representation_yields_a_real_quantitative_share():
    p = _decompose("quantitative")["pooled"]
    assert p["share_quantitative"] > 0.05, (
        "a representation that genuinely tracks expression level must produce a "
        "nonzero quantitative share, or the decomposition lacks power")


def test_quantitative_share_is_structurally_zero_on_target_zero_cells():
    """On target-zero cells the value is constant, so nothing can be attributed to it.

    This is the core of the audit: for ~83% of (cell, address) pairs there is no
    quantitative information available even in principle, so whatever the
    representation carries there is identity and context.
    """
    res = _decompose("identity_context_detection_quantitative")
    zero = res["target_observed_zero"]
    assert zero.get("state") != "NOT_MEASURABLE", zero
    assert zero["share_quantitative"] < 1e-6, (
        f"quantitative share {zero['share_quantitative']:.3e} on target-zero cells, "
        "where the target value is identically zero")
    assert zero["share_detection"] < 1e-6, (
        "detection is also constant within the target-zero stratum")
    explained_without_target = zero["share_identity"] + zero["share_context"]
    assert explained_without_target > 0.5, (
        "on target-zero cells the representation should be largely explained by "
        f"identity + context, got {explained_without_target:.4f}")


def test_strata_are_reported_separately_and_never_silently_pooled():
    res = _decompose("identity_context_detection_quantitative")
    assert "target_observed_zero" in res and "target_observed_nonzero" in res
    assert res["observed_zero_fraction"] > 0.5
    n_zero = res["target_observed_zero"]["n"]
    n_nonzero = res["target_observed_nonzero"]["n"]
    assert n_zero + n_nonzero == res["pooled"]["n"], (
        "strata must partition every attempted unit; none may be dropped")


def test_degenerate_stratum_is_not_measurable_rather_than_zero():
    """Missing evidence must never be reported as a measured zero."""
    n = 40
    value = np.zeros(n)            # every target zero -> nonzero stratum is empty
    res = audit_f.decompose_stratified(
        representation=np.random.default_rng(0).normal(size=n),
        address_code=np.tile(np.arange(4), n // 4),
        context=np.random.default_rng(1).normal(size=(n, 2)),
        target_value=value,
    )
    assert res["target_observed_nonzero"]["state"] == "NOT_MEASURABLE"
    assert "reason" in res["target_observed_nonzero"]


def test_real_measurement_is_marked_as_requiring_a_real_teacher():
    assert audit_f.STATUS_NO_TEACHER == "CHANGED_INPUT_REQUIRES_REAL_TEACHER_REQUALIFICATION"
