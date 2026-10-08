"""Exact, outcome-blind maximum disjoint four-gene panel capacity.

Given four pools of eligible gene addresses, computes maximum K such that K
fully disjoint four-gene panels can be assembled, using one gene from each
slot per panel and NO reuse anywhere. An exact Hall bound, not a greedy claim.

No expression or readout data; pools must be independently frozen / sanitized.
A strong SUFFICIENT criterion: a low disjoint bound does not prove that 199
partially overlapping panels are impossible or that any panel is exchangeable.
"""
from __future__ import annotations
import argparse, csv, itertools, json
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching


def exact_disjoint_capacity(pools, capped_at=None):
    """Return exact Hall maximum and the blocking subset.

    Clone each slot K times and connect every clone to that slot's gene pool.
    Hall's condition reduces to |union_{i in S}(pool_i)| >= K * |S| for
    each of the 2**n_slots - 1 nonempty subsets S. Taking all K clones of
    any represented slot maximizes demand without changing its neighbors.
    Hence K_max = min_S floor(|union(S)|/|S|). No outcome or RNG needed.
    """
    if len(pools) != 4:
        raise ValueError('exactly four frozen partner slots required')
    ps=[]
    for i,p in enumerate(pools):
        if not all(isinstance(g, (int, np.integer)) and not isinstance(g, (bool, np.bool_)) for g in p):
            raise TypeError(f'pool[{i}]: gene addresses must be integer IDs')
        s=set(map(int,p))
        if min(s,default=0) < 0:
            raise ValueError('negative gene address')
        ps.append(s)
    rows=[]
    for r in range(1,5):
        for ids in itertools.combinations(range(4),r):
            u=set().union(*(ps[i] for i in ids))
            rows.append({'slots':list(ids),'slots_n':r,'union_n':len(u),
                         'capacity':len(u)//r})
    limiting=min(rows,key=lambda d:(d['capacity'],len(d['slots']),d['slots']))
    exact=int(limiting['capacity'])
    return {'max_exact_disjoint_panels':exact,'capacity_at_requested':(
         min(exact,capped_at) if capped_at is not None else exact),
         'requested_achievable':(exact>=capped_at if capped_at is not None else None),
         'limiting_subset':limiting,'all_hall_bounds':rows,
         'unique_gene_pool_n':len(set().union(*ps)),
         'per_slot_pool_n':[len(s) for s in ps],
         'null_validity':'NOT_ASSESSED: this is combinatorial feasibility only'}


def witness_allocation(pools, k, max_edges=15_000_000):
    """Construct a deterministic concrete K-disjoint roster via sparse matching.

    Computational guard prevents allocation over huge full-universe all-edge
    rosters; refusal never redefines mathematical infeasibility.
    """
    ps=[sorted(set(map(int,p))) for p in pools]
    if not (isinstance(k,int) and not isinstance(k,bool) and k>=0):
        raise ValueError('k must be a nonnegative integer')
    cap=exact_disjoint_capacity(ps)
    if k>cap['max_exact_disjoint_panels']:
        raise ValueError('mathematically infeasible; see Hall subset')
    if k==0:
        return {'n_panels':0,'panels':[],'method':'Hall + sparse matching'}
    edge_n=k*sum(map(len,ps))
    if edge_n>max_edges:
        raise MemoryError(f'requires {edge_n} edges > limit {max_edges}; theoretical feasibility still determined')
    genes=sorted(set().union(*(set(p) for p in ps)))
    gene_idx={g:i for i,g in enumerate(genes)}
    i_arr=np.concatenate([np.repeat(np.arange(slot*k,(slot+1)*k,dtype=np.int32),len(p))
                          for slot,p in enumerate(ps)])
    # Above rows are emitted clone-major, columns must be clone-major too.
    c_arr=np.concatenate([np.tile(np.asarray([gene_idx[g] for g in p],dtype=np.int32),k)
                          for p in ps])
    graph=csr_matrix((np.ones(len(c_arr),dtype=np.int8),(i_arr,c_arr)),
                     shape=(4*k,len(genes)))
    matches=maximum_bipartite_matching(graph,perm_type='column')
    if np.any(matches<0) or len(matches)!=4*k:
        raise AssertionError('Hall says feasible but matching failed')
    out=[tuple(int(genes[int(matches[slot*k+j])]) for slot in range(4))
         for j in range(k)]
    if len(set(g for quad in out for g in quad))!=4*k:
        raise AssertionError('a gene was reused in a supposedly disjoint roster')
    for slot in range(4):
        assert all(quad[slot] in set(ps[slot]) for quad in out)
    return {'n_panels':k,'panels':out,'method':'Hall + scipy sparse bipartite matching',
            'edges':int(edge_n)}


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('pools_json');ap.add_argument('--k',type=int,default=199)
    ap.add_argument('--allocation',action='store_true');p=ap.parse_args()
    with open(p.pools_json) as f:ps=json.load(f)
    cap=exact_disjoint_capacity(ps,p.k)
    if p.allocation and cap['requested_achievable']:
        cap['allocation']=witness_allocation(ps,p.k)
    print(json.dumps(cap,indent=2))
