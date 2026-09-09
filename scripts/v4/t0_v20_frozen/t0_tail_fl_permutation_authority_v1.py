from __future__ import annotations
import hashlib,struct
import numpy as np
from t0_fl_permutation_authority_v1 import permutation

TAIL_PERMUTATIONS=9999
TAIL_ALLOWED_N={17,18}
NAMESPACE=b'T0-TAIL-FL-PERM-V1'


def tail_permutation_matrix(donors:list[str]) -> np.ndarray:
    if len(donors) not in TAIL_ALLOWED_N or len(set(donors))!=len(donors) or any(not isinstance(d,str) or not d for d in donors):
        raise ValueError('tail inference authority requires exactly 17 or 18 unique nonempty donors')
    base=sorted(donors,key=lambda d:d.encode('utf-8'))
    return np.asarray([permutation(base,r,namespace=NAMESPACE) for r in range(TAIL_PERMUTATIONS)],dtype=np.int16)


def tail_permutation_set_digest(donors:list[str]) -> str:
    mat=tail_permutation_matrix(donors); h=hashlib.sha256()
    for r,p in enumerate(mat):
        h.update(struct.pack('>I',r)); h.update(struct.pack('>H',len(p)))
        for i in p: h.update(struct.pack('>H',int(i)))
    return h.hexdigest()
