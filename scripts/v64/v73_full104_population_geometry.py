#!/usr/bin/env python3
from __future__ import annotations
import base64, hashlib, json, math, zlib
from pathlib import Path
import numpy as np

AUTHORITY = Path('results/v64/V73_FULL104_POPULATION_GEOMETRY_AUTHORITY_V1.json')
SOURCE_ORDER = ('SEA_AD','NPH52','HVS')


def sha256_file(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_authority(path: Path = AUTHORITY):
    a=json.loads(path.read_text())
    if a.get('status')!='QUALIFIED_AGGREGATE_POPULATION_AUTHORITY':
        raise ValueError('population authority is not qualified')
    encoded=''.join(Path(p).read_text().strip() for p in a['triplets_payload_parts'])
    compressed=base64.b64decode(encoded)
    if hashlib.sha256(compressed).hexdigest()!=a['triplets_compressed_sha256']:
        raise ValueError('population triplet compressed digest mismatch')
    raw=zlib.decompress(compressed)
    if hashlib.sha256(raw).hexdigest()!=a['triplets_payload_sha256']:
        raise ValueError('population triplet payload digest mismatch')
    trip=np.frombuffer(raw,dtype='<u4').reshape(tuple(a['triplets_shape'])).astype(np.int64)
    if len(trip)!=a['n_groups'] or int(trip[:,2].sum())!=a['n_cells']:
        raise ValueError('population triplet totals do not reconcile')
    return a,trip


def largest_remainder(weights, total):
    w=np.asarray(weights,dtype=np.float64)
    if total<0 or w.ndim!=1 or np.any(w<0) or w.sum()<=0:
        raise ValueError('invalid apportionment inputs')
    raw=w/w.sum()*int(total)
    out=np.floor(raw).astype(np.int64)
    r=int(total-int(out.sum()))
    if r:
        order=np.argsort(-(raw-out),kind='stable')
        out[order[:r]]+=1
    if int(out.sum())!=int(total): raise RuntimeError('apportionment failed')
    return out


def quotas_for_n(n_cells:int, authority_path:Path=AUTHORITY):
    """Apportion empirical FULL104 geometry hierarchically: source -> operator -> joint groups.

    Direct source->group apportionment can erase a small but real operator at stress scale.
    Operator identity is a physical observation axis, so preserve its marginal support first,
    then distribute each operator quota across its observed donor×operator groups. At exact
    FULL104 scale every stage reproduces the frozen counts byte-for-byte numerically.
    """
    a,trip=load_authority(authority_path)
    op_sources=np.asarray(a['operator_sources'])
    full_sources=np.array([a['source_counts'][s] for s in SOURCE_ORDER],dtype=np.int64)
    source_quota=largest_remainder(full_sources,n_cells)
    full_operator=np.asarray(a['operator_counts'],dtype=np.int64)
    quotas=np.zeros(len(trip),dtype=np.int64)

    for si,source in enumerate(SOURCE_ORDER):
        source_ops=np.flatnonzero(op_sources==source)
        if len(source_ops)==0:
            raise RuntimeError(f'no operators for source {source}')
        op_quota=largest_remainder(full_operator[source_ops],int(source_quota[si]))
        if int(source_quota[si])>=len(source_ops) and np.any(op_quota==0):
            # Largest remainder may still give zero to a tiny positive operator. Preserve
            # observed support by moving one cell from the largest donor operator quota.
            zeros=np.flatnonzero(op_quota==0)
            for zi in zeros:
                donors=np.flatnonzero(op_quota>1)
                if len(donors)==0:
                    raise RuntimeError(f'cannot preserve operator support for source {source}')
                take=donors[np.argmax(op_quota[donors])]
                op_quota[take]-=1
                op_quota[zi]=1

        for local_i,op in enumerate(source_ops):
            mask=(trip[:,1]==int(op))
            if not np.any(mask):
                raise RuntimeError(f'operator {op} has no joint groups')
            oq=int(op_quota[local_i])
            if oq==0:
                continue
            quotas[mask]=largest_remainder(trip[mask,2],oq)

    if int(quotas.sum())!=n_cells: raise RuntimeError('group quotas do not sum')
    realised={s:int(quotas[[op_sources[int(op)]==s for op in trip[:,1]]].sum()) for s in SOURCE_ORDER}
    expected={s:int(source_quota[i]) for i,s in enumerate(SOURCE_ORDER)}
    if realised!=expected: raise RuntimeError('source hierarchy did not reconcile')
    operator_realised=np.bincount(trip[:,1],weights=quotas,minlength=a['n_operators']).astype(np.int64)
    if n_cells>=a['n_operators'] and np.any(operator_realised==0):
        raise RuntimeError('operator support was lost despite sufficient total cells')
    return a,trip,quotas


def _coprime_multiplier(n, seed):
    if n==1:return 1
    x=int((2*(seed%1000003)+1)%n) or 1
    while math.gcd(x,n)!=1:
        x+=1
        if x>=n:x=1
    return x


def assignments_for_ids(ids,n_cells,seed,authority_path:Path=AUTHORITY):
    a,trip,quotas=quotas_for_n(n_cells,authority_path)
    ids=np.asarray(ids,dtype=np.int64)
    m=_coprime_multiplier(n_cells,seed+2729); b=(seed*130363+29)%n_cells
    rank=(m*ids+b)%n_cells
    cum=np.cumsum(quotas)
    gi=np.searchsorted(cum,rank,side='right')
    donor=trip[gi,0].astype(np.int16); operator=trip[gi,1].astype(np.int16)
    source_map={s:i for i,s in enumerate(SOURCE_ORDER)}
    source=np.array([source_map[a['operator_sources'][int(x)]] for x in operator],dtype=np.int8)
    return donor,operator,source,a,trip,quotas


def summary_from_quotas(a,trip,quotas):
    donor=np.bincount(trip[:,0],weights=quotas,minlength=a['n_donors']).astype(np.int64)
    operator=np.bincount(trip[:,1],weights=quotas,minlength=a['n_operators']).astype(np.int64)
    def gini(x):
        x=np.sort(np.asarray(x,dtype=np.float64)); n=len(x); s=x.sum()
        return 0.0 if s==0 else float((2*np.sum(np.arange(1,n+1)*x))/(n*s)-(n+1)/n)
    return {
      'donor_count_summary':{'min':int(donor.min()),'max':int(donor.max()),'mean':float(donor.mean()),'gini':gini(donor)},
      'operator_count_summary':{'min':int(operator.min()),'max':int(operator.max()),'mean':float(operator.mean()),'gini':gini(operator)},
      'source_operator_nonzero_cells':int(np.count_nonzero(operator)),
      'nonzero_donor_operator_groups':int(np.count_nonzero(quotas)),
      'donor_counts':donor.tolist(),'operator_counts':operator.tolist()
    }
