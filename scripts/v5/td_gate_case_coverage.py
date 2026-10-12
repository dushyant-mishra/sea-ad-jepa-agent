"""Coverage-only bridge from a frozen prefreeze registry to per-case evidence."""
from __future__ import annotations
import hashlib, json
from collections import Counter

PREFREEZE_SCHEMA='JEPA_TD_TARGET_TOURNAMENT_PREFREEZE_MANIFEST_V1'
PREFREEZE_FIELDS={
    'schema','fixture_only','family_alpha','multiplicity_method','decision_family_size',
    'decision_family_registry_sha256','alpha_eff','minimum_nonzero_donors_for_sign_resolution',
    'minimum_permutation_draws_for_resolution','tournament_contract_sha256','null_seed_material',
    'case_resolution','authority','manifest_sha256'
}
PREFREEZE_AUTHORITY_KEYS={
    'value_read_authorized','real_tournament_authorized','target_selection_authorized',
    'representation_selection_authorized','td60_authorized','stage4_authorized','training_authorized'
}
PREFREEZE_CASE_FIELDS={
    'case_id','candidate_id','gate_id','source','analysis_tier','endpoint_id',
    'available_donors_upper_bound','resolution_impossible_from_donor_upper_bound',
    'estimability_proven','biological_result'
}
RECEIPT_FIELDS={
    'case_id','candidate_id','gate_id','source','analysis_tier','endpoint_id','status','evidence_sha256'
}
ALLOWED_STATUS={'PASS','FAIL','NOT_ESTIMABLE'}


class CoverageError(ValueError):
    pass


def _canonical_sha(obj):
    return hashlib.sha256(json.dumps(obj,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def _valid_sha(v):
    return isinstance(v,str) and len(v)==64 and all(c in '0123456789abcdef' for c in v)


def _validate_prefreeze(manifest, expected_prefreeze_manifest_sha256):
    if not _valid_sha(expected_prefreeze_manifest_sha256):
        raise CoverageError('expected prefreeze manifest SHA must be lowercase SHA-256')
    if not isinstance(manifest,dict) or set(manifest) != PREFREEZE_FIELDS:
        raise CoverageError('prefreeze manifest fields must be exact')
    if manifest.get('schema') != PREFREEZE_SCHEMA:
        raise CoverageError('invalid prefreeze manifest schema')
    stated=manifest.get('manifest_sha256')
    if not _valid_sha(stated):
        raise CoverageError('invalid prefreeze manifest SHA')
    if stated != expected_prefreeze_manifest_sha256:
        raise CoverageError('prefreeze manifest SHA differs from external frozen pin')
    core=dict(manifest); core.pop('manifest_sha256',None)
    if _canonical_sha(core) != stated:
        raise CoverageError('prefreeze manifest hash mismatch')
    if manifest.get('fixture_only') is not True:
        raise CoverageError('current coverage helper requires fixture prefreeze')
    auth=manifest.get('authority')
    if (
        not isinstance(auth,dict)
        or set(auth) != PREFREEZE_AUTHORITY_KEYS
        or any(v is not False for v in auth.values())
    ):
        raise CoverageError('prefreeze authority must be exact and false')
    rows=manifest.get('case_resolution')
    if not isinstance(rows,list) or not rows:
        raise CoverageError('prefreeze case_resolution required')
    for row in rows:
        if not isinstance(row,dict) or set(row) != PREFREEZE_CASE_FIELDS:
            raise CoverageError('prefreeze case_resolution fields must be exact')
        if row.get('estimability_proven') is not False:
            raise CoverageError('prefreeze cannot claim estimability before outcomes')
        if row.get('biological_result') != 'NOT_OPENED':
            raise CoverageError('prefreeze biological_result must remain NOT_OPENED')
        if type(row.get('resolution_impossible_from_donor_upper_bound')) is not bool:
            raise CoverageError('resolution_impossible_from_donor_upper_bound must be boolean')
    return rows,stated


def audit_gate_case_coverage(
    prefreeze_manifest,
    *,
    expected_prefreeze_manifest_sha256,
    candidate_id,
    gate_id,
    case_receipts,
):
    rows,prefreeze_sha=_validate_prefreeze(
        prefreeze_manifest, expected_prefreeze_manifest_sha256
    )
    expected=[
        r for r in rows
        if r.get('candidate_id')==candidate_id and r.get('gate_id')==gate_id
    ]
    if not expected:
        raise CoverageError('candidate/gate pair absent from frozen decision family')
    expected_by={}
    role_fields=('candidate_id','gate_id','source','analysis_tier','endpoint_id')
    for r in expected:
        cid=r.get('case_id')
        if not isinstance(cid,str) or not cid or cid in expected_by:
            raise CoverageError('invalid or duplicate frozen case_id')
        expected_by[cid]=r
    if not isinstance(case_receipts,list):
        raise CoverageError('case_receipts must be list')
    actual_by={}
    for rec in case_receipts:
        if not isinstance(rec,dict) or set(rec) != RECEIPT_FIELDS:
            raise CoverageError('case receipt fields must be exact')
        cid=rec['case_id']
        if not isinstance(cid,str) or not cid or cid in actual_by:
            raise CoverageError('invalid or duplicate case receipt')
        if rec['status'] not in ALLOWED_STATUS:
            raise CoverageError('invalid case status')
        if not _valid_sha(rec['evidence_sha256']):
            raise CoverageError('invalid case evidence SHA')
        actual_by[cid]=rec
    if set(actual_by) != set(expected_by):
        raise CoverageError('case receipt set does not exactly cover frozen cases')
    for cid, exp in expected_by.items():
        rec=actual_by[cid]
        for field in role_fields:
            if rec[field] != exp.get(field):
                raise CoverageError(f'case role mismatch: {cid}: {field}')
    ordered=[actual_by[cid] for cid in sorted(actual_by)]
    status_counts=Counter(r['status'] for r in ordered)
    return {
        'schema':'JEPA_TD_GATE_CASE_COVERAGE_AUDIT_V1',
        'fixture_only':True,
        'candidate_id':candidate_id,
        'gate_id':gate_id,
        'prefreeze_manifest_sha256':prefreeze_sha,
        'expected_case_count':len(expected_by),
        'received_case_count':len(actual_by),
        'coverage_complete':True,
        'status_counts':{s:int(status_counts.get(s,0)) for s in ('PASS','FAIL','NOT_ESTIMABLE')},
        'case_evidence_bundle_sha256':_canonical_sha(ordered),
        'gate_status_not_adjudicated':True,
        'authority':{
            'target_selected':False,
            'representation_selected':False,
            'training_authorized':False,
            'value_read_authorized':False,
        },
    }
