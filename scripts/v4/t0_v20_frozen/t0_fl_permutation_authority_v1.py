from __future__ import annotations
import hashlib, struct
import numpy as np

CONFIRMATION_DONORS=18
CONFIRMATION_PERMUTATIONS=9999
NAMESPACE=b'T0-FL-PERM-V1'


def _framed(namespace: bytes, replicate: int, donor: str) -> bytes:
    if replicate < 0 or replicate > 0xffffffff: raise ValueError('replicate out of range')
    if not isinstance(donor,str) or not donor: raise ValueError('donor id must be nonempty string')
    b=donor.encode('utf-8')
    if len(b)>0xffff: raise ValueError('donor id too long')
    return namespace+b'\x00'+struct.pack('>I',replicate)+struct.pack('>H',len(b))+b


def permutation(donors: list[str], replicate: int, namespace: bytes=NAMESPACE) -> list[int]:
    if len(set(donors))!=len(donors) or not donors: raise ValueError('donors must be unique/nonempty')
    keys=[]
    for i,d in enumerate(donors):
        dg=hashlib.sha256(_framed(namespace,replicate,d)).digest()
        keys.append((dg,d.encode('utf-8'),i))
    return [i for _,_,i in sorted(keys)]


def confirmation_permutation_matrix(donors: list[str]) -> np.ndarray:
    if len(donors)!=CONFIRMATION_DONORS or len(set(donors))!=CONFIRMATION_DONORS:
        raise ValueError('confirmation authority requires exactly 18 unique donors')
    base=sorted(donors,key=lambda d:d.encode('utf-8'))
    return np.asarray([permutation(base,r) for r in range(CONFIRMATION_PERMUTATIONS)],dtype=np.int16)


def permutation_set_digest(donors: list[str]) -> str:
    mat=confirmation_permutation_matrix(donors)
    h=hashlib.sha256()
    for r,p in enumerate(mat):
        h.update(struct.pack('>I',r)); h.update(struct.pack('>H',len(p)))
        for i in p: h.update(struct.pack('>H',int(i)))
    return h.hexdigest()
