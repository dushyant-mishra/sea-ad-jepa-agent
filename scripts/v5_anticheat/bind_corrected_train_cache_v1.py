#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp

EXPECTED_LOADER_SHA256 = '2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328'
EXPECTED_SHARDS = 42
EXPECTED_ADDRESS_COUNT = 41_238
EXPECTED_FULL_READER_CELLS = 4_553_407
FULL104_BINDER = 'scripts/v5_anticheat/bind_full104_expression_blocks_v4.py'


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(8 << 20), b''):
            h.update(b)
    return h.hexdigest()


def shard_stem(matrix_id: str) -> str:
    return hashlib.sha256(f'corrected|{matrix_id}'.encode()).hexdigest()[:16]


def bind_corrected_train_cache(
    *,
    loader_manifest: Path,
    expected_loader_sha256: str,
    cache_root: Path,
    expected_shards: int = EXPECTED_SHARDS,
    expected_address_count: int = EXPECTED_ADDRESS_COUNT,
    expected_full_reader_cells: int = EXPECTED_FULL_READER_CELLS,
) -> dict:
    if sha256_file(loader_manifest) != expected_loader_sha256:
        raise RuntimeError('STOP_CORRECTED_TRAIN_LOADER_MANIFEST_SHA_MISMATCH')
    loader = json.loads(loader_manifest.read_text())
    shards = loader.get('shards', [])
    if loader.get('schema') != 'foundation-train-loader-v1':
        raise RuntimeError('STOP_CORRECTED_TRAIN_LOADER_SCHEMA_MISMATCH')
    if int(loader.get('address_count', -1)) != expected_address_count:
        raise RuntimeError('STOP_CORRECTED_TRAIN_ADDRESS_COUNT_MISMATCH')
    if len(shards) != expected_shards:
        raise RuntimeError('STOP_CORRECTED_TRAIN_SHARD_COUNT_MISMATCH')

    bound = []
    physical_train_rows = 0
    for operator_index, spec in enumerate(shards):
        matrix_id = str(spec['matrix_id'])
        stem = shard_stem(matrix_id)
        counts_path = cache_root / f'{stem}.counts.npz'
        meta_path = cache_root / f'{stem}.meta.npz'
        if not counts_path.is_file() or not meta_path.is_file():
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_PHYSICAL_SHARD_MISSING:{operator_index}:{matrix_id}')
        counts_sha = sha256_file(counts_path)
        meta_sha = sha256_file(meta_path)
        if counts_sha != spec['counts_sha256']:
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_COUNTS_SHA_MISMATCH:{operator_index}:{matrix_id}')
        if meta_sha != spec['meta_sha256']:
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_META_SHA_MISMATCH:{operator_index}:{matrix_id}')

        meta = np.load(meta_path, allow_pickle=False)
        required = {'donor_id', 'cell_id', 'broad_cell_class', 'source_library'}
        if set(meta.files) != required:
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_META_SCHEMA_MISMATCH:{operator_index}:{matrix_id}')
        n_rows = len(meta['cell_id'])
        if any(len(meta[k]) != n_rows for k in required):
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_META_LENGTH_MISMATCH:{operator_index}:{matrix_id}')
        counts = sp.load_npz(counts_path)
        if counts.shape != (n_rows, expected_address_count):
            raise RuntimeError(f'STOP_CORRECTED_TRAIN_COUNTS_SHAPE_MISMATCH:{operator_index}:{matrix_id}')
        physical_train_rows += n_rows
        bound.append({
            'operator_index': operator_index,
            'matrix_id': matrix_id,
            'physical_train_rows': n_rows,
            'counts_shape': list(counts.shape),
            'counts_sha256': counts_sha,
            'meta_sha256': meta_sha,
        })

    return {
        'schema': 'JEPA_V5_CORRECTED_TRAIN_CACHE_BYTE_BINDING_V1',
        'status': 'PASS_EXACT_CORRECTED_TRAIN_CACHE_BYTE_BINDING_ONLY',
        'production_loader_manifest_sha256': expected_loader_sha256,
        'shards_bound': len(bound),
        'addresses': expected_address_count,
        'physical_train_rows': physical_train_rows,
        'expected_full_reader_fit_cells': expected_full_reader_cells,
        'full_reader_fit_row_delta': expected_full_reader_cells - physical_train_rows,
        'full104_expression_binding_closed': False,
        'full104_required_binder': FULL104_BINDER,
        'full104_required_substrate': 'historical 8,915-block Phase2/FULL104 reader_fit materialization',
        'semantic_boundary': 'foundation-train-loader-v1 shards are TRAIN-cache evidence only and cannot satisfy FULL104 reader_fit expression closure',
        'synthetic_data_used': False,
        'pathology_used': False,
        'training_authorized': False,
        'shards': bound,
    }


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--loader-manifest', type=Path, required=True)
    p.add_argument('--expected-loader-sha256', default=EXPECTED_LOADER_SHA256)
    p.add_argument('--cache-root', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    result = bind_corrected_train_cache(
        loader_manifest=a.loader_manifest,
        expected_loader_sha256=a.expected_loader_sha256,
        cache_root=a.cache_root,
    )
    a.output.parent.mkdir(parents=True, exist_ok=True)
    a.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
