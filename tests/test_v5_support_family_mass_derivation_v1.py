import importlib.util, sqlite3
from pathlib import Path
import numpy as np
import pytest

P=Path(__file__).resolve().parents[1] / "scripts" / "v5_anticheat" / "derive_support_family_mass_v1.py"
spec=importlib.util.spec_from_file_location('m',P)
m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def build(tmp_path, mismatch=False):
    npz=tmp_path/'support.npz'
    states=np.array([[1,0,0],[1,1,1]],dtype=np.uint8)
    np.savez(npz, states=states, matrix_id=np.array(['HVS::a','SEA_AD::b']), operator_index=np.array([0,1],np.int32), molecular_address_index=np.arange(3,dtype=np.int32), state_names=np.array(['MEASURED_COLLISION_UNRESOLVED','MEASURED_SCALAR','STRUCTURALLY_UNMEASURED']))
    db=tmp_path/'meta.sqlite'; c=sqlite3.connect(db)
    c.execute('create table cells(source text,matrix_id text,operator_index integer,donor_id text,partition text,cell_id text)')
    rows=[]
    for i in range(9): rows.append(('HVS','HVS::WRONG' if mismatch else 'HVS::a',0,'d0','reader_fit',f'a{i}'))
    rows.append(('SEA_AD','SEA_AD::b',1,'d1','reader_fit','b0'))
    c.executemany('insert into cells values(?,?,?,?,?,?)',rows); c.commit(); c.close()
    return db,npz

def test_equal_donor_not_raw_cell_weighting(tmp_path):
    db,npz=build(tmp_path)
    out=m.derive(db,npz)
    assert out['geometry']['common_core_addresses']==1
    assert out['donor_equal_estimand']['expected_operator_native_addresses_per_base_cell']['float']==1.0
    assert out['donor_equal_estimand']['family_mass_weights']['COMMON_CORE']['float']==0.5
    assert out['donor_equal_estimand']['family_mass_weights']['OPERATOR_NATIVE']['float']==0.5
    assert abs(out['raw_cell_weighting_non_authority_contrast']['COMMON_CORE_fraction_of_measured_scalar']['float']-(1/1.2))<1e-12
    assert out['training_authorized'] is False
    assert out['synthetic_data_used'] is False

def test_matrix_identity_mismatch_fails(tmp_path):
    db,npz=build(tmp_path,mismatch=True)
    with pytest.raises(RuntimeError,match='MATRIX_ID_MISMATCH'):
        m.derive(db,npz)

def test_address_closure_fails(tmp_path):
    db,npz=build(tmp_path)
    z=np.load(npz)
    bad=tmp_path/'bad.npz'
    np.savez(bad, states=z['states'], matrix_id=z['matrix_id'], operator_index=z['operator_index'], molecular_address_index=np.array([0,2,3],np.int32), state_names=z['state_names'])
    with pytest.raises(RuntimeError,match='ADDRESS_CLOSURE_MISMATCH'):
        m.derive(db,bad)
