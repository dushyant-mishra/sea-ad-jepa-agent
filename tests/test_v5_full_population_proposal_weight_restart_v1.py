import hashlib, importlib.util, json, sqlite3
from pathlib import Path
import numpy as np
import pytest

P=Path(__file__).parents[1]/'scripts'/'v5_anticheat'/'audit_full_population_proposal_weight_restart_v1.py'
spec=importlib.util.spec_from_file_location('m',P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

def sh(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def make(tmp):
    db=tmp/'m.sqlite'; con=sqlite3.connect(db)
    con.execute('create table cells(stable_key integer, donor_id text, partition text)')
    con.executemany('insert into cells values(?,?,?)',[(10,'a','reader_fit'),(20,'a','reader_fit'),(30,'b','reader_fit'),(40,'b','reader_fit')]); con.commit(); con.close()
    md=sh(db)
    rec=np.empty(4,dtype=m.LEDGER_DTYPE); rec['stable_key']=[10,20,30,40]; rec['multiplicity']=[1,2,3,1]
    led=tmp/'l.bin'; led.write_bytes(rec.tobytes()); raw=sh(led); bound=m.bound_ledger_digest(led.read_bytes()); H=7; a,b=m.affine_from(bound,H)
    rep=tmp/'r.json'; rep.write_text(json.dumps({'source_metadata_sha256':md,'partition':'reader_fit','unique_cells':4,'total_presentations':H,'canonical_multiplicity_ledger':{'raw_sha256':raw,'domain_bound_sha256':bound},'scientific_order_permutation':{'H':H,'a':a,'b':b}}))
    return db,md,led,rep

def run(db,md,led,rep): return m.audit(metadata_sqlite=db,expected_metadata_sha256=md,partition='reader_fit',schedule_report=rep,ledger=led,chunk_size=3,_expected_metadata_sha256_for_test=md)

def test_full_replay_passes_and_never_authorizes_training(tmp_path):
    db,md,led,rep=make(tmp_path); out=run(db,md,led,rep)
    assert out['status']=='PASS_FULL_READER_PROPOSAL_WEIGHT_PACKING_RESTART_REPLAY'
    assert out['presentation_stream_digest_sha256']==out['full_horizon_restart_replay']['digest_sha256']
    assert all(x['digest_sha256']==out['presentation_stream_digest_sha256'] for x in out['packing_replays'])
    assert out['training_authorized'] is False and out['full104_expression_binding_closed'] is False

def test_ledger_tamper_fails_closed(tmp_path):
    db,md,led,rep=make(tmp_path); b=bytearray(led.read_bytes()); b[-1]=2; led.write_bytes(b)
    with pytest.raises(RuntimeError,match='STOP_PROPOSAL_LEDGER_RAW_SHA_MISMATCH'): run(db,md,led,rep)

def test_affine_parameter_tamper_fails_closed(tmp_path):
    db,md,led,rep=make(tmp_path); o=json.loads(rep.read_text()); o['scientific_order_permutation']['a']+=1; rep.write_text(json.dumps(o))
    with pytest.raises(RuntimeError,match='STOP_PROPOSAL_AFFINE_REPLAY_MISMATCH'): run(db,md,led,rep)

def test_metadata_key_mismatch_fails_closed_even_with_rehashed_parent(tmp_path):
    db,md,led,rep=make(tmp_path); con=sqlite3.connect(db); con.execute('update cells set stable_key=11 where stable_key=10'); con.commit(); con.close(); md2=sh(db); o=json.loads(rep.read_text()); o['source_metadata_sha256']=md2; rep.write_text(json.dumps(o))
    with pytest.raises(RuntimeError,match='STOP_PROPOSAL_LEDGER_METADATA_KEY_MISMATCH'): run(db,md2,led,rep)

def test_public_alternate_metadata_authority_is_rejected():
    db=Path('never-used.sqlite'); rep=Path('never-used.json'); led=Path('never-used.bin')
    with pytest.raises(RuntimeError,match='STOP_PROPOSAL_METADATA_AUTHORITY_MISMATCH'):
        m.audit(metadata_sqlite=db,expected_metadata_sha256='1'*64,partition='reader_fit',schedule_report=rep,ledger=led)
