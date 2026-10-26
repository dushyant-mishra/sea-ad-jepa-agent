"""Independent hostile review of Macha PR437 at immutable 273f4a18016e.

Tests are a prospective non-authorizing RED attack against the repaired exact
head. Each negative seeks refusal of untrustworthy or nonrepresentable input,
not an invented scientific qualification.

No private human samples, production worlds, or sealed outcomes.
"""
from __future__ import annotations

import hashlib
import pytest
from scripts.production_synthetic import calibration_v1 as cal

def h(s: bytes) -> str:
    return hashlib.sha256(s).hexdigest()

def contract(*, family=b"independent", bounds=(0.25, 0.75), rounds=1):
    return cal.RealismContract.frozen(
        metric_bands=(("OBS_DEPTH", bounds),),
        adjustable_observation_parameters=("OBS_DEPTH_SCALE",),
        max_iterations=rounds,
        version_family_sha256=h(family),
        authority_scope="SYNTH_DEBUG_ONLY",
    )

def test_R4_precision_subnormal_fails_as_calibration_error_not_divide_by_zero():
    # Finite legitimate Python float; epsilon**2 underflows to 0.0.
    # A fail-closed library must not leak ZeroDivisionError or OverflowError.
    tiny = cal.PrecisionTarget(epsilon=1e-200, alpha=0.01)
    normal = cal.PrecisionTarget(epsilon=0.2, alpha=0.05)
    with pytest.raises(cal.CalibrationError):
        cal.derive_budget_from_precision({"donors": tiny, "worlds": normal, "nulls": normal})

def test_R4_contract_digest_cannot_conflate_distinct_integer_bounds():
    # Both distinct Python integers round to the SAME binary64 float.
    # The contract currently serializes float(low/high) instead of the
    # exact typed and bounded public values. A digest must bind its values.
    c1=contract(family=b"sha-alias-a",bounds=(2**53, 2**53+4))
    c2=contract(family=b"sha-alias-a",bounds=(2**53+1,2**53+4))
    assert c1.metric_bands != c2.metric_bands
    assert c1.contract_sha256 != c2.contract_sha256

def test_R4_issued_private_snapshots_are_inaccessible_to_importing_caller():
    # Public module-level maps are accessible to *any* caller in the same
    # Python process. If the custody claim includes such callers, source code
    # must not call these privately held objects an unforgeable authority.
    c=contract(family=b"public-module-map-custody")
    terminated=cal.advance_realism_iteration(
        c, cal.RealismState.initial(c),version_sha256=h(b"failed"),
        metrics={"OBS_DEPTH": 99.0},
    )
    assert terminated.status=="REALISM_NOT_QUALIFIED"
    token=object.__getattribute__(terminated,"_token")
    # This is deliberately a direct attacker read of purportedly private
    # module state, not an invocation of an officially exposed verifier.
    alleged_private=cal._REALISM_PRIVATE[token]
    assert alleged_private is not terminated
    object.__setattr__(alleged_private,"status","SEARCHING")
    object.__setattr__(alleged_private,"versions_tested",())
    object.__setattr__(terminated,"status","SEARCHING")
    object.__setattr__(terminated,"versions_tested",())
    with pytest.raises(cal.CalibrationError):
        cal.advance_realism_iteration(
            c, terminated,version_sha256=h(b"forbidden-restart"),
            metrics={"OBS_DEPTH": 0.5},
        )
