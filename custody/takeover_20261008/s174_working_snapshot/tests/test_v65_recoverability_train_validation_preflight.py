from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import numpy as np
import pytest

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=ROOT/"scripts/v64/privileged_recoverability_train_validation_preflight_v1.py"

def _load():
    spec=importlib.util.spec_from_file_location("preflight",SCRIPT)
    assert spec and spec.loader
    m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

def _fixture(tmp_path):
    donors=[f"D{i:02d}" for i in range(24)]
    donor_id=np.array([d for d in donors for _ in range(90)],dtype=object)
    n=len(donor_id)
    rna_row=np.arange(n,dtype=np.int32)
    rna_col=np.zeros(n,dtype=np.int32)
    rna_val=np.ones(n,dtype=np.int32)
    atac_row=np.arange(n,dtype=np.int32)
    atac_col=np.zeros(n,dtype=np.int32)
    atac_val=np.ones(n,dtype=np.int32)
    p=tmp_path/"paired.npz"
    np.savez_compressed(
        p,
        rna_row=rna_row,rna_col=rna_col,rna_val=rna_val,
        atac_row=atac_row,atac_col=atac_col,atac_val=atac_val,
        n_nuclei=np.int64(n),n_genes=np.int64(4000),n_peaks=np.int64(12000),
        gene_ids=np.array([f"ENSG{i:011d}" for i in range(4000)]),
        gene_symbols=np.array([f"G{i}" for i in range(4000)]),
        peak_names=np.array([f"chr1:{i}-{i+1}" for i in range(12000)]),
        pairing_rna_obs_name=np.array([f"R{i}" for i in range(n)],dtype=object),
        pairing_atac_obs_name=np.array([f"A{i}" for i in range(n)],dtype=object),
        donor_id=donor_id,
        cell_type=np.array(["MG"]*n,dtype=object),
    )
    split={"seed":20260930,"source_sha256":"placeholder",
           "train":donors[:16],"validation":donors[16:20],"test":donors[20:],
           "donors":{"train":16,"validation":4,"test":4}}
    return p,split

def test_test_numeric_rows_are_sealed(tmp_path):
    m=_load(); p,split=_fixture(tmp_path)
    meta=m.load_metadata_explicit(p)
    assert int(m.allowed_row_mask(meta,split,"train").sum())==1440
    assert int(m.allowed_row_mask(meta,split,"validation").sum())==360
    with pytest.raises(m.Stop,match="TEST numeric-row access is sealed"):
        m.allowed_row_mask(meta,split,"test")

def test_numeric_loader_never_requires_pickle(tmp_path):
    m=_load(); p,_=_fixture(tmp_path)
    num=m.load_numeric_pickle_free(p)
    assert set(num)==m.NUMERIC_KEYS
    assert all(np.issubdtype(v.dtype,np.integer) for v in num.values())

def test_metadata_loader_rejects_numeric_key_reclassification(tmp_path,monkeypatch):
    m=_load(); p,_=_fixture(tmp_path)
    monkeypatch.setattr(m,"METADATA_KEYS",set(m.METADATA_KEYS)|{"rna_val"})
    with pytest.raises(m.Stop,match="metadata array rna_val has unexpected dtype"):
        m.load_metadata_explicit(p)

def test_split_overlap_fails_closed(tmp_path):
    m=_load(); p,split=_fixture(tmp_path)
    meta=m.load_metadata_explicit(p)
    split=json.loads(json.dumps(split))
    split["validation"][0]=split["train"][0]
    with pytest.raises(m.Stop,match="split donor sets overlap"):
        m.validate_metadata(meta,split,2160)
