import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_measurement_noise_fixture.py'
spec = importlib.util.spec_from_file_location('td_measurement_noise_fixture', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def test_split_is_exact_complement_and_deterministic():
    counts = {1: 7, 2: 0, 5: 11}
    support = {1, 2, 5, 9}
    a, b = m.split_counts(counts, support, seed_material='s', cell_id='c')
    a2, b2 = m.split_counts(counts, support, seed_material='s', cell_id='c')
    assert (a, b) == (a2, b2)
    for addr in support:
        assert a[addr] + b[addr] == counts.get(addr, 0)


def test_split_preserves_measured_zero_and_support_universe():
    a, b = m.split_counts({1: 0}, {1, 2}, seed_material='s', cell_id='c')
    assert set(a) == {1, 2} and set(b) == {1, 2}
    assert a[1] == b[1] == a[2] == b[2] == 0


def test_unsupported_count_is_rejected():
    with pytest.raises(m.MeasurementFixtureError):
        m.split_counts({3: 1}, {1, 2}, seed_material='s', cell_id='c')


def test_fractional_negative_and_boolean_counts_rejected():
    for bad in [1.5, -1, True]:
        with pytest.raises(m.MeasurementFixtureError):
            m.split_counts({1: bad}, {1}, seed_material='s', cell_id='c')


def test_nested_thinning_uses_frozen_grid_and_is_nested():
    counts = {1: 40, 2: 20}
    support = {1, 2, 3}
    curves = m.nested_depth_thinning(counts, support, seed_material='s', cell_id='c')
    assert tuple(curves) == (0.25, 0.5, 0.75, 1.0)
    for addr in support:
        vals = [curves[p][addr] for p in (0.25, 0.5, 0.75, 1.0)]
        assert vals == sorted(vals)
        assert vals[-1] == counts.get(addr, 0)


def test_thinning_deterministic_and_seed_sensitive():
    counts = {1: 100, 2: 80}
    support = {1, 2}
    a = m.nested_depth_thinning(counts, support, seed_material='A', cell_id='c')
    b = m.nested_depth_thinning(counts, support, seed_material='A', cell_id='c')
    c = m.nested_depth_thinning(counts, support, seed_material='B', cell_id='c')
    assert a == b
    assert a != c


def test_empty_seed_or_cell_identity_rejected():
    with pytest.raises(m.MeasurementFixtureError):
        m.split_counts({1: 1}, {1}, seed_material='', cell_id='c')
    with pytest.raises(m.MeasurementFixtureError):
        m.split_counts({1: 1}, {1}, seed_material='s', cell_id='')


def test_input_objects_are_not_mutated():
    counts = {1: 3, 2: 4}
    support = {1, 2}
    before_counts = dict(counts); before_support = set(support)
    m.split_counts(counts, support, seed_material='s', cell_id='c')
    m.nested_depth_thinning(counts, support, seed_material='s', cell_id='c')
    assert counts == before_counts and support == before_support


def test_addresses_must_be_nonnegative_exact_integers():
    for support, counts in [({'1'}, {'1': 1}), ({-1}, {-1: 1}), ({True}, {True: 1})]:
        with pytest.raises(m.MeasurementFixtureError):
            m.split_counts(counts, support, seed_material='s', cell_id='c')


def test_seed_and_cell_id_must_be_nul_free():
    with pytest.raises(m.MeasurementFixtureError):
        m.split_counts({1: 1}, {1}, seed_material='a\0b', cell_id='c')
    with pytest.raises(m.MeasurementFixtureError):
        m.split_counts({1: 1}, {1}, seed_material='s', cell_id='a\0b')


def test_seed_and_cell_id_must_be_exact_strings_not_coerced():
    for seed, cell in [(7, 'c'), (True, 'c'), ('s', 7), ('s', False), (None, 'c')]:
        with pytest.raises(m.MeasurementFixtureError):
            m.split_counts({1: 1}, {1}, seed_material=seed, cell_id=cell)
