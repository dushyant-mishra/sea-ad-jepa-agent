import importlib.util
from pathlib import Path

P=Path(__file__).resolve().parents[1]/'scripts'/'v5_anticheat'/'validate_full104_execution_plan_v1.py'
spec=importlib.util.spec_from_file_location('m',P); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
H='a'*64

def valid():
    return {
      'schema':m.SCHEMA,'terminal':m.PASS,
      'full104_binding_terminal':'PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE',
      'execution_authorized':False,'training_authorized':False,
      'parent_sha256':{k:H for k in ('full104_manifest','population_membership','identity_authority','observation_state_authority')},
      'geometry':{'cells':4553407,'donors':104,'operators':42,'addresses':41238,'donor_operator_groups':1400,
                  'manifest_authenticated_before_selection':True,'exhaustive_relevant_block_scan':True},
      'coordinate_systems':{'source_row':'ORIGINAL_SOURCE_ROW','logical_row':'FULL104_LOGICAL_ROW','block_key':'MATERIALIZED_BLOCK_KEY','block_row_index':'ROW_WITHIN_BLOCK','canonical_cell_id':'CANONICAL_CELL_ID'},
      'payload_integrity':{k:True for k in ('capture_once_hash_parse_same_bytes','row_bounds_checked','shape_checked','nonnegative_integer_counts_checked')},
      'root_law':{k:True for k in ('parents_bound_into_closure','membership_splice_rejected','physical_plan_restores_logical','roots_recomputed_from_contents','external_expected_roots_required')},
      'authority_byte_classes':sorted(m.REQUIRED_BYTE_CLASSES),
      'publication':{k:True for k in ('atomic_staging_replace','sidecars_required_for_resume_complete','produced_roots_from_produced_bytes_only')},
      'replay':dict(m.REQUIRED_REPLAY),
      'future_run_authority':{'required_scope':'BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY','must_be_external_pre_result_content_addressed':True,'produced_roots_forbidden_in_authority':True},
    }

def test_valid_is_mechanics_only():
    o=m.validate_plan(valid()); assert o['lawful']; assert not o['execution_authorized']; assert not o['training_authorized']

def test_manifest_must_be_authenticated_before_selection():
    r=valid(); r['geometry']['manifest_authenticated_before_selection']=False; assert m.validate_plan(r)['reason']=='manifest_selection_precedes_authentication'

def test_scan_must_be_exhaustive():
    r=valid(); r['geometry']['exhaustive_relevant_block_scan']=False; assert m.validate_plan(r)['reason']=='nonexhaustive_block_scan'

def test_coordinates_cannot_alias():
    r=valid(); r['coordinate_systems']['logical_row']=r['coordinate_systems']['source_row']; assert m.validate_plan(r)['reason']=='coordinate_semantics_aliased'

def test_payload_must_be_hash_parse_same_bytes():
    r=valid(); r['payload_integrity']['capture_once_hash_parse_same_bytes']=False; assert m.validate_plan(r)['reason']=='payload_integrity_missing:capture_once_hash_parse_same_bytes'

def test_membership_splice_must_be_rejected():
    r=valid(); r['root_law']['membership_splice_rejected']=False; assert m.validate_plan(r)['reason']=='root_law_missing:membership_splice_rejected'

def test_physical_plan_must_restore_logical():
    r=valid(); r['root_law']['physical_plan_restores_logical']=False; assert m.validate_plan(r)['reason']=='root_law_missing:physical_plan_restores_logical'

def test_wrong_byte_class_surface_rejected():
    r=valid(); r['authority_byte_classes']=['DISK_BYTES_UNTRACKED_DATA']; assert m.validate_plan(r)['reason']=='authority_byte_classes_not_exact'

def test_resume_needs_sidecars():
    r=valid(); r['publication']['sidecars_required_for_resume_complete']=False; assert m.validate_plan(r)['reason']=='publication_law_missing:sidecars_required_for_resume_complete'

def test_replay_cannot_import_producer():
    r=valid(); r['replay']['replay_imports_producer']=True; assert m.validate_plan(r)['reason']=='replay_independence_violation:replay_imports_producer'

def test_authorization_cannot_be_retroactive():
    r=valid(); r['future_run_authority']['produced_roots_forbidden_in_authority']=False; assert m.validate_plan(r)['reason']=='retroactive_authorization_possible'

def test_plan_cannot_grant_execution():
    r=valid(); r['execution_authorized']=True; assert m.validate_plan(r)['reason']=='plan_cannot_grant_execution_or_training_authority'
