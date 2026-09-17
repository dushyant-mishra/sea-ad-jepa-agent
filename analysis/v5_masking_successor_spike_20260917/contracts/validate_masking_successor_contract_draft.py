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
    if mask.get(k) is not True: errors.append(f'MASK_REQUIREMENT_MISSING:{k}')
if x.get('paired_estimand',{}).get('unit') != 'TARGET_X_OUTER_FOLD':
    errors.append('PAIRED_UNIT_MUST_BE_TARGET_X_OUTER_FOLD')
if x.get('paired_estimand',{}).get('aggregate_unit') != 'TARGET':
    errors.append('AGGREGATE_UNIT_MUST_BE_TARGET')
if x.get('controls',{}).get('planted_shortcut_positive') != 'REQUIRED': errors.append('POSITIVE_CONTROL_REQUIRED')
if x.get('controls',{}).get('within_donor_shuffled_negative') != 'REQUIRED': errors.append('NEGATIVE_CONTROL_REQUIRED')
print('PASS' if not errors else '\n'.join(errors))
raise SystemExit(0 if not errors else 1)
