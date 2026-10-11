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


def test_empty_or_nul_seed_rejected():
    for seed in ['', '   ', 'bad\0seed']:
        with pytest.raises(m.NullContractError):
            m.build_matched_wrong_cell_map(rows(3), seed)


def test_nul_or_empty_cell_id_rejected():
    for bad in ['', '   ', 'c\0x']:
        rs=rows(3); rs[0]=dict(rs[0]); rs[0]['cell_id']=bad
        with pytest.raises(m.NullContractError):
            m.build_matched_wrong_cell_map(rs,'seed')


def test_stratum_fields_must_be_nonempty_nul_free_strings():
    for field in m.STRATUM_KEYS:
        for bad in ['', '   ', 'x\0y', 1, None]:
            rs=rows(3); rs[0]=dict(rs[0]); rs[0][field]=bad
            with pytest.raises(m.NullContractError):
                m.build_matched_wrong_cell_map(rs,'seed')


def test_missing_or_extra_row_fields_rejected():
    rs=rows(3); del rs[0]['support_key']
    with pytest.raises(m.NullContractError):
        m.build_matched_wrong_cell_map(rs,'seed')
    rs=rows(3); rs[0]['extra']='x'
    with pytest.raises(m.NullContractError):
        m.build_matched_wrong_cell_map(rs,'seed')


def test_mapping_is_bijection_within_each_stratum():
    rs=rows(5)+[
      dict(cell_id=f'z{i}',donor_id='d2',operator_id='o2',support_key='s2',depth_bin='b2',detection_bin='k2')
      for i in range(4)
    ]
    mp=m.build_matched_wrong_cell_map(rs,'seed')
    by={r['cell_id']:r for r in rs}
    assert len(set(mp.values()))==len(mp)
    for key in {tuple(r[k] for k in m.STRATUM_KEYS) for r in rs}:
        ids={r['cell_id'] for r in rs if tuple(r[k] for k in m.STRATUM_KEYS)==key}
        assert {mp[x] for x in ids} == ids
