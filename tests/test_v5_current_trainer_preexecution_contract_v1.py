import dataclasses
from pathlib import Path
import pytest
from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS, CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_trainer_preexecution_contract_v1 import CurrentTrainerPreexecutionAuthorityV1

def roots():
    return {name: str(i%10)*64 for i,name in enumerate(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS,1)}
def make_authority():
    return CurrentTrainerPreexecutionAuthorityV1(roots(),'a'*64,'b'*64,False,False)

def test_root_vocab_exact_and_receipt_adds_preexecution():
    assert CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS == (
        'full104_substrate_sha256','representation_authority_sha256','base_training_estimand_sha256',
        'teacher_target_semantics_sha256','target_address_query_authority_sha256','masking_authority_sha256',
        'model_geometry_authority_sha256','schedule_authority_sha256','ema_authority_sha256',
        'anti_cheat_authority_sha256','runtime_source_sha256')
    assert CURRENT_V5_RECEIPT_AUTHORITY_ROOTS[:-2] == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS[:-1]
    assert CURRENT_V5_RECEIPT_AUTHORITY_ROOTS[-2:] == ('preexecution_authority_sha256','runtime_source_sha256')

def test_preexecution_validates_exact_closure_training_off():
    authority=make_authority(); authority.validate()
    assert len(authority.canonical_digest())==64
    assert authority.training_authorized is False

def test_missing_extra_or_phase_open_fails_closed():
    values=roots(); values.pop('masking_authority_sha256')
    with pytest.raises(ValueError,match='exactly'): dataclasses.replace(make_authority(),authority_roots=values).validate()
    values=roots(); values['legacy']='c'*64
    with pytest.raises(ValueError,match='exactly'): dataclasses.replace(make_authority(),authority_roots=values).validate()
    with pytest.raises(ValueError,match='relational'): dataclasses.replace(make_authority(),relational_training_active=True).validate()
    with pytest.raises(ValueError,match='optimizer'): dataclasses.replace(make_authority(),optimizer_started=True).validate()

def test_preexecution_has_no_duplicated_numeric_policy_or_legacy_delegation():
    source=Path('src/sea_ad_jepa/v5/current_trainer_preexecution_contract_v1.py').read_text(encoding='utf-8')
    forbidden=('presentation_horizon','masked_views_per_base_cell','half_life_presentations','TrainerPreexecutionAuthorityV2','trainer_preexecution_contract_v2','PROTECTED_48','HISTORICAL_128X8')
    assert [token for token in forbidden if token in source] == []
