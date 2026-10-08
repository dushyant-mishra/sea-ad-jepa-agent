#!/usr/bin/env python3
from __future__ import annotations
import csv, hashlib, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
PASS='PASS_TEACHER_STUDENT_V5_DATA_FIRST_AUDIT__DESIGN_ONLY__TRAINING_UNAUTHORIZED'


def sha256(p:Path)->str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def require(cond:bool,msg:str)->None:
    if not cond: raise RuntimeError(msg)


def main()->int:
    selection=ROOT/'docs/agent/TEACHER_STUDENT_V5_ACTIVE_TEST_SELECTION.txt'
    manifest=ROOT/'docs/agent/TEACHER_STUDENT_V5_ACTIVE_TEST_MANIFEST.csv'
    tests=[x.strip() for x in selection.read_text().splitlines() if x.strip()]
    require(len(tests)==11 and len(set(tests))==11,'active test selection must contain 11 unique files')
    with manifest.open(newline='',encoding='utf-8') as f:
        rows=list(csv.DictReader(f))
    require([r['path'] for r in rows]==tests,'active manifest paths/order differ from selection')
    for r in rows:
        p=ROOT/r['path']; require(p.is_file(),f'missing active test {p}')
        require(int(r['bytes'])==p.stat().st_size,f'byte-size drift {p}')
        require(r['sha256']==sha256(p),f'SHA drift {p}')

    target=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_SCIENTIFIC_TARGET_AUTHORITY_V2.json').read_text())
    require(target['status']=='SCIENTIFIC_TARGET_REPAIRED__PROPOSAL_AND_EXECUTION_UNFROZEN','scientific target status drift')
    require(target['base_jepa']['policy_id']=='DONOR_UNIFORM__CELL_UNIFORM_WITHIN_DONOR_V1','base scientific target drift')
    require(target['relational']['policy_id']=='DONOR_UNIFORM__ELIGIBLE_ANCHOR_CELL_UNIFORM__SAME_OPERATOR_COMPARATOR_PAIR_UNIFORM_V2','relational scientific target drift')
    require(target['relational']['operator_role']=='ADMISSIBILITY_BOUNDARY_ONLY__NOT_EQUAL_SCIENTIFIC_MASS','operator was promoted back to equal scientific mass')
    require(target['relational']['group_mass']=='eligible_cells_in_group / eligible_cells_in_donor','relational group mass is not anchor-prevalence based')
    require(target['proposal']['base_policy_id'] is None and target['proposal']['relational_policy_id'] is None,'proposal was selected inside target authority')
    require(target['training_authorized'] is False and target['execution_authorized'] is False,'target authority opened execution')

    proposal=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_PROPOSAL_AUTHORITY_V2.json').read_text())
    require(proposal['relational']['proposal_policy_id']=='DIRECT_DONOR_ANCHOR_CELL_TRIPLET_TARGET_PROPOSAL_V2','relational proposal drift')
    require(proposal['relational']['proposal_equals_target'] is True and proposal['relational']['importance_correction_required'] is False,'relational proposal must exactly sample frozen target')
    require(proposal['base']['final_derivation_policy_id'] is None and proposal['base']['selected_policy_id'] is None and proposal['base']['selected_parameters'] is None,'base proposal/derivation was frozen before constraint authority')
    require(proposal['training_authorized'] is False and proposal['execution_authorized'] is False,'proposal authority opened execution')
    coverage=json.loads((ROOT/'docs/agent/READER_FIT_BASE_PROPOSAL_COVERAGE_PROFILE_V1.json').read_text())
    require(coverage['selection']['selected_policy_id'] is None and coverage['selection']['selected_alpha'] is None,'descriptive base proposal profile selected q')
    require(coverage['proposal_families']['TARGET_DONOR_UNIFORM_CELL_WITHIN_DONOR']['importance_ess_fraction']==1.0,'target proposal ESS drift')
    require(coverage['proposal_families']['SOURCE_UNIFORM_CELL_WITHIN_SOURCE']['importance_ess_fraction'] > .40,'source proposal ESS diagnostic drift')
    require(coverage['proposal_families']['DONOR_UNIFORM_OPERATOR_GROUP_UNIFORM_CELL_WITHIN_GROUP__PROPOSAL_ONLY']['expected_group_presentations_at_H_equals_reader_fit_cells']['min'] > 1800,'operator coverage diagnostic drift')

    opsem=json.loads((ROOT/'docs/agent/READER_FIT_OPERATOR_SEMANTICS_PROFILE_V1.json').read_text())
    require(opsem['cross_source_operator_semantics']['common_scientific_axis_established'] is False,'operator was incorrectly declared a common scientific axis')
    require(opsem['eligible_cell_fraction'] > .99998,'relational eligible-cell support unexpectedly collapsed')
    require(opsem['relational_weighting_diagnostic']['max_equal_group_upweight_vs_anchor'] > 100.0,'operator-weighting distortion diagnostic missing')

    pareto=json.loads((ROOT/'docs/agent/READER_FIT_DONOR_PROPOSAL_PARETO_V1.json').read_text())
    require(pareto['selected_proposal_policy'] is None and pareto['selected_alpha'] is None,'proposal Pareto must remain descriptive')
    require(pareto['training_authorized'] is False,'proposal profile opened training')

    support=json.loads((ROOT/'docs/agent/READER_FIT_SUPPORT_OVERLAP_PROFILE_V1.json').read_text())
    require(support['all_42_operators_measured_scalar']==17186,'common-core count drift')
    require(support['common_core_materialization']['csv_sha256']=='8aa8dfebb481aa2e60b12ab0f581ba1a36063b6c12dc2d8514d5fe7a20ad07ac','common-core derived-byte authority drift')
    require(support['common_core_materialization']['checked_in'] is False,'derived common-core rows should not be duplicated in repository')
    anchor=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_COMMON_CORE_ANCHOR_CANDIDATE_V1.json').read_text())
    require(anchor['student_view_families']['COMMON_CORE_ANCHOR']['visible_gene_count'] is None,'common-core visible count prematurely frozen')
    require(anchor['student_view_families']['NATIVE_SUPPORT_COVERAGE']['visible_gene_count'] is None,'native visible count prematurely frozen')
    require(anchor['training_authorized'] is False,'anchor candidate opened training')

    authority=json.loads((ROOT/'docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_AUTHORITY_CANDIDATE.json').read_text())
    require(authority['scientific_target_frozen'] is True and authority['base_proposal_frozen'] is False and authority['relational_proposal_frozen'] is True and authority['proposal_policy_frozen'] is False,'target/proposal boundary drift')
    require(authority['training_authorized'] is False and authority['successor_u0_materialization_authorized'] is False and authority['td60_execution_authorized'] is False,'candidate opened execution')

    geometry=(ROOT/'src/sea_ad_jepa/v5/data_first_geometry.py').read_text()
    require('_HASH_PRIME' not in geometry and 'def keyed_feature_dropout(' not in geometry,'old hash dropout remains as competing RNG authority')
    rng=(ROOT/'src/sea_ad_jepa/v5/keyed_rng_contract_v2.py').read_text()
    require('philox4x32_10' in rng and 'dropout_philox_address' in rng,'Philox V2 RNG contract missing')
    checkpoint=(ROOT/'src/sea_ad_jepa/v5/inactive_update_reference.py').read_text()
    require('V5ReferenceCheckpoint' in checkpoint and 'restore_reference_checkpoint' in checkpoint,'V5 reference checkpoint proof missing')

    v4_runtime=(ROOT/'src/sea_ad_jepa/v4/teacher_student_runtime.py').read_text()
    require('sea_ad_jepa.v5' not in v4_runtime,'V4 runtime imports V5')
    require('keyed_rng_contract_v2' not in v4_runtime,'V4 runtime imports V5 RNG')

    proto_manifest=ROOT/'docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_MANIFEST.csv'
    proto_root=ROOT/'docs/agent/TEACHER_STUDENT_V5_DATA_FIRST_PROTOTYPE_ROOT.txt'
    with proto_manifest.open(newline='',encoding='utf-8') as f:
        proto_rows=list(csv.DictReader(f))
    require(proto_rows and len({r['path'] for r in proto_rows})==len(proto_rows),'prototype manifest empty/duplicate paths')
    for r in proto_rows:
        p=ROOT/r['path']; require(p.is_file(),f'missing prototype payload {p}')
        require(int(r['bytes'])==p.stat().st_size,f'prototype byte-size drift {p}')
        require(r['sha256']==sha256(p),f'prototype SHA drift {p}')
    require(proto_root.read_text().strip()==sha256(proto_manifest),'prototype root does not bind manifest bytes')

    forbidden=[
        ROOT/'docs/agent/HEALTHY_TEACHER_U0_U40_EXECUTION_AUTHORITY_V1.json',
        ROOT/'docs/agent/HEALTHY_TEACHER_CONTINUATION_EXECUTION_AUTHORITY_V1.json',
    ]
    require(not any(p.exists() for p in forbidden),'execution authority present on V5 planning branch')
    print(PASS)
    return 0

if __name__=='__main__': raise SystemExit(main())
