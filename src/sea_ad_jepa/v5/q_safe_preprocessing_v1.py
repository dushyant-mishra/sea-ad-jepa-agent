"""q-safe count preprocessing primitives for current V5 target/student paths.

These functions operate on raw counts plus explicit observation state. They are
implementation primitives only; using them does not itself establish a
production q-intervention pass.
"""
from __future__ import annotations
import numpy as np

MEASURED_SCALAR = np.uint8(1)

def _validate(counts, states, q_index):
    counts=np.asarray(counts)
    states=np.asarray(states)
    if counts.ndim!=2 or states.shape!=counts.shape: raise ValueError("counts/states must be same-shape 2D arrays")
    if not np.issubdtype(counts.dtype,np.number) or np.any(counts<0): raise ValueError("counts must be nonnegative numeric")
    if isinstance(q_index,bool) or not isinstance(q_index,(int,np.integer)) or not 0<=int(q_index)<counts.shape[1]: raise ValueError("q_index out of range")
    return counts.astype(np.float64,copy=False),states,int(q_index)

def q_excluded_detected_count(counts, states, q_index):
    counts,states,q=_validate(counts,states,q_index)
    present=(counts>0)&(states==MEASURED_SCALAR)
    present[:,q]=False
    return present.sum(1).astype(np.int64)

def normalize_q_excluded_total(counts, states, source_library, q_index, scale=10_000.0):
    """Normalize with denominator source_library - raw_q, then drop q token."""
    counts,states,q=_validate(counts,states,q_index)
    source_library=np.asarray(source_library,dtype=np.float64)
    if source_library.shape!=(counts.shape[0],): raise ValueError("source_library shape mismatch")
    q_raw=counts[:,q]
    denom=source_library-q_raw
    if np.any(denom<=0): raise ValueError("q-excluded denominator must be positive")
    out=np.zeros_like(counts,dtype=np.float32)
    measured=states==MEASURED_SCALAR
    scaled=np.divide(counts*float(scale),denom[:,None],out=np.zeros_like(counts),where=measured)
    out[measured]=np.log1p(scaled[measured]).astype(np.float32)
    out[:,q]=0.0
    return out,q_excluded_detected_count(counts,states,q)

def normalize_fixed_reference(counts, states, fixed_reference, q_index, scale=10_000.0):
    """Normalize with a q-independent per-cell reference, then drop q token."""
    counts,states,q=_validate(counts,states,q_index)
    ref=np.asarray(fixed_reference,dtype=np.float64)
    if ref.shape!=(counts.shape[0],) or np.any(ref<=0): raise ValueError("fixed_reference must be positive per cell")
    out=np.zeros_like(counts,dtype=np.float32)
    measured=states==MEASURED_SCALAR
    scaled=np.divide(counts*float(scale),ref[:,None],out=np.zeros_like(counts),where=measured)
    out[measured]=np.log1p(scaled[measured]).astype(np.float32)
    out[:,q]=0.0
    return out,q_excluded_detected_count(counts,states,q)
