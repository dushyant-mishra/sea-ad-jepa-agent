from __future__ import annotations
import ast,csv,hashlib,inspect,json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
CONTRACT=ROOT/'contract'/'T0_TARGET_VALIDITY_EXECUTION_AUTHORITY_SUCCESSOR_V20.md'
V18=ROOT/'contract'/'T0_TARGET_VALIDITY_SCIENTIFIC_FREEZE_CANDIDATE_V18.md'
V18_CONST=ROOT/'contract'/'T0_V18_FROZEN_CONSTANTS.json'
V20_CONST=ROOT/'contract'/'T0_V20_EXECUTION_AUTHORITY_CONSTANTS.json'
API=ROOT/'current'/'authority'/'T0_PUBLIC_API_AUTHORITY_MAP_V3.csv'
IMPL=ROOT/'contract'/'T0_V20_IMPLEMENTATION_MANIFEST.csv'
ACTIVE=ROOT/'contract'/'T0_V20_ACTIVE_TEST_MANIFEST.csv'
SUPERSEDED=ROOT/'contract'/'T0_V20_SUPERSEDED_AUTHORITY_REGISTRY.csv'
V18_SHA='0851b47d2351ded1be35a772bb9d7c05ed57d4bbbe551d81c7845a87ace85050'
V18_CONST_SHA='e255bf4ad878e3277dcdd573dbf17a10b7cd34eb78be64c78435ffa4f38971ec'
ALLOWED={'CANONICAL_CONCLUSION_ENTRYPOINT','AUTHORITY_COMPONENT_BUILDER','AUTHORITY_COMPONENT_VERIFIER','NON_AUTHORITATIVE_PRIMITIVE','DIAGNOSTIC_OR_REGRESSION_ONLY','SUPERSEDED_NON_AUTHORITATIVE_PRIMITIVE'}

def _sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def _public_defs():
    got=set()
    for p in (ROOT/'current/code').glob('*.py'):
        tree=ast.parse(p.read_text(encoding='utf-8'))
        for node in tree.body:
            if isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef)) and not node.name.startswith('_'):
                got.add((p.name,node.name))
    return got

def main():
    checks={}
    checks['v18_contract_unchanged']=_sha(V18)==V18_SHA
    checks['v18_constants_unchanged']=_sha(V18_CONST)==V18_CONST_SHA
    c=json.loads(V20_CONST.read_text())
    checks['v20_embeds_exact_v18_constants']=(c['scientific_constants']==json.loads(V18_CONST.read_text()) and c['v18_scientific_contract_sha256']==V18_SHA and c['v18_frozen_constants_sha256']==V18_CONST_SHA)
    checks['invalid_precedes_not_estimable_declared']=c.get('structural_invalid_precedes_not_estimable') is True

    m=pd.read_csv(API)
    pairs=list(map(tuple,m[['module','function']].itertuples(index=False,name=None)))
    checks['api_map_columns_exact']=list(m.columns)==['module','function','classification','claim_boundary']
    checks['api_map_unique']=len(pairs)==len(set(pairs))
    checks['api_map_complete']=set(pairs)==_public_defs()
    checks['api_classifications_allowed']=set(m.classification)<=ALLOWED
    checks['api_claim_boundaries_nonempty']=m.claim_boundary.astype(str).str.len().gt(0).all()
    q=m[m.classification.eq('CANONICAL_CONCLUSION_ENTRYPOINT')]
    checks['exact_three_v20_entrypoints']=set(zip(q.module,q.function))=={
        ('t0_canonical_freeze_v2.py','freeze_target_after_role_v2'),
        ('t0_canonical_freeze_v2.py','freeze_tail_after_discovery_authority_v2'),
        ('t0_adjudicator_v2.py','adjudicate_from_raw_v2')}
    old={('t0_canonical_freeze_v1.py','freeze_target_after_role'),('t0_canonical_freeze_v1.py','freeze_tail_after_discovery_authority'),('t0_adjudicator_v1.py','adjudicate_from_raw')}
    checks['v18_entrypoints_superseded']=all(m[(m.module==a)&(m.function==b)].iloc[0].classification=='SUPERSEDED_NON_AUTHORITATIVE_PRIMITIVE' for a,b in old)

    import t0_canonical_freeze_v2 as fr, t0_adjudicator_v2 as ad
    checks['production_target_no_bypass_arg']='allow_synthetic_test_fixture' not in inspect.signature(fr.freeze_target_after_role_v2).parameters
    checks['production_tail_no_bypass_arg']='allow_synthetic_test_fixture' not in inspect.signature(fr.freeze_tail_after_discovery_authority_v2).parameters
    checks['production_adjudicator_no_bypass_arg']='allow_synthetic_test_fixture' not in inspect.signature(ad.adjudicate_from_raw_v2).parameters
    checks['test_entrypoints_separate']=all(hasattr(fr,x) for x in ['freeze_target_after_role_v2_for_test','freeze_tail_after_discovery_authority_v2_for_test']) and hasattr(ad,'adjudicate_from_raw_v2_for_test')

    rows=list(csv.DictReader(IMPL.open())); actual=[]
    for sub,kind in [('current/code','code'),('current/tests','test'),('current/authority','authority')]:
        for p in sorted((ROOT/sub).glob('*'),key=lambda x:x.name.encode()):
            if p.is_file(): actual.append((p.relative_to(ROOT).as_posix(),kind,p.stat().st_size,_sha(p)))
    expected=[(r['relative_path'],r['kind'],int(r['bytes']),r['sha256']) for r in rows]
    actual=sorted(actual,key=lambda r:r[0].encode('utf-8'))
    checks['implementation_manifest_exact']=expected==actual

    ar=list(csv.DictReader(ACTIVE.open()))
    active_paths=[r['relative_path'] for r in ar]
    selected=sorted((p.relative_to(ROOT).as_posix() for p in (ROOT/'current/tests').glob('test_*.py')),key=lambda x:x.encode())
    checks['active_test_path_set_exact']=active_paths==selected
    checks['active_test_hashes_exact']=all(_sha(ROOT/r['relative_path'])==r['sha256'] and (ROOT/r['relative_path']).stat().st_size==int(r['bytes']) for r in ar)

    sr=list(csv.DictReader(SUPERSEDED.open()))
    checks['superseded_archives_exact']=all((ROOT/r['archived_path']).is_file() and (ROOT/r['archived_path']).stat().st_size==int(r['bytes']) and _sha(ROOT/r['archived_path'])==r['sha256'] for r in sr)
    checks['superseded_active_paths_absent']=all(not (ROOT/r['active_path']).exists() for r in sr)
    checks['superseded_tests_not_active']=all(r['active_path'] not in active_paths for r in sr)

    text=CONTRACT.read_text(encoding='utf-8')
    citations={
        'api_map':(API.name,_sha(API)),
        'implementation_manifest':(IMPL.name,_sha(IMPL)),
        'active_test_manifest':(ACTIVE.name,_sha(ACTIVE)),
        'superseded_registry':(SUPERSEDED.name,_sha(SUPERSEDED)),
        'v20_constants':(V20_CONST.name,_sha(V20_CONST)),
    }
    checks['contract_exact_authority_citations']=all(name in text and digest in text for name,digest in citations.values())

    # Pandas/numpy predicates can return numpy.bool_; normalize audit output to
    # built-in bool so the frozen report is JSON-serializable on all platforms.
    checks={k:bool(v) for k,v in checks.items()}
    status='PASS_T0_V20_CONTRACT_EQUIVALENCE' if all(checks.values()) else 'STOP_T0_V20_CONTRACT_EQUIVALENCE'
    return {'schema':'T0_V20_EXECUTION_AUTHORITY_CONTRACT_EQUIVALENCE_V1','status':status,'checks':checks,'contract_sha256':_sha(CONTRACT),'implementation_manifest_sha256':_sha(IMPL),'active_test_manifest_sha256':_sha(ACTIVE),'api_map_sha256':_sha(API),'superseded_registry_sha256':_sha(SUPERSEDED)}

if __name__=='__main__':
    r=main(); print(json.dumps(r,sort_keys=True)); raise SystemExit(0 if r['status'].startswith('PASS_') else 2)
