from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
SCORER = ROOT / "scripts" / "v77" / "v78_signed_scoring.py"
V77_SCORER = ROOT / "scripts" / "v77" / "v77_matched_scoring.py"


def _load(path: Path, name: str):
    assert path.exists(), f"missing V78 signed scorer: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


def test_handbuilt_signed_correlation_diagnostics_are_exact():
    S = _load(SCORER, "v78_signed_handbuilt")
    C = np.array([
        [1.0, 0.8, -0.7, 0.0],
        [0.8, 1.0, -0.6, 0.0],
        [-0.7, -0.6, 1.0, 0.4],
        [0.0, 0.0, 0.4, 1.0],
    ])
    rec = S.signed_diagnostics_from_corr(C, strong_threshold=0.3, community_threshold=0.5)
    assert rec["frac_pos_gt_0p3"] == pytest.approx(4 / 12)
    assert rec["frac_neg_lt_m0p3"] == pytest.approx(4 / 12)
    assert rec["pos_over_neg_ratio"] == pytest.approx(1.0)
    assert rec["positive_degree"]["mean"] == pytest.approx(1.0)
    assert rec["negative_degree"]["mean"] == pytest.approx(1.0)
    assert rec["fraction_genes_with_negative_strong_edge"] == pytest.approx(0.75)
    assert rec["negative_edge_participation_by_abs_community"][0]["size"] == 3
    assert rec["negative_edge_participation_by_abs_community"][0]["fraction_with_negative_edge"] == pytest.approx(1.0)


def test_v78_wrapper_preserves_v77_legacy_score_exactly():
    S = _load(SCORER, "v78_signed_wrapper")
    V = _load(V77_SCORER, "v77_scoring_reference")
    rng = np.random.default_rng(20261009)
    counts = rng.poisson(lam=np.linspace(0.4, 4.0, 8), size=(400, 8)).astype(np.int32)
    universe = np.arange(8, dtype=np.int64)
    cls = np.repeat(np.array([0, 1], dtype=np.int16), 200)
    expected = V.score_matched(counts, universe, cls, n_hvg=6)
    got = S.score_v78(counts, universe, cls, n_hvg=6)
    # Canonical JSON preserves literal NaN tokens, avoiding Python's NaN != NaN object-comparison trap.
    assert json.dumps(got["legacy"], sort_keys=True, allow_nan=True) == json.dumps(expected, sort_keys=True, allow_nan=True)
    assert got["selection_rule"] == V.RULE
    assert got["signed_detection"]["strong_threshold"] == 0.3
    assert got["signed_detection"]["selected_gene_count"] == 6


def test_signed_degree_summary_is_not_collapsed_to_one_scalar():
    S = _load(SCORER, "v78_signed_degree")
    d = S.summarize_signed_degree(np.array([0, 1, 3, 6], dtype=np.int64))
    assert set(d) == {"mean", "median", "p90", "max", "fraction_isolated"}
    assert d["max"] == 6
    assert d["fraction_isolated"] == pytest.approx(0.25)
