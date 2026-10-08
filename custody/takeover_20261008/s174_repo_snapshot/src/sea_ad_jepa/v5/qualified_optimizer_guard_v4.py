"""Optimizer guard V4: only the V4 receipt and CurrentTrainingAuthorityV2 may step."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from .current_training_authority_v2 import CurrentTrainingAuthorityV2
from .current_teacher_target_receipt_v4 import validate_current_teacher_target_receipt_v4

STOP="STOP_V5_CURRENT_OPTIMIZER_V4_AUTHORITY_NOT_ARMED"
CURSOR_KWARG="v5_current_guard_schedule_cursor"

def _cursor(v:object)->int:
    if isinstance(v,bool) or not isinstance(v,int) or v<0:
        raise ValueError("schedule_cursor must be nonnegative int")
    return v

@dataclass
class CurrentOptimizerStepGuardV4:
    optimizer:Any
    receipt:Mapping[str,Any]
    training_authority:CurrentTrainingAuthorityV2
    expected_target_package_root:str
    expected_authority_roots:Mapping[str,str]
    expected_closure_v4_sha256:str

    def __post_init__(self):
        if not isinstance(self.training_authority,CurrentTrainingAuthorityV2):
            raise ValueError("optimizer V4 requires CurrentTrainingAuthorityV2")
        self.training_authority.validate()
        r=validate_current_teacher_target_receipt_v4(
            self.receipt,expected_target_package_root=self.expected_target_package_root,
            expected_authority_roots=self.expected_authority_roots,
            expected_closure_v4_sha256=self.expected_closure_v4_sha256)
        if self.training_authority.receipt_v4_sha256!=r["receipt_digest"]:
            raise ValueError("training authority receipt mismatch")
        if self.training_authority.target_package_root!=r["target_package_root"]:
            raise ValueError("training authority target package mismatch")
        if self.training_authority.closure_v4_sha256!=r["closure_v4_sha256"]:
            raise ValueError("training authority closure mismatch")
        if self.training_authority.preexecution_authority_sha256!=r["authority_roots"]["preexecution_authority_sha256"]:
            raise ValueError("training authority preexecution mismatch")
        self._receipt_digest=r["receipt_digest"]
        self._training_digest=self.training_authority.canonical_digest()
        self._armed=None; self._consumed=None; self._last=None; self._closed=False
        self._pre=self.optimizer.register_step_pre_hook(self._pre_step)
        self._post=self.optimizer.register_step_post_hook(self._post_step)

    def _ensure(self):
        if self._closed: raise RuntimeError(f"{STOP}: guard closed")

    def _assert_unchanged(self):
        self._ensure()
        self.training_authority.validate()
        r=validate_current_teacher_target_receipt_v4(
            self.receipt,expected_target_package_root=self.expected_target_package_root,
            expected_authority_roots=self.expected_authority_roots,
            expected_closure_v4_sha256=self.expected_closure_v4_sha256)
        if r["receipt_digest"]!=self._receipt_digest or self.training_authority.canonical_digest()!=self._training_digest:
            raise RuntimeError(f"{STOP}: authority changed after installation")

    def arm_for_step(self,*,schedule_cursor:int)->dict:
        self._assert_unchanged(); c=_cursor(schedule_cursor)
        if self._armed is not None: raise RuntimeError(f"{STOP}: already armed")
        if self._consumed is not None: raise RuntimeError(f"{STOP}: prior step unacknowledged")
        if self._last is not None and c!=self._last+1:
            raise RuntimeError(f"{STOP}: nonsequential cursor expected {self._last+1} got {c}")
        self._armed=c
        return {"armed":True,"schedule_cursor":c,"step_cursor_kwarg":CURSOR_KWARG,
                "receipt_digest":self._receipt_digest,"training_authority_digest":self._training_digest}

    def disarm_uncompleted_step(self,*,schedule_cursor:int,reason:str)->dict:
        c=_cursor(schedule_cursor)
        if self._armed!=c or self._consumed is not None:
            raise RuntimeError(f"{STOP}: no uncompleted authorization")
        self._armed=None
        return {"disarmed":True,"schedule_cursor":c,"reason":str(reason)}

    def _pre_step(self,optimizer,args,kwargs):
        self._assert_unchanged()
        if optimizer is not self.optimizer: raise RuntimeError(f"{STOP}: optimizer identity mismatch")
        if self._armed is None: raise RuntimeError(f"{STOP}: authority not armed")
        supplied=kwargs.pop(CURSOR_KWARG,None)
        if supplied!=self._armed:
            expected=self._armed; self._armed=None
            raise RuntimeError(f"{STOP}: cursor mismatch expected {expected} observed {supplied}")
        if self._consumed is not None: raise RuntimeError(f"{STOP}: authorization replay")
        self._consumed=self._armed
        return args,kwargs

    def _post_step(self,optimizer,args,kwargs):
        self._ensure()
        if self._consumed is None:
            self._armed=None; raise RuntimeError(f"{STOP}: step without consumed authority")
        self._armed=None

    def assert_step_completed(self,*,schedule_cursor:int)->dict:
        self._ensure(); c=_cursor(schedule_cursor)
        if self._consumed!=c or self._armed is not None:
            raise RuntimeError(f"{STOP}: expected guarded step did not complete")
        self._consumed=None; self._last=c
        return {"guarded_optimizer_step":True,"schedule_cursor":c,
                "receipt_digest":self._receipt_digest,
                "training_authority_digest":self._training_digest}

    def close(self):
        if not self._closed:
            self._pre.remove(); self._post.remove()
            self._armed=None; self._consumed=None; self._closed=True

def install_current_optimizer_guard_v4(optimizer:Any,receipt:Mapping[str,Any],*,
                                       training_authority:CurrentTrainingAuthorityV2,
                                       expected_target_package_root:str,
                                       expected_authority_roots:Mapping[str,str],
                                       expected_closure_v4_sha256:str)->CurrentOptimizerStepGuardV4:
    if not isinstance(training_authority,CurrentTrainingAuthorityV2):
        raise ValueError("optimizer V4 rejects historical training-authority schemas")
    g=CurrentOptimizerStepGuardV4(
        optimizer=optimizer,receipt=receipt,training_authority=training_authority,
        expected_target_package_root=expected_target_package_root,
        expected_authority_roots=expected_authority_roots,
        expected_closure_v4_sha256=expected_closure_v4_sha256)
    existing=getattr(optimizer,"_v5_current_optimizer_guard_v4",None)
    if existing is not None:
        g.close()
        if existing._receipt_digest!=g._receipt_digest or existing._training_digest!=g._training_digest:
            raise RuntimeError(f"{STOP}: installed guard authority mismatch")
        existing._assert_unchanged(); return existing
    setattr(optimizer,"_v5_current_optimizer_guard_v4",g)
    return g
