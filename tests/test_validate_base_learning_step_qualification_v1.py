import importlib.util
from pathlib import Path

P = Path(__file__).resolve().parents[1] / 'scripts' / 'v5_anticheat' / 'validate_base_learning_step_qualification_v1.py'
spec = importlib.util.spec_from_file_location('learning_step_gate', P)
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

H = 'a' * 64


def valid_receipt():
    return {
        'schema': m.SCHEMA,
        'terminal': m.PASS_TERMINAL,
        'full104_binding_terminal': m.FULL104_TERMINAL,
        'access': {
            'protected_partition_used': False,
            'pathology_used': False,
            'confirmation_endpoint_used': False,
            'training_authorized': False,
        },
        'qualification_run_authority': {
            'scope': 'BOUNDED_READER_FIT_LEARNING_STEP_QUALIFICATION_ONLY',
            'explicitly_authorized': True,
            'authority_sha256': H,
            'production_training_authorized': False,
        },
        'analysis_level': {
            'representation_observation_unit': 'CELL_WITH_NATIVE_MEASUREMENT_SUPPORT',
            'statistical_generalization_unit': 'DONOR_HELD_OUT_WHERE_BIOLOGICAL_GENERALIZATION_IS_CLAIMED',
            'aggregation_sets_effective_n': False,
            'aggregation_justification': '',
        },
        'comparators': {
            'classes': sorted(m.REQUIRED_COMPARATOR_CLASSES),
            'full_curve_published': True,
            'limiting_object_published': True,
        },
        'boundary_diagnostic': {
            'selected_on_boundary': False,
            'limiting_object_diagnosed': True,
            'grid_expanded_before_diagnosis': False,
        },
        'effective_capacity': {
            'diagnostic_name': 'MODEL_APPROPRIATE_ACTIVE_CAPACITY',
            'threshold_authority': 'PRODUCTION_DERIVED_OR_MODEL_DEFINED',
            'imports_t0_numeric_threshold': False,
        },
        'geometry': {
            'cells': 4553407,
            'donors': 104,
            'operators': 42,
            'addresses': 41238,
            'ragged_native_support_preserved': True,
            'production_matched_simulation_or_adversarial_geometry': True,
            'toy_geometry_is_production_authority': False,
        },
        'evidence_sha256': {k: H for k in ('full_curve', 'comparators', 'capacity', 'geometry', 'negative_controls')},
        'interpretation': {
            'failure_semantics': 'LEARNING_DESIGN_NOT_ESTABLISHED__NOT_BIOLOGY_ABSENT',
            't0_role': 'METHODOLOGICAL_EVIDENCE_ONLY__NOT_BIOLOGICAL_TARGET',
        },
    }


def test_valid_receipt_passes_without_granting_downstream_authority():
    out = m.classify_learning_step_authority(valid_receipt())
    assert out['terminal'] == m.PASS_TERMINAL
    assert out['learning_step_qualified'] is True
    assert out['td60_authorized'] is False
    assert out['relational_target_activation_authorized'] is False
    assert out['training_authorized'] is False


def test_missing_full104_binding_fails_closed():
    r = valid_receipt(); r['full104_binding_terminal'] = 'PASS_SOMETHING_ELSE'
    assert m.classify_learning_step_authority(r)['reason'] == 'full104_binding_not_closed'


def test_winner_only_curve_is_rejected():
    r = valid_receipt(); r['comparators']['full_curve_published'] = False
    assert m.classify_learning_step_authority(r)['reason'] == 'winner_only_without_full_curve'


def test_missing_limiting_comparator_is_rejected():
    r = valid_receipt(); r['comparators']['limiting_object_published'] = False
    assert m.classify_learning_step_authority(r)['reason'] == 'limiting_or_null_comparator_not_published'


def test_boundary_requires_diagnosis_before_expansion():
    r = valid_receipt(); r['boundary_diagnostic'].update(selected_on_boundary=True, limiting_object_diagnosed=False)
    assert m.classify_learning_step_authority(r)['reason'] == 'boundary_selected_without_limiting_object_diagnosis'
    r = valid_receipt(); r['boundary_diagnostic'].update(selected_on_boundary=True, grid_expanded_before_diagnosis=True)
    assert m.classify_learning_step_authority(r)['reason'] == 'grid_expanded_before_boundary_diagnosis'


def test_t0_numeric_capacity_threshold_cannot_be_imported():
    r = valid_receipt(); r['effective_capacity']['imports_t0_numeric_threshold'] = True
    assert m.classify_learning_step_authority(r)['reason'] == 't0_numeric_threshold_import_forbidden'


def test_toy_geometry_cannot_claim_production_authority():
    r = valid_receipt(); r['geometry']['production_matched_simulation_or_adversarial_geometry'] = False
    assert m.classify_learning_step_authority(r)['reason'] == 'toy_or_mismatched_simulation_geometry'


def test_aggregation_that_sets_effective_n_requires_estimand_justification():
    r = valid_receipt(); r['analysis_level']['aggregation_sets_effective_n'] = True
    assert m.classify_learning_step_authority(r)['reason'] == 'aggregation_sets_effective_n_without_estimand_justification'


def test_protected_endpoint_access_is_rejected():
    r = valid_receipt(); r['access']['pathology_used'] = True
    assert m.classify_learning_step_authority(r)['reason'] == 'forbidden_protected_or_endpoint_access'


def test_failure_semantics_cannot_claim_biology_absent():
    r = valid_receipt(); r['interpretation']['failure_semantics'] = 'BIOLOGY_ABSENT'
    assert m.classify_learning_step_authority(r)['reason'] == 'failure_semantics_must_not_claim_biological_null'


def test_missing_evidence_digest_is_rejected():
    r = valid_receipt(); del r['evidence_sha256']['negative_controls']
    out = m.classify_learning_step_authority(r)
    assert out['reason'] == 'missing_or_invalid_evidence_sha256:negative_controls'


def test_unapproved_learning_run_cannot_generate_authority():
    r = valid_receipt(); r['qualification_run_authority']['explicitly_authorized'] = False
    assert m.classify_learning_step_authority(r)['reason'] == 'qualification_run_not_explicitly_authorized'


def test_bounded_qualification_run_cannot_claim_production_training_authority():
    r = valid_receipt(); r['qualification_run_authority']['production_training_authorized'] = True
    assert m.classify_learning_step_authority(r)['reason'] == 'qualification_run_cannot_claim_production_training_authority'
