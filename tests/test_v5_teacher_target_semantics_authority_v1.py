import dataclasses, inspect
from pathlib import Path
import pytest
from sea_ad_jepa.v5.teacher_target_semantics_authority_v1 import TeacherTargetSemanticsAuthorityV1

def make_authority()->TeacherTargetSemanticsAuthorityV1:
    return TeacherTargetSemanticsAuthorityV1(
        authority_id='prospective-teacher-target-semantics',
        representation_authority_sha256='1'*64,
        support_estimability_authority_sha256='2'*64,
        teacher_input_support_authority_sha256='3'*64,
        teacher_state_location_id='EXPLICIT_STATE_LOCATION',
        target_aggregation_id='EXPLICIT_AGGREGATION',
        target_normalization_id='EXPLICIT_NORMALIZATION',
        target_address_query_authority_sha256='4'*64,
        student_visible_support_authority_sha256='5'*64,
        scientific_weight_authority_sha256='6'*64,
        masking_authority_sha256='7'*64,
        gradient_boundary_authority_id='EXPLICIT_GRADIENT_BOUNDARY',
        ema_boundary_authority_sha256='8'*64,
    )

def test_all_semantic_choices_are_explicit():
    for name,param in inspect.signature(TeacherTargetSemanticsAuthorityV1).parameters.items():
        if name != 'training_authorized': assert param.default is inspect._empty

def test_semantics_authority_binds_support_semantics_and_is_training_off():
    authority=make_authority(); authority.validate()
    assert authority.support_estimability_authority_sha256 == '2'*64
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64

def test_bad_support_or_masking_dependency_fails_closed():
    with pytest.raises(ValueError,match='support_estimability_authority_sha256'):
        dataclasses.replace(make_authority(),support_estimability_authority_sha256='bad').validate()
    with pytest.raises(ValueError,match='masking_authority_sha256'):
        dataclasses.replace(make_authority(),masking_authority_sha256='bad').validate()

def test_source_does_not_select_inherited_v4_target_semantics():
    source=Path('src/sea_ad_jepa/v5/teacher_target_semantics_authority_v1.py').read_text(encoding='utf-8')
    forbidden=('LN(mean','final_layer','block_mean','target_blocks = 16','target_blocks: int = 16','0.40','PRODUCTION_CONFIG','z_bio')
    assert [token for token in forbidden if token in source] == []
