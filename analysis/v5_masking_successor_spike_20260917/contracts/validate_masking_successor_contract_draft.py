import json, sys
from pathlib import Path

p = Path(sys.argv[1])
x = json.loads(p.read_text())
errors = []
if x.get('training_authorized') is not False:
    errors.append('TRAINING_MUST_REMAIN_OFF')
if x.get('protected_outcomes_authorized') is not False:
    errors.append('PROTECTED_OUTCOMES_MUST_REMAIN_CLOSED')
if x.get('status') != 'PROSPECTIVE_DRAFT_NOT_AUTHORITY':
    errors.append('DRAFT_STATUS_REQUIRED')

sem = x.get('scientific_semantics', {})
expected_semantics = {
    'foundation_objective': 'INFER_UNDERLYING_BIOLOGICAL_CELLULAR_STATE_FROM_PARTIAL_RNA_EVIDENCE',
    'query_local_target': 'QUERY_LOCAL_BIOLOGICAL_STATE_ASSOCIATED_WITH_A_MASKED_ADDRESS',
    'hidden_address_role': 'DEFINE_WHICH_LOCAL_STATE_MUST_BE_INFERRED_NOT_A_SCALAR_RECONSTRUCTION_TARGET',
    'forbidden_foundation_objective': 'PREDICT_NUMERICAL_EXPRESSION_OF_THE_HIDDEN_GENE',
    'masking_role': 'REMOVE_EASY_PROXY_EVIDENCE_WHILE_PRESERVING_A_STATE_INFERENCE_TASK',
    'expression_attacker_role': 'ANTI_SHORTCUT_DIAGNOSTIC_ONLY_NOT_THE_JEPA_TARGET_OR_TRAINING_LOSS',
    'qualification_scope_limit': 'EXPRESSION_PROXY_REMOVAL_DOES_NOT_BY_ITSELF_ESTABLISH_BIOLOGICAL_STATE_RECOVERY',
}
for k, v in expected_semantics.items():
    if sem.get(k) != v:
        errors.append(f'SCIENTIFIC_SEMANTICS_MISMATCH:{k}')

req = x.get('required_authority_roots', {})
unresolved = [k for k,v in req.items() if not isinstance(v,str) or v.startswith('UNRESOLVED')]
if unresolved and x.get('execution_authorized') is not False:
    errors.append('UNRESOLVED_ROOTS_MUST_BLOCK_EXECUTION')
if x.get('address_universe_ladder','').startswith('UNRESOLVED') and x.get('execution_authorized') is not False:
    errors.append('UNRESOLVED_UNIVERSE_LADDER_MUST_BLOCK_EXECUTION')
if str(x.get('target_count','')).startswith('UNRESOLVED') and x.get('execution_authorized') is not False:
    errors.append('UNRESOLVED_TARGET_COUNT_MUST_BLOCK_EXECUTION')
mask = x.get('masking_requirements', {})
for k in ('common_random_base_mask','method_absent_from_base_mask_seed','burden_preserving_swaps','exact_mask_cardinality_assertion','target_always_masked'):
    if mask.get(k) is not True:
        errors.append(f'MASK_REQUIREMENT_MISSING:{k}')
if x.get('primary_attacker',{}).get('role') != 'EXPRESSION_PROXY_SHORTCUT_DIAGNOSTIC_ONLY':
    errors.append('PRIMARY_ATTACKER_ROLE_MUST_BE_DIAGNOSTIC_ONLY')
if x.get('secondary_attacker',{}).get('role') != 'EXPRESSION_PROXY_ROBUSTNESS_CHALLENGE_NOT_SELECTION_TUNER_OR_TRAINING_OBJECTIVE':
    errors.append('SECONDARY_ATTACKER_ROLE_MUST_BE_DIAGNOSTIC_ONLY')
if x.get('paired_estimand',{}).get('unit') != 'TARGET_X_OUTER_FOLD':
    errors.append('PAIRED_UNIT_MUST_BE_TARGET_X_OUTER_FOLD')
if x.get('paired_estimand',{}).get('aggregate_unit') != 'TARGET':
    errors.append('AGGREGATE_UNIT_MUST_BE_TARGET')
if x.get('controls',{}).get('planted_shortcut_positive') != 'REQUIRED':
    errors.append('POSITIVE_CONTROL_REQUIRED')
if x.get('controls',{}).get('within_donor_shuffled_negative') != 'REQUIRED':
    errors.append('NEGATIVE_CONTROL_REQUIRED')
print('PASS' if not errors else '\n'.join(errors))
raise SystemExit(0 if not errors else 1)
