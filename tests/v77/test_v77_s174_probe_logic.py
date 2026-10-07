"""The S174 probe's decision logic must be able to return each verdict. A synthetic source whose
physical columns are in genomic order while the family map is in Ensembl order lets the test
build a cache the defective way (POS), the correct way (ID), or at random."""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("s174_probe", ROOT / "scripts" / "v77" / "probe_v77_s174_cache_axis.py")
P = importlib.util.module_from_spec(spec)
sys.modules["s174_probe"] = P
spec.loader.exec_module(P)

# Ensembl order E00..E39 gives addresses 0..39; the physical var axis is a fixed shuffle of it.
N = 40
ENSG = [f"E{i:02d}" for i in range(N)]
ENSG2ADDR = {e: i for i, e in enumerate(ENSG)}
VAR = [ENSG[i] for i in np.random.default_rng(3).permutation(N)]   # genomic order
S2A = {j: j for j in range(N)}                                     # family map keyed by rank, applied to columns


def _rows(seed, cells=6):
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(cells):
        idx = np.sort(rng.choice(N, 15, replace=False))
        out.append((idx, rng.integers(1, 9, size=15)))
    return out


def _matrix(build):
    agree_id = agree_pos = tot_id = tot_pos = 0
    space = set(S2A.values())
    for idx, val in _rows(7):
        pid, ppos, amb = P.predict(idx, val, VAR, ENSG2ADDR, S2A)
        cache = build(pid, ppos)
        a, t = P.agreement(cache, pid, amb, space)
        agree_id, tot_id = agree_id + a, tot_id + t
        a, t = P.agreement(cache, ppos, set(), space)
        agree_pos, tot_pos = agree_pos + a, tot_pos + t
    return dict(agree_id=agree_id / tot_id, agree_pos=agree_pos / tot_pos)


def _random(pid, ppos):
    rng = np.random.default_rng(11)
    return {int(k): int(rng.integers(1, 9)) for k in rng.choice(N, 15, replace=False)}


def test_a_cache_built_the_defective_way_is_value_verified():
    m = _matrix(lambda pid, ppos: dict(ppos))
    assert m["agree_pos"] == 1.0 and m["agree_id"] < 0.5
    assert P.classify([m, m, m]) == "S174_VALUE_VERIFIED"


def test_a_correct_cache_revises_s174():
    m = _matrix(lambda pid, ppos: dict(pid))
    assert m["agree_id"] == 1.0 and m["agree_pos"] < 0.5
    assert P.classify([m, m, m]) == "CACHE_CORRECT__S174_NEEDS_REVISION"


def test_a_random_or_mixed_cache_is_inconclusive():
    assert P.classify([_matrix(_random)]) == "INCONCLUSIVE__STOP"
    pos, idm = _matrix(lambda pid, ppos: dict(ppos)), _matrix(lambda pid, ppos: dict(pid))
    assert P.classify([pos, idm]) == "INCONCLUSIVE__STOP", "matrices that disagree decide nothing"
    assert P.classify([]) == "INCONCLUSIVE__STOP"


def test_an_identity_axis_cannot_produce_a_verdict_either_way():
    var_identity = list(ENSG)
    agree = []
    for idx, val in _rows(9):
        pid, ppos, amb = P.predict(idx, val, var_identity, ENSG2ADDR, S2A)
        a, t = P.agreement(dict(ppos), pid, amb, set(S2A.values()))
        agree.append(a / t)
    m = dict(agree_id=float(np.mean(agree)), agree_pos=1.0)
    assert P.classify([m]) == "INCONCLUSIVE__STOP", "when both maps agree, the probe cannot tell them apart"
