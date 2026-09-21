"""Controls for Audit B (effective mask burden) and Audit C (source estimability).

Both audits consume the shared core sufficient statistics, so both are tested by
synthesizing a statistics file whose answer is known by construction and
requiring the audit to recover it.

The negative controls are the point. Audit B's claim is that screening-selected
addresses carry more evidence than the addresses they displace; a calculator that
reported a ratio above 1 even when selection is unrelated to burden would
manufacture that finding. Audit C's claim is that targets are often unvarying
within a donor; a calculator that flagged genuinely varying targets would
manufacture that one.

Nothing here opens a terminal masking outcome, target-panel ladder,
null-equivalence margin, D_shared, protected/pathology/DEV/SEALED data, or
training.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
LANE = ROOT / "analysis/v5_full104_information_channel_redteam_20260920/scripts"
B_SCRIPT = LANE / "audit_b_effective_burden_20260920.py"
C_SCRIPT = LANE / "audit_c_target_source_estimability_20260920.py"
BUILD_SCRIPT = LANE / "build_core_sufficient_statistics_20260920.py"

N_DONORS = 12
N_CORE = 200
POOL = 24
SOURCES = np.array([0] * 4 + [1] * 4 + [2] * 4, dtype=np.int64)


def _write_stats(path: Path, *, donor_nnz, donor_umi, donor_nsum, donor_nsq,
                 donor_cells, pool_burden_rank=None, pool_screening_link=True,
                 seed=7) -> Path:
    """Synthesize a statistics NPZ, optionally with a pool whose screening score
    is or is not linked to per-address burden."""
    rng = np.random.default_rng(seed)
    core = np.arange(N_CORE, dtype=np.int64)
    payload = {
        "schema": np.array("V5_FULL104_CORE_SUFFICIENT_STATISTICS_V1"),
        "core": core,
        "duniq": np.array([f"D{i:02d}" for i in range(N_DONORS)], dtype=object),
        "donor_src": SOURCES,
        "source_names": np.array(["HVS", "NPH52", "SEA_AD"], dtype=object),
        "donor_nnz": donor_nnz, "donor_umi": donor_umi,
        "donor_nsum": donor_nsum, "donor_nsq": donor_nsq,
        "donor_cells": donor_cells,
        "depth_nnz": donor_nnz[:10], "depth_umi": donor_umi[:10],
        "depth_cells": donor_cells[:10], "depth_edges": np.arange(11, dtype=np.float64),
        "corenz_nnz": donor_nnz[:10], "corenz_umi": donor_umi[:10],
        "corenz_cells": donor_cells[:10], "corenz_edges": np.arange(11, dtype=np.float64),
        "libraries": np.ones(int(donor_cells.sum()), dtype=np.int64) * 1000,
        "src_of_cell": np.zeros(int(donor_cells.sum()), dtype=np.int64),
        "total_core_umi": np.array(int(donor_umi.sum()), dtype=np.int64),
        "total_core_nnz": np.array(int(donor_nnz.sum()), dtype=np.int64),
        "partial": np.array(False),
    }
    if pool_burden_rank is not None:
        pool = np.sort(pool_burden_rank[:POOL]).astype(np.int64)
        p = pool.size
        # Build per-donor pool statistics such that the |correlation| structure
        # either does or does not track per-address burden.
        dn = donor_cells.astype(np.float64)
        sx = np.zeros((N_DONORS, p)); sxx = np.zeros((N_DONORS, p))
        cross = np.zeros((N_DONORS, p, p))
        for d in range(N_DONORS):
            n = max(int(dn[d]), 3)
            base = rng.normal(size=(n, 1))
            if pool_screening_link:
                # Addresses with higher burden also covary more strongly, so the
                # screening score ranks them highly.
                w = np.linspace(0.05, 1.0, p)
            else:
                # Covariance strength deliberately REVERSED relative to burden,
                # so a calculator that reports ratio > 1 regardless would fail.
                w = np.linspace(1.0, 0.05, p)
            x = base * w[None, :] + 0.3 * rng.normal(size=(n, p))
            sx[d] = x.sum(axis=0); sxx[d] = (x * x).sum(axis=0)
            cross[d] = x.T @ x
            dn[d] = n
        payload.update({
            "pool": pool, "pool_dn": dn, "pool_sx": sx, "pool_sxx": sxx,
            "pool_cross": cross,
            "pool_NN": np.zeros((p, p)), "pool_SD": np.zeros((p, p)),
            "pool_QQ": np.zeros((p, p)), "pool_SQ": np.zeros((p, p)),
            "pool_det": np.zeros(p), "pool_cells": np.array(int(donor_cells.sum())),
        })
    np.savez_compressed(path, **payload)
    return path


def _base_arrays(rng):
    donor_cells = rng.integers(200, 400, size=N_DONORS).astype(np.int64)
    donor_nnz = np.zeros((N_DONORS, N_CORE), dtype=np.int64)
    for d in range(N_DONORS):
        donor_nnz[d] = rng.integers(0, donor_cells[d] // 2, size=N_CORE)
    donor_umi = donor_nnz * rng.integers(1, 6, size=(N_DONORS, N_CORE))
    donor_nsum = donor_nnz.astype(np.float64) * 0.7
    donor_nsq = donor_nnz.astype(np.float64) * 0.9
    return donor_nnz, donor_umi, donor_nsum, donor_nsq, donor_cells


def _run_b(tmp: Path, stats: Path) -> dict:
    out = tmp / "b"
    proc = subprocess.run([sys.executable, str(B_SCRIPT), "--stats", str(stats),
                           "--out-dir", str(out)], capture_output=True, text=True, timeout=900)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads((out / "MASK_EFFECTIVE_BURDEN.json").read_text())


# --------------------------------------------------------------------------- #
# Shared FULL104 metadata semantics
# --------------------------------------------------------------------------- #

def _load_build_module():
    spec = importlib.util.spec_from_file_location("audit_stats_builder", BUILD_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.mark.parametrize("token, expected", [
    ("61129", 61129),
    ("61129.0", 61129),
    ("6.1129e4", 61129),
    ("+61129.000", 61129),
])
def test_shared_stats_builder_accepts_only_production_legal_integral_library_forms(token, expected):
    mod = _load_build_module()
    assert mod.parse_source_library(token) == expected


@pytest.mark.parametrize("token", [
    "1_000", "0x10", "nan", "NaN", "inf", "-inf", "1.5", "0", "-1", "",
])
def test_shared_stats_builder_rejects_production_illegal_library_forms(token):
    mod = _load_build_module()
    with pytest.raises(ValueError, match="invalid source_library"):
        mod.parse_source_library(token)


# --------------------------------------------------------------------------- #
# Audit B
# --------------------------------------------------------------------------- #

def test_b_positive_control_recovers_a_constructed_burden_advantage(tmp_path: Path):
    """When screening tracks burden, the selected/baseline ratio must exceed 1."""
    rng = np.random.default_rng(11)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    # Make burden increase with address index, and let the pool be the first POOL
    # addresses so the screening weights (increasing) align with burden.
    order = np.arange(POOL, dtype=np.int64)
    for i, a in enumerate(order):
        nnz[:, a] = (cells // 3) * (i + 1) // POOL + 1
        umi[:, a] = nnz[:, a] * 4
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells,
                         pool_burden_rank=order, pool_screening_link=True)
    payload = _run_b(tmp_path, stats)
    sel = payload["targeted_selection_vs_uniform"]
    assert sel["state"] == "MEASURED"
    assert sel["detected_tokens_B2"]["ratio_selected_to_baseline"] > 1.1, sel
    assert sel["umi_mass_B3"]["ratio_selected_to_baseline"] > 1.1, sel


def test_b_negative_control_reports_no_advantage_when_selection_is_anti_correlated(tmp_path: Path):
    """The load-bearing negative case.

    Screening strength is deliberately REVERSED relative to burden. A calculator
    that reported an advantage regardless would manufacture Audit B's finding.
    """
    rng = np.random.default_rng(11)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    order = np.arange(POOL, dtype=np.int64)
    for i, a in enumerate(order):
        nnz[:, a] = (cells // 3) * (i + 1) // POOL + 1
        umi[:, a] = nnz[:, a] * 4
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells,
                         pool_burden_rank=order, pool_screening_link=False)
    payload = _run_b(tmp_path, stats)
    ratio = payload["targeted_selection_vs_uniform"]["detected_tokens_B2"]["ratio_selected_to_baseline"]
    assert ratio < 1.0, (
        f"ratio {ratio:.3f} >= 1 when screening is anti-correlated with burden -- "
        "the calculator reports an advantage that does not exist")


def test_b_reports_not_measurable_without_a_pool(tmp_path: Path):
    rng = np.random.default_rng(3)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    payload = _run_b(tmp_path, stats)
    assert payload["targeted_selection_vs_uniform"]["state"] == "NOT_MEASURABLE"
    assert "reason" in payload["targeted_selection_vs_uniform"]


def test_b_burden_rungs_match_the_frozen_mask_count_arithmetic(tmp_path: Path):
    """Rung address counts must equal (17185 * pct) // 100, the frozen rule."""
    rng = np.random.default_rng(5)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    payload = _run_b(tmp_path, stats)
    for row in payload["burden_rungs"]:
        assert row["masked_addresses"] == (17185 * row["burden_rung_percent"]) // 100
    assert payload["burden_rungs"][0]["masked_addresses"] == 859     # the 5% rung


def test_b_detection_entropy_is_zero_at_the_degenerate_endpoints():
    spec = importlib.util.spec_from_file_location("audit_b", B_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    h = mod.bernoulli_entropy(np.array([0.0, 1.0, 0.5]))
    assert h[0] == 0.0 and h[1] == 0.0
    assert h[2] == pytest.approx(np.log(2))


# --------------------------------------------------------------------------- #
# Audit C
# --------------------------------------------------------------------------- #

def _run_c(tmp: Path, stats: Path, eligible: list[int]) -> dict:
    elig = tmp / "elig.json"
    elig.write_text(json.dumps({"eligible_target_cols_all_folds": eligible}), encoding="utf-8")
    out = tmp / "c"
    proc = subprocess.run([sys.executable, str(C_SCRIPT), "--stats", str(stats),
                           "--eligibility", str(elig), "--out-dir", str(out)],
                          capture_output=True, text=True, timeout=900)
    assert proc.returncode == 0, proc.stderr[-2000:]
    return json.loads((out / "TARGET_SOURCE_ESTIMABILITY.json").read_text())


def test_c_positive_control_counts_constructed_zero_variance_exactly(tmp_path: Path):
    """Targets made undetected in a known donor set must be counted exactly."""
    rng = np.random.default_rng(21)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    nnz = np.maximum(nnz, 1)                       # everything detected somewhere
    silent_targets = [3, 9, 15]
    silent_donors = [0, 1, 5]
    for t in silent_targets:
        for d in silent_donors:
            nnz[d, t] = 0                          # identically zero in that donor
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=nnz * 2,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    eligible = list(range(40))
    payload = _run_c(tmp_path, stats, eligible)

    total_exact = sum(r["zero_variance_pairs_exact"] for r in payload["c3_zero_variance"])
    assert total_exact == len(silent_targets) * len(silent_donors), (
        f"expected {len(silent_targets) * len(silent_donors)} zero-variance pairs, "
        f"got {total_exact}")
    # targets_with_any_donor_zero_variance is reported PER SOURCE, and the silent
    # donors [0, 1, 5] span two sources (donors 0-3 source 0, 4-7 source 1), so
    # each of the three targets is flagged in exactly those two sources and in
    # neither of the third source's rows.
    by_source = {r["source"]: r["targets_with_any_donor_zero_variance"]
                 for r in payload["c3_zero_variance"]}
    assert by_source["HVS"] == len(silent_targets)      # donors 0, 1
    assert by_source["NPH52"] == len(silent_targets)    # donor 5
    assert by_source["SEA_AD"] == 0                     # no silent donor here


def test_c_negative_control_flags_nothing_when_every_target_varies(tmp_path: Path):
    """A varying target must never be reported as zero-variance."""
    rng = np.random.default_rng(22)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    nnz = np.maximum(nnz, 1)
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=nnz * 2,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    payload = _run_c(tmp_path, stats, list(range(40)))
    total = sum(r["zero_variance_pairs_exact"] for r in payload["c3_zero_variance"])
    assert total == 0, f"{total} zero-variance pairs reported where every target varies"


def test_c_never_alters_the_eligibility_set(tmp_path: Path):
    rng = np.random.default_rng(23)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    eligible = list(range(40))
    payload = _run_c(tmp_path, stats, eligible)
    assert payload["eligibility_set_altered"] is False
    assert payload["targets_examined"] == len(eligible)


def test_c_weak_source_accounting_partitions_every_target(tmp_path: Path):
    rng = np.random.default_rng(24)
    nnz, umi, nsum, nsq, cells = _base_arrays(rng)
    # Make one source structurally unsupported for half the targets.
    for t in range(0, 40, 2):
        for d in np.flatnonzero(SOURCES == 1):
            nnz[d, t] = 0
    stats = _write_stats(tmp_path / "s.npz", donor_nnz=nnz, donor_umi=umi,
                         donor_nsum=nsum, donor_nsq=nsq, donor_cells=cells)
    payload = _run_c(tmp_path, stats, list(range(40)))
    total = (payload["estimable_in_all_three_sources"]
             + payload["targets_with_one_weak_source"]
             + payload["targets_with_two_weak_sources"]
             + payload["targets_with_three_weak_sources"])
    assert total == payload["targets_examined"], (
        "weak-source accounting must partition every target exactly once")
