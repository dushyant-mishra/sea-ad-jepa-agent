import hashlib
from pathlib import Path
import pytest
from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS, CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_authority_closure_v1 import validate_current_v5_authority_closure_v1

def h(name): return hashlib.sha256(name.encode()).hexdigest()
class Stub:
    def __init__(self,name,**attrs): self._d=h(name); self.__dict__.update(attrs); self.training_authorized=False
    def validate(self): return None
    def canonical_digest(self): return self._d

def fixtures():
    full=h('full'); schedule=h('schedule'); runtime=h('runtime'); firewall=h('firewall')
    rep=Stub('rep',substrate_authority_sha256=full,support_authority_sha256=h('measurement-support'))
    support=Stub('support',full104_substrate_sha256=full,measurement_support_authority_sha256=h('measurement-support'))
    est=Stub('est',support_estimability_authority_sha256=support.canonical_digest())
    address=Stub('address')
    masking=Stub('masking')
    ema=Stub('ema',base_training_estimand_sha256=est.canonical_digest(),schedule_authority_sha256=schedule)
    teacher=Stub('teacher',representation_authority_sha256=rep.canonical_digest(),support_estimability_authority_sha256=support.canonical_digest(),target_address_query_authority_sha256=address.canonical_digest(),scientific_weight_authority_sha256=est.canonical_digest(),masking_authority_sha256=masking.canonical_digest(),ema_boundary_authority_sha256=ema.canonical_digest())
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
    return validate_current_v5_authority_closure_v1(full104_substrate_sha256=f['full'],representation=f['rep'],support_estimability=f['support'],base_training_estimand=f['est'],target_address=f['address'],masking=f['masking'],ema=f['ema'],teacher_target=f['teacher'],measurement_robustness=f['measurement'],target_identity_gate=f['identity'],critical_test=f['critical'],anti_cheat=f['anticheat'],model_geometry=f['geometry'],protected_registry=f['registry'],preexecution=f['pre'],observation_gradient_firewall_authority_sha256=f['firewall'],schedule_authority_sha256=f['schedule'],runtime_source_sha256=f['runtime'])
def test_valid_closure_produces_exact_receipt_root_vocab():
    f=fixtures(); out=call(f)
    assert tuple(out['authority_roots']) == CURRENT_V5_UPSTREAM_AUTHORITY_ROOTS
    assert tuple(out['receipt_authority_roots']) == CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
    assert out['receipt_authority_roots']['preexecution_authority_sha256']==f['pre'].canonical_digest()
    assert out['training_authorized'] is False
def test_teacher_mask_splice_rejected():
    f=fixtures(); f['teacher'].masking_authority_sha256=h('other')
    with pytest.raises(ValueError,match='teacher.*masking'): call(f)
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
    f=fixtures(); f['est'].support_estimability_authority_sha256=h('other')
    with pytest.raises(ValueError,match='estimand.*support'): call(f)
