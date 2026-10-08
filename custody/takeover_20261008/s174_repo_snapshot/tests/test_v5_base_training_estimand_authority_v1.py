import dataclasses
from pathlib import Path
import pytest
from sea_ad_jepa.v5.base_training_estimand_authority_v1 import BaseTrainingEstimandAuthorityV1

def make_authority() -> BaseTrainingEstimandAuthorityV1:
    return BaseTrainingEstimandAuthorityV1(
        authority_id='prospective-base-estimand-candidate',
        population_authority_sha256='1'*64,
        support_estimability_authority_sha256='2'*64,
        support_eligibility_authority_sha256='3'*64,
        estimand_id='EXPLICIT_CALLER_SELECTED_BASE_ESTIMAND',
        scientific_weight_artifact_sha256='4'*64,
        scientific_weight_schema_id='EXPLICIT_CELL_WEIGHT_SCHEMA',
        weight_normalization_id='EXPLICIT_NORMALIZATION_RULE',
        weight_unit_id='SCIENTIFIC_CELL_MASS',
    )

def test_base_estimand_authority_is_separate_from_proposal_packing_and_dimension():
    fields={field.name for field in dataclasses.fields(BaseTrainingEstimandAuthorityV1)}
    assert not any('proposal' in name for name in fields)
    assert not any('packing' in name for name in fields)
    assert not any('dimension' in name for name in fields)

def test_base_estimand_binds_support_semantics_and_external_weight_root_without_training_authority():
    authority=make_authority(); authority.validate()
    assert authority.support_estimability_authority_sha256 == '2'*64
    assert authority.training_authorized is False
    assert len(authority.canonical_digest()) == 64

def test_bad_support_or_weight_root_fails_closed():
    with pytest.raises(ValueError,match='support_estimability_authority_sha256'):
        dataclasses.replace(make_authority(),support_estimability_authority_sha256='bad').validate()
    with pytest.raises(ValueError,match='scientific_weight_artifact_sha256'):
        dataclasses.replace(make_authority(),scientific_weight_artifact_sha256='bad').validate()

def test_source_does_not_import_dimension_estimand_or_pick_candidate_estimand():
    source=Path('src/sea_ad_jepa/v5/base_training_estimand_authority_v1.py').read_text(encoding='utf-8')
    forbidden=('EQUAL_DONOR__EQUAL_CELL_WITHIN_DONOR','EMPIRICAL_FULL104','SOURCE_UNIFORM','DONOR_PRIMARY_OPERATOR_BALANCED','full104_dimension_interface')
    assert [token for token in forbidden if token in source] == []
