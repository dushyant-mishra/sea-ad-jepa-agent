from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'/'v5'))

import td_test_qualification_package_v1 as P
import td_relational_successor_disk_runner_v1 as D


def _write_fit(path: Path, *, extra=False, object_ids=False):
    n=6
    control_ids=np.array([{'bad':'object'}],dtype=object) if object_ids else np.array(['opaque-control-0'],dtype='U32')
    payload={
        'source':np.array('UNIT'),
        'panel_id':np.array('P0'),
        'z_values':np.zeros((n,512),dtype=float),
        'x_values':np.zeros((n,512),dtype=float),
        'y_values':np.zeros((n,512),dtype=float),
        'z_measured':np.ones((n,512),dtype=bool),
        'x_measured':np.ones((n,512),dtype=bool),
        'y_measured':np.ones((n,512),dtype=bool),
        'z_feature_ids':np.array([f'Z{i:04d}' for i in range(512)],dtype='U8'),
        'x_feature_ids':np.array([f'X{i:04d}' for i in range(512)],dtype='U8'),
        'y_feature_ids':np.array([f'Y{i:04d}' for i in range(512)],dtype='U8'),
        'donor_ids':np.array(['D0']*3+['D1']*3,dtype='U8'),
        'operator_ids':np.array(['O0']*n,dtype='U8'),
        'global_rows':np.arange(n,dtype=np.int64),
        'source_library':np.full(n,1000.0),
        'detected_genes':np.full(n,512,dtype=np.int64),
        'focal_mask':np.ones(n,dtype=bool),
        'neighbor_pool_mask':np.ones(n,dtype=bool),
        'min_focal_anchors_per_donor':np.array(1,dtype=np.int64),
        'control_ids':control_ids,
        'control_focal_masks':np.ones((1,n),dtype=bool),
        'control_neighbor_pool_masks':np.ones((1,n),dtype=bool),
        'control_min_focal_anchors_per_donor':np.array([1],dtype=np.int64),
    }
    if extra: payload['controller_truth']=np.array('LEAK')
    np.savez(path,**payload)


def _package_for(path: Path):
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    return P.ValidatedExternalPackage('pkg','a'*64,{'opaque-00':sha},'b'*64,{}),sha


def test_disk_loader_authenticates_sha_named_npz_and_reconstructs_blinded_payload(tmp_path):
    provisional=tmp_path/'tmp.npz'
    _write_fit(provisional)
    package,sha=_package_for(provisional)
    final=tmp_path/f'{sha}.npz'
    provisional.rename(final)
    payloads=D.load_authenticated_fit_payloads(package,tmp_path)
    rec=payloads['opaque-00']
    assert rec['authenticated_fit_view_sha256']==sha
    inp=rec['executor_input']
    assert inp['source']=='UNIT' and inp['panel_id']=='P0'
    assert inp['z_values'].shape==(6,512)
    assert tuple(inp['control_profiles'])==('opaque-control-0',)
    assert inp['control_profiles']['opaque-control-0']['min_focal_anchors_per_donor']==1
    assert 'controller_truth' not in inp


def test_disk_loader_fails_closed_on_hash_drift_extra_fields_and_object_arrays(tmp_path):
    provisional=tmp_path/'tmp.npz'
    _write_fit(provisional)
    package,sha=_package_for(provisional)
    final=tmp_path/f'{sha}.npz'
    provisional.rename(final)
    with final.open('ab') as fh: fh.write(b'drift')
    with pytest.raises(D.DiskRunnerError,match='SHA-256 mismatch'):
        D.load_authenticated_fit_payloads(package,tmp_path)

    extra=tmp_path/'extra.npz'; _write_fit(extra,extra=True)
    package2,sha2=_package_for(extra); final2=tmp_path/f'{sha2}.npz'; extra.rename(final2)
    with pytest.raises(D.DiskRunnerError,match='exact frozen NPZ schema'):
        D.load_authenticated_fit_payloads(package2,tmp_path)

    obj=tmp_path/'obj.npz'; _write_fit(obj,object_ids=True)
    package3,sha3=_package_for(obj); final3=tmp_path/f'{sha3}.npz'; obj.rename(final3)
    with pytest.raises(D.DiskRunnerError,match='object arrays'):
        D.load_authenticated_fit_payloads(package3,tmp_path)
