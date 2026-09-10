import hashlib
import importlib.util
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import pytest

P = Path(__file__).resolve().parents[1] / 'scripts' / 'v5_anticheat' / 'bind_corrected_train_cache_v1.py'
spec = importlib.util.spec_from_file_location('bind_corrected_train_cache_v1', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)


def sh(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''):
            h.update(b)
    return h.hexdigest()


def fixture(tmp_path: Path):
    cache = tmp_path / 'cache'
    cache.mkdir()
    shards = []
    for i, n in enumerate((2, 3)):
        matrix_id = f'HVS::{i}'
        stem = m.shard_stem(matrix_id)
        cp = cache / f'{stem}.counts.npz'
        mp = cache / f'{stem}.meta.npz'
        sp.save_npz(cp, sp.csr_matrix((n, 8), dtype=np.int32))
        np.savez(
            mp,
            donor_id=np.asarray([f'd{i}'] * n),
            cell_id=np.asarray([f'c{i}_{j}' for j in range(n)]),
            broad_cell_class=np.asarray(['x'] * n),
            source_library=np.asarray([1] * n, dtype=np.int64),
        )
        shards.append({'matrix_id': matrix_id, 'counts_sha256': sh(cp), 'meta_sha256': sh(mp)})
    lm = tmp_path / 'loader.json'
    lm.write_text(json.dumps({'schema':'foundation-train-loader-v1','address_count':8,'shards':shards}))
    return cache, lm


def test_train_cache_is_bound_but_never_claims_full104(tmp_path):
    cache, lm = fixture(tmp_path)
    out = m.bind_corrected_train_cache(
        loader_manifest=lm,
        expected_loader_sha256=sh(lm),
        cache_root=cache,
        expected_shards=2,
        expected_address_count=8,
        expected_full_reader_cells=100,
    )
    assert out['status'] == 'PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY'
    assert out['shards_bound'] == 2
    assert out['physical_train_rows'] == 5
    assert out['full104_expression_binding_closed'] is False
    assert out['training_authorized'] is False


def test_even_equal_row_count_does_not_promote_train_cache_to_full104(tmp_path):
    cache, lm = fixture(tmp_path)
    out = m.bind_corrected_train_cache(
        loader_manifest=lm,
        expected_loader_sha256=sh(lm),
        cache_root=cache,
        expected_shards=2,
        expected_address_count=8,
        expected_full_reader_cells=5,
    )
    assert out['physical_train_rows'] == 5
    assert out['full104_expression_binding_closed'] is False
    assert out['full104_required_binder'] == 'scripts/v5_anticheat/bind_full104_expression_blocks_v4.py'


def test_hash_mismatch_fails_closed(tmp_path):
    cache, lm = fixture(tmp_path)
    obj = json.loads(lm.read_text())
    obj['shards'][0]['counts_sha256'] = '0' * 64
    lm.write_text(json.dumps(obj))
    with pytest.raises(RuntimeError, match='STOP_CORRECTED_TRAIN_COUNTS_SHA_MISMATCH'):
        m.bind_corrected_train_cache(
            loader_manifest=lm,
            expected_loader_sha256=sh(lm),
            cache_root=cache,
            expected_shards=2,
            expected_address_count=8,
            expected_full_reader_cells=100,
        )
