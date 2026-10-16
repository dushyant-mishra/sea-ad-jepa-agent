"""Proof that each Lane A control detects the thing it claims to detect.

Every control in the decision sheet is run against a synthetic population in which
its target failure mode is *planted*, and against a healthy population in which it
is absent. A control must fire on the planted failure and stay quiet on the healthy
one. A control that does only one of those is not evidence, and one of the controls
originally specified turns out to do only one of those; that is recorded here as a
failing-by-design case with its own test rather than quietly dropped.

Synthetic structure only. No FULL104, no protected outcome, no training.
"""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "scripts/v5/lane_a/v29_lane_a_control_sensitivity_fixture_v1.py"

_spec = importlib.util.spec_from_file_location("lane_a_control_fixture", FIXTURE)
fx = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(fx)

_EVAL_CACHE: dict = {}
_TARGET_CACHE: dict = {}


def result(regime: str) -> dict:
    if regime not in _EVAL_CACHE:
        _EVAL_CACHE[regime] = fx.evaluate(regime)
    return _EVAL_CACHE[regime]


def population_and_targets(regime: str):
    if regime not in _TARGET_CACHE:
        pop = fx.build_population()
        _TARGET_CACHE[regime] = (pop, fx.build_targets(pop, regime))
    return _TARGET_CACHE[regime]


def fires(regime: str, condition: str) -> bool:
    return fx.control_fires(result(regime), condition)


# --------------------------------------------------------------------------- #
# The harness itself must not manufacture signal
# --------------------------------------------------------------------------- #

def test_null_fixture_produces_no_signal():
    """On a target that depends on nothing, the probe must explain nothing."""
    assert result("PURE_NOISE")["FULL"]["score"] < 0.05


def test_healthy_fixture_produces_strong_signal():
    """Positive control for the harness: planted query-local structure is recovered."""
    assert result("QUERY_LOCAL")["FULL"]["score"] > 0.5


def test_every_condition_sees_the_same_population_and_split():
    """Common random numbers: only the ablated channel may differ."""
    first = fx.build_population()
    second = fx.build_population()
    assert (first.counts == second.counts).all()
    assert (first.donor_of_cell == second.donor_of_cell).all()
    assert (first.queries == second.queries).all()


def test_donor_is_the_independent_unit_not_the_cell():
    scores = fx.per_donor_scores(*population_and_targets("QUERY_LOCAL"), "FULL")
    assert len(scores) == fx.FIXTURE_HELD_OUT_DONORS
    assert fx.FIXTURE_HELD_OUT_DONORS < fx.FIXTURE_DONORS
    pop, _ = population_and_targets("QUERY_LOCAL")
    assert pop.n_cells > fx.FIXTURE_DONORS  # cells are nested, not independent


# --------------------------------------------------------------------------- #
# C1 identity-only
# --------------------------------------------------------------------------- #

def test_c1_identity_only_fires_when_the_target_is_address_identity():
    assert fires("IDENTITY_ONLY", "IDENTITY_ONLY")


def test_c1_identity_only_stays_quiet_on_a_healthy_target():
    assert not fires("QUERY_LOCAL", "IDENTITY_ONLY")


def test_c1_identity_only_stays_quiet_on_a_cell_level_target():
    """It must not fire for the wrong reason: a global target is C2's failure, not C1's."""
    assert not fires("GLOBAL_ONLY", "IDENTITY_ONLY")


# --------------------------------------------------------------------------- #
# C2 global-context-only: the control that does NOT discriminate
# --------------------------------------------------------------------------- #

def test_c2_global_context_only_fails_to_fire_on_its_own_planted_failure():
    """Recorded defect, not an accident.

    With a query-conditioned predictor, a pooled cell summary that carries the
    cell's state is sufficient to emit a query-local answer, because the query
    conditioning supplies the per-address read-out. So global-context-only cannot
    separate "the target has no query-local content" from "the target's query-local
    content is computable from the cell's global state". It stays quiet on the very
    regime it was meant to catch.
    """
    assert not fires("GLOBAL_ONLY", "GLOBAL_CONTEXT_ONLY")


def test_c2_undercapacity_summary_can_never_fire():
    """An under-capacity pooled summary looks worse than full for numerical reasons.

    It therefore always shows a positive delta and never fires, which would wrongly
    credit the construction. Capacity matching is a requirement, not a detail.
    """
    for regime in ("QUERY_LOCAL", "GLOBAL_ONLY", "TECHNICAL_ONLY"):
        assert not fires(regime, "GLOBAL_CONTEXT_ONLY_UNDERCAPACITY")


def test_c2_undercapacity_is_strictly_weaker_than_capacity_matched():
    for regime in ("QUERY_LOCAL", "GLOBAL_ONLY", "TECHNICAL_ONLY"):
        rows = result(regime)
        assert (
            rows["GLOBAL_CONTEXT_ONLY_UNDERCAPACITY"]["score"]
            < rows["GLOBAL_CONTEXT_ONLY"]["score"]
        )


# --------------------------------------------------------------------------- #
# C2B query exchangeability: the replacement that does discriminate
# --------------------------------------------------------------------------- #

def test_c2b_query_exchangeability_fires_on_a_cell_level_target():
    outcome = fx.query_exchangeability(*population_and_targets("GLOBAL_ONLY"))
    assert outcome["fires"]


def test_c2b_query_exchangeability_fires_on_a_technical_target():
    outcome = fx.query_exchangeability(*population_and_targets("TECHNICAL_ONLY"))
    assert outcome["fires"]


def test_c2b_query_exchangeability_fires_on_an_identity_target():
    outcome = fx.query_exchangeability(*population_and_targets("IDENTITY_ONLY"))
    assert outcome["fires"]


def test_c2b_query_exchangeability_stays_quiet_on_a_healthy_target():
    outcome = fx.query_exchangeability(*population_and_targets("QUERY_LOCAL"))
    assert not outcome["fires"]
    assert outcome["own_query_score"] > outcome["wrong_query_score"]


def test_c2b_catches_what_c2_misses():
    """The whole point: on GLOBAL_ONLY, C2 is silent and C2B fires."""
    assert not fires("GLOBAL_ONLY", "GLOBAL_CONTEXT_ONLY")
    assert fx.query_exchangeability(*population_and_targets("GLOBAL_ONLY"))["fires"]


# --------------------------------------------------------------------------- #
# C3 technical-only
# --------------------------------------------------------------------------- #

def test_c3_technical_only_fires_when_the_target_is_a_measurement_state_object():
    assert fires("TECHNICAL_ONLY", "TECHNICAL_ONLY")


def test_c3_technical_only_stays_quiet_on_a_healthy_target():
    assert not fires("QUERY_LOCAL", "TECHNICAL_ONLY")


def test_c3_technical_only_stays_quiet_on_a_molecular_cell_level_target():
    assert not fires("GLOBAL_ONLY", "TECHNICAL_ONLY")


# --------------------------------------------------------------------------- #
# C4 remaining-RNA necessity
# --------------------------------------------------------------------------- #

def test_c4_rna_necessity_fires_when_the_target_ignores_rna():
    assert fires("IDENTITY_ONLY", "RNA_SHUFFLED_WITHIN_CELL")


def test_c4_rna_necessity_fires_on_the_null_target():
    assert fires("PURE_NOISE", "RNA_SHUFFLED_WITHIN_CELL")


def test_c4_rna_necessity_stays_quiet_when_rna_is_genuinely_used():
    assert not fires("QUERY_LOCAL", "RNA_SHUFFLED_WITHIN_CELL")
    assert not fires("GLOBAL_ONLY", "RNA_SHUFFLED_WITHIN_CELL")


def test_c4_within_cell_shuffle_leaves_depth_and_detection_exactly_unchanged():
    """The shuffle must change only molecular content, never a technical channel."""
    import numpy as np

    pop, _ = population_and_targets("QUERY_LOCAL")
    rng = np.random.default_rng(1)
    visible = fx._log1p_visible(pop, int(pop.queries[0]))
    shuffled = fx._shuffle_within_cell(visible, rng)
    assert np.allclose(visible.sum(axis=1), shuffled.sum(axis=1))
    assert np.allclose((visible > 0).sum(axis=1), (shuffled > 0).sum(axis=1))
    assert not np.allclose(visible, shuffled)


# --------------------------------------------------------------------------- #
# C5 leak injection: the positive control that must succeed
# --------------------------------------------------------------------------- #

def test_c5_leak_detector_is_sensitive_when_the_target_depends_on_the_hidden_count():
    assert fx.leak_detector_is_sensitive(result("QUERY_SCALAR"))


def test_c5_leak_injection_gain_is_large_when_the_target_is_the_hidden_scalar():
    assert result("QUERY_SCALAR")["LEAKED"]["score"] - result("QUERY_SCALAR")["FULL"]["score"] > 0.3


def test_c5_leak_detector_is_sensitive_on_a_healthy_target_too():
    assert fx.leak_detector_is_sensitive(result("QUERY_LOCAL"))


def test_c5_leak_detector_is_not_trivially_always_positive():
    """If injection always helped, the positive control would prove nothing."""
    assert not fx.leak_detector_is_sensitive(result("IDENTITY_ONLY"))
    assert not fx.leak_detector_is_sensitive(result("PURE_NOISE"))


# --------------------------------------------------------------------------- #
# C6 donor / cell-key cheat
# --------------------------------------------------------------------------- #

def test_c6_donor_key_fires_when_the_target_carries_no_cell_specific_content():
    assert fires("IDENTITY_ONLY", "DONOR_KEY_ONLY")


def test_c6_donor_key_stays_quiet_on_a_cell_specific_target():
    assert not fires("QUERY_LOCAL", "DONOR_KEY_ONLY")
    assert not fires("GLOBAL_ONLY", "DONOR_KEY_ONLY")


# --------------------------------------------------------------------------- #
# D7 pre-training teacher-only screen, and its tested limitation
# --------------------------------------------------------------------------- #

def test_screen_finds_query_local_structure_when_it_is_present():
    _, targets = population_and_targets("QUERY_LOCAL")
    assert fx.variance_decomposition(targets)["interaction_share"] > 0.5


def test_screen_reports_a_cell_level_target_as_cell_level():
    _, targets = population_and_targets("GLOBAL_ONLY")
    shares = fx.variance_decomposition(targets)
    assert shares["cell_share"] > 0.9
    assert shares["interaction_share"] < 0.05


def test_screen_reports_an_address_level_target_as_address_level():
    _, targets = population_and_targets("IDENTITY_ONLY")
    shares = fx.variance_decomposition(targets)
    assert shares["address_share"] > 0.9
    assert shares["interaction_share"] < 0.05


def test_screen_reports_a_technical_target_as_cell_level():
    _, targets = population_and_targets("TECHNICAL_ONLY")
    assert fx.variance_decomposition(targets)["cell_share"] > 0.9


def test_screen_cannot_separate_interaction_from_noise_without_replicates():
    """Documented limitation, asserted so it cannot be forgotten.

    Pure noise also shows a high interaction share. The screen is only
    interpretable next to the probe score, which is near zero on pure noise and
    high on genuine query-local structure.
    """
    _, noise_targets = population_and_targets("PURE_NOISE")
    assert fx.variance_decomposition(noise_targets)["interaction_share"] > 0.5
    assert result("PURE_NOISE")["FULL"]["score"] < 0.05
    assert result("QUERY_LOCAL")["FULL"]["score"] > 0.5


# --------------------------------------------------------------------------- #
# The healthy construction must survive every negative control at once
# --------------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "condition",
    ["IDENTITY_ONLY", "TECHNICAL_ONLY", "RNA_SHUFFLED_WITHIN_CELL", "DONOR_KEY_ONLY"],
)
def test_healthy_construction_survives_every_negative_control(condition):
    assert not fires("QUERY_LOCAL", condition)


@pytest.mark.parametrize(
    "regime,condition",
    [
        ("IDENTITY_ONLY", "IDENTITY_ONLY"),
        ("TECHNICAL_ONLY", "TECHNICAL_ONLY"),
        ("IDENTITY_ONLY", "RNA_SHUFFLED_WITHIN_CELL"),
        ("IDENTITY_ONLY", "DONOR_KEY_ONLY"),
    ],
)
def test_each_planted_failure_is_caught_by_its_own_control(regime, condition):
    assert fires(regime, condition)


# --------------------------------------------------------------------------- #
# Fixture constants are not project parameters
# --------------------------------------------------------------------------- #

def test_no_forbidden_historical_or_synthetic_constant_appears_in_the_fixture():
    text = FIXTURE.read_text(encoding="utf-8")
    for banned in ("0.40", "0.99", "0.996", "128x8"):
        assert banned not in text, banned


def test_fixture_declares_it_is_not_full104_and_trains_nothing():
    text = FIXTURE.read_text(encoding="utf-8")
    assert "It is not FULL104" in text
    assert "It trains nothing" in text
    assert "TRAINING=OFF" in text
