"""Declared trust model for calibration_v1 custody (response to independent PR #439 R4-3).

The module detects cooperative-caller mutation of issued handles. It does not,
and must not claim to, protect against hostile code in the same interpreter.
These tests pin that declaration so it cannot silently drift into an overclaim.
"""
from __future__ import annotations

import hashlib
import inspect

from scripts.production_synthetic import calibration_v1 as cal


def test_trust_model_is_declared_and_narrow():
    assert cal.HOSTILE_SAME_PROCESS_PROTECTION is False
    assert cal.TRUST_MODEL == "COOPERATIVE_SAME_PROCESS_CALLERS__FIXTURE_ONLY__NO_HOSTILE_CALLER_PROTECTION"


def test_authority_bearing_outputs_carry_the_trust_model():
    raw = b"DUMMY"
    sha = hashlib.sha256(raw).hexdigest()
    art = cal.CalibrationArtifact(sha, "DUMMY_SCOPE", ("F1",), "CALIBRATION_FIT", "OBSERVATION_DEPTH", (),
                                  "AUTHENTICATED_EMPIRICAL_CALIBRATION")
    check = cal.validate_calibration_firewall(
        art, raw_bytes=raw, independently_pinned_sha256=sha, expected_source_scope="DUMMY_SCOPE",
        eligible_fit_donors=("F1",),
        protected_partitions={"VALIDATION": ("V",), "ORACLE": ("O",), "RESERVED": ("R",), "DEVELOPMENT": ("D",)})
    assert check.trust_model == cal.TRUST_MODEL
    c = cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", (0.25, 0.75)),), adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=1, version_family_sha256=hashlib.sha256(b"tm").hexdigest(), authority_scope="SYNTH_DEBUG_ONLY")
    assert cal.RealismState.initial(c).trust_model == cal.TRUST_MODEL


def test_source_makes_no_unqualified_unreachability_claim():
    text = inspect.getsource(cal)
    for claim in ("never leave the module", "never leaves the module", "caller cannot edit it"):
        assert claim not in text, f"overclaiming custody language remains: {claim!r}"
    assert "NOT a security boundary" in text
