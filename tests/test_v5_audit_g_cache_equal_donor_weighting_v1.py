"""Pin the calibration cache's equal-donor-weighting design.

Why this test exists
--------------------
An earlier revision of Audit G reported that the cache over-represented the HVS
source by 9.1x and was biased toward high-complexity cells. Both conclusions were
wrong: they compared the cache against the **population marginal**, which the
design explicitly rejects. From `FULL104_MASKING_NONLINEAR_CHALLENGE_20260918.md`:

    "each donor receives equal total fit weight so large donors cannot dominate
     merely because they contain more cells"

Against the baseline the design actually targets, the cache matches to within
0.05%. These tests pin that, so the same misreading cannot be made again without
a test failing.

They are written against the real artifacts and skip-free: if the cache or pass1
is absent the test FAILS rather than skips, because a silently skipped test would
restore exactly the blind spot this file exists to close.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

CACHE = Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/control_calibration_cache_v1")
PASS1 = Path("D:/jepa_full104_preterminal_20260919_a51cdbe8_outputs/"
             "full104_pass1_v2_selection_row_keyed.npz")

MAX_ROWS_PER_DONOR = 1024
SOURCE_NAMES = ("HVS", "NPH52", "SEA_AD")

#: Tolerances are properties of the design, declared here before comparison:
#: equal-donor weighting predicts the marginal exactly up to donors that hold
#: fewer cells than the cap, so only a small residual is admissible.
SOURCE_SHARE_TOLERANCE = 0.01          # absolute, on a fraction
COMPLEXITY_RELATIVE_TOLERANCE = 0.01   # 1% of the predicted mean
LOW_TAIL_RATIO_BAND = (0.80, 1.20)     # observed / expected under hash sampling


def _require(path: Path):
    if not path.exists():
        pytest.fail(
            f"required artifact missing: {path}. This test is deliberately not skipped -- "
            "a skip here would restore the blind spot the file exists to close.")


@pytest.fixture(scope="module")
def artifacts():
    _require(CACHE)
    _require(PASS1)
    p1 = np.load(PASS1, allow_pickle=True)
    return {
        "cell_donor": np.asarray(p1["cell_donor"], dtype=np.int64),
        "cell_nnz_core": np.asarray(p1["cell_nnz_core"], dtype=np.float64),
        "donor_src": np.asarray(p1["donor_src"], dtype=np.int64),
        "selection": np.load(CACHE / "selection_rows_i64.npy").astype(np.int64),
        "retained": np.load(CACHE / "retained_count_by_donor_i64.npy").astype(np.int64),
    }


def test_every_donor_is_at_the_cap_or_holds_fewer_cells_than_the_cap(artifacts):
    """The design is 1,024 per donor; the only admissible shortfall is a short donor."""
    retained = artifacts["retained"]
    cell_donor = artifacts["cell_donor"]
    for donor in range(retained.size):
        available = int((cell_donor == donor).sum())
        if retained[donor] < MAX_ROWS_PER_DONOR:
            assert retained[donor] == available, (
                f"donor {donor} retained {retained[donor]} of {available} available cells "
                f"without reaching the {MAX_ROWS_PER_DONOR} cap -- that is neither the cap "
                "nor exhaustion, so the selection is not equal-donor weighting")
        else:
            assert retained[donor] == MAX_ROWS_PER_DONOR


def test_source_shares_match_the_equal_donor_weight_target_not_the_population(artifacts):
    """The load-bearing test: the design target is equal donor weight, not the corpus."""
    retained = artifacts["retained"].astype(np.float64)
    donor_src = artifacts["donor_src"]
    cell_donor = artifacts["cell_donor"]

    total = retained.sum()
    for source in range(len(SOURCE_NAMES)):
        donors = np.flatnonzero(donor_src == source)
        target = donors.size / donor_src.size          # equal donor weight
        observed = retained[donors].sum() / total
        assert abs(observed - target) < SOURCE_SHARE_TOLERANCE, (
            f"{SOURCE_NAMES[source]}: cache share {observed:.4%} deviates from the "
            f"equal-donor-weight target {target:.4%} by more than "
            f"{SOURCE_SHARE_TOLERANCE:.1%}")

    # And the population marginal is emphatically NOT the target -- pinned so that
    # comparing against it is visibly the wrong reference.
    population = np.array([float((donor_src[cell_donor] == s).sum())
                           for s in range(len(SOURCE_NAMES))])
    population /= population.sum()
    sea_ad = SOURCE_NAMES.index("SEA_AD")
    assert population[sea_ad] > 0.85, "fixture assumption: SEA_AD dominates the corpus"
    observed_sea_ad = retained[np.flatnonzero(donor_src == sea_ad)].sum() / total
    assert observed_sea_ad < 0.60, (
        "the cache should NOT reproduce the corpus marginal -- that is what the "
        "per-donor cap exists to prevent")


def test_complexity_marginal_matches_the_equal_donor_weight_prediction(artifacts):
    """The apparent complexity 'bias' is fully predicted by equal-donor weighting."""
    cell_donor = artifacts["cell_donor"]
    nnz = artifacts["cell_nnz_core"]
    retained = artifacts["retained"].astype(np.float64)
    selection = artifacts["selection"]

    donor_mean = np.array([nnz[cell_donor == d].mean() for d in range(retained.size)])
    predicted = float((donor_mean * retained).sum() / retained.sum())
    observed = float(nnz[selection].mean())

    assert abs(observed - predicted) / predicted < COMPLEXITY_RELATIVE_TOLERANCE, (
        f"cache mean core nonzeros {observed:.1f} deviates from the equal-donor-weight "
        f"prediction {predicted:.1f} by more than {COMPLEXITY_RELATIVE_TOLERANCE:.0%}")

    # The population mean is a materially different number, which is exactly why
    # comparing against it produced a false 'bias' finding.
    assert abs(float(nnz.mean()) - predicted) / predicted > 0.10, (
        "fixture assumption: the population mean and the equal-donor-weight "
        "prediction should differ enough that confusing them matters")


def test_low_tail_retention_matches_hash_sampling_expectation(artifacts):
    """There is no sparse-cell filter; the low tail is retained as sampling predicts."""
    cell_donor = artifacts["cell_donor"]
    nnz = artifacts["cell_nnz_core"]
    retained = artifacts["retained"].astype(np.float64)
    selection = artifacts["selection"]

    threshold = float(np.quantile(nnz, 0.01))
    expected = sum(float((nnz[cell_donor == d] <= threshold).mean()) * retained[d]
                   for d in range(retained.size))
    observed = float((nnz[selection] <= threshold).sum())
    ratio = observed / expected
    lo, hi = LOW_TAIL_RATIO_BAND
    assert lo < ratio < hi, (
        f"low-tail retention ratio {ratio:.3f} outside the admissible band "
        f"[{lo}, {hi}] -- that would indicate a sparse-cell filter, which the "
        "content-blind hash selector should make impossible")


def test_within_donor_selection_is_blind_to_expression_content():
    """The selector hashes scientific identity, so it cannot see complexity.

    Static guard: if this ever changes, the complexity conclusions above stop
    following and must be re-derived rather than inherited.
    """
    import inspect

    from sea_ad_jepa.v5.full104_control_calibration_cache_v1 import row_priority

    source = inspect.getsource(row_priority)
    assert "selection_row" in source and "donor_code" in source
    for forbidden in ("counts", "expression", "nnz", "library", "matrix", "value"):
        assert forbidden not in source, (
            f"row_priority now references {forbidden!r}; the selector may no longer be "
            "content-blind, so Audit G's complexity conclusions must be re-derived")
