import copy
from pathlib import Path
import pytest
from sea_ad_jepa.v5.anti_cheat_authority_bundle_v1 import AntiCheatAuthorityBundleV1
from sea_ad_jepa.v5.production_protected_registry_authority_v1 import ProductionProtectedRegistryAuthorityV1, PROTECTED_ROLES, PROTECTED_PARAMETERS
from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_atomic_checkpoint_guard_v1 import seal_current_atomic_checkpoint_v1, validate_current_atomic_checkpoint_v1

def bundle(): return AntiCheatAuthorityBundleV1('a','1'*64,'2'*64,'3'*64,'4'*64,'5'*64)
def records(depth): return [{'block_index':b,'role':r,'parameter':p,'tensor_name':f'b{b}.{r}.{p}'} for b in range(depth) for r in PROTECTED_ROLES for p in PROTECTED_PARAMETERS]
def registry(): return ProductionProtectedRegistryAuthorityV1('r',2,records(2))
def roots(): return {name: format(i,'x')[-1]*64 for i,name in enumerate(CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS,1)}
def checkpoint():
    return seal_current_atomic_checkpoint_v1(authority_roots=roots(),preexecution_authority_sha256='d'*64,protected_registry=registry(),critical_test_authority_sha256='e'*64,telemetry_section_sha256_by_name={'optimizer':'a'*64,'ema':'b'*64},forbidden_gate_states={'d_shared_open':False,'protected_outcome_open':False})

def test_anticheat_bundle_binds_independent_roots():
    authority=bundle(); authority.validate()
    assert len(authority.canonical_digest())==64 and authority.training_authorized is False
    assert not hasattr(authority,'anti_cheat_passed')

def test_bad_anticheat_root_fails_closed():
    values=bundle().__dict__.copy(); values['masking_authority_sha256']='bad'
    with pytest.raises(ValueError): AntiCheatAuthorityBundleV1(**values).validate()

def test_checkpoint_valid_and_dynamic_count():
    sealed=checkpoint(); verified=validate_current_atomic_checkpoint_v1(sealed,expected_authority_roots=roots(),expected_preexecution_authority_sha256='d'*64,protected_registry=registry(),expected_critical_test_authority_sha256='e'*64,required_telemetry_sections=('optimizer','ema'),forbidden_gate_names=('d_shared_open','protected_outcome_open'))
    assert verified['protected_tensor_count']==16 and len(verified['checkpoint_digest'])==64

def test_checkpoint_rejects_splice_count_or_open_gate():
    sealed=checkpoint(); bad=copy.deepcopy(sealed); bad['protected_tensor_count']=48
    with pytest.raises(ValueError,match='protected_tensor_count'): validate_current_atomic_checkpoint_v1(bad,expected_authority_roots=roots(),expected_preexecution_authority_sha256='d'*64,protected_registry=registry(),expected_critical_test_authority_sha256='e'*64,required_telemetry_sections=('optimizer','ema'),forbidden_gate_names=('d_shared_open','protected_outcome_open'))
    bad=copy.deepcopy(sealed); bad['authority_roots']['masking_authority_sha256']='f'*64
    with pytest.raises(ValueError,match='authority_roots'): validate_current_atomic_checkpoint_v1(bad,expected_authority_roots=roots(),expected_preexecution_authority_sha256='d'*64,protected_registry=registry(),expected_critical_test_authority_sha256='e'*64,required_telemetry_sections=('optimizer','ema'),forbidden_gate_names=('d_shared_open','protected_outcome_open'))
    bad=copy.deepcopy(sealed); bad['forbidden_gate_states']['d_shared_open']=True
    with pytest.raises(ValueError,match='forbidden gate'): validate_current_atomic_checkpoint_v1(bad,expected_authority_roots=roots(),expected_preexecution_authority_sha256='d'*64,protected_registry=registry(),expected_critical_test_authority_sha256='e'*64,required_telemetry_sections=('optimizer','ema'),forbidden_gate_names=('d_shared_open','protected_outcome_open'))

def test_checkpoint_source_has_neutral_vocabulary():
    source=Path('src/sea_ad_jepa/v5/current_atomic_checkpoint_guard_v1.py').read_text(encoding='utf-8')
    forbidden=('z_bio','biology','PROTECTED_48','HISTORICAL_128X8','trainer_preexecution_contract_v2')
    assert [token for token in forbidden if token in source] == []
