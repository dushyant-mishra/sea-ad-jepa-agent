"""Resident optimizer guard bound only to the exact current-V5 target receipt."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Mapping
from .current_teacher_target_receipt_v1 import validate_current_teacher_target_receipt_v1

STOP='STOP_V5_CURRENT_OPTIMIZER_AUTHORITY_NOT_ARMED'
CURSOR_KWARG='v5_current_guard_schedule_cursor'

def _cursor(v:object)->int:
    if isinstance(v,bool) or not isinstance(v,int) or v<0: raise ValueError('schedule_cursor must be a nonnegative integer')
    return v

@dataclass
class CurrentOptimizerStepGuard:
    optimizer: Any
    receipt: Mapping[str,Any]
    expected_target_package_root: str
    expected_authority_roots: Mapping[str,str]
    def __post_init__(self)->None:
        verified=validate_current_teacher_target_receipt_v1(self.receipt,expected_target_package_root=self.expected_target_package_root,expected_authority_roots=self.expected_authority_roots)
        self._receipt_digest=verified['receipt_digest']; self._target_package_root=verified['target_package_root']
        self._armed_cursor=None; self._consumed_cursor=None; self._closed=False
        self._pre_handle=self.optimizer.register_step_pre_hook(self._pre_step)
        self._post_handle=self.optimizer.register_step_post_hook(self._post_step)
    @property
    def receipt_digest(self)->str: return self._receipt_digest
    @property
    def target_package_root(self)->str: return self._target_package_root
    @property
    def is_armed(self)->bool: return self._armed_cursor is not None
    def _ensure_open(self)->None:
        if self._closed: raise RuntimeError(f'{STOP}: guard has been closed')
    def _assert_receipt_unchanged(self)->None:
        try:
            current=validate_current_teacher_target_receipt_v1(self.receipt,expected_target_package_root=self.expected_target_package_root,expected_authority_roots=self.expected_authority_roots)
        except Exception as exc:
            raise RuntimeError(f'{STOP}: receipt is no longer valid') from exc
        if current['receipt_digest']!=self._receipt_digest: raise RuntimeError(f'{STOP}: receipt changed after guard installation')
    def arm_for_step(self,*,schedule_cursor:int)->dict[str,Any]:
        self._ensure_open(); self._assert_receipt_unchanged(); cursor=_cursor(schedule_cursor)
        if self._armed_cursor is not None: raise RuntimeError(f'{STOP}: guard is already armed')
        self._armed_cursor=cursor; self._consumed_cursor=None
        return {'armed':True,'schedule_cursor':cursor,'step_cursor_kwarg':CURSOR_KWARG,'target_receipt_digest':self._receipt_digest}
    def disarm_uncompleted_step(self,*,schedule_cursor:int,reason:str)->dict[str,Any]:
        cursor=_cursor(schedule_cursor)
        if self._armed_cursor!=cursor or self._consumed_cursor is not None: raise RuntimeError(f'{STOP}: no uncompleted authorization for cursor {cursor}')
        self._armed_cursor=None
        return {'disarmed':True,'schedule_cursor':cursor,'reason':str(reason)}
    def _pre_step(self,optimizer:Any,args:tuple[Any,...],kwargs:dict[str,Any]):
        self._ensure_open(); self._assert_receipt_unchanged()
        if optimizer is not self.optimizer: self._armed_cursor=None; raise RuntimeError(f'{STOP}: optimizer identity mismatch')
        if self._armed_cursor is None: raise RuntimeError(f'{STOP}: current target receipt was not armed for this optimizer step')
        supplied=kwargs.pop(CURSOR_KWARG,None)
        if supplied!=self._armed_cursor:
            expected=self._armed_cursor; self._armed_cursor=None
            raise RuntimeError(f'{STOP}: schedule cursor mismatch expected {expected} observed {supplied}')
        if self._consumed_cursor is not None: self._armed_cursor=None; raise RuntimeError(f'{STOP}: authorization already consumed')
        self._consumed_cursor=self._armed_cursor
        return args,kwargs
    def _post_step(self,optimizer:Any,args:tuple[Any,...],kwargs:dict[str,Any])->None:
        self._ensure_open()
        if self._consumed_cursor is None: self._armed_cursor=None; raise RuntimeError(f'{STOP}: optimizer stepped without consuming authorization')
        self._armed_cursor=None
    def assert_step_completed(self,*,schedule_cursor:int)->dict[str,Any]:
        cursor=_cursor(schedule_cursor)
        if self._consumed_cursor!=cursor or self._armed_cursor is not None: raise RuntimeError(f'{STOP}: expected guarded optimizer step did not complete')
        return {'guarded_optimizer_step':True,'schedule_cursor':cursor,'target_receipt_digest':self._receipt_digest,'target_package_root':self._target_package_root}
    def close(self)->None:
        if self._closed: return
        self._pre_handle.remove(); self._post_handle.remove(); self._armed_cursor=None; self._closed=True

def install_current_optimizer_guard(optimizer:Any,receipt:Mapping[str,Any],*,expected_target_package_root:str,expected_authority_roots:Mapping[str,str])->CurrentOptimizerStepGuard:
    verified=validate_current_teacher_target_receipt_v1(receipt,expected_target_package_root=expected_target_package_root,expected_authority_roots=expected_authority_roots)
    existing=getattr(optimizer,'_v5_current_optimizer_guard',None)
    if existing is not None:
        if existing.receipt_digest!=verified['receipt_digest']: raise RuntimeError(f'{STOP}: installed guard receipt mismatch')
        existing._assert_receipt_unchanged(); return existing
    guard=CurrentOptimizerStepGuard(optimizer,receipt,expected_target_package_root,expected_authority_roots)
    setattr(optimizer,'_v5_current_optimizer_guard',guard); return guard
