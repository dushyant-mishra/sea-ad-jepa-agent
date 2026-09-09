#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, sqlite3
from pathlib import Path
import numpy as np

def sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for b in iter(lambda:f.read(8<<20),b''): h.update(b)
    return h.hexdigest()

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--metadata-sqlite',type=Path,required=True)
    p.add_argument('--loader-manifest',type=Path,required=True)
    p.add_argument('--observation-state',type=Path,required=True)
    p.add_argument('--location-manifest',type=Path)
    p.add_argument('--out-json',type=Path,required=True)
    a=p.parse_args(argv)
    expected={
      'metadata':'a771f08be31a840b5472448c438a153fbca7de93ba2ed31fe692eaeda02e6913',
      'loader':'2413390355a42365f6575800ae5f83ab373d05490e8e4567d419366e4ed5b328',
      'observation':'852cb3ec6365cbd326dc6d5e8c8d885656f383b8f75b6e7a8d7aab72d9a42537'}
    observed={'metadata':sha(a.metadata_sqlite),'loader':sha(a.loader_manifest),'observation':sha(a.observation_state)}
    if observed!=expected: raise SystemExit(f'frozen input hash mismatch: {observed}')
    loader=json.load(open(a.loader_manifest)); obs=np.load(a.observation_state,allow_pickle=False)
    if loader.get('schema')!='foundation-train-loader-v1' or loader.get('address_count')!=41238 or len(loader.get('shards',[]))!=42: raise SystemExit('loader semantic surface mismatch')
    if obs['states'].shape!=(42,41238) or list(obs['matrix_id'].astype(str))!=[str(x['matrix_id']) for x in loader['shards']]: raise SystemExit('observation-state/loader matrix order mismatch')
    con=sqlite3.connect(f'file:{a.metadata_sqlite}?mode=ro&immutable=1',uri=True); c=con.cursor(); part='reader_fit'
    cells=int(c.execute('select count(*) from cells where partition=?',(part,)).fetchone()[0])
    unique=int(c.execute('select count(distinct stable_key) from cells where partition=?',(part,)).fetchone()[0])
    donors=int(c.execute('select count(distinct donor_id) from cells where partition=?',(part,)).fetchone()[0])
    operators=int(c.execute('select count(distinct operator_index) from cells where partition=?',(part,)).fetchone()[0])
    groups=int(c.execute('select count(*) from (select 1 from cells where partition=? group by donor_id,operator_index)',(part,)).fetchone()[0])
    matrices=int(c.execute('select count(distinct matrix_id) from cells where partition=?',(part,)).fetchone()[0]); con.close()
    if (cells,unique,donors,operators,groups,matrices)!=(4553407,4553407,104,42,1400,42): raise SystemExit('reader-fit population geometry mismatch')
    location_status='MISSING'
    if a.location_manifest:
        if not a.location_manifest.is_file(): raise SystemExit('declared location manifest missing')
        loc=json.load(open(a.location_manifest)); entries=loc.get('shards',[])
        if loc.get('schema')!='D1_EXPRESSION_SHARD_LOCATION_MANIFEST_V2' or len(entries)!=42: raise SystemExit('location manifest semantic mismatch')
        for i,(declared,frozen) in enumerate(zip(entries,loader['shards'])):
            if int(declared.get('operator_index',-1))!=i or str(declared.get('matrix_id'))!=str(frozen['matrix_id']) or str(declared.get('counts_sha256'))!=str(frozen['counts_sha256']) or str(declared.get('meta_sha256'))!=str(frozen['meta_sha256']): raise SystemExit(f'location manifest binding mismatch at operator {i}')
            cp=Path(str(declared.get('counts_path',''))); mp=Path(str(declared.get('meta_path','')))
            if not cp.is_file() or not mp.is_file(): raise SystemExit(f'physical expression shard missing at operator {i}')
            if sha(cp)!=frozen['counts_sha256'] or sha(mp)!=frozen['meta_sha256']: raise SystemExit(f'physical shard hash drift at operator {i}')
        location_status='PASS_42_OF_42_PHYSICAL_SHARDS_BOUND'
    terminal='PASS_FULL_READER_TARGET_QUALIFICATION_EXPRESSION_PREFLIGHT' if location_status.startswith('PASS_') else 'STOP_FULL_READER_EXPRESSION_LOCATION_BINDING_MISSING'
    out={'schema':'JEPA_FULL_READER_RELATIONAL_TARGET_QUALIFICATION_PREFLIGHT_V1','terminal':terminal,'authenticated_real_population':{'cells':cells,'unique_stable_keys':unique,'donors':donors,'operators':operators,'donor_operator_groups':groups,'matrices':matrices,'addresses':41238},'frozen_inputs_sha256':observed,'physical_expression_location_binding':location_status,'target_framework':'TD57B_TD59_SCALE_FREE_RELATIONAL_GEOMETRY__NO_LOCALITY_FRACTION_RETUNING','full_reader_action_if_pass':'Run fixed relational qualification/shortcut attacks over reader_fit using d1_expression_reader_v2; do not perform outcome-responsive target search.','substitutions_forbidden':['50K discovery archive as if it were the 4,553,407-cell population','synthetic expression','reader_validation','reader_oracle','DEV','SEALED','pathology'],'pathology_used':False,'synthetic_data_used':False,'training_authorized':False}
    a.out_json.parent.mkdir(parents=True,exist_ok=True); a.out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n'); print(json.dumps(out,indent=2,sort_keys=True)); return 0 if terminal.startswith('PASS_') else 3
if __name__=='__main__': raise SystemExit(main())
