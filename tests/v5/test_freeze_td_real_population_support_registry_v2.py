import csv, pathlib, sqlite3, sys
import pytest
ROOT=pathlib.Path(__file__).resolve().parents[2]; sys.path.insert(0,str(ROOT))
from scripts.v5 import freeze_td_real_population_support_registry_v2 as F

def make_db(tmp_path):
    p=tmp_path/'m.sqlite'; con=sqlite3.connect(p)
    con.execute('create table cells(source text,matrix_id text,donor_id text,partition text)')
    con.executemany('insert into cells values(?,?,?,?)',[
      ('HVS','H1','D1','reader_fit'),('HVS','H1','D1','reader_fit'),
      ('SEA_AD','S1','D2','reader_validation'),('NPH52','N1','D3','reader_oracle')])
    con.commit(); con.close(); return p

def make_split(tmp_path, rows):
    p=tmp_path/'split.csv'
    with p.open('w',newline='') as f:
      w=csv.writer(f); w.writerow(['donor_id','reader_partition']); w.writerows(rows)
    return p

def test_build_registry_preserves_exact_donor_operator_pairs_and_partitions(tmp_path):
    db=make_db(tmp_path); split=make_split(tmp_path,[('D1','reader_fit'),('D2','reader_validation'),('D3','reader_oracle')])
    r=F.build_registry(db,split)
    assert len(r['strata'])==3
    assert {x['reader_partition'] for x in r['strata']}=={'reader_fit','reader_validation','reader_oracle'}
    for row in r['strata']:
      assert all(row['candidate_support_state'][c]=='BLOCKED_EVIDENCE_CONTRACT' for c in F.FOUNDATION)
      assert row['candidate_support_state'][F.SPECIALIST]=='UNSUPPORTED_STRUCTURAL'

def test_split_mismatch_fails_closed(tmp_path):
    db=make_db(tmp_path); split=make_split(tmp_path,[('D1','reader_fit'),('D2','reader_fit'),('D3','reader_oracle')])
    with pytest.raises(F.RegistryFreezeError,match='partition mismatch'):
      F.build_registry(db,split)

def test_donor_missing_from_split_fails_closed(tmp_path):
    db=make_db(tmp_path); split=make_split(tmp_path,[('D1','reader_fit'),('D2','reader_validation')])
    with pytest.raises(F.RegistryFreezeError,match='donor roster mismatch'):
      F.build_registry(db,split)

def test_duplicate_split_donor_fails_closed(tmp_path):
    db=make_db(tmp_path); split=make_split(tmp_path,[('D1','reader_fit'),('D1','reader_fit'),('D2','reader_validation'),('D3','reader_oracle')])
    with pytest.raises(F.RegistryFreezeError,match='duplicate donor'):
      F.build_registry(db,split)
