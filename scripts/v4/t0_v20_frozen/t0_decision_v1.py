#!/usr/bin/env python3
"""Fail-closed three-valued T0 decision logic."""
from __future__ import annotations
import math

STATE_POS_ALPHA=.025
TAIL_POS_ALPHA=.020
NEG_ALPHA=.005
SENS_ALPHA=.05
# Backward-compatible state alias for non-tail callers.
POS_ALPHA=STATE_POS_ALPHA


def _validate_result(r):
    if not isinstance(r,dict):
        raise ValueError('result must be a dict')
    estimable=r.get('estimable',False)
    if not isinstance(estimable,bool):
        raise ValueError('estimable must be boolean')
    if not estimable:
        return False
    for k in ('beta','p_upper','p_lower'):
        if k not in r:
            raise ValueError(f'missing {k}')
        v=float(r[k])
        if not math.isfinite(v):
            raise ValueError(f'nonfinite {k}')
    pu=float(r['p_upper']); pl=float(r['p_lower'])
    if not (0.0<=pu<=1.0 and 0.0<=pl<=1.0):
        raise ValueError('p-values must lie in [0,1]')
    return True


def _pos(r,alpha):
    return _validate_result(r) and float(r['beta'])>0 and float(r['p_upper'])<=alpha


def _neg(r,alpha):
    return _validate_result(r) and float(r['beta'])<0 and float(r['p_lower'])<=alpha


def _strict_bool(name,x):
    if type(x) is not bool:
        raise ValueError(f'{name} must be bool')
    return x


def decide_state(primary, composition, measurements):
    if not isinstance(measurements,list) or len(measurements)==0:
        raise ValueError('mandatory measurement sensitivities must be explicit/nonempty')
    if not _validate_result(primary):
        return 'TARGET_UNDERDETERMINED_INTERNAL'
    if _pos(primary,STATE_POS_ALPHA):
        if not _pos(composition,SENS_ALPHA):
            return 'BROAD_IMMUNE_EXPRESSION_TARGET_UNDERDETERMINED_COMPOSITION'
        if not all(_pos(x,SENS_ALPHA) for x in measurements):
            return 'BROAD_IMMUNE_EXPRESSION_TARGET_UNDERDETERMINED_MEASUREMENT'
        return 'BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL'
    if _neg(primary,NEG_ALPHA):
        if not _neg(composition,SENS_ALPHA):
            return 'BROAD_IMMUNE_EXPRESSION_TARGET_UNDERDETERMINED_COMPOSITION'
        if not all(_neg(x,SENS_ALPHA) for x in measurements):
            return 'BROAD_IMMUNE_EXPRESSION_TARGET_UNDERDETERMINED_MEASUREMENT'
        return 'BROAD_IMMUNE_LINEAR_TARGET_DISQUALIFIED_INTERNAL'
    return 'TARGET_UNDERDETERMINED_INTERNAL'


def decide_tail(parent_state_terminal, primary_tail, composition, measurements, support_ok, coherence_ok, qc_ok):
    if not isinstance(measurements,list) or len(measurements)==0:
        raise ValueError('mandatory tail measurement sensitivities must be explicit/nonempty')
    support_ok=_strict_bool('support_ok',support_ok)
    coherence_ok=_strict_bool('coherence_ok',coherence_ok)
    qc_ok=_strict_bool('qc_ok',qc_ok)
    if parent_state_terminal!='BROAD_IMMUNE_EXPRESSION_TARGET_SUPPORTED_INTERNAL':
        return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
    if not _validate_result(primary_tail):
        return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
    if _pos(primary_tail,TAIL_POS_ALPHA):
        if not support_ok or not coherence_ok:
            return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
        if not qc_ok:
            return 'RARE_TAIL_UNDERDETERMINED_MEASUREMENT'
        if not _pos(composition,SENS_ALPHA):
            return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
        if not all(_pos(x,SENS_ALPHA) for x in measurements):
            return 'RARE_TAIL_UNDERDETERMINED_MEASUREMENT'
        return 'RARE_TAIL_EXPRESSION_TARGET_SUPPORTED_INTERNAL'
    if _neg(primary_tail,NEG_ALPHA):
        if not support_ok or not coherence_ok:
            return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
        if not qc_ok:
            return 'RARE_TAIL_UNDERDETERMINED_MEASUREMENT'
        if not _neg(composition,SENS_ALPHA):
            return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
        if not all(_neg(x,SENS_ALPHA) for x in measurements):
            return 'RARE_TAIL_UNDERDETERMINED_MEASUREMENT'
        return 'RARE_TAIL_EXPRESSION_TARGET_DISQUALIFIED_INTERNAL'
    return 'RARE_TAIL_UNDERDETERMINED_INTERNAL'
