#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np

BASE = Path('/mnt/data/td57b_fixed_relational_recurrence.py')
spec = importlib.util.spec_from_file_location('td57b_frozen_base', BASE)
if spec is None or spec.loader is None:
    raise RuntimeError('cannot load frozen TD57B base executor')
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)


def exact_fast_distance_matrix(signs: np.ndarray) -> np.ndarray:
    p = signs.shape[1]
    pos = (signs == 1).astype(np.float32)
    neg = (signs == -1).astype(np.float32)
    zero = (signs == 0).astype(np.float32)
    nonzero = (signs != 0).sum(axis=1).astype(np.int32)
    # Counts are <= 2048, hence exactly representable in float32.
    same = np.rint(pos @ pos.T + neg @ neg.T).astype(np.int32)
    both_zero = np.rint(zero @ zero.T).astype(np.int32)
    l1 = nonzero[:, None] + nonzero[None, :] - 2 * same
    informative = p - both_zero
    out = np.full((len(signs), len(signs)), np.nan, dtype=np.float64)
    good = informative >= base.MIN_INFORMATIVE
    out[good] = l1[good] / (2.0 * informative[good])
    return out


base.distance_matrix = exact_fast_distance_matrix
raise SystemExit(base.main())
