from pathlib import Path
import importlib.util
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / 'scripts/v64/v73_full104_population_geometry.py'


def load():
    spec = importlib.util.spec_from_file_location('g_v75', MOD)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def _summary(G, n):
    a, trip, q = G.quotas_for_n(n)
    return a, trip, q, G.summary_from_quotas(a, trip, q)


def test_2k_smoke_preserves_all_42_operators(monkeypatch):
    monkeypatch.chdir(ROOT)
    G = load()
    _, _, _, s = _summary(G, 2_000)
    assert s['source_operator_nonzero_cells'] == 42
    assert min(s['operator_counts']) >= 1


def test_10k_preserves_all_42_operators(monkeypatch):
    monkeypatch.chdir(ROOT)
    G = load()
    _, _, _, s = _summary(G, 10_000)
    assert s['source_operator_nonzero_cells'] == 42
    assert min(s['operator_counts']) >= 1


def test_large_scale_operator_minima_and_exact_full104(monkeypatch):
    monkeypatch.chdir(ROOT)
    G = load()
    expected = {100_000: 4, 500_000: 20, 4_553_407: 179}
    for n, minimum in expected.items():
        a, trip, q, s = _summary(G, n)
        assert s['source_operator_nonzero_cells'] == 42
        assert min(s['operator_counts']) == minimum
        if n == 4_553_407:
            assert np.array_equal(q, trip[:, 2])
            assert s['operator_counts'] == a['operator_counts']
