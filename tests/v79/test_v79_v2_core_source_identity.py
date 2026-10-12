from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts" / "v79"))

import v79_v2_core_structural_support as S  # noqa: E402

BRIDGE = ROOT / "results/v78/V78_S174_SHARD_OPERATOR_BRIDGE_V1.json"


def test_source_identity_comes_from_frozen_bridge_not_realized_matrix_count():
    # Only one operator from each source is present, and the integer source codes are permuted.
    design = {
        "op": np.array([0, 0, 35, 35, 24, 24], dtype=np.int64),
        "src": np.array([2, 2, 0, 0, 1, 1], dtype=np.int64),
    }
    mapping = S.load_source_code_map_from_bridge(BRIDGE, design)
    assert mapping == {"HVS": 2, "NPH52": 0, "SEA_AD": 1}


def test_source_identity_fails_closed_if_operator_source_codes_conflict():
    design = {
        "op": np.array([0, 0, 35, 35, 24, 24], dtype=np.int64),
        "src": np.array([2, 1, 0, 0, 1, 1], dtype=np.int64),
    }
    with pytest.raises(SystemExit):
        S.load_source_code_map_from_bridge(BRIDGE, design)
