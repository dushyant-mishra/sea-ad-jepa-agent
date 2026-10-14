from __future__ import annotations

import numpy as np

import scripts.v80.v80_sparse_positive_benchmark as B


def test_zero_detection_probability_is_not_posthoc_rescued(monkeypatch):
    """A generator may not manufacture positives after a stochastic draw.

    Estimability of the frozen normal worlds is established by their prospective
    construction and fixed seed, not by editing realized outcomes.
    """
    monkeypatch.setattr(B, "_sigmoid", lambda x: np.zeros_like(x, dtype=float))
    worlds = B.build_sparse_positive_worlds(seed_root=41000000)
    for world in worlds:
        assert not np.asarray(world.detected, dtype=bool).any()
