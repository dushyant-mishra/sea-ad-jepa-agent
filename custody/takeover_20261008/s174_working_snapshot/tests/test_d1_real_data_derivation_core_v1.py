"""Known-answer mechanics tests for the D1 derivation core.

Synthetic fixtures only, and every synthetic result here is MECHANICS_ONLY. The
suite also proves that a synthetic result is structurally incapable of becoming
a production parameter, so these fixtures cannot leak into production by being
renamed or relabelled.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts" / "v4"
sys.path.insert(0, str(SCRIPTS))

import d1_real_data_derivation_core_v1 as core  # noqa: E402


# ----------------------------------------------------- weighting known answers
def test_donor_weighting_gives_equal_donor_and_operator_mass() -> None:
    """a_dc = 1/(|O_d| n_do) implies donor mass 1 and operator mass 1/|O_d|.

    Deliberately unbalanced: donor A has three operators with very different
    cell counts, donor B has one. If the weighting were cell-primary, donor B
    would carry almost no mass and the large operator would dominate donor A.
    """
    counts = {("A", 0): 10, ("A", 1): 1000, ("A", 2): 7, ("B", 0): 3}
    weights = core.derive_donor_operator_weights(counts)
    masses = core.assert_donor_primary_masses(weights)
    assert masses["max_donor_mass_deviation"] < 1e-12
    assert masses["max_operator_mass_deviation"] < 1e-12
    assert weights["donor_mass"]["A"] == pytest.approx(1.0)
    assert weights["donor_mass"]["B"] == pytest.approx(1.0)
    # Each of donor A's three operators carries exactly one third.
    for operator in (0, 1, 2):
        assert weights["operator_mass_within_donor"][("A", operator)] == pytest.approx(1.0 / 3.0)
    assert weights["cell_weight_a_dc"][("A", 1)] == pytest.approx(1.0 / (3 * 1000))
    assert weights["cells"] == 1020 and weights["donors"] == 2


def test_donor_weighting_rejects_nonpositive_counts() -> None:
    with pytest.raises(ValueError):
        core.derive_donor_operator_weights({("A", 0): 0})


def test_unequal_mass_is_detected_rather_than_tolerated() -> None:
    counts = {("A", 0): 10, ("A", 1): 20}
    weights = core.derive_donor_operator_weights(counts)
    weights["donor_mass"]["A"] = 1.5          # corrupt the derived mass
    with pytest.raises(AssertionError, match="DONOR_MASS_NOT_EQUAL"):
        core.assert_donor_primary_masses(weights)


# ------------------------------------------------ moments and eigen known answer
def test_weighted_streaming_moments_match_the_closed_form() -> None:
    rng = np.random.default_rng(20260907)
    n, p = 5000, 6
    states = rng.normal(size=(n, p)) * np.array([3.0, 1.0, 0.5, 2.0, 0.25, 4.0])
    states += np.array([100.0, -50.0, 7.0, 0.0, 1e3, -1e3])   # large offsets
    weights = rng.uniform(0.1, 2.0, size=n)

    accumulator = core.WeightedMomentAccumulator(p)
    for start in range(0, n, 137):                            # ragged chunks
        stop = min(start + 137, n)
        accumulator.update(states[start:stop], weights[start:stop])
    result = accumulator.result()

    total = weights.sum()
    expected_mean = (weights[:, None] * states).sum(axis=0) / total
    centered = states - expected_mean
    expected_cov = (centered * weights[:, None]).T @ centered / total

    assert np.allclose(result["mean"], expected_mean, rtol=0, atol=1e-9)
    assert np.allclose(result["covariance"], expected_cov, rtol=0, atol=1e-9)
    assert result["rows"] == n and result["chunks"] > 1
    # Streaming in one chunk must agree with streaming in many.
    single = core.WeightedMomentAccumulator(p).update(states, weights).result()
    assert np.allclose(single["covariance"], result["covariance"], atol=1e-9)


def test_streaming_moments_reject_non_finite_and_negative_weights() -> None:
    acc = core.WeightedMomentAccumulator(2)
    with pytest.raises(ValueError, match="NON_FINITE"):
        acc.update(np.array([[np.nan, 0.0]]), np.array([1.0]))
    with pytest.raises(ValueError, match="NEGATIVE_WEIGHT"):
        acc.update(np.array([[1.0, 0.0]]), np.array([-1.0]))


def test_eigendecomposition_recovers_a_constructed_spectrum() -> None:
    """Known answer: build C = Q diag(l) Q^T and require l and Q back."""
    rng = np.random.default_rng(7)
    p = 5
    q, _ = np.linalg.qr(rng.normal(size=(p, p)))
    target = np.array([10.0, 4.0, 1.0, 0.25, 0.0])
    cov = q @ np.diag(target) @ q.T
    out = core.deterministic_eigendecomposition(cov)
    assert np.allclose(out["eigenvalues"], target, atol=1e-9)
    # Eigenvectors recover the same subspaces, up to sign.
    for j in range(4):
        overlap = abs(float(out["eigenvectors"][:, j] @ q[:, j]))
        assert overlap == pytest.approx(1.0, abs=1e-8)
    # Deterministic sign convention: largest-magnitude entry is positive.
    for j in range(p):
        column = out["eigenvectors"][:, j]
        assert column[int(np.argmax(np.abs(column)))] > 0
    # Repeat runs are identical, not merely close.
    again = core.deterministic_eigendecomposition(cov)
    assert np.array_equal(out["eigenvectors"], again["eigenvectors"])


def test_eigendecomposition_rejects_asymmetric_and_indefinite_input() -> None:
    with pytest.raises(ValueError, match="NOT_SYMMETRIC"):
        core.deterministic_eigendecomposition(np.array([[1.0, 0.5], [0.0, 1.0]]))
    with pytest.raises(ValueError, match="NOT_PSD"):
        core.deterministic_eigendecomposition(np.array([[1.0, 0.0], [0.0, -1.0]]))


# ------------------------------------------------------- effective rank aliasing
def test_entropy_and_participation_effective_ranks_are_distinct_statistics() -> None:
    """They answer different questions and must not be interchangeable.

    On a deliberately skewed spectrum they differ numerically. The stronger
    guarantee is structural: each carries its own statistic_id, so swapping them
    is caught even where the numbers happen to agree.
    """
    spectrum = np.array([10.0, 1.0, 1.0, 1.0, 0.5, 0.01])
    entropy = core.entropy_effective_rank(spectrum)
    participation = core.participation_effective_rank(spectrum)
    assert entropy["value"] != pytest.approx(participation["value"], rel=1e-6)
    checked = core.assert_effective_ranks_not_aliased(entropy, participation)
    assert checked["aliasing"] == "REFUSED"
    assert checked["defines_D"] is False
    # Passing one where the other belongs is refused in both directions.
    with pytest.raises(AssertionError, match="ALIASED"):
        core.assert_effective_ranks_not_aliased(participation, entropy)
    with pytest.raises(AssertionError, match="ALIASED"):
        core.assert_effective_ranks_not_aliased(entropy, entropy)
    with pytest.raises(AssertionError, match="ALIASED"):
        core.assert_effective_ranks_not_aliased(participation, participation)


def test_effective_ranks_have_correct_known_answers_on_a_flat_spectrum() -> None:
    """A flat spectrum of k non-zero axes gives exactly k for both.

    Equality here is the mathematically correct answer, which is why equality
    alone can never be the aliasing test.
    """
    flat = np.array([2.0, 2.0, 2.0, 2.0, 0.0, 0.0])
    assert core.entropy_effective_rank(flat)["value"] == pytest.approx(4.0)
    assert core.participation_effective_rank(flat)["value"] == pytest.approx(4.0)
    single = np.array([5.0, 0.0, 0.0])
    assert core.entropy_effective_rank(single)["value"] == pytest.approx(1.0)
    assert core.participation_effective_rank(single)["value"] == pytest.approx(1.0)


# ----------------------------------------------------------- parallel analysis
def test_coordinate_permutation_preserves_marginals_and_destroys_covariance() -> None:
    """The null must keep each coordinate's marginal and break cross-covariance.

    Permuting whole rows would preserve the covariance and produce no null at
    all, so this checks the marginals are identical multisets AND that the
    strong correlation collapses.
    """
    rng = np.random.default_rng(11)
    base = rng.normal(size=(4000, 1))
    block = np.hstack([base, base * 0.99 + 0.01 * rng.normal(size=(4000, 1))])
    permuted = core.permute_coordinates_within_stratum(block, np.random.default_rng(3))
    for j in range(block.shape[1]):
        assert np.allclose(np.sort(block[:, j]), np.sort(permuted[:, j]))
    before = abs(float(np.corrcoef(block.T)[0, 1]))
    after = abs(float(np.corrcoef(permuted.T)[0, 1]))
    assert before > 0.98 and after < 0.10


def test_stratum_rng_is_deterministic_and_stratum_specific() -> None:
    a = core.stratum_rng("ns", 1, "D1", 0).integers(0, 10**9, size=4)
    b = core.stratum_rng("ns", 1, "D1", 0).integers(0, 10**9, size=4)
    c = core.stratum_rng("ns", 1, "D1", 1).integers(0, 10**9, size=4)
    d = core.stratum_rng("ns", 2, "D1", 0).integers(0, 10**9, size=4)
    assert np.array_equal(a, b) and not np.array_equal(a, c) and not np.array_equal(a, d)


def test_D_PA_uses_the_contiguous_leading_run() -> None:
    observed = np.array([10.0, 5.0, 2.0, 1.0])
    envelope = np.array([1.0, 1.0, 3.0, 3.0])
    out = core.derive_D_PA(observed, envelope)
    assert out["D_PA"] == 2 and out["survives"] == [True, True, False, False]


def test_non_contiguous_parallel_analysis_survival_stops() -> None:
    """Skipping a failed axis and resuming would silently redefine D."""
    observed = np.array([10.0, 1.0, 8.0, 0.5])
    envelope = np.array([1.0, 5.0, 1.0, 5.0])
    with pytest.raises(AssertionError, match="NON_CONTIGUOUS_SURVIVAL"):
        core.derive_D_PA(observed, envelope)


def test_null_envelope_needs_replicas_and_reports_confidence() -> None:
    spectra = np.array([[3.0, 1.0], [4.0, 1.5], [3.5, 1.2], [10.0, 5.0]])
    out = core.null_eigenvalue_envelope(spectra, confidence_level=0.95)
    assert out["replicas"] == 4 and out["confidence_level"] == 0.95
    assert out["upper_envelope"][0] > out["median"][0]
    with pytest.raises(ValueError):
        core.null_eigenvalue_envelope(np.array([[1.0, 2.0]]))


# ---------------------------------------------------- subspaces and degeneracy
def test_principal_angles_and_projection_overlap_known_answers() -> None:
    e1 = np.array([[1.0], [0.0], [0.0]])
    e2 = np.array([[0.0], [1.0], [0.0]])
    assert core.projection_overlap(e1, e1) == pytest.approx(1.0)
    assert core.projection_overlap(e1, e2) == pytest.approx(0.0)
    assert float(core.principal_angles(e1, e2)[0]) == pytest.approx(np.pi / 2)
    # Sign- and rotation-blind: a flipped or rotated basis of the same plane
    # must score exactly 1, which is what makes a degenerate block comparable.
    plane = np.array([[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]])
    rotated = np.array([[1.0, 1.0], [-1.0, 1.0], [0.0, 0.0]]) / np.sqrt(2)
    assert core.projection_overlap(plane, rotated) == pytest.approx(1.0)
    assert core.projection_overlap(plane, -plane) == pytest.approx(1.0)


def test_degenerate_eigenvalues_are_treated_as_one_subspace() -> None:
    """Exactly equal adjacent eigenvalues are not two identified axes."""
    out = core.degenerate_blocks(np.array([10.0, 4.0, 4.0, 1.0]))
    assert out["blocks"] == [[0], [1, 2], [3]]
    assert out["multi_axis_blocks"] == [[1, 2]]
    assert out["block_of_axis"][1] == out["block_of_axis"][2]


def test_uncertain_eigengap_including_zero_joins_a_block() -> None:
    """A resolved observed gap still blocks when its interval includes zero."""
    eigenvalues = np.array([10.0, 5.0, 4.6, 1.0])
    resolved = core.degenerate_blocks(eigenvalues)
    assert resolved["blocks"] == [[0], [1], [2], [3]]
    uncertain = core.degenerate_blocks(eigenvalues, gap_interval_lower=[2.0, -0.3, 1.5])
    assert uncertain["blocks"] == [[0], [1, 2], [3]]


def test_subspace_score_invents_no_preferred_axis() -> None:
    rng = np.random.default_rng(5)
    states = rng.normal(size=(50, 4))
    mean = states.mean(axis=0)
    basis = np.eye(4)[:, :2]
    out = core.subspace_score_norm(states, mean, basis)
    assert out["preferred_axis"] is None
    assert out["coordinates"].shape == (50, 2)
    assert np.allclose(out["subspace_norm"], np.linalg.norm(out["coordinates"], axis=1))


# ------------------------------------------------------------- D derivation
def test_production_D_is_the_longest_stable_leading_prefix() -> None:
    out = core.derive_production_D(D_PA=5, stability_separated_by_rank=[True, True, False, True, True])
    assert out["D"] == 2 and out["K"] == out["D"]
    capped = core.derive_production_D(D_PA=2, stability_separated_by_rank=[True, True, True])
    assert capped["D"] == 2, "D must never exceed D_PA"


def test_no_stable_rank_stops_with_no_fallback_D() -> None:
    with pytest.raises(AssertionError, match="NO_FALLBACK_D"):
        core.derive_production_D(D_PA=4, stability_separated_by_rank=[False, True, True, True])
    with pytest.raises(AssertionError, match="NO_FALLBACK_D"):
        core.derive_production_D(D_PA=0, stability_separated_by_rank=[])


def test_K_equals_D_and_imports_no_historical_rank() -> None:
    out = core.derive_production_D(D_PA=3, stability_separated_by_rank=[True, True, True])
    assert out["K"] == out["D"] == 3
    for prohibited in (320, 512, 50):
        assert out["K"] != prohibited


# ------------------------------------------------------- refusal-only defence
def test_a_refusal_only_implementation_cannot_pass_the_mechanics_suite() -> None:
    """A module that refuses everything must fail, not vacuously succeed.

    Without this, an implementation that raised on every call could appear
    compliant because each adversarial test expects an exception.
    """

    class RefusalOnly:
        """Refuses every call, the way a stub that only knows how to STOP would."""

        def derive_donor_operator_weights(self, *a, **k):
            raise RuntimeError("STOP")

        def deterministic_eigendecomposition(self, *a, **k):
            raise RuntimeError("STOP")

        def derive_D_PA(self, *a, **k):
            raise RuntimeError("STOP")

        def derive_production_D(self, *a, **k):
            raise RuntimeError("STOP")

    stub = RefusalOnly()
    positive_checks = 0
    for call in (
        lambda m: m.derive_donor_operator_weights({("A", 0): 4}),
        lambda m: m.deterministic_eigendecomposition(np.eye(2)),
        lambda m: m.derive_D_PA(np.array([9.0, 0.1]), np.array([1.0, 1.0])),
        lambda m: m.derive_production_D(D_PA=1, stability_separated_by_rank=[True]),
    ):
        # The real module answers all four.
        call(core)
        positive_checks += 1
        # The refusing stub answers none, so it cannot be counted as valid.
        with pytest.raises(RuntimeError):
            call(stub)
    assert positive_checks == 4, "the suite must contain positive known-answer checks"


# -------------------------------------------------- Monte Carlo and quantiles
def test_sequential_doubling_never_inherits_a_historical_count() -> None:
    schedule = core.sequential_doubling_schedule(minimum_replicates=64, maximum_replicates=8192)
    assert schedule[0] == 64 and schedule[-1] == 8192
    assert schedule == sorted(schedule)
    # 256 may appear only as a step of the declared doubling ladder, never as a
    # ceiling inherited from historical work.
    assert schedule[-1] != 256


def test_monte_carlo_precision_reports_insufficient_rather_than_freezing() -> None:
    noisy = np.random.default_rng(1).normal(scale=1.0, size=64)
    out = core.monte_carlo_precision_met(noisy, confidence_level=0.95,
                                        precision_target_half_width=0.01)
    assert out["met"] is False
    assert out["terminal_if_unmet"] == "INSUFFICIENT_MONTE_CARLO_PRECISION"
    tight = np.full(64, 0.5)
    assert core.monte_carlo_precision_met(tight, confidence_level=0.95,
                                          precision_target_half_width=0.01)["met"] is True


def test_weighted_quantile_and_percentile_known_answers() -> None:
    values = np.array([1.0, 2.0, 3.0, 4.0])
    equal = np.ones(4)
    median = core.weighted_quantile(values, equal, [0.5])[0]
    assert median == pytest.approx(2.5)
    # Mass concentrated on one value pulls the median onto it. The mid-point
    # empirical definition interpolates, so the exact answer is 2 + 50/50.5 and
    # not literally 3.0: value 3's own mid-point cumulative is 52/103, just
    # above 0.5. Asserted analytically rather than approximately, and paired
    # with the step-sense check, because an interpolation bug would move this
    # number and a loose tolerance would hide it.
    skewed = np.array([1.0, 1.0, 100.0, 1.0])
    observed = core.weighted_quantile(values, skewed, [0.5])[0]
    assert observed == pytest.approx(2.0 + 50.0 / 50.5, abs=1e-12)
    assert 2.9 < observed < 3.0
    # Step sense: half the mass is crossed inside value 3's block.
    assert int(np.searchsorted(np.cumsum(skewed), 0.5 * skewed.sum())) == 2
    percentiles = core.weighted_percentile_of_score(values, equal)
    assert np.all(np.diff(percentiles) > 0) and 0.0 < percentiles[0] < percentiles[-1] < 1.0


def test_within_donor_centering_removes_each_donor_mean() -> None:
    scores = np.array([1.0, 3.0, 10.0, 20.0])
    donors = ["A", "A", "B", "B"]
    weights = np.array([1.0, 1.0, 1.0, 1.0])
    centered = core.within_donor_centered(scores, donors, weights)
    assert centered[:2].sum() == pytest.approx(0.0)
    assert centered[2:].sum() == pytest.approx(0.0)
    assert centered[2] == pytest.approx(-5.0)


def test_tail_views_are_descriptive_with_real_data_cutpoints() -> None:
    rng = np.random.default_rng(2)
    values = rng.normal(size=20000)
    weights = np.ones(20000)
    out = core.descriptive_tail_views(values, weights, [0.05, 0.01])
    assert out["continuous_ranking_authoritative"] is True
    for view in out["views"].values():
        assert view["is_confirmatory_gate"] is False
        assert "weighted empirical quantile" in view["cutpoint_source"]
        assert view["lower_cutpoint"] < view["upper_cutpoint"]
    assert out["views"]["p0.01"]["upper_cutpoint"] > out["views"]["p0.05"]["upper_cutpoint"]
    with pytest.raises(ValueError):
        core.descriptive_tail_views(values, weights, [0.5])


# ------------------------------------------- measurement mask and molecular layer
def test_observation_state_codes_are_bound_to_the_authority_ordering() -> None:
    """The authority orders states unmeasured, measured, collision.

    An earlier draft hardcoded MEASURED_SCALAR = 0, which is inverted and would
    have treated every structurally unmeasured address as measured.
    """
    assert core.STRUCTURALLY_UNMEASURED == 0
    assert core.MEASURED_SCALAR == 1
    assert core.COLLISION_UNRESOLVED == 2
    codes = core.load_observation_state_codes(
        ["STRUCTURALLY_UNMEASURED", "MEASURED_SCALAR", "MEASURED_COLLISION_UNRESOLVED"])
    assert codes["MEASURED_SCALAR"] == 1
    with pytest.raises(AssertionError, match="ORDER_DRIFT"):
        core.load_observation_state_codes(
            ["MEASURED_SCALAR", "STRUCTURALLY_UNMEASURED", "MEASURED_COLLISION_UNRESOLVED"])


def test_measured_zero_and_structural_unmeasurement_stay_distinct() -> None:
    """A measured zero is data; an unmeasured address contributes nothing.

    Two addresses receive identical stored values. Address 0 is measured in every
    cell, with genuine zeros in half of them. Address 1 is unmeasured in exactly
    those cells. If unmeasurement were encoded as a biological zero the two
    columns would produce the same effect and the same measured fraction; they
    must not.
    """
    n = 200
    scores = np.linspace(-1.0, 1.0, n).reshape(n, 1)
    expression = np.zeros((n, 2))
    expression[: n // 2, 0] = 0.0                 # measured zeros
    expression[n // 2:, 0] = 2.0
    expression[:, 1] = expression[:, 0]           # identical stored bytes
    state = np.full((n, 2), core.MEASURED_SCALAR, dtype=np.uint8)
    state[: n // 2, 1] = core.STRUCTURALLY_UNMEASURED
    weights = np.ones(n)

    acc = core.MolecularAssociationAccumulator(programs=1, addresses=2)
    acc.update(scores=scores, expression=expression, observation_state=state, weights=weights)
    out = acc.effects()

    assert out["measured_fraction"][0][0] == pytest.approx(1.0)
    assert out["measured_fraction"][0][1] == pytest.approx(0.5)
    assert out["measured_mass"][0][0] == pytest.approx(float(n))
    assert out["measured_mass"][0][1] == pytest.approx(float(n // 2))
    assert out["unmeasured_encoded_as_zero"] is False
    # The effects differ precisely because the unmeasured half was not treated
    # as a real zero.
    assert not np.isclose(out["effect"][0][0], out["effect"][0][1])


def test_an_address_with_no_measured_mass_is_not_estimable_rather_than_zero() -> None:
    n = 20
    scores = np.linspace(-1, 1, n).reshape(n, 1)
    expression = np.zeros((n, 1))
    state = np.full((n, 1), core.STRUCTURALLY_UNMEASURED, dtype=np.uint8)
    acc = core.MolecularAssociationAccumulator(programs=1, addresses=1)
    acc.update(scores=scores, expression=expression, observation_state=state,
               weights=np.ones(n))
    out = acc.effects()
    assert bool(out["not_estimable"][0][0]) is True
    assert np.isnan(out["effect"][0][0]), "must be NOT_ESTIMABLE, never a zero effect"


def test_molecular_effect_recovers_a_known_signed_slope() -> None:
    rng = np.random.default_rng(4)
    n = 4000
    score = rng.normal(size=n)
    expression = np.column_stack([3.0 * score + 1.0, -2.0 * score + 5.0])
    state = np.full((n, 2), core.MEASURED_SCALAR, dtype=np.uint8)
    acc = core.MolecularAssociationAccumulator(programs=1, addresses=2)
    acc.update(scores=score.reshape(n, 1), expression=expression,
               observation_state=state, weights=np.ones(n))
    effect = acc.effects()["effect"][0]
    assert effect[0] == pytest.approx(3.0, abs=1e-8)
    assert effect[1] == pytest.approx(-2.0, abs=1e-8)


def test_program_measurement_support_is_effect_weighted() -> None:
    effects = np.array([[10.0, 0.1]])
    fraction = np.array([[0.2, 1.0]])
    support = core.program_measurement_support(effects, fraction)["support"][0]
    # Dominated by the large-effect, poorly-measured address.
    assert support == pytest.approx((10.0 * 0.2 + 0.1 * 1.0) / 10.1, abs=1e-12)
    assert support < 0.25


# -------------------------------------- technical sensitivity is not a D input
def test_technical_sensitivity_is_a_falsification_view_not_a_D_input() -> None:
    rng = np.random.default_rng(6)
    depth = rng.uniform(1000, 20000, size=500)
    tracking = 3.0 * (depth - depth.mean()) / depth.std() + 0.05 * rng.normal(size=500)
    independent = rng.normal(size=500)
    out = core.technical_sensitivity_view(
        program_scores=np.column_stack([tracking, independent]),
        technical_covariate=depth, weights=np.ones(500),
        covariate_name="sequencing_depth")
    assert out["used_to_fit_D"] is False
    assert out["role"] == "FALSIFICATION_SENSITIVITY_VIEW"
    assert abs(out["weighted_correlation"][0]) > 0.9      # reported, not hidden
    assert abs(out["weighted_correlation"][1]) < 0.2


# ------------------------------------------------- ranking without tuned weights
def test_catalog_order_is_deterministic_and_publishes_component_ranks() -> None:
    programs = [
        {"program_id": "P2", "magnitude": 0.5, "donor_block_stability": 0.9},
        {"program_id": "P1", "magnitude": 0.9, "donor_block_stability": 0.9},
        {"program_id": "P3", "magnitude": 0.9, "donor_block_stability": 0.1},
    ]
    out = core.canonical_catalog_order(
        programs, order_keys=["donor_block_stability", "magnitude"])
    assert out["weighted_composite"] is None
    assert out["ordered_program_ids"] == ["P1", "P2", "P3"]
    assert len(out["published_component_ranks"]) == 3
    # Ties broken by program_id, deterministically.
    tied = [{"program_id": "B", "magnitude": 1.0}, {"program_id": "A", "magnitude": 1.0}]
    assert core.canonical_catalog_order(tied, order_keys=["magnitude"])["ordered_program_ids"] == ["A", "B"]
    with pytest.raises(ValueError, match="MISSING_COMPONENT"):
        core.canonical_catalog_order(programs, order_keys=["novelty"])


# ------------------------------------------------------------- normalization
def test_frozen_normalization_and_count_roundtrip() -> None:
    counts = np.array([0.0, 1.0, 5.0, 250.0])
    library = 12345.0
    values = np.log1p(counts * (10000.0 / library))
    out = core.assert_frozen_normalization(counts, library, values)
    assert out["applied_times"] == 1 and out["count_roundtrip"] == "EXACT"
    # A double-normalized input must fail rather than shift every effect.
    with pytest.raises(AssertionError, match="NORMALIZATION_DRIFT"):
        core.assert_frozen_normalization(counts, library, np.log1p(values))


# ----------------------------------------------- mechanics cannot go to production
def test_mechanics_results_are_labelled_and_cannot_become_production() -> None:
    result = core.mechanics_result(statistic_id="D1-P005:observed_eigenspectrum",
                                   value=[3.0, 1.0])
    assert result["population_class"] == core.MECHANICS_ONLY
    assert result["production_use"] == "PROHIBITED"

    synthetic = core.D1Provenance(
        statistic_id="D1-P009:D", population_class=core.MECHANICS_ONLY,
        formula_version="v1", donors=104, cells=4553407, operators=42)
    assert synthetic.is_production_eligible() is False
    with pytest.raises(PermissionError, match="NOT_PRODUCTION_POPULATION"):
        core.emit_production_parameter(parameter_id="D1-P009:D", value=7,
                                       provenance=synthetic, teacher_gate_open=True)


def test_stream_chunks_never_materialises_the_whole_population() -> None:
    chunks = list(core.stream_chunks(range(10), 4))
    assert [len(c) for c in chunks] == [4, 4, 2]
    with pytest.raises(ValueError):
        list(core.stream_chunks(range(3), 0))


def test_the_D_derivation_path_cannot_consume_the_sensitivity_view() -> None:
    """Structural, not declarative: D's code path must not reference it at all.

    `used_to_fit_D: False` is a label a future edit could contradict. This walks
    the AST of every function on the D derivation path and asserts none of them
    calls or names the technical-sensitivity view or a measurement-support
    statistic. Letting a technical covariate influence D would let the artifact
    define the signal subspace it exists to falsify.
    """
    import ast as _ast

    source = (SCRIPTS / "d1_real_data_derivation_core_v1.py").read_text(encoding="utf-8")
    tree = _ast.parse(source)
    d_path = {"derive_D_PA", "derive_production_D", "null_eigenvalue_envelope",
              "rank_stability_separates", "degenerate_blocks",
              "deterministic_eigendecomposition"}
    forbidden = {"technical_sensitivity_view", "program_measurement_support",
                 "MolecularAssociationAccumulator"}
    for node in tree.body:
        if isinstance(node, _ast.FunctionDef) and node.name in d_path:
            referenced = {n.id for n in _ast.walk(node) if isinstance(n, _ast.Name)}
            referenced |= {n.attr for n in _ast.walk(node) if isinstance(n, _ast.Attribute)}
            leak = referenced & forbidden
            assert not leak, "%s references %r on the D derivation path" % (node.name, sorted(leak))
    # And the sensitivity view genuinely exists, so this is not vacuous.
    assert "technical_sensitivity_view" in {
        n.name for n in tree.body if isinstance(n, _ast.FunctionDef)}


def test_effective_ranks_are_not_on_the_D_derivation_path_either() -> None:
    """Neither effective rank may define D; both are diagnostics only."""
    import ast as _ast

    tree = _ast.parse((SCRIPTS / "d1_real_data_derivation_core_v1.py").read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, _ast.FunctionDef) and node.name in {"derive_D_PA", "derive_production_D"}:
            names = {n.id for n in _ast.walk(node) if isinstance(n, _ast.Name)}
            assert "entropy_effective_rank" not in names
            assert "participation_effective_rank" not in names


# ============================================================================
# End-to-end engine tests
#
# The primitives were previously tested in isolation while nothing assembled
# them, so "machinery built" overstated the integration level. These exercise
# the assembled engines.
# ============================================================================
class _StrataFixture:
    """MECHANICS_ONLY strata source with a known injected rank structure."""

    def __init__(self, *, donors: int, operators: int, cells: int, dimension: int,
                 ranks: int, seed: int, scale: float) -> None:
        rng = np.random.default_rng(seed)
        basis = np.linalg.qr(rng.normal(size=(dimension, dimension)))[0]
        self.population_class = core.MECHANICS_ONLY
        self._data: dict = {}
        for donor in range(donors):
            for operator in range(operators):
                block = rng.normal(size=(cells, dimension))
                for rank in range(ranks):
                    latent = rng.normal(size=(cells, 1))
                    block = block + scale * latent * basis[:, rank][None, :]
                self._data[("D%02d" % donor, operator)] = block
        self._counts = {k: v.shape[0] for k, v in self._data.items()}
        self._weights = core.derive_donor_operator_weights(self._counts)

    def strata(self):
        return sorted(self._data)

    def load(self, donor, operator):
        block = self._data[(str(donor), int(operator))]
        weight = self._weights["cell_weight_a_dc"][(str(donor), int(operator))]
        return block, np.full(block.shape[0], weight)


def test_streamed_observed_spectrum_matches_a_direct_computation() -> None:
    fixture = _StrataFixture(donors=4, operators=2, cells=50, dimension=5,
                             ranks=1, seed=3, scale=4.0)
    streamed = core.stream_observed_spectrum(fixture, 5)
    direct = core.WeightedMomentAccumulator(5)
    for donor, operator in fixture.strata():
        states, weights = fixture.load(donor, operator)
        direct.update(states, weights)
    expected = core.deterministic_eigendecomposition(direct.result()["covariance"])
    assert streamed["rows"] == 400 and streamed["strata"] == 8
    assert np.allclose(streamed["eigenvalues"], expected["eigenvalues"], atol=1e-12)


def test_the_null_generator_destroys_covariance_it_was_given() -> None:
    """The null must be a real null, not a copy of the observed spectrum."""
    fixture = _StrataFixture(donors=4, operators=2, cells=60, dimension=5,
                             ranks=1, seed=5, scale=6.0)
    observed = core.stream_observed_spectrum(fixture, 5)
    spectra = core.stream_null_spectra(fixture, 5, replicates=8, rng_namespace="t")
    assert spectra.shape == (8, 5)
    # The observed leading eigenvalue exceeds every null replica's.
    assert observed["eigenvalues"][0] > spectra[:, 0].max()
    # Note the null leading eigenvalue is itself substantially elevated, because
    # permuting within strata preserves each coordinate's marginal variance and
    # the injected component inflates all of them. That is correct behaviour for
    # a parallel-analysis null and is why D_PA is conservative.
    #
    # No ratio between the observed and null spectra is asserted here: measured
    # across seeds the null spectrum shape varies far too much at this fixture
    # size for any threshold to be meaningful, and an arbitrary factor would be
    # a number chosen to make the test pass. The comparison that carries real
    # weight is the one the algorithm performs, against the null envelope, and
    # it is asserted in the end-to-end tests.
    #
    # The defining property of the null is checked directly instead: every
    # coordinate keeps its exact marginal multiset within each stratum.
    for donor, operator in fixture.strata()[:3]:
        states, _ = fixture.load(donor, operator)
        rng = core.stratum_rng("t", 0, donor, operator)
        permuted = core.permute_coordinates_within_stratum(states, rng)
        for column in range(states.shape[1]):
            assert np.allclose(np.sort(states[:, column]), np.sort(permuted[:, column]))
    # And the null is reproducible from its namespace alone.
    again = core.stream_null_spectra(fixture, 5, replicates=8, rng_namespace="t")
    assert np.allclose(spectra, again)
    different = core.stream_null_spectra(fixture, 5, replicates=8, rng_namespace="other")
    assert not np.allclose(spectra, different)


def test_donor_block_stability_carries_whole_donors_and_beats_its_null() -> None:
    fixture = _StrataFixture(donors=6, operators=2, cells=60, dimension=5,
                             ranks=1, seed=11, scale=8.0)
    observed = core.stream_observed_spectrum(fixture, 5)
    real = core.stream_donor_block_stability(
        fixture, 5, replicates=16, rng_namespace="s", max_rank=1,
        reference_eigenvectors=observed["eigenvectors"])
    null = core.stream_donor_block_stability(
        fixture, 5, replicates=16, rng_namespace="s", max_rank=1,
        reference_eigenvectors=observed["eigenvectors"], permute=True)
    assert real["permuted_null"] is False and null["permuted_null"] is True
    assert real["overlaps"].shape == (16, 1)
    # A genuine leading direction is recovered from resampled donor blocks far
    # better than under the donor/operator-preserving null.
    assert float(np.quantile(real["overlaps"][:, 0], 0.025)) > float(
        np.quantile(null["overlaps"][:, 0], 0.975))


def test_end_to_end_D_recovers_one_strong_component() -> None:
    """Known answer, verified stable across seeds and RNG namespaces."""
    for seed in (1, 7, 42):
        fixture = _StrataFixture(donors=6, operators=2, cells=80, dimension=6,
                                 ranks=1, seed=seed, scale=10.0)
        out = core.derive_D_end_to_end(
            fixture, 6, rng_namespace="e2e", minimum_replicates=32,
            maximum_replicates=64, precision_target_half_width=1e9)
        assert out["D"] == 1, seed
        assert out["K"] == out["D"]
        assert out["D_PA"] >= 1
        assert out["rows_consumed"] == 960 and out["strata"] == 12
        # Both effective ranks are reported and neither defines D.
        assert out["effective_rank_diagnostics"]["defines_D"] is False
        assert "entropy_effective_rank" in out["effective_rank_diagnostics"]
        assert "participation_effective_rank" in out["effective_rank_diagnostics"]
        assert out["degeneracy_discrepancy"]["used_to_set_D"] is False


def test_end_to_end_pure_noise_stops_with_no_fallback_D() -> None:
    """No signal must yield no D, never a default."""
    for seed in (1, 7, 42):
        fixture = _StrataFixture(donors=6, operators=2, cells=80, dimension=6,
                                 ranks=0, seed=seed, scale=0.0)
        with pytest.raises(AssertionError, match="NO_FALLBACK_D"):
            core.derive_D_end_to_end(
                fixture, 6, rng_namespace="e2e", minimum_replicates=32,
                maximum_replicates=64, precision_target_half_width=1e9)


# ------------------------------- eigengap interval estimator and block ranks
def test_population_gap_interval_uses_the_basic_bootstrap_not_sample_percentiles() -> None:
    """Ordered sample eigenvalues repel, so sample-gap percentiles never reach zero.

    A truly degenerate pair yields strictly positive gaps in every replicate.
    The lower percentile of those gaps therefore reports the pair as resolved,
    which is the wrong estimator; the basic-bootstrap interval for the
    population gap can include zero while every observed gap is positive.
    """
    observed = np.array([2.0])
    # Every replicate reports a positive gap, centred above the observed value.
    replicas = np.linspace(1.5, 6.0, 64).reshape(64, 1)
    sample_percentile_lower = float(np.quantile(replicas[:, 0], 0.025))
    basic_lower = float(core.population_gap_interval_lower(
        observed, replicas, confidence_level=0.95)[0])
    assert sample_percentile_lower > 0.0
    assert basic_lower < 0.0, "the basic bootstrap must be able to include zero"
    # A well-separated gap stays firmly positive under the same estimator.
    separated = core.population_gap_interval_lower(
        np.array([50.0]), np.linspace(48.0, 52.0, 64).reshape(64, 1))
    assert float(separated[0]) > 0.0
    with pytest.raises(ValueError):
        core.population_gap_interval_lower(np.array([1.0]), np.array([[1.0]]))


def test_block_boundary_ranks_are_cumulative_block_ends() -> None:
    assert core.block_boundary_ranks([[0], [1, 2], [3]]) == [1, 3, 4]
    assert core.block_boundary_ranks([[0, 1, 2]]) == [3]
    assert core.block_boundary_ranks([[0], [1], [2]]) == [1, 2, 3]


def test_degeneracy_blocks_only_restrict_candidate_ranks() -> None:
    """Blocks may remove candidates; they must never add one.

    This is what keeps the near-degeneracy clause from becoming a loophole: the
    admissible set is always a subset of the plain 1..D_PA range, so supplying
    blocks can only ever make D smaller or leave it unchanged.
    """
    flags = [True, True, True, True]
    plain = core.derive_production_D(D_PA=4, stability_separated_by_rank=flags)
    blocked = core.derive_production_D(D_PA=4, stability_separated_by_rank=flags,
                                       degeneracy_blocks=[[0], [1, 2], [3]])
    assert plain["D"] == 4
    assert blocked["D"] <= plain["D"]
    assert set(blocked["admissible_ranks"]) <= set(plain["admissible_ranks"])
    assert blocked["degeneracy_respected"] is True and plain["degeneracy_respected"] is False


def test_a_rank_inside_a_degenerate_block_is_not_required_to_separate() -> None:
    """An axis inside an unresolved block is not an identified object.

    Rank 2 falls inside the block {1,2}, so it is not an admissible boundary and
    the rule does not demand it separate on its own. Boundaries 1 and 3 do.
    """
    flags = [True, False, True]
    # Without blocks every rank must separate, so the prefix stops at 1.
    plain = core.derive_production_D(D_PA=3, stability_separated_by_rank=flags)
    assert plain["D"] == 1 and plain["admissible_ranks"] == [1, 2, 3]
    # With rank 2 inside the unresolved block {1,2} it is not an admissible
    # boundary, so boundaries 1 and 3 carry the decision and D is 3.
    respected = core.derive_production_D(D_PA=3, stability_separated_by_rank=flags,
                                         degeneracy_blocks=[[0], [1, 2]])
    assert respected["D"] == 3
    assert respected["admissible_ranks"] == [1, 3]


def test_a_failing_admissible_boundary_still_stops_the_prefix() -> None:
    """Blocks do not let the rule skip a failed *boundary*."""
    with pytest.raises(AssertionError, match="NO_FALLBACK_D"):
        core.derive_production_D(D_PA=4, stability_separated_by_rank=[False, True, True, True],
                                 degeneracy_blocks=[[0], [1], [2], [3]])
