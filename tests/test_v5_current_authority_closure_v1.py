import hashlib
from dataclasses import replace
from pathlib import Path
import pytest
from sea_ad_jepa.v5.base_training_estimand_recovery_v1 import (
    EXPECTED_FULL_READER_REPLAY_SHA256,
    EXPECTED_OPERATOR_MASS_POLICY_ID,
    EXPECTED_POPULATION_AUTHORITY_SHA256,
    EXPECTED_PROPOSAL_SEPARATION_POLICY_ID,
    EXPECTED_SOURCE_MASS_POLICY_ID,
    EXPECTED_SUPPORT_ELIGIBILITY_SHA256,
    EXPECTED_SUPPORT_ESTIMABILITY_SHA256,
    EXPECTED_TARGET_AUTHORITY_SHA256,
    EXPECTED_TARGET_PROBABILITY_FORMULA,
    EXPECTED_WEIGHT_NORMALIZATION_ID,
    EXPECTED_WEIGHT_UNIT_ID,
    EXPECTED_ESTIMAND_ID,
    RecoveredScientificWeightLawV1,
    build_current_recovered_base_estimand_v1,
)
from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS, CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_authority_closure_v1 import validate_current_v5_authority_closure_v1
from sea_ad_jepa.v5.current_masking_policy_authority_v2 import CurrentMaskingPolicyAuthorityV2
from sea_ad_jepa.v5.current_target_address_provider_authority_v1 import (
    CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
    CurrentTargetAddressProviderAuthorityV1,
)
from sea_ad_jepa.v5.remaining_rna_necessity_v1 import RemainingRnaNecessityAuthorityV1
from sea_ad_jepa.v5.teacher_target_semantics_authority_v2 import TeacherTargetSemanticsAuthorityV2


def h(name): return hashlib.sha256(name.encode()).hexdigest()
class Stub:
    def __init__(self,name,digest=None,**attrs): self._d=digest or h(name); self.__dict__.update(attrs); self.training_authorized=False
    def validate(self): return None
    def canonical_digest(self): return self._d


def recovered_weight_law():
    return RecoveredScientificWeightLawV1(
        authority_id='JEPA_V5_RECOVERED_BASE_TRAINING_SCIENTIFIC_WEIGHT_LAW_V1',
        source_scientific_target_authority_sha256=EXPECTED_TARGET_AUTHORITY_SHA256,
        source_full_reader_replay_sha256=EXPECTED_FULL_READER_REPLAY_SHA256,
        population_authority_sha256=EXPECTED_POPULATION_AUTHORITY_SHA256,
        support_estimability_authority_sha256=EXPECTED_SUPPORT_ESTIMABILITY_SHA256,
        support_eligibility_authority_sha256=EXPECTED_SUPPORT_ELIGIBILITY_SHA256,
        estimand_id=EXPECTED_ESTIMAND_ID,
        target_probability_formula=EXPECTED_TARGET_PROBABILITY_FORMULA,
        weight_normalization_id=EXPECTED_WEIGHT_NORMALIZATION_ID,
        weight_unit_id=EXPECTED_WEIGHT_UNIT_ID,
        source_mass_policy_id=EXPECTED_SOURCE_MASS_POLICY_ID,
        operator_mass_policy_id=EXPECTED_OPERATOR_MASS_POLICY_ID,
        proposal_separation_policy_id=EXPECTED_PROPOSAL_SEPARATION_POLICY_ID,
    )


def fixtures():
    full='66f589e56badb1487058f2c95940c3e4b37196e3ab5e9c6ea1ffbe7098d2ea29'; schedule=h('schedule'); runtime=h('runtime'); firewall=h('firewall')
    rep=Stub('rep',substrate_authority_sha256=full,support_authority_sha256=EXPECTED_SUPPORT_ELIGIBILITY_SHA256)
    support=Stub('support',digest=EXPECTED_SUPPORT_ESTIMABILITY_SHA256,full104_substrate_sha256=full,measurement_support_authority_sha256=EXPECTED_SUPPORT_ELIGIBILITY_SHA256)
    weight_law=recovered_weight_law()
    est=build_current_recovered_base_estimand_v1(weight_law)
    address=CurrentTargetAddressProviderAuthorityV1(
        authority_id='JEPA_V5_CURRENT_TARGET_ADDRESS_PROVIDER_AUTHORITY_V1',
        address_registry_authority_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
        query_provider_id='V5_SHARED_ADDRESS_QUERY_PROVIDER_V1',
        query_artifact_sha256=h('query-artifact'),
        replay_policy_id='FULL_PROVIDER_STATE_DETERMINISTIC_REPLAY_V1',
        parameter_sharing_policy_id='SHARED_TRAINABLE_ADDRESS_QUERY_MECHANISM_V1',
        gradient_policy_id='CONTEXT_EVIDENCE_TO_PREDICTION_GRADIENT_REACHABLE_V1',
    )
    masking=CurrentMaskingPolicyAuthorityV2(
        authority_id='JEPA_V5_CURRENT_MASKING_POLICY_AUTHORITY_V2',
        canonical_registry_authority_sha256=CURRENT_CANONICAL_ADDRESS_REGISTRY_AUTHORITY_SHA256,
        support_estimability_authority_sha256=support.canonical_digest(),
        shortcut_artifact_sha256=h('shortcut-authority'),
        masking_policy_id='V5_UNIFORM_RANDOM_MASK_V1',
        target_evidence_budget_authority_id='V5_TARGET_EVIDENCE_BUDGET_AUTHORITY_V1',
        target_evidence_budget_authority_sha256=h('target-evidence-budget-authority'),
        rng_replay_authority_id='V5_DETERMINISTIC_MASK_REPLAY_AUTHORITY_V1',
        eligibility_policy_id='SUPPORT_ESTIMABILITY_AUTHORITY_ELIGIBILITY_V1',
        fallback_policy_id='DETERMINISTIC_UNIFORM_FALLBACK_V1',
        rng_replay_authority_sha256=h('rng-replay-authority'),
    )
    ema=Stub('ema',base_training_estimand_sha256=est.canonical_digest(),schedule_authority_sha256=schedule)
    necessity=RemainingRnaNecessityAuthorityV1(
        authority_id='V5_REMAINING_RNA_NECESSITY_AUTHORITY_V1',
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        target_address_provider_authority_sha256=address.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        precision_authority_sha256=h('remaining-rna-precision'),
        protocol_id='KEEP_QUERY_IDENTITY_AND_LAWFUL_GLOBAL_CONTEXT_FIXED__ABLATE_REMAINING_RNA_V1',
        metric_id='QUERY_LOCAL_LATENT_STATE_COSINE_SIMILARITY_V1',
        min_median_advantage_numerator=1,
        min_median_advantage_denominator=10,
        min_win_fraction_numerator=2,
        min_win_fraction_denominator=3,
        identity_only_comparator_id='QUERY_IDENTITY_ONLY_V1',
        global_context_no_rna_comparator_id='QUERY_IDENTITY_PLUS_LAWFUL_GLOBAL_CONTEXT_NO_REMAINING_RNA_V1',
        failure_semantics_id='FAIL_CLOSED_IF_REMAINING_RNA_NOT_NECESSARY_V1',
    )
    teacher=TeacherTargetSemanticsAuthorityV2(
        authority_id='V5_TEACHER_TARGET_SEMANTICS_AUTHORITY_V2',
        representation_authority_sha256=rep.canonical_digest(),
        support_estimability_authority_sha256=support.canonical_digest(),
        teacher_input_support_authority_sha256=h('teacher-input-support'),
        target_address_query_authority_sha256=address.canonical_digest(),
        student_visible_support_authority_sha256=h('student-visible-support'),
        scientific_weight_authority_sha256=est.canonical_digest(),
        masking_authority_sha256=masking.canonical_digest(),
        ema_boundary_authority_sha256=ema.canonical_digest(),
        target_construction_authority_sha256=h('target-construction'),
        gradient_boundary_authority_sha256=h('gradient-boundary'),
        remaining_rna_necessity_authority_sha256=necessity.canonical_digest(),
        state_semantics_id='BIOLOGICAL_CELLULAR_LATENT_STATE_V1',
        query_local_semantics_id='QUERY_LOCAL_STATE_CONDITIONED_ON_CANONICAL_ADDRESS_V1',
        scalar_expression_objective_policy_id='HIDDEN_GENE_SCALAR_RECONSTRUCTION_FORBIDDEN_V1',
        route_sufficiency_policy_id='REMAINING_RNA_REQUIRED__IDENTITY_ONLY_AND_GLOBAL_ONLY_INSUFFICIENT_V1',
    )
    measurement=Stub('measurement',representation_authority_sha256=rep.canonical_digest(),teacher_target_semantics_sha256=teacher.canonical_digest())
    identity=Stub('identity',teacher_target_semantics_sha256=teacher.canonical_digest(),representation_authority_sha256=rep.canonical_digest(),base_training_estimand_sha256=est.canonical_digest(),masking_authority_sha256=masking.canonical_digest())
    critical=Stub('critical')
    anticheat=Stub('anticheat',target_identity_gate_authority_sha256=identity.canonical_digest(),masking_authority_sha256=masking.canonical_digest(),measurement_robustness_authority_sha256=measurement.canonical_digest(),observation_gradient_firewall_authority_sha256=firewall,critical_test_authority_sha256=critical.canonical_digest())
    registry=Stub('registry')
    geometry=Stub('geometry',protected_registry_authority_sha256=registry.canonical_digest())
    roots={'full104_substrate_sha256':full,'representation_authority_sha256':rep.canonical_digest(),'support_estimability_authority_sha256':support.canonical_digest(),'base_training_estimand_sha256':est.canonical_digest(),'teacher_target_semantics_sha256':teacher.canonical_digest(),'target_address_query_authority_sha256':address.canonical_digest(),'masking_authority_sha256':masking.canonical_digest(),'model_geometry_authority_sha256':geometry.canonical_digest(),'schedule_authority_sha256':schedule,'ema_authority_sha256':ema.canonical_digest(),'anti_cheat_authority_sha256':anticheat.canonical_digest(),'runtime_source_sha256':runtime}
    pre=Stub('pre',protected_registry_authority_sha256=registry.canonical_digest(),critical_test_authority_sha256=critical.canonical_digest())
    pre.normalized_roots=lambda: dict(roots)
    return locals()


def call(f):
    return validate_current_v5_authority_closure_v1(full104_substrate_sha256=f['full'],representation=f['rep'],support_estimability=f['support'],base_training_weight_law=f['weight_law'],base_training_estimand=f['est'],target_address=f['address'],masking=f['masking'],remaining_rna_necessity=f['necessity'],ema=f['ema'],teacher_target=f['teacher'],measurement_robustness=f['measurement'],target_identity_gate=f['identity'],critical_test=f['critical'],anti_cheat=f['anticheat'],model_geometry=f['geometry'],protected_registry=f['registry'],preexecution=f['pre'],observation_gradient_firewall_authority_sha256=f['firewall'],schedule_authority_sha256=f['schedule'],runtime_source_sha256=f['runtime'])


def test_valid_closure_produces_exact_receipt_root_vocab():
    f=fixtures(); out=call(f)
    assert tuple(out['authority_roots']) == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS
    assert tuple(out['receipt_authority_roots']) == CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
    assert out['receipt_authority_roots']['preexecution_authority_sha256']==f['pre'].canonical_digest()
    assert out['training_authorized'] is False


def test_teacher_mask_splice_rejected():
    f=fixtures(); f['teacher']=replace(f['teacher'],masking_authority_sha256=h('other'))
    with pytest.raises(ValueError,match='teacher.*masking'): call(f)


def test_teacher_remaining_rna_necessity_splice_rejected():
    f=fixtures(); f['teacher']=replace(f['teacher'],remaining_rna_necessity_authority_sha256=h('other'))
    with pytest.raises(ValueError,match='teacher.*remaining-RNA'): call(f)


def test_anticheat_splice_rejected():
    f=fixtures(); f['anticheat'].measurement_robustness_authority_sha256=h('other')
    with pytest.raises(ValueError,match='anti-cheat.*measurement'): call(f)


def test_preexecution_root_splice_rejected():
    f=fixtures(); bad=dict(f['roots']); bad['masking_authority_sha256']=h('other'); f['pre'].normalized_roots=lambda:bad
    with pytest.raises(ValueError,match='preexecution.*roots'): call(f)


def test_source_has_no_historical_runtime_or_training_shortcut():
    source=Path('src/sea_ad_jepa/v5/current_authority_closure_v1.py').read_text(encoding='utf-8')
    forbidden=('PRODUCTION_CONFIG','production_update','trainer_preexecution_contract_v2','PROTECTED_48','HISTORICAL_128X8','0.996','z_bio','training_authorized=True')
    assert [token for token in forbidden if token in source] == []


def test_support_splice_rejected():
    f=fixtures(); f['est']=replace(f['est'],support_estimability_authority_sha256=h('other'))
    with pytest.raises(ValueError,match='recovered current V5 authority|current recovered estimand binding mismatch|does not match recovered'): call(f)


def test_alternative_estimand_substitution_rejected_even_when_generic_schema_valid():
    f=fixtures(); f['est']=replace(f['est'],estimand_id='SOURCE_UNIFORM')
    with pytest.raises(ValueError,match='does not match recovered'): call(f)
