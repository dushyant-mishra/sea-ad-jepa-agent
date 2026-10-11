import importlib.util
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parents[2]
MOD = ROOT / 'scripts/v5/td_target_tournament_nulls.py'
spec = importlib.util.spec_from_file_location('td_target_tournament_nulls', MOD)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def rows(n=5):
    return [dict(cell_id=f'c{i}', donor_id='d1', operator_id='o1', support_key='s1', depth_bin='b1', detection_bin='k1') for i in range(n)]


def test_mapping_changes_identity_and_preserves_strata():
    rs = rows(6)
    mp = m.build_matched_wrong_cell_map(rs, 'seed-A')
    by = {r['cell_id']: r for r in rs}
    assert set(mp) == set(by)
    for src, dst in mp.items():
        assert src != dst
        a,b = by[src], by[dst]
        for k in ['donor_id','operator_id','support_key','depth_bin','detection_bin']:
            assert a[k] == b[k]


def test_mapping_is_deterministic():
    rs = rows(7)
    assert m.build_matched_wrong_cell_map(rs, 'same') == m.build_matched_wrong_cell_map(list(reversed(rs)), 'same')


def test_changed_seed_can_change_mapping():
    rs = rows(8)
    assert m.build_matched_wrong_cell_map(rs, 'a') != m.build_matched_wrong_cell_map(rs, 'b')


def test_singleton_stratum_is_not_estimable():
    rs = rows(4) + [dict(cell_id='lonely', donor_id='d2', operator_id='o1', support_key='s1', depth_bin='b1', detection_bin='k1')]
    with pytest.raises(m.NotEstimableStratum): m.build_matched_wrong_cell_map(rs, 'x')


def test_duplicate_cell_id_rejected():
    rs = rows(3) + [rows(3)[0]]
    with pytest.raises(ValueError): m.build_matched_wrong_cell_map(rs, 'x')
