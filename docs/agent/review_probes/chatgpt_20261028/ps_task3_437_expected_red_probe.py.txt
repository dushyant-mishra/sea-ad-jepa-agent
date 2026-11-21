"""Independent ChatGPT RED probes on Macha PR437 exact source.

All values are synthetic. These tests intentionally FAIL until the exposed
fixture-consistency and tunable-parameter contracts are repaired. No human
donor, pathology, latent biology, source archive or calibration issuer is used.
"""
from __future__ import annotations

from hashlib import sha256
import pytest

from scripts.production_synthetic import calibration_v1 as cal


def digest(label: bytes) -> str:
    return sha256(label).hexdigest()


def test_r1_distinct_large_integer_universe_statistics_must_not_alias_via_float():
    """2**53 and 2**53+1 are not equal integer observations.

    Casting both to binary64 before comparing erases this difference. This is
    fixture witness correctness, NOT a claim of current human count validity.
    """
    pilot = {"SYNTH_FIT_A": 2**53}
    full = {"SYNTH_FIT_A": 2**53 + 1}
    assert pilot != full
    assert float(pilot["SYNTH_FIT_A"]) == float(full["SYNTH_FIT_A"])
    universe = digest(b"synthetic-universe-not-externally-attested")
    with pytest.raises(cal.CalibrationError):
        cal.validate_address_universe_agnostic(
            "OBSERVATION_MEAN_DEPTH", pilot, full,
            pilot_n_addresses=96, full_n_addresses=41238,
            full_universe_sha256=universe,
            expected_full_universe_sha256=universe,
        )


@pytest.mark.parametrize("forged_observation_name", [
    "OBS_DISEASE_PREVALENCE",
    "OBS_TARGET_WINNER",
])
def test_r2_observation_prefix_cannot_make_biological_tunable_parameters_legal(
    forged_observation_name,
):
    """OBS_ prefix alone must not authorize latent biological search tuning."""
    with pytest.raises(cal.CalibrationError):
        cal.RealismContract.frozen(
            metric_bands=(("OBS_DEPTH", (0.2, 0.8)),),
            adjustable_observation_parameters=(forged_observation_name,),
            max_iterations=1,
            version_family_sha256=digest(forged_observation_name.encode()),
            authority_scope="SYNTH_DEBUG_ONLY",
        )


def test_r3_self_matched_calibration_sha_never_issues_real_empirical_authority():
    """Independent GREEN control: preserve the already accepted fail-closed floor."""
    raw = b"fixture-observation-statistics-not-real-human-data"
    h = sha256(raw).hexdigest()
    artifact = cal.CalibrationArtifact(
        h, "SYNTH_ONLY", ("FAKE_FIT_A",), "CALIBRATION_FIT",
        "OBSERVATION_DEPTH", (), "AUTHENTICATED_EMPIRICAL_CALIBRATION",
    )
    result = cal.validate_calibration_firewall(
        artifact, raw_bytes=raw, independently_pinned_sha256=h,
        expected_source_scope="SYNTH_ONLY",
        eligible_fit_donors=("FAKE_FIT_A",),
        protected_partitions={
            "VALIDATION": ("FAKE_V",), "ORACLE": ("FAKE_O",),
            "RESERVED": ("FAKE_R",), "DEVELOPMENT": ("FAKE_D",),
        },
    )
    assert result.status == cal.UNAUTHENTICATED_FIXTURE
    assert result.authenticated is False
    assert cal.HOSTILE_SAME_PROCESS_PROTECTION is False
    assert cal._AUTHENTICATED_CALIBRATION_REGISTRY == frozenset()
