#!/usr/bin/env python3
from __future__ import annotations

import argparse, json, re
from pathlib import Path
from typing import Any, Mapping

SCHEMA = 'JEPA_V5_FULL104_EXECUTION_PLAN_V1'
PASS = 'PASS_V5_FULL104_EXECUTION_PLAN_MECHANICS__NO_EXECUTION_AUTHORITY'
STOP = 'STOP_V5_FULL104_EXECUTION_PLAN_NOT_LAWFUL'
HEX64 = re.compile(r'^[0-9a-f]{64}$')

REQUIRED_COORDS = {
    'source_row', 'logical_row', 'block_key', 'block_row_index', 'canonical_cell_id'
}
REQUIRED_BYTE_CLASSES = {'GIT_BLOB_BYTES_TRACKED_SOURCE', 'DISK_BYTES_UNTRACKED_DATA'}
REQUIRED_REPLAY = {
    'producer_imports_replay': False,
    'replay_imports_producer': False,
    'replay_derives_geometry_independently': True,
}


def _sha(x: object) -> bool:
    return isinstance(x, str) and HEX64.fullmatch(x) is not None


def _fail(reason: str) -> dict[str, Any]:
    return {'terminal': STOP, 'lawful': False, 'reason': reason,
            'execution_authorized': False, 'training_authorized': False}


def validate_plan(p: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(p, Mapping) or p.get('schema') != SCHEMA:
        return _fail('schema_mismatch')
    if p.get('full104_binding_terminal') != 'PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE':
        return _fail('full104_binding_not_closed')
    if bool(p.get('execution_authorized', False)) or bool(p.get('training_authorized', False)):
        return _fail('plan_cannot_grant_execution_or_training_authority')

    parents = p.get('parent_sha256', {})
    if not isinstance(parents, Mapping): return _fail('parent_digests_missing')
    for k in ('full104_manifest','population_membership','identity_authority','observation_state_authority'):
        if not _sha(parents.get(k)): return _fail('parent_digest_missing:' + k)

    g = p.get('geometry', {})
    expected = {'cells':4553407,'donors':104,'operators':42,'addresses':41238,'donor_operator_groups':1400}
    if not isinstance(g, Mapping) or any(int(g.get(k,-1)) != v for k,v in expected.items()):
        return _fail('full104_geometry_mismatch')
    if not bool(g.get('manifest_authenticated_before_selection', False)):
        return _fail('manifest_selection_precedes_authentication')
    if not bool(g.get('exhaustive_relevant_block_scan', False)):
        return _fail('nonexhaustive_block_scan')

    coords = p.get('coordinate_systems', {})
    if not isinstance(coords, Mapping) or set(coords) != REQUIRED_COORDS:
        return _fail('coordinate_systems_not_exact')
    if len(set(str(v) for v in coords.values())) != len(REQUIRED_COORDS):
        return _fail('coordinate_semantics_aliased')

    payload = p.get('payload_integrity', {})
    for k in ('capture_once_hash_parse_same_bytes','row_bounds_checked','shape_checked','nonnegative_integer_counts_checked'):
        if not bool(payload.get(k, False)): return _fail('payload_integrity_missing:' + k)

    roots = p.get('root_law', {})
    for k in ('parents_bound_into_closure','membership_splice_rejected','physical_plan_restores_logical','roots_recomputed_from_contents','external_expected_roots_required'):
        if not bool(roots.get(k, False)): return _fail('root_law_missing:' + k)

    byte_classes = p.get('authority_byte_classes', [])
    if set(byte_classes) != REQUIRED_BYTE_CLASSES:
        return _fail('authority_byte_classes_not_exact')

    pub = p.get('publication', {})
    for k in ('atomic_staging_replace','sidecars_required_for_resume_complete','produced_roots_from_produced_bytes_only'):
        if not bool(pub.get(k, False)): return _fail('publication_law_missing:' + k)

    replay = p.get('replay', {})
    for k,v in REQUIRED_REPLAY.items():
        if replay.get(k) is not v: return _fail('replay_independence_violation:' + k)

    auth = p.get('future_run_authority', {})
    if auth.get('required_scope') != 'BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY':
        return _fail('future_run_scope_wrong')
    if not bool(auth.get('must_be_external_pre_result_content_addressed', False)):
        return _fail('future_run_authority_not_external_preresult')
    if not bool(auth.get('produced_roots_forbidden_in_authority', False)):
        return _fail('retroactive_authorization_possible')

    if p.get('terminal') != PASS: return _fail('pass_terminal_missing')
    return {'terminal': PASS, 'lawful': True,
            'execution_authorized': False, 'training_authorized': False,
            'next_required_stage': 'CURRENT_BYTE_FULL104_BINDING_THEN_SEPARATE_BOUNDED_RUN_AUTHORITY'}


def main(argv=None) -> int:
    ap=argparse.ArgumentParser(); ap.add_argument('--plan',type=Path,required=True); ap.add_argument('--out-json',type=Path,required=True)
    a=ap.parse_args(argv); out=validate_plan(json.loads(a.plan.read_text()))
    a.out_json.parent.mkdir(parents=True,exist_ok=True); a.out_json.write_text(json.dumps(out,indent=2,sort_keys=True)+'\n')
    print(json.dumps(out,indent=2,sort_keys=True)); return 0 if out['lawful'] else 3

if __name__ == '__main__': raise SystemExit(main())
