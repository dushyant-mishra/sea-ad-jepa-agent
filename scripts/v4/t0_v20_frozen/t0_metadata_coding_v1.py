from __future__ import annotations
from typing import Iterable
import numpy as np


def encode_binary_utf8(labels: Iterable[object]) -> tuple[np.ndarray, dict[str, int]]:
    vals=list(labels)
    if not vals:
        raise ValueError('labels must be nonempty')
    out=[]
    for x in vals:
        if x is None:
            raise ValueError('missing category')
        if isinstance(x,float) and np.isnan(x):
            raise ValueError('missing category')
        s=str(x)
        if not s:
            raise ValueError('empty category')
        out.append(s)
    cats=sorted(set(out),key=lambda s:s.encode('utf-8'))
    if len(cats)!=2:
        raise ValueError('exactly two complete canonical categories required')
    mapping={cats[0]:0,cats[1]:1}
    encoded=np.asarray([mapping[s] for s in out],dtype=np.float64)
    return encoded,mapping
