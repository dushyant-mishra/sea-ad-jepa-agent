from __future__ import annotations

import hashlib
import math
from dataclasses import dataclass
from itertools import combinations
from typing import Mapping

import numpy as np

import td_relational_successor_estimability_v1 as E


class RelationalGateError(ValueError):
    pass


SCALE_GRID = ((1, 8), (1, 6), (1, 4), (1, 3), (1, 2))
SCALE_LABELS = tuple(f"{a}/{b}" for a, b in SCALE_GRID)
MIN_NEIGHBORS = 5
MIN_SOURCE_DONORS = 5
MIN_RESOLVED_RELATIONS_PER_DONOR = 20
TRIPLET_CAP_PER_STRATUM = 64
N_NULL = 64
NULL_P95_INDEX = 60

_AUTHORITY = {
    "target_selection_authorized": False,
    "td60_authorized": False,
    "stage4_authorized": False,
    "training_authorized": False,
}


@dataclass(frozen=True)
class ScaleResult:
    scale_label: str
    numerator: int
    denominator: int
    status: str
    reason: str
    observed_statistic: float | None
    family_null_p95: float | None
    n_observed_donors: int
    observed_donor_agreements: dict[str, float]
    observed_resolved_relations: dict[str, int]
    null_source_statistics: tuple[float | None, ...]
    n_sampled_triplets: int
    eligible_donors: tuple[str, ...]


@dataclass(frozen=True)
class RelationalProfileReceipt:
    source: str
    panel_id: str
    profile_id: str
    scale_results: dict[str, ScaleResult]
    characterization: tuple[str, ...]
    focal_anchor_count: int
    failure_scope: str
    authority: dict[str, bool]


@dataclass(frozen=True)
class RareIncrementScaleResult:
    scale_label: str
    status: str
    reason: str
    program_margin: float | None
    max_control_margin: float | None


@dataclass(frozen=True)
class RareIncrementReceipt:
    source: str
    panel_id: str
    program_profile_id: str
    scale_results: dict[str, RareIncrementScaleResult]
    failure_scope: str
    authority: dict[str, bool]


def _as_square(name: str, value, n: int | None = None) -> np.ndarray:
    arr = np.asarray(value, dtype=float)
    if arr.ndim != 2 or arr.shape[0] != arr.shape[1]:
        raise RelationalGateError(f"{name} must be square")
    if n is not None and arr.shape != (n, n):
        raise RelationalGateError(f"{name} shape mismatch")
    return arr


def _validate_inputs(*, z_distances, x_distances, y_distances, donor_ids, operator_ids, global_rows,
                     focal_mask, neighbor_pool_mask, null_y_identity_maps):
    donors = np.asarray(donor_ids, dtype=object)
    operators = np.asarray(operator_ids, dtype=object)
    rows = np.asarray(global_rows)
    focal = np.asarray(focal_mask, dtype=bool)
    pool = np.asarray(neighbor_pool_mask, dtype=bool)
    n = len(donors)
    if n == 0:
        raise RelationalGateError("empty profile")
    if any(len(v) != n for v in (operators, rows, focal, pool)):
        raise RelationalGateError("cell-vector length mismatch")
    if len(set(rows.tolist())) != n:
        raise RelationalGateError("global_rows must be unique")
    if np.any(focal & ~pool):
        raise RelationalGateError("focal anchors must belong to the lawful neighbor pool")
    z = _as_square("z_distances", z_distances, n)
    x = _as_square("x_distances", x_distances, n)
    y = _as_square("y_distances", y_distances, n)
    maps = np.asarray(null_y_identity_maps)
    if maps.shape != (N_NULL, n):
        raise RelationalGateError(f"exactly {N_NULL} null Y identity maps are required")
    target = np.arange(n)
    for q, m in enumerate(maps):
        if not np.issubdtype(m.dtype, np.integer):
            raise RelationalGateError(f"null map {q} must contain integer indices")
        if not np.array_equal(np.sort(m), target):
            raise RelationalGateError(f"null map {q} must be a full identity permutation")
        if np.any(donors[m] != donors) or np.any(operators[m] != operators):
            raise RelationalGateError(f"null map {q} violates donor/operator matched reassignment")
    return z, x, y, donors, operators, rows.astype(np.int64), focal, pool, maps.astype(np.int64)


def _triplet_digest(source: str, panel_id: str, donor: str, operator: str, rows: tuple[int, int, int]) -> bytes:
    a, b, c = rows
    pre = f"TD316|triplet|source|{source}|panel|{panel_id}|donor|{donor}|operator|{operator}|anchor|{a}|j|{b}|k|{c}"
    return hashlib.sha256(pre.encode("utf-8")).digest()


def _sample_triplets(triplets, *, source: str, panel_id: str, donor: str, operator: str, global_rows: np.ndarray):
    if len(triplets) <= TRIPLET_CAP_PER_STRATUM:
        return triplets
    ranked=[]
    for t in triplets:
        i,j,k=t
        rr=(int(global_rows[i]), int(global_rows[j]), int(global_rows[k]))
        ranked.append((_triplet_digest(source,panel_id,str(donor),str(operator),rr), rr, t))
    ranked.sort(key=lambda x:(x[0],x[1]))
    return [t for _,_,t in ranked[:TRIPLET_CAP_PER_STRATUM]]


def _order_sign(a: float, b: float) -> int | None:
    if not np.isfinite(a) or not np.isfinite(b) or a == b:
        return None
    return 1 if a > b else -1


def _median(values) -> float:
    return float(np.median(np.asarray(list(values), dtype=float)))


def _build_scale_population(*, source, panel_id, scale, z, donors, operators, rows, focal, pool,
                            min_focal_anchors_per_donor):
    num, den = scale
    neighbor_counts_by_donor = {str(d): [] for d in dict.fromkeys(donors.tolist())}
    by_donor: dict[str, list[tuple[int,int,int]]] = {str(d): [] for d in dict.fromkeys(donors.tolist())}
    seen=[]
    for d,o in zip(donors.tolist(),operators.tolist()):
        key=(str(d),str(o))
        if key not in seen: seen.append(key)
    for d,o in seen:
        stratum=np.where((donors.astype(str)==d)&(operators.astype(str)==o)&pool)[0]
        anchors=[int(i) for i in stratum if focal[i]]
        all_triplets=[]
        for i in anchors:
            candidates=[]
            for j in stratum:
                if j==i: continue
                dz=z[i,j]
                if np.isfinite(dz): candidates.append((float(dz), int(rows[j]), int(j)))
            candidates.sort(key=lambda v:(v[0],v[1]))
            m=len(candidates)
            k=math.ceil(m*num/den) if m else 0
            neighbor_counts_by_donor[d].append(k)
            if k < MIN_NEIGHBORS:
                continue
            selected=[j for _,_,j in candidates[:k]]
            for j,kidx in combinations(selected,2):
                if rows[j] <= rows[kidx]: all_triplets.append((i,j,kidx))
                else: all_triplets.append((i,kidx,j))
        sampled=_sample_triplets(all_triplets,source=source,panel_id=panel_id,donor=d,operator=o,global_rows=rows)
        by_donor[d].extend(sampled)
    estim=E.assess_relational_stratum_estimability(
        neighbor_counts_by_donor=neighbor_counts_by_donor,
        min_neighbors=MIN_NEIGHBORS,
        min_recurring_donors=MIN_SOURCE_DONORS,
        min_estimable_focal_cells_per_donor=min_focal_anchors_per_donor,
    )
    eligible=set(estim.eligible_donors)
    by_donor={d:ts for d,ts in by_donor.items() if d in eligible}
    total_sampled=sum(len(v) for v in by_donor.values())
    return estim, by_donor, total_sampled


def _donor_observed(triplets, x, y):
    resolved=0; agree=0
    for i,j,k in triplets:
        qx=_order_sign(x[i,j],x[i,k])
        if qx is None: continue
        qy=_order_sign(y[i,j],y[i,k])
        if qy is None: continue
        resolved += 1
        agree += int(qx==qy)
    return (float(agree/resolved) if resolved>=MIN_RESOLVED_RELATIONS_PER_DONOR else None, resolved)


def _donor_null(triplets, x, y, mapping):
    resolved=0; agree=0
    for i,j,k in triplets:
        qx=_order_sign(x[i,j],x[i,k])
        if qx is None: continue
        mi,mj,mk=int(mapping[i]),int(mapping[j]),int(mapping[k])
        qy=_order_sign(y[mi,mj],y[mi,mk])
        if qy is None: continue
        resolved += 1
        agree += int(qx==qy)
    return float(agree/resolved) if resolved>=MIN_RESOLVED_RELATIONS_PER_DONOR else None


def evaluate_relational_profile(*, source: str, panel_id: str, profile_id: str, z_distances, x_distances,
                                y_distances, donor_ids, operator_ids, global_rows, focal_mask,
                                neighbor_pool_mask, null_y_identity_maps, min_focal_anchors_per_donor: int) -> RelationalProfileReceipt:
    if not all(isinstance(v,str) and v for v in (source,panel_id,profile_id)):
        raise RelationalGateError("source, panel_id and profile_id must be nonempty strings")
    if not isinstance(min_focal_anchors_per_donor,int) or isinstance(min_focal_anchors_per_donor,bool) or min_focal_anchors_per_donor<1:
        raise RelationalGateError("min_focal_anchors_per_donor must be a positive integer")
    z,x,y,donors,operators,rows,focal,pool,maps=_validate_inputs(
        z_distances=z_distances,x_distances=x_distances,y_distances=y_distances,donor_ids=donor_ids,
        operator_ids=operator_ids,global_rows=global_rows,focal_mask=focal_mask,neighbor_pool_mask=neighbor_pool_mask,
        null_y_identity_maps=null_y_identity_maps,
    )
    work={}
    for scale in SCALE_GRID:
        label=f"{scale[0]}/{scale[1]}"
        estim, by_donor, ntrip=_build_scale_population(
            source=source,panel_id=panel_id,scale=scale,z=z,donors=donors,operators=operators,rows=rows,
            focal=focal,pool=pool,min_focal_anchors_per_donor=min_focal_anchors_per_donor,
        )
        observed={}; resolved={}
        for d,triplets in by_donor.items():
            val,nres=_donor_observed(triplets,x,y)
            resolved[d]=nres
            if val is not None: observed[d]=val
        obs_stat=_median(observed.values()) if len(observed)>=MIN_SOURCE_DONORS else None
        null_stats=[]
        for q in range(N_NULL):
            vals=[]
            for d,triplets in by_donor.items():
                val=_donor_null(triplets,x,y,maps[q])
                if val is not None: vals.append(val)
            null_stats.append(_median(vals) if len(vals)>=MIN_SOURCE_DONORS else None)
        work[label]=dict(scale=scale,estim=estim,ntrip=ntrip,observed=observed,resolved=resolved,
                         obs_stat=obs_stat,null_stats=null_stats)
    family=[label for label,w in work.items() if w['obs_stat'] is not None and all(v is not None for v in w['null_stats'])]
    family_p95=None
    if family:
        maxima=[]
        for q in range(N_NULL):
            maxima.append(max(float(work[label]['null_stats'][q]) for label in family))
        maxima.sort()
        family_p95=float(maxima[NULL_P95_INDEX])
    results={}
    for label in SCALE_LABELS:
        w=work[label]; num,den=w['scale']
        if w['obs_stat'] is None:
            status='NOT_ESTIMABLE'; reason='INSUFFICIENT_SUPPORT'
        elif not all(v is not None for v in w['null_stats']):
            status='NOT_ESTIMABLE'; reason='INCOMPLETE_MATCHED_NULL_SUPPORT'
        else:
            assert family_p95 is not None
            status='PASS' if (w['obs_stat']>0.5 and w['obs_stat']>family_p95) else 'FAIL'
            reason='RELATION_ESTABLISHED' if status=='PASS' else 'RELATION_NOT_ESTABLISHED'
        results[label]=ScaleResult(
            scale_label=label,numerator=num,denominator=den,status=status,reason=reason,
            observed_statistic=w['obs_stat'],family_null_p95=family_p95 if label in family else None,
            n_observed_donors=len(w['observed']),observed_donor_agreements=dict(w['observed']),
            observed_resolved_relations=dict(w['resolved']),null_source_statistics=tuple(w['null_stats']),
            n_sampled_triplets=w['ntrip'],eligible_donors=tuple(w['estim'].eligible_donors),
        )
    estimable=[r for r in results.values() if r.status in {'PASS','FAIL'}]
    chars=[]
    if any(r.status=='PASS' and (r.numerator/r.denominator)<=1/3 for r in results.values()):
        chars.append('FINE_SCALE_RELATION_ESTABLISHED')
    if results['1/2'].status=='PASS': chars.append('MESOSCALE_RELATION_ESTABLISHED')
    if any(r.status=='PASS' for r in estimable) and any(r.status=='FAIL' for r in estimable):
        chars.append('SCALE_DEPENDENT_RELATION_ESTABLISHED')
    if estimable and all(r.status=='FAIL' for r in estimable): chars.append('NO_RELATION_ESTABLISHED')
    if not estimable: chars.append('NOT_ESTIMABLE')
    return RelationalProfileReceipt(
        source=source,panel_id=panel_id,profile_id=profile_id,scale_results=results,
        characterization=tuple(chars),focal_anchor_count=int(focal.sum()),
        failure_scope='SCALE_SPECIFIC_RELATIONAL_CLAIM_ONLY',authority=dict(_AUTHORITY),
    )


def _margin(result: ScaleResult) -> float | None:
    if result.observed_statistic is None or result.family_null_p95 is None:
        return None
    return float(result.observed_statistic - max(0.5, result.family_null_p95))


def adjudicate_rare_increment(program: RelationalProfileReceipt,
                              controls: Mapping[str, RelationalProfileReceipt]) -> RareIncrementReceipt:
    if not controls:
        raise RelationalGateError("at least one matched control is required")
    for name,control in controls.items():
        if control.source!=program.source or control.panel_id!=program.panel_id:
            raise RelationalGateError(f"control source/panel mismatch: {name}")
        if tuple(control.scale_results)!=tuple(program.scale_results):
            raise RelationalGateError(f"control scale grid mismatch: {name}")
    out={}
    for label,p in program.scale_results.items():
        if p.status=='NOT_ESTIMABLE':
            out[label]=RareIncrementScaleResult(label,'NOT_ESTIMABLE','PROGRAM_NOT_ESTIMABLE',None,None); continue
        cvals=[c.scale_results[label] for c in controls.values()]
        if any(c.status=='NOT_ESTIMABLE' for c in cvals):
            out[label]=RareIncrementScaleResult(label,'NOT_ESTIMABLE','CONTROL_NOT_ESTIMABLE',_margin(p),None); continue
        pm=_margin(p)
        cms=[_margin(c) for c in cvals]
        if p.status!='PASS' or pm is None:
            out[label]=RareIncrementScaleResult(label,'FAIL','PROGRAM_SCALE_NOT_ESTABLISHED',pm,max(v for v in cms if v is not None)); continue
        maxc=max(v for v in cms if v is not None)
        if pm>maxc:
            out[label]=RareIncrementScaleResult(label,'PASS','RARE_RELATIONAL_INCREMENT_ESTABLISHED',pm,maxc)
        else:
            out[label]=RareIncrementScaleResult(label,'FAIL','CONTROL_MATCHES_OR_EXCEEDS_PROGRAM',pm,maxc)
    return RareIncrementReceipt(program.source,program.panel_id,program.profile_id,out,'RARE_RELATIONAL_INCREMENT_ONLY',dict(_AUTHORITY))
