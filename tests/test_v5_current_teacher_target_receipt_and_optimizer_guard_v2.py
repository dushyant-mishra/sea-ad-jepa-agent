import copy
from pathlib import Path
import pytest
from sea_ad_jepa.v5.current_authority_roots_v1 import CURRENT_V5_RECEIPT_AUTHORITY_ROOTS
from sea_ad_jepa.v5.current_teacher_target_receipt_v1 import seal_current_teacher_target_receipt_v1, validate_current_teacher_target_receipt_v1
from sea_ad_jepa.v5.qualified_optimizer_guard_v2 import install_current_optimizer_guard
from sea_ad_jepa.v5.current_training_authority_v1 import STOP_STALE_TRAINING_CHAIN

def roots(): return {name: format(i,'x')[-1]*64 for i,name in enumerate(CURRENT_V5_RECEIPT_AUTHORITY_ROOTS,1)}
def receipt(): return seal_current_teacher_target_receipt_v1('f'*64, roots())

class Handle:
    def __init__(self, coll, fn): self.coll=coll; self.fn=fn
    def remove(self): self.coll.remove(self.fn)
class FakeOptimizer:
    def __init__(self): self.pre=[]; self.post=[]; self.mutations=0
    def register_step_pre_hook(self, fn): self.pre.append(fn); return Handle(self.pre,fn)
    def register_step_post_hook(self, fn): self.post.append(fn); return Handle(self.post,fn)
    def step(self,*args,**kwargs):
        for fn in list(self.pre):
            out=fn(self,args,kwargs)
            if out is not None: args,kwargs=out
        self.mutations += 1
        for fn in list(self.post): fn(self,args,kwargs)

def test_receipt_exact_root_set_and_tamper_detection():
    sealed=receipt(); verified=validate_current_teacher_target_receipt_v1(sealed,expected_target_package_root='f'*64,expected_authority_roots=roots())
    assert verified['training_authorized'] is False and len(verified['receipt_digest'])==64
    bad=copy.deepcopy(sealed); bad['authority_roots'].pop('masking_authority_sha256')
    with pytest.raises(ValueError): validate_current_teacher_target_receipt_v1(bad,expected_target_package_root='f'*64,expected_authority_roots=roots())
    bad=copy.deepcopy(sealed); bad['target_package_root']='e'*64
    with pytest.raises(ValueError): validate_current_teacher_target_receipt_v1(bad,expected_target_package_root='f'*64,expected_authority_roots=roots())

def test_receipt_rejects_wrong_kind_and_extra_root():
    bad=copy.deepcopy(receipt()); bad['kind']='old_receipt'
    with pytest.raises(ValueError,match='kind'): validate_current_teacher_target_receipt_v1(bad,expected_target_package_root='f'*64,expected_authority_roots=roots())
    extra=roots(); extra['extra']='a'*64
    with pytest.raises(ValueError): seal_current_teacher_target_receipt_v1('f'*64,extra)

def test_optimizer_guard_v2_is_hard_stopped_as_superseded():
    opt = FakeOptimizer()
    with pytest.raises(RuntimeError, match=STOP_STALE_TRAINING_CHAIN):
        install_current_optimizer_guard(
            opt,
            receipt(),
            expected_target_package_root='f'*64,
            expected_authority_roots=roots(),
        )
    assert opt.mutations == 0
    assert opt.pre == []
    assert opt.post == []


def test_sources_do_not_import_old_receipt_or_old_geometry():
    for path in ('current_teacher_target_receipt_v1.py','qualified_optimizer_guard_v2.py'):
        source=Path('src/sea_ad_jepa/v5/'+path).read_text(encoding='utf-8')
        forbidden=('qualified_teacher_target_receipt_v1','validate_qualified_teacher_target_receipt','PROTECTED_48','HISTORICAL_128X8','46_donor','V21')
        assert [token for token in forbidden if token in source] == []
