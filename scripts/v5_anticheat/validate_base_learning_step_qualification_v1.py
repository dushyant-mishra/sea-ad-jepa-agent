#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any, Mapping

SCHEMA = 'JEPA_V5_BASE_LEARNING_STEP_QUALIFICATION_RECEIPT_V1'
PASS_TERMINAL = 'PASS_BASE_LEARNING_STEP_QUALIFICATION__NO_TRAINING_AUTHORITY'
STOP_NOT_ESTABLISHED = 'STOP_BASE_LEARNING_STEP_NOT_ESTABLISHED__DOWNSTREAM_SCIENTIFIC_INTERPRETATION_BLOCKED'
FULL104_TERMINAL = 'PASS_FULL104_4553407_EXPRESSION_BLOCK_AND_IDENTITY_CLOSURE'
REQUIRED_COMPARATOR_CLASSES = {
    'NO_LEARNED_SIGNAL_OR_LIMITING_OBJECT',
    'TECHNICAL_ONLY_OR_IDENTITY_ONLY',
    'RANDOMIZED_OR_MATCHED_NULL',
}
HEX64 = re.compile(r'^[0-9a-f]{64}$')


def _fail(reason: str) -> dict[str, Any]:
    return {
        'terminal': STOP_NOT_ESTABLISHED,
        'learning_step_qualified': False,
        'reason': reason,
        'td60_authorized': False,
        'relational_target_activation_authorized': False,
        'training_authorized': False,
    }


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and HEX64.fullmatch(value) is not None


def classify_learning_step_authority(receipt: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a prospective V5 learning-step receipt.

    This validates evidence binding and ordering semantics only. It does not
    compute the learning metrics and cannot grant training or protected-data
    access.
    """
    if not isinstance(receipt, Mapping):
        return _fail('receipt_not_mapping')
    if receipt.get('schema') != SCHEMA:
        return _fail('schema_mismatch')
    if receipt.get('full104_binding_terminal') != FULL104_TERMINAL:
        return _fail('full104_binding_not_closed')

    access = receipt.get('access', {})
    if not isinstance(access, Mapping):
        return _fail('access_block_missing')
    if any(bool(access.get(k, False)) for k in ('protected_partition_used', 'pathology_used', 'confirmation_endpoint_used')):
        return _fail('forbidden_protected_or_endpoint_access')
    if bool(access.get('training_authorized', False)):
        return _fail('receipt_must_not_claim_training_authority')

    run_authority = receipt.get('qualification_run_authority', {})
    if not isinstance(run_authority, Mapping):
        return _fail('qualification_run_authority_missing')
    if run_authority.get('scope') != 'BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY':
        return _fail('qualification_run_scope_not_bounded')
    if not bool(run_authority.get('explicitly_authorized', False)):
        return _fail('qualification_run_not_explicitly_authorized')
    if not _is_sha256(run_authority.get('authority_sha256')):
        return _fail('qualification_run_authority_digest_missing')
    if bool(run_authority.get('production_training_authorized', False)):
        return _fail('qualification_run_cannot_claim_production_training_authority')

    analysis = receipt.get('analysis_level', {})
    if not isinstance(analysis, Mapping):
        return _fail('analysis_level_missing')
    if not str(analysis.get('representation_observation_unit', '')).strip():
        return _fail('representation_observation_unit_missing')
    if not str(analysis.get('statistical_generalization_unit', '')).strip():
        return _fail('statistical_generalization_unit_missing')
    if bool(analysis.get('aggregation_sets_effective_n', False)) and not str(analysis.get('aggregation_justification', '')).strip():
        return _fail('aggregation_sets_effective_n_without_estimand_justification')

    comparators = receipt.get('comparators', {})
    if not isinstance(comparators, Mapping):
        return _fail('comparators_missing')
    classes = set(comparators.get('classes', [])) if isinstance(comparators.get('classes', []), list) else set()
    missing = REQUIRED_COMPARATOR_CLASSES - classes
    if missing:
        return _fail('missing_comparator_classes:' + ','.join(sorted(missing)))
    if not bool(comparators.get('full_curve_published', False)):
        return _fail('winner_only_without_full_curve')
    if not bool(comparators.get('limiting_object_published', False)):
        return _fail('limiting_or_null_comparator_not_published')

    boundary = receipt.get('boundary_diagnostic', {})
    if not isinstance(boundary, Mapping):
        return _fail('boundary_diagnostic_missing')
    if bool(boundary.get('selected_on_boundary', False)):
        if not bool(boundary.get('limiting_object_diagnosed', False)):
            return _fail('boundary_selected_without_limiting_object_diagnosis')
        if bool(boundary.get('grid_expanded_before_diagnosis', False)):
            return _fail('grid_expanded_before_boundary_diagnosis')

    capacity = receipt.get('effective_capacity', {})
    if not isinstance(capacity, Mapping) or not str(capacity.get('diagnostic_name', '')).strip():
        return _fail('effective_capacity_diagnostic_missing')
    if capacity.get('threshold_authority') != 'PRODUCTION_DERIVED_OR_MODEL_DEFINED':
        return _fail('effective_capacity_threshold_not_production_derived')
    if bool(capacity.get('imports_t0_numeric_threshold', False)):
        return _fail('t0_numeric_threshold_import_forbidden')

    geometry = receipt.get('geometry', {})
    if not isinstance(geometry, Mapping):
        return _fail('geometry_missing')
    expected = {'cells': 4553407, 'donors': 104, 'operators': 42, 'addresses': 41238}
    if any(int(geometry.get(k, -1)) != v for k, v in expected.items()):
        return _fail('full104_geometry_mismatch')
    if not bool(geometry.get('ragged_native_support_preserved', False)):
        return _fail('ragged_native_support_not_preserved')
    if not bool(geometry.get('production_matched_simulation_or_adversarial_geometry', False)):
        return _fail('toy_or_mismatched_simulation_geometry')
    if bool(geometry.get('toy_geometry_is_production_authority', False)):
        return _fail('toy_geometry_cannot_be_production_authority')

    evidence = receipt.get('evidence_sha256', {})
    if not isinstance(evidence, Mapping):
        return _fail('evidence_digests_missing')
    required_digests = ('full_curve', 'comparators', 'capacity', 'geometry', 'negative_controls')
    bad = [k for k in required_digests if not _is_sha256(evidence.get(k))]
    if bad:
        return _fail('missing_or_invalid_evidence_sha256:' + ','.join(bad))

    interpretation = receipt.get('interpretation', {})
    if not isinstance(interpretation, Mapping):
        return _fail('interpretation_block_missing')
    if interpretation.get('failure_semantics') != 'LEARNING_DESIGN_NOT_ESTABLISHED__NOT_BIOLOGY_ABSENT':
        return _fail('failure_semantics_must_not_claim_biological_null')
    if interpretation.get('t0_role') != 'METHODOLOGICAL_EVIDENCE_ONLY__NOT_BIOLOGICAL_TARGET':
        return _fail('t0_lane_separation_missing')

    if receipt.get('terminal') != PASS_TERMINAL:
        return _fail('pass_terminal_missing')

    return {
        'terminal': PASS_TERMINAL,
        'learning_step_qualified': True,
        'reason': 'all_prospective_learning_step_requirements_bound',
        'td60_authorized': False,
        'relational_target_activation_authorized': False,
        'training_authorized': False,
        'next_required_stage': 'LAWFUL_EXPOSURE_DEFINED_BASE_EMA_TEACHER_THEN_TD60',
    }


def main(argv=None) -> int:
    p = argparse.ArgumentParser()
    p.add_argument('--receipt', type=Path, required=True)
    p.add_argument('--out-json', type=Path, required=True)
    a = p.parse_args(argv)
    receipt = json.loads(a.receipt.read_text())
    out = classify_learning_step_authority(receipt)
    a.out_json.parent.mkdir(parents=True, exist_ok=True)
    a.out_json.write_text(json.dumps(out, indent=2, sort_keys=True) + '\n')
    print(json.dumps(out, indent=2, sort_keys=True))
    return 0 if out['learning_step_qualified'] else 3


if __name__ == '__main__':
    raise SystemExit(main())
