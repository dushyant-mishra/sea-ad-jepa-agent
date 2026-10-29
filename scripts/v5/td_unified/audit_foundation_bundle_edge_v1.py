#!/usr/bin/env python3
"""Read-only August Foundation bundle observation-edge audit.

Checks 42 x 41,238 support keys, the main+supplemental collision mask,
archived loader code semantics and conditional q-in-denominator leak.
Does not read cell-level expression or protected metadata and NEVER issues
R1/R1D/R2 producer or training authority.
"""
from __future__ import annotations
import argparse
import csv
import gzip
import hashlib
import io
import json
import math
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

TARGETS=(
    'BUNDLE_STATUS.json', 'BUNDLE_SHA256_MANIFEST.csv',
    'contracts/address_measurement_support.csv.gz',
    'contracts/collision_ledger.csv.gz',
    'contracts/unregistered_collisions.csv',
    'contracts/address_namespace.csv',
    'contracts/production_loader_manifest.json',
    'code/production_train_loader.py',
)


def _member(z, relative):
    matches=[n for n in z.namelist() if n.endswith('/'+relative) or n==relative]
    if len(matches)!=1: raise ValueError('missing or ambiguous bundle member '+relative)
    return matches[0]


def _bytes(z, relative):
    return z.read(_member(z,relative))


def _csv(z, relative):
    name=_member(z,relative)
    with z.open(name) as f:
        reader=gzip.GzipFile(fileobj=f) if name.endswith('.gz') else f
        with io.TextIOWrapper(reader, encoding='utf-8', newline='') as text:
            yield from csv.DictReader(text)


def _sha(data):return hashlib.sha256(data).hexdigest()


def _file_sha(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for ch in iter(lambda:f.read(8<<20),b''):h.update(ch)
    return h.hexdigest()


def source_library_counterfactual(base_count=3, query_low=7, query_high=100):
    """Pure conditional witness; not measurement of actual source-library rows."""
    if not all(type(x) is int and x>=0 for x in (base_count,query_low,query_high)):
        raise ValueError('exact nonnegative synthetic counts required')
    low=math.log1p(base_count*10000/max(base_count+query_low,1))
    high=math.log1p(base_count*10000/max(base_count+query_high,1))
    return {'base_count_fixed':base_count,'queried_count_low':query_low,
            'queried_count_high':query_high,
            'log1p_cp10k_base_low':low,'log1p_cp10k_base_high':high,
            'base_value_changed_due_to_denominator':low!=high}


def summarize_collision_contract(support_rows,ledger_rows,supplemental_rows,*,address_count=None,operator_count=None):
    """Fail closed on structural contradictions; no claim of physical closure."""
    ledger=defaultdict(list)
    for x in ledger_rows:
        key=(x['matrix_id'],x['molecular_address_id'])
        if x.get('scalar_materialization_status')!='MEASURED_COLLISION_UNRESOLVED':
            raise ValueError('registered collision not unresolved')
        ledger[key].append(x)
    registered=set(ledger)
    unregistered={}
    for x in supplemental_rows:
        key=(x['matrix_id'],x['molecular_address_id'])
        if key in unregistered:raise ValueError('duplicate supplemental collision pair')
        if type(x.get('unregistered_source_rows')) is not str or int(x['unregistered_source_rows'])<2:
            raise ValueError('supplemental source multiplicity absent')
        unregistered[key]=x
    if registered & set(unregistered):raise ValueError('a supplementary pair duplicates the registered ledger')
    blocked=registered|set(unregistered)
    support_keys=set(); matrix_counts=Counter(); support_measured=Counter(); states=Counter(); blocked_seen=set()
    support_collisions=0
    for x in support_rows:
        key=(x['matrix_id'],x['molecular_address_id'])
        if key in support_keys:raise ValueError('duplicate support matrix/address')
        support_keys.add(key)
        matrix_counts[x['matrix_id']]+=1
        flag=x['measured_address']
        if flag not in ('True','False'):raise ValueError('noncanonical measured_address')
        measured=flag=='True'
        state='MEASURED_COLLISION_UNRESOLVED' if key in blocked else (
              'MEASURED_SCALAR' if measured else 'STRUCTURALLY_UNMEASURED')
        states[state]+=1
        if measured:support_measured['measured_before_collision_mask']+=1
        if key in blocked:
            blocked_seen.add(key)
            if not measured:raise ValueError('collision mask targets unmeasured support')
            support_collisions+=1
    if not blocked<=support_keys:raise ValueError('collision pair missing from support')
    if address_count is not None and any(n!=address_count for n in matrix_counts.values()):
        raise ValueError('incomplete support address universe')
    if operator_count is not None and len(matrix_counts)!=operator_count:
        raise ValueError('operator support roster incomplete')
    return {
        'operators':len(matrix_counts),'support_rows':len(support_keys),
        'registered_collision_pairs':len(registered),'registered_collision_source_rows':sum(map(len,ledger.values())),
        'supplemental_collision_pairs':len(unregistered),
        'supplemental_collision_source_rows':sum(int(x['unregistered_source_rows']) for x in unregistered.values()),
        'registered_supplemental_overlap_pairs':len(registered&set(unregistered)),
        'combined_collision_pairs':len(blocked),'all_blocked_pairs_present_in_support':blocked_seen==blocked,
        'measured_before_collision_override':support_measured['measured_before_collision_mask'],
        'final_state_counts':dict(states),
        'all_supplemental_pairs_finally_unresolved':all(key in blocked_seen for key in unregistered),
        'source_feature_alias_closure_authenticated':False,
        'physical_unit_identity_authenticated':False,
        'donor_identity_authenticated':False,
    }


def run(bundle):
    with zipfile.ZipFile(bundle) as z:
        status=json.loads(_bytes(z,'BUNDLE_STATUS.json'))
        original_manifest=_bytes(z,'BUNDLE_SHA256_MANIFEST.csv')
        if _sha(original_manifest)!=status['manifest_sha256']:
            raise ValueError('bundle content manifest digest mismatch')
        manifest={x['path']:x for x in csv.DictReader(io.StringIO(original_manifest.decode('utf8')))}
        for relative in TARGETS:
            if relative in ('BUNDLE_SHA256_MANIFEST.csv','BUNDLE_STATUS.json'):continue
            if relative not in manifest:raise ValueError('member absent from archive manifest: '+relative)
            blob=_bytes(z,relative)
            if _sha(blob)!=manifest[relative]['sha256'] or len(blob)!=int(manifest[relative]['bytes']):
                raise ValueError('member digest/size mismatch: '+relative)
        result=summarize_collision_contract(
            _csv(z,'contracts/address_measurement_support.csv.gz'),
            _csv(z,'contracts/collision_ledger.csv.gz'),
            _csv(z,'contracts/unregistered_collisions.csv'),
            address_count=status['addresses'],operator_count=status['operators'],
        )
        namespace_count=sum(1 for _ in _csv(z,'contracts/address_namespace.csv'))
        if namespace_count!=status['addresses']:
            raise ValueError('address namespace coverage mismatch')
        code=_bytes(z,'code/production_train_loader.py').decode('utf8')
        # This confirms the archived text, not the physical path actually run.
        exact_clauses=(
            'blocked.update(zip(supplemental.matrix_id.astype(str), supplemental.molecular_address_id.astype(str)))',
            'state[unresolved] = MEASURED_COLLISION_UNRESOLVED',
            'library = local.source_library.to_numpy(np.float32)',
            'normalized = matrix.multiply((10_000.0 / np.maximum(library, 1.0))[:, None]).tocsr()',
            'normalized.data = np.log1p(normalized.data)',
        )
        archived_code_contract={
            'supplemental_mask_union_in_archived_code':all(t in code for t in exact_clauses[:2]),
            'source_library_log1p_cp10k_in_archived_code':all(t in code for t in exact_clauses[2:]),
        }
        if not all(archived_code_contract.values()):raise ValueError('archived loader code contract changed')
        witness=source_library_counterfactual()
        return {
            'schema':'JEPA_AUG2026_BUNDLE_R2_CONTRACT_EDGE_AUDIT_V1',
            'evidence_class':'LOCAL_USER_UPLOADED_HISTORICAL_ARCHIVE_CONTRACTS__NOT_CURRENT_REAL_SOURCE',
            'archive_sha256':_file_sha(bundle),
            'bundle_manifest_sha256':status['manifest_sha256'],
            'loader_code_sha256':_sha(code.encode('utf8')),
            'namespace_addresses':namespace_count,
            'collision_support':result,
            'archived_loader_code':archived_code_contract,
            'conditional_denominator_counterfactual':witness,
            'interpretation':{
                'supplemental_pairs':'All supplemental collision pairs are overridden to unresolved by the archived loader contract; support measured=True alone is NOT scalar materialization.',
                'conditional_normalizer':'If source_library includes queried molecules, the archived full-source-library CP10K transform makes unchanged base values vary when query mass changes.',
                'not_established':'No current source alias closure, q-independent source_library, per-query cell QC roster, actual counts/shard execution, donor/physical identity, or independent source issuer authenticated.'
            },
            'authority_effect':'NONE','real_training_authorized':False,
            'stage4_authorized':False,
            'target_winner':'NONE','representation_winner':'NONE',
        }


def main():
    p=argparse.ArgumentParser();p.add_argument('bundle');p.add_argument('--receipt')
    a=p.parse_args();out=run(Path(a.bundle));s=json.dumps(out,indent=2,sort_keys=True)+'\n'
    if a.receipt:Path(a.receipt).write_text(s,encoding='utf8')
    else:print(s)
if __name__=='__main__':main()
